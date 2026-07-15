"""Training pipeline orchestrator.

Coordinates the full ML training workflow:
1. Load training data from Feature Store
2. Prepare features and targets
3. Train all three model architectures (Ridge, LightGBM, Bi-LSTM)
4. Evaluate with TimeSeriesSplit cross-validation
5. Compute SHAP explanations
6. Register the best model in the Model Registry
7. Run data drift detection and anomaly detection

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
from training_pipeline.registry import ModelRegistryManager

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Feature columns (excluding target and non-numeric columns)
# ──────────────────────────────────────────────────────────────────────────────

FEATURE_COLUMNS: List[str] = [
    # Raw pollutants
    "pm25", "pm10", "no2", "so2", "co", "o3",
    # Meteorological
    "temperature_c", "humidity_pct", "wind_speed_ms", "wind_direction_deg",
    "pressure_hpa", "precipitation_mm",
    # Temporal (cyclical)
    "hour_sin", "hour_cos", "day_sin", "day_cos", "month_sin", "month_cos",
    "hour", "day_of_week", "day_of_year",
    # Derived
    "aqi_change_rate_1h", "aqi_change_rate_3h", "aqi_change_rate_6h",
    "wind_u_component", "wind_v_component",
    "wind_pm25_interaction", "wind_pm10_interaction",
    "temperature_humidity_index", "pollution_intensity",
    # Lag features
    "aqi_lag_1h", "aqi_lag_3h", "aqi_lag_6h", "aqi_lag_12h", "aqi_lag_24h",
    "pm25_lag_1h", "pm25_lag_3h",
    "pm25_rolling_mean_6h", "pm25_rolling_std_6h", "pm25_rolling_mean_24h",
]

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

    def train_baseline(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        feature_names: List[str],
    ) -> Tuple[BaselineRegressor, EvaluationMetrics]:
        """Train and evaluate the baseline Ridge regression model.

        Args:
            X_train: Training features.
            y_train: Training targets.
            X_test: Test features.
            y_test: Test targets.
            feature_names: Feature name list.

        Returns:
            Tuple of (trained model, evaluation metrics).
        """
        logger.info("=" * 60)
        logger.info("TRAINING: Ridge Regression Baseline")
        logger.info("=" * 60)

        model = BaselineRegressor(model_type="ridge", alpha=1.0)
        model.fit(X_train, y_train, feature_names=feature_names)

        y_pred = model.predict(X_test)
        metrics = self.evaluator.evaluate(y_test, y_pred, model_name="Ridge")

        return model, metrics

    def train_lightgbm(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        feature_names: List[str],
    ) -> Tuple[LightGBMOptimized, EvaluationMetrics]:
        """Train and evaluate the LightGBM model with Optuna tuning.

        Args:
            X_train: Training features.
            y_train: Training targets.
            X_test: Test features.
            y_test: Test targets.
            feature_names: Feature name list.

        Returns:
            Tuple of (trained model, evaluation metrics).
        """
        logger.info("=" * 60)
        logger.info("TRAINING: LightGBM with Optuna Optimization")
        logger.info("=" * 60)

        model = LightGBMOptimized(n_trials=self.settings.optuna_n_trials)
        model.fit(X_train, y_train, feature_names=feature_names)

        y_pred = model.predict(X_test)
        metrics = self.evaluator.evaluate(y_test, y_pred, model_name="LightGBM")

        return model, metrics

    def train_bilstm(
        self,
        X: np.ndarray,
        y: np.ndarray,
        feature_names: List[str],
    ) -> Tuple[BiLSTMAttention, EvaluationMetrics]:
        """Train and evaluate the Bi-LSTM with Attention model.

        Creates sequences from the flat feature matrix and trains
        the sequence-to-sequence model.

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

        model = BiLSTMAttention(
            input_size=X.shape[1],
            hidden_size=self.settings.lstm_hidden_size,
            num_layers=self.settings.lstm_num_layers,
            dropout=self.settings.lstm_dropout,
            forecast_horizon=horizon,
        )

        model.fit(
            X_train_seq, y_train_seq,
            X_val_seq, y_val_seq,
            feature_names=feature_names,
        )

        # Evaluate on validation sequences
        y_pred = model.predict(X_val_seq)
        metrics = self.evaluator.evaluate(
            y_val_seq.flatten(),
            y_pred.flatten(),
            model_name="BiLSTM",
        )

        return model, metrics

    def run(
        self,
        csv_path: Optional[Path] = None,
        skip_lstm: bool = False,
    ) -> Dict[str, Any]:
        """Execute the complete training pipeline.

        Args:
            csv_path: Optional path to training CSV.
            skip_lstm: Whether to skip LSTM training (for quick iteration).

        Returns:
            Dict with training results, metrics, and champion info.
        """
        logger.info("=" * 60)
        logger.info("PEARLS AQI PREDICTOR — TRAINING PIPELINE")
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

        # Ridge Baseline
        ridge_model, ridge_metrics = self.train_baseline(
            X_train, y_train, X_test, y_test, feature_names
        )
        results["Ridge"] = ridge_metrics
        trained_models["Ridge"] = ridge_model

        # LightGBM
        try:
            lgbm_model, lgbm_metrics = self.train_lightgbm(
                X_train, y_train, X_test, y_test, feature_names
            )
            results["LightGBM"] = lgbm_metrics
            trained_models["LightGBM"] = lgbm_model
        except Exception as e:
            logger.error("LightGBM training failed: %s", e)
            results["LightGBM"] = EvaluationMetrics(rmse=float("inf"), model_name="LightGBM")

        # Bi-LSTM
        if not skip_lstm:
            try:
                lstm_model, lstm_metrics = self.train_bilstm(X, y, feature_names)
                if lstm_model is not None:
                    results["BiLSTM"] = lstm_metrics
                    trained_models["BiLSTM"] = lstm_model
            except Exception as e:
                logger.error("BiLSTM training failed: %s", e)
                results["BiLSTM"] = EvaluationMetrics(
                    rmse=float("inf"), model_name="BiLSTM"
                )

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
    args = parser.parse_args()

    csv_path = Path(args.csv) if args.csv else None

    orchestrator = TrainingOrchestrator()
    results = orchestrator.run(csv_path=csv_path, skip_lstm=args.skip_lstm)

    print(f"\n{'='*60}")
    print(f"Champion: {results['champion']}")
    for name, metrics in results["metrics"].items():
        print(f"  {name}: RMSE={metrics['rmse']:.4f}, R²={metrics['r2']:.4f}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
