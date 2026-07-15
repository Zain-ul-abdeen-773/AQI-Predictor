"""Tests for the data pipeline module.

Covers data ingestion, feature engineering, synthetic data generation,
and backfill pipeline functionality.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone

import numpy as np
import pytest

from config.schemas import DataSource, PollutantReading, RawDataPayload, WeatherReading
from data_pipeline.ingest import SyntheticDataGenerator
from data_pipeline.transformers import FeatureEngineer


# ──────────────────────────────────────────────────────────────────────────────
# Synthetic Data Generator Tests
# ──────────────────────────────────────────────────────────────────────────────


class TestSyntheticDataGenerator:
    """Test suite for SyntheticDataGenerator."""

    def setup_method(self):
        """Initialize generator for each test."""
        self.generator = SyntheticDataGenerator()

    def test_generates_valid_payload(self):
        """Generator produces a valid RawDataPayload."""
        dt = datetime(2024, 6, 15, 12, 0, tzinfo=timezone.utc)
        payload = self.generator.generate_for_timestamp(dt)

        assert isinstance(payload, RawDataPayload)
        assert payload.source == DataSource.SYNTHETIC
        assert len(payload.pollutants) == 6
        assert payload.weather is not None
        assert payload.aqi_value is not None

    def test_aqi_within_valid_range(self):
        """Generated AQI values are within 10-450 range."""
        for month in range(1, 13):
            dt = datetime(2024, month, 15, 12, 0, tzinfo=timezone.utc)
            payload = self.generator.generate_for_timestamp(dt)
            assert 10 <= payload.aqi_value <= 450, f"AQI {payload.aqi_value} out of range"

    def test_seasonal_pattern(self):
        """Winter months should have higher average AQI than summer."""
        winter_aqis = []
        summer_aqis = []

        for _ in range(100):
            winter_dt = datetime(2024, 12, 15, 12, 0, tzinfo=timezone.utc)
            summer_dt = datetime(2024, 6, 15, 12, 0, tzinfo=timezone.utc)

            winter_aqis.append(self.generator.generate_for_timestamp(winter_dt).aqi_value)
            summer_aqis.append(self.generator.generate_for_timestamp(summer_dt).aqi_value)

        assert np.mean(winter_aqis) > np.mean(summer_aqis), \
            "Winter AQI should be higher than summer"

    def test_pollutant_names_normalized(self):
        """All pollutant names are in standard format."""
        dt = datetime(2024, 6, 15, 12, 0, tzinfo=timezone.utc)
        payload = self.generator.generate_for_timestamp(dt)

        expected_names = {"pm25", "pm10", "no2", "so2", "co", "o3"}
        actual_names = {p.name for p in payload.pollutants}
        assert actual_names == expected_names

    def test_weather_values_realistic(self):
        """Weather values are within physically realistic ranges."""
        dt = datetime(2024, 6, 15, 14, 0, tzinfo=timezone.utc)
        payload = self.generator.generate_for_timestamp(dt)
        w = payload.weather

        assert -20 <= w.temperature_c <= 55
        assert 0 <= w.humidity_pct <= 100
        assert w.wind_speed_ms >= 0
        assert 0 <= w.wind_direction_deg <= 360
        assert 900 <= w.pressure_hpa <= 1080


# ──────────────────────────────────────────────────────────────────────────────
# Feature Engineer Tests
# ──────────────────────────────────────────────────────────────────────────────


class TestFeatureEngineer:
    """Test suite for FeatureEngineer."""

    def setup_method(self):
        """Initialize engineer for each test."""
        self.engineer = FeatureEngineer()

    def test_temporal_features_cyclical(self):
        """Cyclical encodings maintain sin²+cos²=1 identity."""
        dt = datetime(2024, 6, 15, 14, 30, tzinfo=timezone.utc)
        temporal = self.engineer.compute_temporal_features(dt)

        # Hour encoding: sin² + cos² should ≈ 1
        assert abs(temporal.hour_sin ** 2 + temporal.hour_cos ** 2 - 1.0) < 1e-10
        assert abs(temporal.day_sin ** 2 + temporal.day_cos ** 2 - 1.0) < 1e-10
        assert abs(temporal.month_sin ** 2 + temporal.month_cos ** 2 - 1.0) < 1e-10

    def test_temporal_features_values(self):
        """Temporal features have correct values."""
        dt = datetime(2024, 6, 15, 14, 30, tzinfo=timezone.utc)  # Saturday
        temporal = self.engineer.compute_temporal_features(dt)

        assert temporal.hour == 14
        assert temporal.day_of_week == 5  # Saturday
        assert temporal.month == 6
        assert temporal.is_weekend is True

    def test_wind_decomposition(self):
        """Wind decomposition produces correct U/V components."""
        # North wind (0°) should have V < 0, U = 0
        u, v = self.engineer.compute_wind_components(10.0, 0.0)
        assert abs(u) < 0.01
        assert v < 0

        # East wind (90°) should have U < 0
        u, v = self.engineer.compute_wind_components(10.0, 90.0)
        assert u < 0

        # Zero wind speed
        u, v = self.engineer.compute_wind_components(0.0, 45.0)
        assert u == 0.0
        assert v == 0.0

    def test_thi_computation(self):
        """Temperature-Humidity Index computes correctly."""
        thi = self.engineer.compute_temperature_humidity_index(30.0, 60.0)
        assert isinstance(thi, float)
        assert thi > 0

    def test_thermal_inversion_detection(self):
        """Thermal inversion detection logic works correctly."""
        # Conditions favorable for inversion: cold, humid night, calm winds
        assert self.engineer.detect_thermal_inversion(10.0, 80.0, 1.0, 5) is True

        # Conditions not favorable: hot, dry afternoon, windy
        assert self.engineer.detect_thermal_inversion(35.0, 30.0, 8.0, 14) is False

    def test_pollution_intensity_weighted(self):
        """Pollution intensity is weighted sum with PM2.5 dominant."""
        pollutants = {"pm25": 100, "pm10": 100, "no2": 100, "so2": 100, "co": 100, "o3": 100}
        intensity = self.engineer.compute_pollution_intensity(pollutants)
        assert intensity == 100.0  # All equal, weights sum to 1.0

    def test_transform_produces_feature_vector(self):
        """Full transform produces a valid FeatureVector."""
        generator = SyntheticDataGenerator()
        dt = datetime(2024, 6, 15, 12, 0, tzinfo=timezone.utc)
        payload = generator.generate_for_timestamp(dt)

        fv = self.engineer.transform(payload)

        assert fv.timestamp == dt
        assert fv.year == 2024
        assert fv.month == 6
        assert fv.pm25 >= 0
        assert fv.temporal is not None
        assert fv.derived is not None

    def test_flat_dict_has_all_fields(self):
        """to_flat_dict() contains all expected feature columns."""
        generator = SyntheticDataGenerator()
        dt = datetime(2024, 6, 15, 12, 0, tzinfo=timezone.utc)
        payload = generator.generate_for_timestamp(dt)

        fv = self.engineer.transform(payload)
        flat = fv.to_flat_dict()

        expected_keys = {
            "timestamp", "year", "month", "aqi_value",
            "pm25", "pm10", "no2", "so2", "co", "o3",
            "temperature_c", "humidity_pct", "wind_speed_ms",
            "hour_sin", "hour_cos", "day_sin", "day_cos",
            "wind_u_component", "wind_v_component",
            "temperature_humidity_index",
        }
        assert expected_keys.issubset(set(flat.keys()))

    def test_lag_features_accumulate(self):
        """Lag features update as history buffer grows."""
        generator = SyntheticDataGenerator()

        # Feed multiple timestamps
        for h in range(5):
            dt = datetime(2024, 6, 15, h, 0, tzinfo=timezone.utc)
            payload = generator.generate_for_timestamp(dt)
            self.engineer.transform(payload)

        lags = self.engineer.compute_lag_features()

        # After 5 observations, lag_1h should be available
        assert lags.aqi_lag_1h is not None

    def test_batch_transform_creates_dataframe(self):
        """Batch transform produces a DataFrame with correct shape."""
        generator = SyntheticDataGenerator()
        payloads = []

        for h in range(10):
            dt = datetime(2024, 6, 15, h, 0, tzinfo=timezone.utc)
            payloads.append(generator.generate_for_timestamp(dt))

        df = self.engineer.transform_batch(payloads)

        assert len(df) == 10
        assert "aqi_value" in df.columns
        assert "pm25" in df.columns
        assert "hour_sin" in df.columns
