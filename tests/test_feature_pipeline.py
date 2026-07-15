"""Tests for the feature pipeline module."""

from __future__ import annotations

import pandas as pd
import pytest

from feature_pipeline.register import FeatureStoreManager, FEATURE_SCHEMA


class TestFeatureSchema:
    """Test suite for feature schema definition."""

    def test_schema_has_required_fields(self):
        """Schema contains all required feature definitions."""
        names = {f["name"] for f in FEATURE_SCHEMA}

        required = {
            "timestamp", "year", "month", "aqi_value",
            "pm25", "pm10", "no2", "so2", "co", "o3",
            "temperature_c", "humidity_pct", "wind_speed_ms",
            "hour_sin", "hour_cos", "day_sin", "day_cos",
        }
        assert required.issubset(names), f"Missing: {required - names}"

    def test_schema_types_valid(self):
        """All schema entries have valid type definitions."""
        valid_types = {"TIMESTAMP", "INT", "DOUBLE", "BOOLEAN", "STRING", "FLOAT"}
        for feature in FEATURE_SCHEMA:
            assert feature["type"] in valid_types, \
                f"Invalid type '{feature['type']}' for '{feature['name']}'"

    def test_schema_no_duplicate_names(self):
        """No duplicate feature names in schema."""
        names = [f["name"] for f in FEATURE_SCHEMA]
        assert len(names) == len(set(names)), "Duplicate feature names found"


class TestFeatureStoreManager:
    """Test suite for FeatureStoreManager."""

    def test_local_feature_group_creation(self):
        """Local feature group creation works without Hopsworks."""
        manager = FeatureStoreManager()
        fg = manager._create_local_feature_group()

        assert fg["name"] == "sargodha_aqi_features"
        assert fg["version"] == 1
        assert fg["primary_key"] == ["timestamp"]
        assert fg["event_time"] == "timestamp"

    def test_schema_validation_adds_missing_columns(self):
        """Schema validation adds missing columns with defaults."""
        manager = FeatureStoreManager()

        df = pd.DataFrame({
            "timestamp": ["2024-01-01"],
            "year": [2024],
            "month": [1],
        })

        manager._validate_schema(df)

        # Missing columns should be added
        assert "pm25" in df.columns
        assert "hour_sin" in df.columns

    def test_insert_and_read_local(self):
        """Local insert and read cycle works correctly."""
        manager = FeatureStoreManager()

        # Create a minimal test DataFrame
        df = pd.DataFrame({
            "timestamp": pd.to_datetime(["2024-01-01 00:00", "2024-01-01 01:00"]),
            "year": [2024, 2024],
            "month": [1, 1],
            "aqi_value": [100.0, 110.0],
            "pm25": [50.0, 55.0],
        })

        # Add required columns
        manager._validate_schema(df)

        # Insert
        manager._insert_local(df)

        # Read back
        result = manager._read_local()
        assert len(result) >= 2
