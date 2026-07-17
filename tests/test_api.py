"""Tests for the Flask API backend."""

from __future__ import annotations

import pytest

from deployment.api.main import app


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    def test_health_returns_200(self, client):
        """Health endpoint returns 200 status."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_structure(self, client):
        """Health response has expected structure."""
        response = client.get("/health")
        data = response.get_json()

        assert "status" in data
        assert "version" in data
        assert "feature_store_connected" in data
        assert "model_loaded" in data
        assert "uptime_seconds" in data

    def test_health_version_format(self, client):
        """Health version follows semver format."""
        response = client.get("/health")
        data = response.get_json()
        version = data["version"]

        parts = version.split(".")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)


class TestHistoricalEndpoint:
    """Tests for the /historical endpoint."""

    def test_historical_returns_200(self, client):
        """Historical endpoint returns 200 status."""
        response = client.get("/historical?hours=24")
        assert response.status_code == 200

    def test_historical_response_structure(self, client):
        """Historical response has data and count."""
        response = client.get("/historical?hours=24")
        data = response.get_json()

        assert "data" in data
        assert "count" in data
        assert data["count"] > 0

    def test_historical_respects_hours_param(self, client):
        """Historical endpoint respects the hours parameter."""
        response = client.get("/historical?hours=48")
        data = response.get_json()

        assert data["count"] <= 48


class TestModelZooEndpoints:
    """Tests for 8-Model Zoo selection and metrics endpoints."""

    def test_list_models_returns_8_models(self, client):
        """Verify /models returns exactly 8 models with metrics and default selection."""
        response = client.get("/models")
        assert response.status_code == 200
        data = response.get_json()
        assert "models" in data
        assert "default_model_id" in data
        assert len(data["models"]) == 8
        default_model = next(m for m in data["models"] if m["is_default"])
        assert default_model["id"] == data["default_model_id"]
        assert default_model["r2"] >= 0.90

    def test_predict_with_specific_model_id(self, client):
        """Verify /predict accepts model_id and returns predictions using that model."""
        response = client.post("/predict?model_id=ridge")
        assert response.status_code == 200
        data = response.get_json()
        assert data["model_type"] == "ridge"
        assert len(data["hourly_predictions"]) == 72
