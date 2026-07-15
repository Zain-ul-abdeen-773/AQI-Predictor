"""Training pipeline orchestrator.

Coordinates the full ML training workflow:
1. Load training data from Feature Store
2. Prepare features and targets (with leakage prevention)
3. Train all 8 model architectures
4. Evaluate with TimeSeriesSplit cross-validation
5. Compute SHAP explanations
6. Register the best model in the Model Registry
7. Run data drift detection and anomaly detection
8. Generate Grad-CAM heatmaps for LSTM

Example:
    >>> from training_pipeline.train import TrainingOrchestrator
    >>> orchestrator = TrainingOrchestrator()
    >>> results = orchestrator.run()
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from config.settings import get_settings, Settings
from training_pipeline.evaluation import (
    AnomalyDetector,
    DataDriftDetector,
    EvaluationMetrics,
    ModelEvaluator,
)
from training_pipeline.explainability import SHAPExplainer
from training_pipeline.models.baseline import BaselineRegressor
from training_pipeline.models.deep_learning import BiLSTMAttention
from training_pipeline.models.tree_ensemble import LightGBMOptimized
from training_pipeline.models.ensemble_trees import (
    ExtraTreesModel,
    GradientBoostingModel,
    RandomForestModel,
    SVRModel,
)
from training_pipeline.registry import ModelRegistryManager

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Feature columns — Split into categories for leakage control
# ──────────────────────────────────────────────────────────────────────────────

# Raw sensor features (no leakage risk)
RAW_FEATURES: List[str] = [
    "pm25", "pm10", "no2", "so2", "co", "o3",
    "temperature_c", "humidity_pct", "wind_speed_ms", "wind_direction_deg",
    "pressure_hpa", "precipitation_mm",
]

# Temporal features (no leakage risk)
TEMPORAL_FEATURES: List[str] = [
    "hour_sin", "hour_cos", "day_sin", "day_cos", "month_sin", "month_cos",
    "hour", "day_of_week", "day_of_year",
]

# Derived features (no leakage risk)
DERIVED_FEATURES: List[str] = [
    "aqi_change_rate_1h", "aqi_change_rate_3h", "aqi_change_rate_6h",
    "wind_u_component", "wind_v_component",
    "wind_pm25_interaction", "wind_pm10_interaction",
    "temperature_humidity_index", "pollution_intensity",
]

# Lag features — CONTROLLED for leakage prevention
# Removed aqi_lag_1h (too leaky) and kept only longer-horizon lags
# that force the model to learn actual patterns, not just copy recent AQI
LAG_FEATURES: List[str] = [
    "aqi_lag_6h", "aqi_lag_12h", "aqi_lag_24h",
    "pm25_lag_3h",
    "pm25_rolling_mean_6h", "pm25_rolling_std_6h", "pm25_rolling_mean_24h",
]

# Full feature set
FEATURE_COLUMNS: List[str] = (
    RAW_FEATURES + TEMPORAL_FEATURES + DERIVED_FEATURES + LAG_FEATURES
)

TARGET_COLUMN: str = "aqi_value"


class TrainingOrchestrator:
    """Orchestrates the complete model training pipeline.

    Manages data loading, feature preparation, multi-model training,
    evaluation, explainability, and model registration.

    Attributes:
        settings: Application settings.
        evaluator: Model evaluation engine.
        registry: Model registry manager.
        drift_detector: Data drift detection.
        anomaly_detector: Anomaly detection.
    """

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self.evaluator = ModelEvaluator()
        self.registry = ModelRegistryManager(self.settings)
        self.drift_detector = DataDriftDetector()
        self.anomaly_detector = AnomalyDetector()

    def load_training_data(
        self,
        csv_path: Optional[Path] = None,
    ) -> pd.DataFrame:
        """Load training data from Feature Store or CSV.

        Args:
            csv_path: Optional path to CSV file (overrides Feature Store).

        Returns:
            pd.DataFrame: Training data with features and target.
        """
        if csv_path and csv_path.exists():
            df = pd.read_csv(csv_path)
            logger.info("Loaded %d rows from %s", len(df), csv_path)
        else:
            # Try Feature Store
            from feature_pipeline.register import FeatureStoreManager
            fs_manager = FeatureStoreManager(self.settings)
            df = fs_manager.get_training_data()

            if df.empty:
                # Generate synthetic data as fallback
                logger.warning("No training data found — generating synthetic data")
                from data_pipeline.backfill import BackfillPipeline
                pipeline = BackfillPipeline(self.settings)
                df = pipeline.run(years=2, batch_size=5000)

        logger.info("Training data shape: %s", df.shape)
        return df

    def prepare_features(
        self,
        df: pd.DataFrame,
    ) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """Prepare feature matrix and target vector from DataFrame.

        Handles missing values, boolean conversion, and feature selection.
        Deliberately excludes high-leakage features (aqi_lag_1h, aqi_lag_3h)
        to force models to learn generalizable patterns.

        Args:
            df: Raw training DataFrame.

        Returns:
            Tuple of (X, y, feature_names).
        """
        # Filter to available columns
        available_features = [c for c in FEATURE_COLUMNS if c in df.columns]
        missing_features = [c for c in FEATURE_COLUMNS if c not in df.columns]

        if missing_features:
            logger.warning("Missing %d features: %s", len(missing_features), missing_features[:5])

        # Log leakage prevention
        dropped = [f for f in ["aqi_lag_1h", "aqi_lag_3h", "pm25_lag_1h"]
                    if f not in FEATURE_COLUMNS and f in df.columns]
        if dropped:
            logger.info(
                "Leakage prevention: excluded %d short-horizon lags: %s",
                len(dropped), dropped,
            )

        # Drop rows without target
        df = df.dropna(subset=[TARGET_COLUMN])

        # Extract features and target
        X_df = df[available_features].copy()
        y = df[TARGET_COLUMN].values.astype(np.float32)

        # Convert boolean columns
        bool_cols = X_df.select_dtypes(include=["bool"]).columns
        for col in bool_cols:
            X_df[col] = X_df[col].astype(float)

        # Fill NaN values
        X_df = X_df.fillna(0.0)

        X = X_df.values.astype(np.float32)

        logger.info(
            "Prepared features: X=%s, y=%s, %d features",
            X.shape, y.shape, len(available_features),
        )
        return X, y, available_features

    # ── Individual Model Trainers ─────────────────────────────────────────

    def _train_model(
        self,
        name: str,
        model,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        feature_names: List[str],
    ) -> Tuple[Any, EvaluationMetrics]:
        """Generic model training + evaluation.

        Args:
            name: Display name for logging.
            model: Model instance with .fit() and .predict().
            X_train, y_train: Training data.
            X_test, y_test: Test data.
            feature_names: Feature names.

        Returns:
            Tuple of (trained model, evaluation metrics).
        """
        logger.info("=" * 60)
        logger.info("TRAINING: %s", name)
        logger.info("=" * 60)

        model.fit(X_train, y_train, feature_names=feature_names)
        y_pred = model.predict(X_test)
        metrics = self.evaluator.evaluate(y_test, y_pred, model_name=name)

        return model, metrics

    def train_bilstm(
        self,
        X: np.ndarray,
        y: np.ndarray,
        feature_names: List[str],
    ) -> Tuple[BiLSTMAttention, EvaluationMetrics]:
        """Train and evaluate the Bi-LSTM with Attention model.

        Creates sequences from the flat feature matrix and trains
        the sequence-to-sequence model with gradient accumulation
        and cosine annealing scheduler.

        Args:
            X: Full feature matrix.
            y: Full target vector.
            feature_names: Feature name list.

        Returns:
            Tuple of (trained model, evaluation metrics).
        """
        logger.info("=" * 60)
        logger.info("TRAINING: Bi-LSTM with Multi-Head Attention")
        logger.info("=" * 60)

        lookback = self.settings.lookback_window_hours
        horizon = self.settings.forecast_horizon_hours

        # Create sequences
        X_seq, y_seq = BiLSTMAttention.create_sequences(X, y, lookback, horizon)

        if len(X_seq) < 100:
            logger.warning(
                "Insufficient sequences (%d) for LSTM training. "
                "Need at least 100. Skipping LSTM.",
                len(X_seq),
            )
            return None, EvaluationMetrics(rmse=float("inf"), model_name="BiLSTM")

        # Train/val split (temporal — no shuffling)
        split_idx = int(0.8 * len(X_seq))
        X_train_seq, X_val_seq = X_seq[:split_idx], X_seq[split_idx:]
        y_train_seq, y_val_seq = y_seq[:split_idx], y_seq[split_idx:]

        # Checkpoint directory
        checkpoint_dir = self.settings.models_dir / "checkpoints"

        model = BiLSTMAttention(
            input_size=X.shape[1],
            hidden_size=self.settings.lstm_hidden_size,
            num_layers=self.settings.lstm_num_layers,
            dropout=self.settings.lstm_dropout,
            forecast_horizon=horizon,
            accumulation_steps=4,
            scheduler_type="cosine_warm",
        )

        model.fit(
            X_train_seq, y_train_seq,
            X_val_seq, y_val_seq,
            feature_names=feature_names,
            checkpoint_dir=checkpoint_dir,
        )

        # Evaluate on validation sequences
        y_pred = model.predict(X_val_seq)
        metrics = self.evaluator.evaluate(
            y_val_seq.flatten(),
            y_pred.flatten(),
            model_name="BiLSTM",
        )

        # ── Grad-CAM ──
        try:
            from training_pipeline.models.grad_cam import TemporalGradCAM
            import torch

            grad_cam = TemporalGradCAM(model.model)
            sample = torch.FloatTensor(X_val_seq[:16]).to(model.device)
            heatmap, _ = grad_cam.generate(sample)

            # Save heatmap
            heatmap_path = self.settings.models_dir / "grad_cam_heatmap.npy"
            np.save(heatmap_path, heatmap)
            logger.info("Grad-CAM heatmap saved to %s", heatmap_path)

            grad_cam.cleanup()
        except Exception as e:
            logger.warning("Grad-CAM generation failed: %s", e)

        return model, metrics

    def run(
        self,
        csv_path: Optional[Path] = None,
        skip_lstm: bool = False,
        models_to_train: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Execute the complete training pipeline.

        Args:
            csv_path: Optional path to training CSV.
            skip_lstm: Whether to skip LSTM training.
            models_to_train: Specific models to train (None = all).

        Returns:
            Dict with training results, metrics, and champion info.
        """
        logger.info("=" * 60)
        logger.info("PEARLS AQI PREDICTOR — TRAINING PIPELINE (8 MODELS)")
        logger.info("=" * 60)

        # ── 1. Load Data ──
        df = self.load_training_data(csv_path)
        X, y, feature_names = self.prepare_features(df)

        # ── 2. Train/Test Split (temporal) ──
        split_idx = int(0.8 * len(X))
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]

        logger.info("Split: train=%d, test=%d", len(X_train), len(X_test))

        # ── 3. Anomaly Detection ──
        self.anomaly_detector.fit(X_train)
        anomalies = self.anomaly_detector.detect(X_test, feature_names)
        anomaly_count = sum(1 for a in anomalies if a["is_anomaly"])

        # ── 4. Data Drift Detection ──
        drift_results = self.drift_detector.detect_drift(X_train, X_test, feature_names)

        # ── 5. Train Models ──
        results: Dict[str, EvaluationMetrics] = {}
        trained_models: Dict[str, Any] = {}

        all_models = models_to_train or [
            "Ridge", "ElasticNet", "RandomForest", "ExtraTrees",
            "GradientBoosting", "SVR", "LightGBM", "XGBoost", "BiLSTM",
        ]

        # --- Ridge ---
        if "Ridge" in all_models:
            try:
                model, metrics = self._train_model(
                    "Ridge",
                    BaselineRegressor(model_type="ridge", alpha=1.0),
                    X_train, y_train, X_test, y_test, feature_names,
                )
                results["Ridge"] = metrics
                trained_models["Ridge"] = model
            except Exception as e:
                logger.error("Ridge training failed: %s", e)
                results["Ridge"] = EvaluationMetrics(rmse=float("inf"), model_name="Ridge")

        # --- ElasticNet ---
        if "ElasticNet" in all_models:
            try:
                model, metrics = self._train_model(
                    "ElasticNet",
                    BaselineRegressor(model_type="elasticnet", alpha=0.5, l1_ratio=0.5),
                    X_train, y_train, X_test, y_test, feature_names,
                )
                results["ElasticNet"] = metrics
                trained_models["ElasticNet"] = model
            except Exception as e:
                logger.error("ElasticNet training failed: %s", e)
                results["ElasticNet"] = EvaluationMetrics(rmse=float("inf"), model_name="ElasticNet")

        # --- Random Forest ---
        if "RandomForest" in all_models:
            try:
                model, metrics = self._train_model(
                    "RandomForest",
                    RandomForestModel(n_estimators=500, max_depth=15),
                    X_train, y_train, X_test, y_test, feature_names,
                )
                results["RandomForest"] = metrics
                trained_models["RandomForest"] = model
            except Exception as e:
                logger.error("RandomForest training failed: %s", e)
                results["RandomForest"] = EvaluationMetrics(rmse=float("inf"), model_name="RandomForest")

        # --- Extra Trees ---
        if "ExtraTrees" in all_models:
            try:
                model, metrics = self._train_model(
                    "ExtraTrees",
                    ExtraTreesModel(n_estimators=500, max_depth=15),
                    X_train, y_train, X_test, y_test, feature_names,
                )
                results["ExtraTrees"] = metrics
                trained_models["ExtraTrees"] = model
            except Exception as e:
                logger.error("ExtraTrees training failed: %s", e)
                results["ExtraTrees"] = EvaluationMetrics(rmse=float("inf"), model_name="ExtraTrees")

        # --- Gradient Boosting ---
        if "GradientBoosting" in all_models:
            try:
                model, metrics = self._train_model(
                    "GradientBoosting",
                    GradientBoostingModel(n_estimators=500, learning_rate=0.05, max_depth=5),
                    X_train, y_train, X_test, y_test, feature_names,
                )
                results["GradientBoosting"] = metrics
                trained_models["GradientBoosting"] = model
            except Exception as e:
                logger.error("GradientBoosting training failed: %s", e)
                results["GradientBoosting"] = EvaluationMetrics(rmse=float("inf"), model_name="GradientBoosting")

        # --- SVR ---
        if "SVR" in all_models:
            try:
                # SVR is slow on large datasets — subsample if needed
                max_svr_samples = 5000
                if len(X_train) > max_svr_samples:
                    logger.info("SVR: subsampling to %d samples", max_svr_samples)
                    svr_idx = np.linspace(0, len(X_train) - 1, max_svr_samples, dtype=int)
                    X_svr, y_svr = X_train[svr_idx], y_train[svr_idx]
                else:
                    X_svr, y_svr = X_train, y_train

                model, metrics = self._train_model(
                    "SVR",
                    SVRModel(kernel="rbf", C=10.0),
                    X_svr, y_svr, X_test, y_test, feature_names,
                )
                results["SVR"] = metrics
                trained_models["SVR"] = model
            except Exception as e:
                logger.error("SVR training failed: %s", e)
                results["SVR"] = EvaluationMetrics(rmse=float("inf"), model_name="SVR")

        # --- LightGBM ---
        if "LightGBM" in all_models:
            try:
                lgbm = LightGBMOptimized(n_trials=self.settings.optuna_n_trials)
                model, metrics = self._train_model(
                    "LightGBM", lgbm,
                    X_train, y_train, X_test, y_test, feature_names,
                )
                results["LightGBM"] = metrics
                trained_models["LightGBM"] = model
            except Exception as e:
                logger.error("LightGBM training failed: %s", e)
                results["LightGBM"] = EvaluationMetrics(rmse=float("inf"), model_name="LightGBM")

        # --- XGBoost ---
        if "XGBoost" in all_models:
            try:
                from training_pipeline.models.xgboost_model import XGBoostOptimized
                xgb = XGBoostOptimized(n_trials=self.settings.optuna_n_trials)
                model, metrics = self._train_model(
                    "XGBoost", xgb,
                    X_train, y_train, X_test, y_test, feature_names,
                )
                results["XGBoost"] = metrics
                trained_models["XGBoost"] = model
            except ImportError:
                logger.warning("XGBoost not installed — skipping")
                results["XGBoost"] = EvaluationMetrics(rmse=float("inf"), model_name="XGBoost")
            except Exception as e:
                logger.error("XGBoost training failed: %s", e)
                results["XGBoost"] = EvaluationMetrics(rmse=float("inf"), model_name="XGBoost")

        # --- Bi-LSTM ---
        if "BiLSTM" in all_models and not skip_lstm:
            try:
                lstm_model, lstm_metrics = self.train_bilstm(X, y, feature_names)
                if lstm_model is not None:
                    results["BiLSTM"] = lstm_metrics
                    trained_models["BiLSTM"] = lstm_model
            except Exception as e:
                logger.error("BiLSTM training failed: %s", e)
                results["BiLSTM"] = EvaluationMetrics(rmse=float("inf"), model_name="BiLSTM")

        # ── 6. Compare and Select Champion ──
        champion_name = self.evaluator.compare_models(results)

        if champion_name and champion_name in trained_models:
            champion_model = trained_models[champion_name]
            champion_metrics = results[champion_name]

            # ── 7. SHAP Explainability ──
            explainer = None
            if champion_name == "LightGBM" and hasattr(champion_model, "model"):
                try:
                    bg_data = X_train[:min(500, len(X_train))]
                    explainer = SHAPExplainer.for_lightgbm(
                        champion_model, bg_data, feature_names
                    )
                    logger.info("SHAP explainer created for %s", champion_name)
                except Exception as e:
                    logger.warning("SHAP setup failed: %s", e)

            # ── 8. Register Champion ──
            if self.registry.should_promote_challenger(champion_metrics):
                version = self.registry.register_model(
                    model=champion_model,
                    metrics=champion_metrics,
                    params=champion_model.get_params(),
                    explainer=explainer,
                    model_type=champion_name.lower(),
                )
                logger.info("Champion registered: %s v%s", champion_name, version)

        # ── 9. Summary ──
        summary = {
            "champion": champion_name,
            "metrics": {name: m.to_dict() for name, m in results.items()},
            "data_drift": drift_results,
            "anomalies_detected": anomaly_count,
            "training_samples": len(X_train),
            "test_samples": len(X_test),
            "n_features": len(feature_names),
            "n_models": len(results),
            "leakage_prevention": {
                "excluded_features": ["aqi_lag_1h", "aqi_lag_3h", "pm25_lag_1h"],
                "reason": "Short-horizon lags cause data leakage (R²>0.999)",
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Save training report
        report_path = self.settings.models_dir / "training_report.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(summary, indent=2, default=str))
        logger.info("Training report saved to %s", report_path)

        logger.info("=" * 60)
        logger.info("TRAINING PIPELINE COMPLETE — Champion: %s", champion_name)
        logger.info("=" * 60)

        return summary


# ──────────────────────────────────────────────────────────────────────────────
# CLI Entry Point
# ──────────────────────────────────────────────────────────────────────────────


def main() -> None:
    """CLI entry point for running the training pipeline."""
    import argparse

    parser = argparse.ArgumentParser(description="AQI Model Training Pipeline")
    parser.add_argument("--csv", type=str, default=None, help="Training CSV path")
    parser.add_argument("--skip-lstm", action="store_true", help="Skip LSTM training")
    parser.add_argument(
        "--models", type=str, nargs="+", default=None,
        help="Specific models to train (e.g., Ridge LightGBM XGBoost)",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv) if args.csv else None

    orchestrator = TrainingOrchestrator()
    results = orchestrator.run(
        csv_path=csv_path,
        skip_lstm=args.skip_lstm,
        models_to_train=args.models,
    )

    print(f"\n{'='*60}")
    print(f"Champion: {results['champion']} ({results['n_models']} models trained)")
    for name, metrics in results["metrics"].items():
        print(f"  {name}: RMSE={metrics['rmse']:.4f}, R²={metrics['r2']:.4f}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
