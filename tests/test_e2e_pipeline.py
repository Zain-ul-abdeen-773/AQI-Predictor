"""End-to-end pipeline integration test.

Tests the complete flow: ingest -> transform -> feature store -> train -> registry -> predict.
Uses synthetic data and local storage (no external services required).

Run with:
    python -m pytest tests/test_e2e_pipeline.py -v --tb=short
"""

from __future__ import annotations

import shutil
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    d = tempfile.mkdtemp(prefix="aqi_e2e_")
    yield Path(d)
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def mock_settings(temp_dir):
    """Create settings pointing to temp directory."""
    from config.settings import get_settings

    with patch.dict(
        "os.environ",
        {
            "AQICN_API_KEY": "test_key",
            "CLEARML_OFF": "1",
        },
    ):
        settings = get_settings()
        models_dir = temp_dir / "models"
        models_dir.mkdir(parents=True, exist_ok=True)
        # Patch models_dir property to use temp
        with patch.object(
            type(settings), "models_dir", new_callable=lambda: property(lambda self: models_dir)
        ):
            with patch("training_pipeline.registry.get_settings", return_value=settings):
                yield settings


class TestEndToEndPipeline:
    """Integration tests covering the full ML pipeline lifecycle."""

    def test_synthetic_data_generation(self):
        """Test that the synthetic data generator produces valid payloads."""
        from data_pipeline.ingest import SyntheticDataGenerator

        generator = SyntheticDataGenerator()
        now = datetime.now(UTC)

        payload = generator.generate_for_timestamp(now)

        assert payload is not None
        assert payload.aqi_value > 0
        assert len(payload.pollutants) == 6
        assert payload.weather.temperature_c is not None
        assert payload.weather.humidity_pct >= 0

    def test_feature_transformation(self):
        """Test feature engineering produces expected columns."""
        from data_pipeline.ingest import SyntheticDataGenerator
        from data_pipeline.transformers import FeatureEngineer

        generator = SyntheticDataGenerator()
        engineer = FeatureEngineer()

        now = datetime.now(UTC)
        payloads = [generator.generate_for_timestamp(now - timedelta(hours=i)) for i in range(5)]

        for payload in payloads:
            features = engineer.transform(payload)

        assert features is not None
        # FeatureVector should have temporal and derived attributes
        assert hasattr(features, "temporal")
        assert hasattr(features, "derived")
        assert features.temporal.hour_sin is not None
        assert features.derived.wind_u_component is not None

    def test_model_training_and_prediction(self, mock_settings):
        """Test that models can be trained on synthetic data and produce predictions."""
        from training_pipeline.models.baseline import BaselineRegressor
        from training_pipeline.models.ensemble_trees import GradientBoostingModel
        from training_pipeline.train import FEATURE_COLUMNS

        # Generate synthetic training data
        rng = np.random.default_rng(42)
        n_samples = 50
        X = rng.normal(50, 20, (n_samples, len(FEATURE_COLUMNS))).astype(np.float32)
        y = rng.uniform(30, 200, n_samples).astype(np.float32)

        # Train Ridge
        ridge = BaselineRegressor(model_type="ridge")
        ridge.fit(X, y, feature_names=FEATURE_COLUMNS)
        preds_ridge = ridge.predict(X[:5])

        assert len(preds_ridge) == 5
        assert all(np.isfinite(preds_ridge))

        # Train GradientBoosting
        gb = GradientBoostingModel(n_estimators=10)
        gb.fit(X, y, feature_names=FEATURE_COLUMNS)
        preds_gb = gb.predict(X[:5])

        assert len(preds_gb) == 5
        assert all(np.isfinite(preds_gb))

    def test_model_registry_save_and_load(self, mock_settings, temp_dir):
        """Test model registration and retrieval from local manifest."""
        from training_pipeline.evaluation import EvaluationMetrics
        from training_pipeline.models.baseline import BaselineRegressor
        from training_pipeline.registry import ModelRegistryManager
        from training_pipeline.train import FEATURE_COLUMNS

        # Train a model
        rng = np.random.default_rng(42)
        X = rng.normal(50, 20, (20, len(FEATURE_COLUMNS))).astype(np.float32)
        y = rng.uniform(30, 200, 20).astype(np.float32)

        model = BaselineRegressor(model_type="ridge")
        model.fit(X, y, feature_names=FEATURE_COLUMNS)

        # Register it
        metrics = EvaluationMetrics(rmse=5.0, mae=3.0, r2=0.95, model_name="ridge")
        registry = ModelRegistryManager(mock_settings)
        registry.register_all_models(
            trained_models={"ridge": model},
            results={"ridge": metrics},
            champion_name="ridge",
        )

        # Verify manifest exists
        manifest_path = mock_settings.models_dir / "model_registry.json"
        assert manifest_path.exists()

        # Verify model can be listed
        registered = registry.list_registered_models()
        assert len(registered) >= 1
        assert any(m["id"] == "ridge" for m in registered)

    def test_champion_promotion_logic(self, mock_settings):
        """Test that champion promotion compares RMSE correctly."""
        from training_pipeline.evaluation import EvaluationMetrics
        from training_pipeline.models.baseline import BaselineRegressor
        from training_pipeline.registry import ModelRegistryManager
        from training_pipeline.train import FEATURE_COLUMNS

        rng = np.random.default_rng(42)
        X = rng.normal(50, 20, (20, len(FEATURE_COLUMNS))).astype(np.float32)
        y = rng.uniform(30, 200, 20).astype(np.float32)

        model = BaselineRegressor(model_type="ridge")
        model.fit(X, y, feature_names=FEATURE_COLUMNS)

        registry = ModelRegistryManager(mock_settings)

        # Register first model as champion
        metrics_v1 = EvaluationMetrics(rmse=10.0, mae=7.0, r2=0.90, model_name="ridge")
        registry.register_all_models(
            trained_models={"ridge": model},
            results={"ridge": metrics_v1},
            champion_name="ridge",
        )

        # Challenger with worse RMSE should NOT be promoted
        worse_metrics = EvaluationMetrics(rmse=12.0, mae=8.0, r2=0.85, model_name="ridge_v2")
        assert not registry.should_promote_challenger(worse_metrics)

        # Challenger with significantly better RMSE should be promoted
        better_metrics = EvaluationMetrics(rmse=8.0, mae=5.0, r2=0.95, model_name="ridge_v3")
        assert registry.should_promote_challenger(better_metrics)

    def test_full_api_prediction_flow(self):
        """Test the API serves predictions end-to-end."""
        import os

        os.environ.setdefault("CLEARML_OFF", "1")

        from deployment.api.main import app

        app.config["TESTING"] = True
        client = app.test_client()

        # Health should work
        r = client.get("/health")
        assert r.status_code == 200
        data = r.get_json()
        assert data["version"] == "1.0.0"

        # Models should return 8
        r = client.get("/models")
        assert r.status_code == 200
        data = r.get_json()
        assert len(data["models"]) == 8

        # Predict should work
        r = client.post("/predict?model_id=ridge")
        assert r.status_code == 200
        data = r.get_json()
        assert "current_aqi" in data
        assert "hourly_predictions" in data
        assert len(data["hourly_predictions"]) == 72
        assert 0 <= data["current_aqi"] <= 500

        # Explain should work
        r = client.post("/explain")
        assert r.status_code == 200
        data = r.get_json()
        assert "contributions" in data
        assert "source" in data

    def test_data_drift_detection(self):
        """Test that PSI drift detector works on synthetic distributions."""
        from training_pipeline.evaluation import DataDriftDetector

        rng = np.random.default_rng(42)

        # Reference distribution (large sample for stability)
        reference = rng.normal(50, 10, 1000)

        # Similar distribution (no drift)
        similar = rng.normal(50, 10, 1000)

        # Drifted distribution (mean shifted by 3 std devs)
        drifted = rng.normal(80, 20, 1000)

        detector = DataDriftDetector()

        # No drift case — PSI should be relatively low
        psi_no_drift = detector.compute_psi(reference, similar)
        assert psi_no_drift < 0.5  # Same distribution, should be small

        # Drift case — PSI should be much higher than no-drift
        psi_drift = detector.compute_psi(reference, drifted)
        assert psi_drift > psi_no_drift * 2  # Drifted should be clearly worse

    def test_anomaly_detection(self):
        """Test anomaly detector identifies outliers."""
        from training_pipeline.evaluation import AnomalyDetector

        rng = np.random.default_rng(42)

        # Normal data
        X_train = rng.normal(50, 10, (200, 5))

        # Test data with one extreme outlier
        X_test = rng.normal(50, 10, (10, 5))
        X_test[0] = [500, 500, 500, 500, 500]  # Extreme outlier

        detector = AnomalyDetector(contamination=0.05)
        detector.fit(X_train)

        results = detector.detect(X_test, feature_names=[f"f{i}" for i in range(5)])
        assert len(results) == 10
        # The extreme outlier should be detected
        assert results[0]["is_anomaly"] is True
