"""Locust load test for the AQI Predictor API.

Run with:
    locust -f tests/load_test.py --host=https://pearls-aqi-api.onrender.com

Or headless:
    locust -f tests/load_test.py --host=http://localhost:8000 \
        --headless -u 50 -r 5 -t 60s
"""

from locust import HttpUser, between, task


class AQIAPIUser(HttpUser):
    """Simulates a typical frontend user interacting with the AQI API."""

    wait_time = between(1, 3)

    @task(5)
    def health_check(self):
        self.client.get("/health")

    @task(3)
    def list_models(self):
        self.client.get("/models")

    @task(10)
    def predict_default(self):
        self.client.post("/predict?model_id=ridge")

    @task(5)
    def predict_gradient_boosting(self):
        self.client.post("/predict?model_id=gradient_boosting")

    @task(3)
    def explain_shap(self):
        self.client.post("/explain")

    @task(2)
    def explain_lime(self):
        self.client.post("/explain/lime")

    @task(2)
    def simulate_policy(self):
        self.client.post(
            "/simulate",
            json={
                "traffic_reduction_pct": 30.0,
                "crop_burning_increase_pct": 10.0,
                "wind_speed_delta_ms": 2.0,
            },
        )

    @task(2)
    def satellite_data(self):
        self.client.get("/satellite/sentinel5p")

    @task(1)
    def shadow_metrics(self):
        self.client.get("/shadow/metrics")

    @task(1)
    def historical_data(self):
        self.client.get("/historical?hours=24&page=1")
