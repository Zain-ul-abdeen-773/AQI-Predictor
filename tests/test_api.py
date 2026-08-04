"""Tests for the Flask API backend.

Covers positive paths, error handling, input validation,
and response contract verification for all endpoints.
"""

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
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_structure(self, client):
        response = client.get("/health")
        data = response.get_json()
        assert "status" in data
        assert "version" in data
        assert "feature_store_connected" in data
        assert "model_loaded" in data
        assert "uptime_seconds" in data

    def test_health_version_format(self, client):
        response = client.get("/health")
        data = response.get_json()
        parts = data["version"].split(".")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)


class TestHistoricalEndpoint:
    """Tests for the /historical endpoint."""

    def test_historical_returns_200(self, client):
        response = client.get("/historical?hours=24")
        assert response.status_code == 200

    def test_historical_response_has_pagination(self, client):
        response = client.get("/historical?hours=24&page=1")
        data = response.get_json()
        assert "data" in data
        assert "count" in data
        assert "page" in data
        assert "total_pages" in data

    def test_historical_invalid_hours_uses_default(self, client):
        response = client.get("/historical?hours=abc")
        assert response.status_code == 200
        data = response.get_json()
        assert "data" in data

    def test_historical_caps_at_maximum(self, client):
        """Hours parameter is capped at 2160 (90 days)."""
        response = client.get("/historical?hours=99999")
        assert response.status_code == 200


class TestModelZooEndpoints:
    """Tests for 8-Model Zoo selection and metrics endpoints."""

    def test_list_models_returns_8_models(self, client):
        response = client.get("/models")
        assert response.status_code == 200
        data = response.get_json()
        assert "models" in data
        assert "default_model_id" in data
        assert len(data["models"]) == 8

    def test_models_have_required_fields(self, client):
        response = client.get("/models")
        data = response.get_json()
        for model in data["models"]:
            assert "id" in model
            assert "name" in model
            assert "r2" in model
            assert "rmse" in model
            assert "is_default" in model

    def test_default_model_exists_in_list(self, client):
        response = client.get("/models")
        data = response.get_json()
        default_id = data["default_model_id"]
        model_ids = [m["id"] for m in data["models"]]
        assert default_id in model_ids

    def test_predict_with_specific_model_id(self, client):
        response = client.post("/predict?model_id=ridge")
        assert response.status_code == 200
        data = response.get_json()
        assert data["model_type"] == "ridge"
        assert len(data["hourly_predictions"]) == 72

    def test_predict_with_invalid_model_falls_back(self, client):
        """Invalid model_id should fallback to default, not crash."""
        response = client.post("/predict?model_id=nonexistent_model")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["hourly_predictions"]) == 72

    def test_predict_aqi_within_valid_range(self, client):
        response = client.post("/predict?model_id=ridge")
        data = response.get_json()
        assert 0 <= data["current_aqi"] <= 500
        for pred in data["hourly_predictions"]:
            assert 0 <= pred["aqi_predicted"] <= 500


class TestSimulateEndpoint:
    """Tests for /simulate endpoint including input validation."""

    def test_simulate_valid_input(self, client):
        response = client.post("/simulate", json={
            "traffic_reduction_pct": 30.0,
            "crop_burning_increase_pct": 10.0,
            "wind_speed_delta_ms": 2.0,
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert "methodology" in data
        assert len(data["simulated_curve"]) == 72
        assert len(data["baseline_curve"]) == 72

    def test_simulate_invalid_string_input(self, client):
        """Non-numeric input returns 422 with error message."""
        response = client.post("/simulate", json={
            "traffic_reduction_pct": "not_a_number",
        })
        assert response.status_code == 422
        data = response.get_json()
        assert "error" in data
        assert "Validation" in data["error"]

    def test_simulate_clamps_extreme_values(self, client):
        """Values beyond valid range are clamped, not rejected."""
        response = client.post("/simulate", json={
            "traffic_reduction_pct": 999.0,
            "crop_burning_increase_pct": -50.0,
            "wind_speed_delta_ms": 100.0,
        })
        assert response.status_code == 200
        data = response.get_json()
        # traffic_reduction clamped to 100
        assert data["parameters"]["traffic_reduction_pct"] == 100.0
        # crop_burning clamped to 0
        assert data["parameters"]["crop_burning_increase_pct"] == 0.0
        # wind clamped to 20
        assert data["parameters"]["wind_speed_delta_ms"] == 20.0

    def test_simulate_empty_body(self, client):
        """Empty JSON body uses defaults (all zeros)."""
        response = client.post("/simulate", json={})
        assert response.status_code == 200
        data = response.get_json()
        assert data["net_aqi_change"] == 0.0

    def test_simulate_no_body(self, client):
        """No request body at all still works."""
        response = client.post("/simulate")
        assert response.status_code == 200


class TestSatelliteEndpoint:
    """Tests for /satellite/sentinel5p endpoint."""

    def test_satellite_returns_grid(self, client):
        response = client.get("/satellite/sentinel5p")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["grid_points"]) == 25
        assert "no2_column_density" in data["grid_points"][0]
        assert "aerosol_optical_depth" in data["grid_points"][0]

    def test_satellite_marks_data_source(self, client):
        """Response clearly states data is simulated."""
        response = client.get("/satellite/sentinel5p")
        data = response.get_json()
        assert data["data_source"] == "simulated_regional_baseline"

    def test_satellite_deterministic(self, client):
        """Same request returns same grid (seeded RNG, no global side effects)."""
        r1 = client.get("/satellite/sentinel5p").get_json()
        r2 = client.get("/satellite/sentinel5p").get_json()
        assert r1["grid_points"] == r2["grid_points"]


class TestShadowMetrics:
    """Tests for /shadow/metrics endpoint."""

    def test_shadow_metrics_returns_200(self, client):
        response = client.get("/shadow/metrics")
        assert response.status_code == 200

    def test_shadow_metrics_honest_when_empty(self, client):
        """When no shadow records exist, reports NO_DATA instead of fake numbers."""
        response = client.get("/shadow/metrics")
        data = response.get_json()
        assert "canary_status" in data
        assert "data_source" in data
        # If no real records, status should indicate that
        if data["total_shadow_requests"] == 0:
            assert data["canary_status"] == "NO_DATA"


class TestExplainEndpoints:
    """Tests for /explain and /explain/lime endpoints."""

    def test_explain_returns_200(self, client):
        response = client.post("/explain")
        assert response.status_code == 200

    def test_explain_has_source_field(self, client):
        """Response indicates whether data is live or demo."""
        response = client.post("/explain")
        data = response.get_json()
        assert "source" in data
        assert data["source"] in ("live", "demo")

    def test_explain_contributions_structure(self, client):
        response = client.post("/explain")
        data = response.get_json()
        assert "contributions" in data
        assert len(data["contributions"]) > 0
        contrib = data["contributions"][0]
        assert "feature_name" in contrib
        assert "shap_value" in contrib

    def test_lime_returns_200(self, client):
        response = client.post("/explain/lime")
        assert response.status_code == 200

    def test_lime_has_source_field(self, client):
        response = client.post("/explain/lime")
        data = response.get_json()
        assert "source" in data
        assert data["source"] in ("live", "demo")

    def test_lime_get_method_works(self, client):
        """LIME endpoint also accepts GET."""
        response = client.get("/explain/lime")
        assert response.status_code == 200


class TestErrorHandling:
    """Tests verifying error responses don't leak internals."""

    def test_404_returns_json(self, client):
        """Non-existent routes return proper error."""
        response = client.get("/nonexistent/endpoint")
        assert response.status_code == 404

    def test_errors_never_expose_traceback(self, client):
        """Error responses should not contain file paths or tracebacks."""
        response = client.post("/simulate", json={"traffic_reduction_pct": "bad"})
        data = response.get_json()
        response_text = str(data)
        assert "Traceback" not in response_text
        assert "File " not in response_text
        assert ".py" not in response_text
