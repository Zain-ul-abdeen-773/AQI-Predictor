"""Model evaluation framework with temporal cross-validation.

Implements TimeSeriesSplit evaluation with RMSE, MAE, R² metrics,
model comparison, data drift detection, and anomaly detection.

Example:
    >>> from training_pipeline.evaluation import ModelEvaluator
    >>> evaluator = ModelEvaluator()
    >>> metrics = evaluator.evaluate(model, X_test, y_test)
    >>> comparison = evaluator.compare_models(models, X_test, y_test)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol

import numpy as np
from sklearn.model_selection import TimeSeriesSplit

from config.settings import get_settings

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Protocols & Data Classes
# ──────────────────────────────────────────────────────────────────────────────


class Predictor(Protocol):
    """Protocol for any model with a predict method."""

    def predict(self, X: np.ndarray) -> np.ndarray:
        ...

    def get_params(self) -> Dict[str, Any]:
        ...


@dataclass
class EvaluationMetrics:
    """Container for model evaluation metrics.

    Attributes:
        rmse: Root Mean Squared Error.
        mae: Mean Absolute Error.
        r2: Coefficient of Determination.
        mape: Mean Absolute Percentage Error.
        max_error: Maximum absolute error.
        within_50: Percentage of predictions within ±50 AQI.
        model_name: Name of the evaluated model.
        fold_metrics: Per-fold metrics for cross-validation.
    """

    rmse: float = 0.0
    mae: float = 0.0
    r2: float = 0.0
    mape: float = 0.0
    max_error: float = 0.0
    within_50: float = 0.0
    model_name: str = ""
    fold_metrics: List[Dict[str, float]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for serialization."""
        return {
            "rmse": round(self.rmse, 4),
            "mae": round(self.mae, 4),
            "r2": round(self.r2, 4),
            "mape": round(self.mape, 4),
            "max_error": round(self.max_error, 4),
            "within_50_pct": round(self.within_50, 2),
            "model_name": self.model_name,
            "n_folds": len(self.fold_metrics),
        }

    def __repr__(self) -> str:
        return (
            f"EvaluationMetrics({self.model_name}: "
            f"RMSE={self.rmse:.4f}, MAE={self.mae:.4f}, "
            f"R²={self.r2:.4f}, MAPE={self.mape:.2f}%)"
        )


# ──────────────────────────────────────────────────────────────────────────────
# Core Evaluation Functions
# ──────────────────────────────────────────────────────────────────────────────


def compute_rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Root Mean Squared Error."""
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def compute_mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Mean Absolute Error."""
    return float(np.mean(np.abs(y_true - y_pred)))


def compute_r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Coefficient of Determination (R²)."""
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    if ss_tot == 0:
        return 0.0
    return float(1 - ss_res / ss_tot)


def compute_mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Mean Absolute Percentage Error (handles zero values)."""
    mask = y_true != 0
    if not mask.any():
        return 0.0
    return float(100 * np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])))


# ──────────────────────────────────────────────────────────────────────────────
# Model Evaluator
# ──────────────────────────────────────────────────────────────────────────────


class ModelEvaluator:
    """Comprehensive model evaluation with temporal cross-validation.

    Uses TimeSeriesSplit to prevent data leakage from future observations.
    Computes standard regression metrics and AQI-specific accuracy measures.

    Attributes:
        n_splits: Number of TimeSeriesSplit folds.
    """

    def __init__(self, n_splits: Optional[int] = None) -> None:
        settings = get_settings()
        self.n_splits = n_splits or settings.cv_n_splits

    def evaluate(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        model_name: str = "unknown",
    ) -> EvaluationMetrics:
        """Evaluate predictions against ground truth.

        Args:
            y_true: True AQI values.
            y_pred: Predicted AQI values.
            model_name: Model identifier for reporting.

        Returns:
            EvaluationMetrics: Complete evaluation metrics.
        """
        metrics = EvaluationMetrics(
            rmse=compute_rmse(y_true, y_pred),
            mae=compute_mae(y_true, y_pred),
            r2=compute_r2(y_true, y_pred),
            mape=compute_mape(y_true, y_pred),
            max_error=float(np.max(np.abs(y_true - y_pred))),
            within_50=float(100 * np.mean(np.abs(y_true - y_pred) <= 50)),
            model_name=model_name,
        )

        logger.info(
            "%s evaluation: RMSE=%.4f, MAE=%.4f, R²=%.4f, MAPE=%.2f%%",
            model_name, metrics.rmse, metrics.mae, metrics.r2, metrics.mape,
        )
        return metrics

    def cross_validate(
        self,
        model: Any,
        X: np.ndarray,
        y: np.ndarray,
        model_name: str = "unknown",
    ) -> EvaluationMetrics:
        """Perform TimeSeriesSplit cross-validation.

        Args:
            model: Model with fit() and predict() methods.
            X: Feature matrix (n_samples, n_features).
            y: Target values (n_samples,).
            model_name: Model identifier.

        Returns:
            EvaluationMetrics: Averaged metrics across folds.
        """
        tscv = TimeSeriesSplit(n_splits=self.n_splits)
        fold_metrics: List[Dict[str, float]] = []

        logger.info(
            "Starting %d-fold TimeSeriesSplit CV for %s",
            self.n_splits, model_name,
        )

        for fold, (train_idx, val_idx) in enumerate(tscv.split(X), 1):
            X_train, X_val = X[train_idx], X[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]

            # Fit model on fold
            model.fit(X_train, y_train)
            y_pred = model.predict(X_val)

            # Flatten if multi-output
            if y_val.ndim > 1:
                y_val = y_val.flatten()
            if y_pred.ndim > 1:
                y_pred = y_pred.flatten()

            fold_result = {
                "fold": fold,
                "rmse": compute_rmse(y_val, y_pred),
                "mae": compute_mae(y_val, y_pred),
                "r2": compute_r2(y_val, y_pred),
                "mape": compute_mape(y_val, y_pred),
                "train_size": len(train_idx),
                "val_size": len(val_idx),
            }
            fold_metrics.append(fold_result)

            logger.info(
                "  Fold %d: RMSE=%.4f, MAE=%.4f, R²=%.4f (train=%d, val=%d)",
                fold, fold_result["rmse"], fold_result["mae"],
                fold_result["r2"], len(train_idx), len(val_idx),
            )

        # Aggregate across folds
        avg_metrics = EvaluationMetrics(
            rmse=np.mean([f["rmse"] for f in fold_metrics]),
            mae=np.mean([f["mae"] for f in fold_metrics]),
            r2=np.mean([f["r2"] for f in fold_metrics]),
            mape=np.mean([f["mape"] for f in fold_metrics]),
            model_name=model_name,
            fold_metrics=fold_metrics,
        )

        logger.info(
            "%s CV Results: RMSE=%.4f±%.4f, MAE=%.4f±%.4f, R²=%.4f±%.4f",
            model_name,
            avg_metrics.rmse, np.std([f["rmse"] for f in fold_metrics]),
            avg_metrics.mae, np.std([f["mae"] for f in fold_metrics]),
            avg_metrics.r2, np.std([f["r2"] for f in fold_metrics]),
        )
        return avg_metrics

    def compare_models(
        self,
        model_results: Dict[str, EvaluationMetrics],
    ) -> str:
        """Compare multiple models and identify the champion.

        Uses RMSE as the primary ranking metric.

        Args:
            model_results: Dict mapping model name to evaluation metrics.

        Returns:
            str: Name of the best performing model.
        """
        if not model_results:
            return ""

        ranked = sorted(model_results.items(), key=lambda x: x[1].rmse)

        logger.info("=" * 60)
        logger.info("MODEL COMPARISON (ranked by RMSE)")
        logger.info("=" * 60)
        for rank, (name, metrics) in enumerate(ranked, 1):
            marker = " ★ CHAMPION" if rank == 1 else ""
            logger.info(
                "  %d. %s: RMSE=%.4f, MAE=%.4f, R²=%.4f%s",
                rank, name, metrics.rmse, metrics.mae, metrics.r2, marker,
            )
        logger.info("=" * 60)

        champion = ranked[0][0]
        return champion


class DataDriftDetector:
    """Detects feature distribution shifts between training and inference data.

    Uses population stability index (PSI) to quantify drift magnitude
    and flag features that may require model retraining.

    Attributes:
        threshold: PSI threshold above which drift is flagged.
        n_bins: Number of bins for PSI computation.
    """

    def __init__(self, threshold: float = 0.2, n_bins: int = 20) -> None:
        self.threshold = threshold
        self.n_bins = n_bins

    def compute_psi(
        self,
        reference: np.ndarray,
        current: np.ndarray,
    ) -> float:
        """Compute Population Stability Index between two distributions.

        Args:
            reference: Reference (training) distribution.
            current: Current (production) distribution.

        Returns:
            float: PSI value. > 0.2 indicates significant drift.
        """
        eps = 1e-6

        # Create bins from reference distribution
        bins = np.linspace(
            min(reference.min(), current.min()),
            max(reference.max(), current.max()),
            self.n_bins + 1,
        )

        ref_hist, _ = np.histogram(reference, bins=bins)
        cur_hist, _ = np.histogram(current, bins=bins)

        # Normalize to proportions
        ref_pct = (ref_hist + eps) / (ref_hist.sum() + eps * len(ref_hist))
        cur_pct = (cur_hist + eps) / (cur_hist.sum() + eps * len(cur_hist))

        psi = np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct))
        return float(psi)

    def detect_drift(
        self,
        reference_df: np.ndarray,
        current_df: np.ndarray,
        feature_names: List[str],
    ) -> Dict[str, Any]:
        """Check for data drift across all features.

        Args:
            reference_df: Reference (training) data matrix.
            current_df: Current (production) data matrix.
            feature_names: Feature name list.

        Returns:
            Dict with drift detection results per feature.
        """
        results: Dict[str, Any] = {
            "overall_drift": False,
            "drifted_features": [],
            "psi_scores": {},
        }

        for i, name in enumerate(feature_names):
            if i >= reference_df.shape[1] or i >= current_df.shape[1]:
                continue

            ref_col = reference_df[:, i]
            cur_col = current_df[:, i]

            # Skip constant features
            if np.std(ref_col) == 0 and np.std(cur_col) == 0:
                continue

            psi = self.compute_psi(ref_col, cur_col)
            results["psi_scores"][name] = round(psi, 4)

            if psi > self.threshold:
                results["drifted_features"].append(name)
                logger.warning(
                    "Data drift detected in '%s': PSI=%.4f > %.4f",
                    name, psi, self.threshold,
                )

        results["overall_drift"] = len(results["drifted_features"]) > 0

        if results["overall_drift"]:
            logger.warning(
                "Data drift detected in %d features: %s",
                len(results["drifted_features"]),
                results["drifted_features"],
            )
        else:
            logger.info("No significant data drift detected")

        return results


class AnomalyDetector:
    """Isolation Forest-based anomaly detector for AQI readings.

    Identifies unusual air quality readings that may indicate sensor
    malfunction, extreme weather events, or other anomalies.

    Attributes:
        contamination: Expected proportion of anomalies.
        model: Fitted Isolation Forest model.
    """

    def __init__(self, contamination: float = 0.05) -> None:
        self.contamination = contamination
        self.model = None

    def fit(self, X: np.ndarray) -> "AnomalyDetector":
        """Fit the anomaly detector on training data.

        Args:
            X: Training feature matrix.

        Returns:
            Self for method chaining.
        """
        from sklearn.ensemble import IsolationForest

        self.model = IsolationForest(
            contamination=self.contamination,
            random_state=42,
            n_estimators=200,
        )
        self.model.fit(X)
        logger.info("Anomaly detector fitted on %d samples", len(X))
        return self

    def detect(
        self,
        X: np.ndarray,
        feature_names: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Detect anomalies in the input data.

        Args:
            X: Feature matrix to check for anomalies.
            feature_names: Optional feature names.

        Returns:
            List of anomaly detection results per sample.
        """
        if self.model is None:
            raise RuntimeError("Anomaly detector must be fitted first")

        predictions = self.model.predict(X)
        scores = self.model.score_samples(X)

        results = []
        for i in range(len(X)):
            is_anomaly = predictions[i] == -1
            result = {
                "index": i,
                "is_anomaly": bool(is_anomaly),
                "anomaly_score": float(scores[i]),
            }
            if is_anomaly and feature_names:
                # Find contributing features (highest absolute z-scores)
                z_scores = np.abs((X[i] - np.mean(X, axis=0)) / (np.std(X, axis=0) + 1e-8))
                top_features = np.argsort(z_scores)[-3:][::-1]
                result["contributing_features"] = [
                    feature_names[idx] for idx in top_features
                    if idx < len(feature_names)
                ]
            results.append(result)

        anomaly_count = sum(1 for r in results if r["is_anomaly"])
        logger.info(
            "Anomaly detection: %d/%d anomalies detected (%.1f%%)",
            anomaly_count, len(results), 100 * anomaly_count / len(results),
        )
        return results
