"""Tests for the training pipeline module."""

from __future__ import annotations

import numpy as np
import pytest

from training_pipeline.evaluation import (
    ModelEvaluator,
    compute_mae,
    compute_mape,
    compute_r2,
    compute_rmse,
    DataDriftDetector,
)
from training_pipeline.models.baseline import BaselineRegressor


# ──────────────────────────────────────────────────────────────────────────────
# Metric Function Tests
# ──────────────────────────────────────────────────────────────────────────────


class TestMetrics:
    """Test suite for evaluation metric functions."""

    def test_rmse_perfect_predictions(self):
        """RMSE is 0 for perfect predictions."""
        y = np.array([1.0, 2.0, 3.0])
        assert compute_rmse(y, y) == 0.0

    def test_rmse_known_value(self):
        """RMSE computes correctly for known values."""
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([1.0, 2.0, 4.0])
        rmse = compute_rmse(y_true, y_pred)
        assert abs(rmse - (1.0 / 3 ** 0.5)) < 1e-6

    def test_mae_perfect_predictions(self):
        """MAE is 0 for perfect predictions."""
        y = np.array([1.0, 2.0, 3.0])
        assert compute_mae(y, y) == 0.0

    def test_r2_perfect_predictions(self):
        """R² is 1.0 for perfect predictions."""
        y = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        assert compute_r2(y, y) == 1.0

    def test_r2_mean_predictions(self):
        """R² is 0 when predictions equal the mean."""
        y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = np.full_like(y_true, y_true.mean())
        assert abs(compute_r2(y_true, y_pred)) < 1e-10

    def test_mape_handles_zeros(self):
        """MAPE handles zero values gracefully."""
        y_true = np.array([0.0, 1.0, 2.0])
        y_pred = np.array([0.5, 1.0, 2.5])
        mape = compute_mape(y_true, y_pred)
        assert mape >= 0


# ──────────────────────────────────────────────────────────────────────────────
# Baseline Model Tests
# ──────────────────────────────────────────────────────────────────────────────


class TestBaselineRegressor:
    """Test suite for BaselineRegressor."""

    def test_ridge_fit_predict(self):
        """Ridge regression can fit and predict."""
        np.random.seed(42)
        X = np.random.randn(100, 10)
        y = X[:, 0] * 5 + X[:, 1] * 3 + np.random.randn(100) * 0.1

        model = BaselineRegressor(model_type="ridge")
        model.fit(X, y)

        assert model.is_fitted
        predictions = model.predict(X)
        assert len(predictions) == 100
        assert all(0 <= p <= 500 for p in predictions)

    def test_elasticnet_fit_predict(self):
        """ElasticNet regression can fit and predict."""
        np.random.seed(42)
        X = np.random.randn(100, 10)
        y = np.abs(X[:, 0] * 50 + 100)

        model = BaselineRegressor(model_type="elasticnet", alpha=0.1)
        model.fit(X, y)

        assert model.is_fitted
        predictions = model.predict(X)
        assert len(predictions) == 100

    def test_unfitted_predict_raises(self):
        """Predict on unfitted model raises RuntimeError."""
        model = BaselineRegressor()
        with pytest.raises(RuntimeError, match="fitted"):
            model.predict(np.zeros((1, 10)))

    def test_get_coefficients(self):
        """Coefficients accessible after fitting."""
        X = np.random.randn(50, 5)
        y = X[:, 0] * 10

        model = BaselineRegressor()
        model.fit(X, y, feature_names=["a", "b", "c", "d", "e"])

        coefs = model.get_coefficients()
        assert "a" in coefs
        assert len(coefs) == 5

    def test_save_load_roundtrip(self, tmp_path):
        """Model can be saved and loaded."""
        X = np.random.randn(50, 5)
        y = X[:, 0] * 10

        model = BaselineRegressor()
        model.fit(X, y)

        path = tmp_path / "test_model.pkl"
        model.save(path)

        loaded = BaselineRegressor.load(path)
        assert loaded.is_fitted

        # Predictions should match
        np.testing.assert_array_almost_equal(
            model.predict(X), loaded.predict(X)
        )


# ──────────────────────────────────────────────────────────────────────────────
# Evaluator Tests
# ──────────────────────────────────────────────────────────────────────────────


class TestModelEvaluator:
    """Test suite for ModelEvaluator."""

    def test_evaluate_returns_metrics(self):
        """Evaluate produces all expected metric fields."""
        evaluator = ModelEvaluator()
        y_true = np.array([100, 120, 130, 150, 160])
        y_pred = np.array([105, 115, 135, 145, 165])

        metrics = evaluator.evaluate(y_true, y_pred, model_name="test")

        assert metrics.rmse > 0
        assert metrics.mae > 0
        assert metrics.model_name == "test"

    def test_compare_models_selects_best(self):
        """Compare models returns the model with lowest RMSE."""
        from training_pipeline.evaluation import EvaluationMetrics

        evaluator = ModelEvaluator()
        results = {
            "model_A": EvaluationMetrics(rmse=15.0, model_name="model_A"),
            "model_B": EvaluationMetrics(rmse=10.0, model_name="model_B"),
            "model_C": EvaluationMetrics(rmse=20.0, model_name="model_C"),
        }

        champion = evaluator.compare_models(results)
        assert champion == "model_B"


# ──────────────────────────────────────────────────────────────────────────────
# Data Drift Tests
# ──────────────────────────────────────────────────────────────────────────────


class TestDataDriftDetector:
    """Test suite for DataDriftDetector."""

    def test_no_drift_same_distribution(self):
        """No drift detected when distributions are identical."""
        detector = DataDriftDetector()
        data = np.random.randn(1000, 5)

        results = detector.detect_drift(data, data, [f"f{i}" for i in range(5)])
        assert not results["overall_drift"]

    def test_drift_detected_different_distribution(self):
        """Drift detected when distributions are significantly different."""
        detector = DataDriftDetector(threshold=0.1)
        ref = np.random.randn(1000, 3)
        cur = np.random.randn(1000, 3) + 5  # Shifted distribution

        results = detector.detect_drift(ref, cur, ["a", "b", "c"])
        assert results["overall_drift"]
        assert len(results["drifted_features"]) > 0
