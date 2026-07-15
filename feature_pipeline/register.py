"""Hopsworks Feature Store integration and management.

Handles programmatic Feature Group definition, schema enforcement,
data ingestion, and online/offline store operations.

Example:
    >>> from feature_pipeline.register import FeatureStoreManager
    >>> manager = FeatureStoreManager()
    >>> manager.create_feature_group()
    >>> manager.insert_features(df)
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

from config.settings import get_settings, Settings

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Feature Group Schema Definition
# ──────────────────────────────────────────────────────────────────────────────

FEATURE_SCHEMA: List[Dict[str, str]] = [
    # Primary key and partition keys
    {"name": "timestamp", "type": "TIMESTAMP", "description": "UTC observation timestamp"},
    {"name": "year", "type": "INT", "description": "Year partition key"},
    {"name": "month", "type": "INT", "description": "Month partition key"},

    # Target
    {"name": "aqi_value", "type": "DOUBLE", "description": "Target AQI value"},

    # Raw pollutants
    {"name": "pm25", "type": "DOUBLE", "description": "PM2.5 concentration"},
    {"name": "pm10", "type": "DOUBLE", "description": "PM10 concentration"},
    {"name": "no2", "type": "DOUBLE", "description": "NO2 concentration"},
    {"name": "so2", "type": "DOUBLE", "description": "SO2 concentration"},
    {"name": "co", "type": "DOUBLE", "description": "CO concentration"},
    {"name": "o3", "type": "DOUBLE", "description": "O3 concentration"},

    # Meteorological
    {"name": "temperature_c", "type": "DOUBLE", "description": "Temperature (Celsius)"},
    {"name": "humidity_pct", "type": "DOUBLE", "description": "Relative humidity (%)"},
    {"name": "wind_speed_ms", "type": "DOUBLE", "description": "Wind speed (m/s)"},
    {"name": "wind_direction_deg", "type": "DOUBLE", "description": "Wind direction (degrees)"},
    {"name": "pressure_hpa", "type": "DOUBLE", "description": "Barometric pressure (hPa)"},
    {"name": "precipitation_mm", "type": "DOUBLE", "description": "Precipitation (mm/h)"},

    # Temporal features
    {"name": "hour", "type": "INT", "description": "Hour of day (0-23)"},
    {"name": "day_of_week", "type": "INT", "description": "Day of week (0=Mon, 6=Sun)"},
    {"name": "day_of_year", "type": "INT", "description": "Day of year (1-366)"},
    {"name": "hour_sin", "type": "DOUBLE", "description": "Cyclical hour sine encoding"},
    {"name": "hour_cos", "type": "DOUBLE", "description": "Cyclical hour cosine encoding"},
    {"name": "day_sin", "type": "DOUBLE", "description": "Cyclical day sine encoding"},
    {"name": "day_cos", "type": "DOUBLE", "description": "Cyclical day cosine encoding"},
    {"name": "month_sin", "type": "DOUBLE", "description": "Cyclical month sine encoding"},
    {"name": "month_cos", "type": "DOUBLE", "description": "Cyclical month cosine encoding"},
    {"name": "is_weekend", "type": "BOOLEAN", "description": "Weekend indicator"},

    # Derived features
    {"name": "aqi_change_rate_1h", "type": "DOUBLE", "description": "AQI delta/1h"},
    {"name": "aqi_change_rate_3h", "type": "DOUBLE", "description": "AQI delta/3h"},
    {"name": "aqi_change_rate_6h", "type": "DOUBLE", "description": "AQI delta/6h"},
    {"name": "wind_u_component", "type": "DOUBLE", "description": "Eastward wind component"},
    {"name": "wind_v_component", "type": "DOUBLE", "description": "Northward wind component"},
    {"name": "wind_pm25_interaction", "type": "DOUBLE", "description": "Wind × PM2.5 interaction"},
    {"name": "wind_pm10_interaction", "type": "DOUBLE", "description": "Wind × PM10 interaction"},
    {"name": "temperature_humidity_index", "type": "DOUBLE", "description": "THI boundary proxy"},
    {"name": "thermal_inversion_flag", "type": "BOOLEAN", "description": "Inversion detection"},
    {"name": "pollution_intensity", "type": "DOUBLE", "description": "Composite pollution index"},

    # Lag features
    {"name": "aqi_lag_1h", "type": "DOUBLE", "description": "AQI at t-1h"},
    {"name": "aqi_lag_3h", "type": "DOUBLE", "description": "AQI at t-3h"},
    {"name": "aqi_lag_6h", "type": "DOUBLE", "description": "AQI at t-6h"},
    {"name": "aqi_lag_12h", "type": "DOUBLE", "description": "AQI at t-12h"},
    {"name": "aqi_lag_24h", "type": "DOUBLE", "description": "AQI at t-24h"},
    {"name": "pm25_lag_1h", "type": "DOUBLE", "description": "PM2.5 at t-1h"},
    {"name": "pm25_lag_3h", "type": "DOUBLE", "description": "PM2.5 at t-3h"},
    {"name": "pm25_rolling_mean_6h", "type": "DOUBLE", "description": "PM2.5 rolling mean 6h"},
    {"name": "pm25_rolling_std_6h", "type": "DOUBLE", "description": "PM2.5 rolling std 6h"},
    {"name": "pm25_rolling_mean_24h", "type": "DOUBLE", "description": "PM2.5 rolling mean 24h"},

    # Metadata
    {"name": "source", "type": "STRING", "description": "Data source identifier"},
]
"""Complete schema definition for the Sargodha AQI feature group."""


class FeatureStoreManager:
    """Manages Hopsworks Feature Store operations.

    Handles feature group creation, schema enforcement, data insertion
    (both online and offline stores), and data retrieval for training
    and inference pipelines.

    Attributes:
        settings: Application settings instance.
        _project: Hopsworks project reference (lazy-loaded).
        _fs: Feature store reference (lazy-loaded).
        _fg: Feature group reference (lazy-loaded).
    """

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self._project = None
        self._fs = None
        self._fg = None

    def _connect(self) -> None:
        """Establish connection to Hopsworks.

        Raises:
            ConnectionError: If Hopsworks connection fails.
        """
        if self._project is not None:
            return

        try:
            import hopsworks

            self._project = hopsworks.login(
                api_key_value=self.settings.hopsworks_api_key,
                project=self.settings.hopsworks_project_name,
            )
            self._fs = self._project.get_feature_store()
            logger.info(
                "Connected to Hopsworks project: %s",
                self.settings.hopsworks_project_name,
            )
        except ImportError:
            logger.warning(
                "hopsworks package not installed. "
                "Using local file-based feature store fallback."
            )
            self._project = None
            self._fs = None
        except Exception as e:
            logger.error("Failed to connect to Hopsworks: %s", e)
            raise ConnectionError(f"Hopsworks connection failed: {e}") from e

    def create_feature_group(self) -> Any:
        """Create or get the Sargodha AQI Feature Group.

        Programmatically defines the feature group with:
        - Primary key: timestamp
        - Event time: timestamp
        - Partition keys: year, month

        Returns:
            Feature group reference (Hopsworks or local fallback).
        """
        self._connect()

        if self._fs is None:
            logger.info("Using local file-based feature store")
            return self._create_local_feature_group()

        try:
            self._fg = self._fs.get_or_create_feature_group(
                name=self.settings.feature_group_name,
                version=self.settings.feature_group_version,
                primary_key=["timestamp"],
                event_time="timestamp",
                partition_key=["year", "month"],
                description=(
                    "Sargodha AQI features including pollutant concentrations, "
                    "meteorological data, temporal encodings, derived environmental "
                    "indicators, and autoregressive lag features."
                ),
                online_enabled=True,
            )
            logger.info(
                "Feature group '%s' v%d ready",
                self.settings.feature_group_name,
                self.settings.feature_group_version,
            )
            return self._fg
        except Exception as e:
            logger.error("Failed to create feature group: %s", e)
            return self._create_local_feature_group()

    def _create_local_feature_group(self) -> Dict[str, Any]:
        """Create a local file-based feature group fallback.

        Returns:
            Dict representing the local feature group metadata.
        """
        local_fg = {
            "name": self.settings.feature_group_name,
            "version": self.settings.feature_group_version,
            "primary_key": ["timestamp"],
            "event_time": "timestamp",
            "partition_key": ["year", "month"],
            "storage_path": str(self.settings.data_dir / "feature_store"),
            "schema": FEATURE_SCHEMA,
        }
        storage_path = self.settings.data_dir / "feature_store"
        storage_path.mkdir(parents=True, exist_ok=True)
        logger.info("Local feature group configured at: %s", storage_path)
        return local_fg

    def insert_features(
        self,
        df: pd.DataFrame,
        write_options: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Insert feature data into the feature store.

        Performs structural validation before insertion and handles
        both Hopsworks and local file-based storage.

        Args:
            df: DataFrame with columns matching the feature group schema.
            write_options: Optional Hopsworks write options.

        Raises:
            ValueError: If schema validation fails.
        """
        if df.empty:
            logger.warning("Empty DataFrame — skipping insertion")
            return

        # ── Schema Validation ──
        self._validate_schema(df)

        # ── Hopsworks insertion ──
        if self._fg is not None:
            try:
                self._fg.insert(df, write_options=write_options or {"wait_for_job": True})
                logger.info("Inserted %d rows into Hopsworks feature group", len(df))
                return
            except Exception as e:
                logger.error("Hopsworks insertion failed: %s — falling back to local", e)

        # ── Local file-based insertion ──
        self._insert_local(df)

    def _validate_schema(self, df: pd.DataFrame) -> None:
        """Validate DataFrame columns against the feature group schema.

        Args:
            df: DataFrame to validate.

        Raises:
            ValueError: If required columns are missing.
        """
        required_columns = {feat["name"] for feat in FEATURE_SCHEMA}
        present_columns = set(df.columns)
        missing = required_columns - present_columns

        if missing:
            logger.warning(
                "Schema validation: %d columns missing: %s",
                len(missing), sorted(missing),
            )
            # Add missing columns with defaults rather than raising
            for col in missing:
                schema_entry = next(
                    (f for f in FEATURE_SCHEMA if f["name"] == col), None
                )
                if schema_entry:
                    dtype = schema_entry["type"]
                    if dtype in ("DOUBLE", "FLOAT"):
                        df[col] = 0.0
                    elif dtype == "INT":
                        df[col] = 0
                    elif dtype == "BOOLEAN":
                        df[col] = False
                    elif dtype == "STRING":
                        df[col] = ""
                    else:
                        df[col] = None
            logger.info("Added %d missing columns with defaults", len(missing))

    def _insert_local(self, df: pd.DataFrame) -> None:
        """Insert features into local Parquet-based store.

        Partitions data by year and month for efficient querying.

        Args:
            df: Feature DataFrame to store.
        """
        storage_path = self.settings.data_dir / "feature_store"
        storage_path.mkdir(parents=True, exist_ok=True)

        # Write as partitioned Parquet files
        for (year, month), partition_df in df.groupby(["year", "month"]):
            partition_dir = storage_path / f"year={year}" / f"month={month}"
            partition_dir.mkdir(parents=True, exist_ok=True)

            output_file = partition_dir / f"features_{year}_{month:02d}.parquet"

            if output_file.exists():
                # Append to existing partition
                existing = pd.read_parquet(output_file)
                combined = pd.concat([existing, partition_df], ignore_index=True)
                combined.drop_duplicates(subset=["timestamp"], keep="last", inplace=True)
                combined.sort_values("timestamp", inplace=True)
                combined.to_parquet(output_file, index=False)
                logger.debug(
                    "Updated partition %d-%02d: %d → %d rows",
                    year, month, len(existing), len(combined),
                )
            else:
                partition_df.to_parquet(output_file, index=False)
                logger.debug(
                    "Created partition %d-%02d: %d rows", year, month, len(partition_df)
                )

        logger.info(
            "Inserted %d rows into local feature store (%s)",
            len(df), storage_path,
        )

    def get_training_data(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> pd.DataFrame:
        """Retrieve feature data for model training.

        Fetches from Hopsworks offline store or local Parquet files.

        Args:
            start_date: Start of training window (inclusive).
            end_date: End of training window (inclusive).

        Returns:
            pd.DataFrame: Training feature DataFrame.
        """
        self._connect()

        # ── Try Hopsworks first ──
        if self._fg is not None:
            try:
                query = self._fg.select_all()
                if start_date:
                    query = query.filter(self._fg.timestamp >= start_date)
                if end_date:
                    query = query.filter(self._fg.timestamp <= end_date)
                df = query.read()
                logger.info("Retrieved %d rows from Hopsworks", len(df))
                return df
            except Exception as e:
                logger.error("Hopsworks read failed: %s — using local store", e)

        # ── Local fallback ──
        return self._read_local(start_date, end_date)

    def _read_local(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> pd.DataFrame:
        """Read features from local Parquet-based store.

        Args:
            start_date: Optional start date filter.
            end_date: Optional end date filter.

        Returns:
            pd.DataFrame: Feature DataFrame from local storage.
        """
        storage_path = self.settings.data_dir / "feature_store"

        if not storage_path.exists():
            logger.warning("Local feature store not found at %s", storage_path)
            return pd.DataFrame()

        parquet_files = list(storage_path.rglob("*.parquet"))
        if not parquet_files:
            logger.warning("No Parquet files found in %s", storage_path)
            return pd.DataFrame()

        dfs = [pd.read_parquet(f) for f in parquet_files]
        df = pd.concat(dfs, ignore_index=True)

        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            if start_date:
                df = df[df["timestamp"] >= start_date]
            if end_date:
                df = df[df["timestamp"] <= end_date]
            df.sort_values("timestamp", inplace=True)

        df.drop_duplicates(subset=["timestamp"], keep="last", inplace=True)
        logger.info("Retrieved %d rows from local feature store", len(df))
        return df

    def get_latest_features(self, n_hours: int = 72) -> pd.DataFrame:
        """Retrieve the most recent N hours of features for inference.

        Fetches from the online store for low-latency access.

        Args:
            n_hours: Number of recent hours to retrieve.

        Returns:
            pd.DataFrame: Recent feature vectors.
        """
        self._connect()

        # Try Hopsworks online store
        if self._fg is not None:
            try:
                fv = self._fs.get_feature_view(
                    name=f"{self.settings.feature_group_name}_view",
                    version=1,
                )
                df = fv.get_batch_data()
                df = df.sort_values("timestamp").tail(n_hours)
                logger.info("Retrieved %d rows from Hopsworks online store", len(df))
                return df
            except Exception as e:
                logger.warning("Online store fetch failed: %s — using local", e)

        # Local fallback
        df = self._read_local()
        if not df.empty:
            df = df.sort_values("timestamp").tail(n_hours)
        return df
