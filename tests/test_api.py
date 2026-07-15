"""Tests for the FastAPI backend."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from deployment.api.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    def test_health_returns_200(self, client):
        """Health endpoint returns 200 status."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_structure(self, client):
        """Health response has expected structure."""
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert "version" in data
        assert "feature_store_connected" in data
        assert "model_loaded" in data
        assert "uptime_seconds" in data

    def test_health_version_format(self, client):
        """Health version follows semver format."""
        response = client.get("/health")
        data = response.json()
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
        data = response.json()

        assert "data" in data
        assert "count" in data
        assert data["count"] > 0

    def test_historical_respects_hours_param(self, client):
        """Historical endpoint respects the hours parameter."""
        response = client.get("/historical?hours=48")
        data = response.json()

        assert data["count"] <= 48

    def test_historical_invalid_hours(self, client):
        """Historical endpoint rejects invalid hours parameter."""
        response = client.get("/historical?hours=0")
        assert response.status_code == 422


class TestAPIDocumentation:
    """Tests for API documentation endpoints."""

    def test_docs_available(self, client):
        """Swagger docs are accessible."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_available(self, client):
        """ReDoc docs are accessible."""
        response = client.get("/redoc")
        assert response.status_code == 200

    def test_openapi_schema(self, client):
        """OpenAPI schema is accessible."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert schema["info"]["title"] == "Pearls AQI Predictor API"
