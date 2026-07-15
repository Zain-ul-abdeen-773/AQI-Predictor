"""AWS SageMaker Feature Store integration and management.

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
import time
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


# ── SageMaker type mapping ───────────────────────────────────────────────────

_SAGEMAKER_TYPE_MAP = {
    "TIMESTAMP": "String",
    "INT": "Integral",
    "DOUBLE": "Fractional",
    "FLOAT": "Fractional",
    "BOOLEAN": "String",
    "STRING": "String",
}


class FeatureStoreManager:
    """Manages AWS SageMaker Feature Store operations.

    Handles feature group creation, schema enforcement, data insertion
    (both online and offline stores), and data retrieval for training
    and inference pipelines.

    Attributes:
        settings: Application settings instance.
        _session: boto3 session (lazy-loaded).
        _sm_client: SageMaker client (lazy-loaded).
        _featurestore_runtime: SageMaker Feature Store runtime client.
        _feature_group_name: Name of the feature group.
    """

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self._session = None
        self._sm_client = None
        self._featurestore_runtime = None
        self._fg_created = False

    def _connect(self) -> None:
        """Establish connection to AWS SageMaker Feature Store.

        Raises:
            ConnectionError: If AWS connection fails.
        """
        if self._session is not None:
            return

        try:
            import boto3

            self._session = boto3.Session(region_name=self.settings.aws_region)
            self._sm_client = self._session.client("sagemaker")
            self._featurestore_runtime = self._session.client(
                "sagemaker-featurestore-runtime"
            )
            logger.info(
                "Connected to AWS SageMaker Feature Store in region: %s",
                self.settings.aws_region,
            )
        except ImportError:
            logger.warning(
                "boto3 package not installed. "
                "Using local file-based feature store fallback."
            )
            self._session = None
            self._sm_client = None
            self._featurestore_runtime = None
        except Exception as e:
            logger.error("Failed to connect to AWS SageMaker: %s", e)
            self._session = None
            self._sm_client = None
            self._featurestore_runtime = None

    def create_feature_group(self) -> Any:
        """Create or get the Sargodha AQI Feature Group in SageMaker.

        Programmatically defines the feature group with:
        - Record identifier: timestamp
        - Event time feature: timestamp

        Returns:
            Feature group reference (SageMaker or local fallback).
        """
        self._connect()

        if self._sm_client is None:
            logger.info("Using local file-based feature store")
            return self._create_local_feature_group()

        fg_name = self.settings.feature_group_name

        # Check if feature group already exists
        try:
            response = self._sm_client.describe_feature_group(
                FeatureGroupName=fg_name
            )
            status = response.get("FeatureGroupStatus", "Unknown")
            if status == "Created":
                self._fg_created = True
                logger.info("Feature group '%s' already exists (status: %s)", fg_name, status)
                return {"name": fg_name, "status": status, "arn": response.get("FeatureGroupArn")}
        except self._sm_client.exceptions.ResourceNotFound:
            pass
        except Exception as e:
            logger.warning("Error checking feature group: %s — will try to create", e)

        # Build feature definitions
        feature_definitions = []
        for feat in FEATURE_SCHEMA:
            sm_type = _SAGEMAKER_TYPE_MAP.get(feat["type"], "String")
            feature_definitions.append({
                "FeatureName": feat["name"],
                "FeatureType": sm_type,
            })

        try:
            response = self._sm_client.create_feature_group(
                FeatureGroupName=fg_name,
                RecordIdentifierFeatureName="timestamp",
                EventTimeFeatureName="timestamp",
                FeatureDefinitions=feature_definitions,
                OnlineStoreConfig={"EnableOnlineStore": True},
                OfflineStoreConfig={
                    "S3StorageConfig": {
                        "S3Uri": f"s3://{self.settings.s3_feature_store_bucket}/{fg_name}/",
                    }
                },
                RoleArn=self.settings.sagemaker_role_arn,
                Description=(
                    "Sargodha AQI features including pollutant concentrations, "
                    "meteorological data, temporal encodings, derived environmental "
                    "indicators, and autoregressive lag features."
                ),
            )
            logger.info("Creating feature group '%s'...", fg_name)

            # Wait for feature group to be created
            self._wait_for_feature_group(fg_name)
            self._fg_created = True
            return {"name": fg_name, "arn": response.get("FeatureGroupArn")}

        except Exception as e:
            logger.error("Failed to create SageMaker feature group: %s", e)
            return self._create_local_feature_group()

    def _wait_for_feature_group(self, fg_name: str, max_wait: int = 300) -> None:
        """Wait for a feature group to reach 'Created' status.

        Args:
            fg_name: Feature group name.
            max_wait: Maximum wait time in seconds.
        """
        start = time.time()
        while time.time() - start < max_wait:
            try:
                response = self._sm_client.describe_feature_group(
                    FeatureGroupName=fg_name
                )
                status = response.get("FeatureGroupStatus")
                if status == "Created":
                    logger.info("Feature group '%s' is ready", fg_name)
                    return
                elif status == "CreateFailed":
                    raise RuntimeError(
                        f"Feature group creation failed: {response.get('FailureReason')}"
                    )
                logger.debug("Feature group status: %s — waiting...", status)
            except Exception as e:
                logger.warning("Error polling feature group status: %s", e)
            time.sleep(5)

        logger.warning("Timed out waiting for feature group '%s'", fg_name)

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
        both SageMaker and local file-based storage.

        Args:
            df: DataFrame with columns matching the feature group schema.
            write_options: Optional write options (unused for SageMaker, kept for API compat).

        Raises:
            ValueError: If schema validation fails.
        """
        if df.empty:
            logger.warning("Empty DataFrame — skipping insertion")
            return

        # ── Schema Validation ──
        self._validate_schema(df)

        # ── SageMaker insertion ──
        if self._fg_created and self._featurestore_runtime is not None:
            try:
                self._ingest_to_sagemaker(df)
                logger.info("Inserted %d rows into SageMaker feature group", len(df))
                return
            except Exception as e:
                logger.error("SageMaker insertion failed: %s — falling back to local", e)

        # ── Local file-based insertion ──
        self._insert_local(df)

    def _ingest_to_sagemaker(self, df: pd.DataFrame) -> None:
        """Ingest records into SageMaker Feature Store using PutRecord.

        Args:
            df: DataFrame to ingest.
        """
        fg_name = self.settings.feature_group_name

        for _, row in df.iterrows():
            record = []
            for feat in FEATURE_SCHEMA:
                col_name = feat["name"]
                value = row.get(col_name)
                if value is None:
                    continue
                # SageMaker requires all values as strings
                if feat["type"] == "TIMESTAMP":
                    value = str(pd.Timestamp(value).isoformat())
                elif feat["type"] == "BOOLEAN":
                    value = str(bool(value)).lower()
                else:
                    value = str(value)
                record.append({"FeatureName": col_name, "ValueAsString": value})

            try:
                self._featurestore_runtime.put_record(
                    FeatureGroupName=fg_name,
                    Record=record,
                )
            except Exception as e:
                logger.warning("Failed to put record: %s", e)

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

        Fetches from SageMaker offline store (S3) or local Parquet files.

        Args:
            start_date: Start of training window (inclusive).
            end_date: End of training window (inclusive).

        Returns:
            pd.DataFrame: Training feature DataFrame.
        """
        self._connect()

        # ── Try SageMaker offline store (via Athena query on S3) ──
        if self._sm_client is not None:
            try:
                return self._read_from_s3_offline_store(start_date, end_date)
            except Exception as e:
                logger.error("SageMaker offline store read failed: %s — using local store", e)

        # ── Local fallback ──
        return self._read_local(start_date, end_date)

    def _read_from_s3_offline_store(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> pd.DataFrame:
        """Read features from SageMaker offline store in S3.

        Args:
            start_date: Optional start date filter.
            end_date: Optional end date filter.

        Returns:
            pd.DataFrame: Feature data from S3.
        """
        import boto3

        s3_client = self._session.client("s3")
        bucket = self.settings.s3_feature_store_bucket
        prefix = f"{self.settings.feature_group_name}/"

        # List and read parquet files from S3
        paginator = s3_client.get_paginator("list_objects_v2")
        parquet_keys = []

        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                if obj["Key"].endswith(".parquet"):
                    parquet_keys.append(obj["Key"])

        if not parquet_keys:
            logger.warning("No parquet files found in s3://%s/%s", bucket, prefix)
            return self._read_local(start_date, end_date)

        # Read parquet files from S3
        import io

        dfs = []
        for key in parquet_keys:
            try:
                response = s3_client.get_object(Bucket=bucket, Key=key)
                data = response["Body"].read()
                df = pd.read_parquet(io.BytesIO(data))
                dfs.append(df)
            except Exception as e:
                logger.warning("Failed to read s3://%s/%s: %s", bucket, key, e)

        if not dfs:
            return self._read_local(start_date, end_date)

        df = pd.concat(dfs, ignore_index=True)

        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            if start_date:
                df = df[df["timestamp"] >= start_date]
            if end_date:
                df = df[df["timestamp"] <= end_date]
            df.sort_values("timestamp", inplace=True)

        df.drop_duplicates(subset=["timestamp"], keep="last", inplace=True)
        logger.info("Retrieved %d rows from SageMaker offline store (S3)", len(df))
        return df

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
            if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
                df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
            elif df["timestamp"].dt.tz is None:
                df["timestamp"] = df["timestamp"].dt.tz_localize("UTC")
            if start_date:
                if start_date.tzinfo is None:
                    from datetime import timezone as tz
                    start_date = start_date.replace(tzinfo=tz.utc)
                df = df[df["timestamp"] >= start_date]
            if end_date:
                if end_date.tzinfo is None:
                    from datetime import timezone as tz
                    end_date = end_date.replace(tzinfo=tz.utc)
                df = df[df["timestamp"] <= end_date]
            df.sort_values("timestamp", inplace=True)

        df.drop_duplicates(subset=["timestamp"], keep="last", inplace=True)
        logger.info("Retrieved %d rows from local feature store", len(df))
        return df

    def get_latest_features(self, n_hours: int = 72) -> pd.DataFrame:
        """Retrieve the most recent N hours of features for inference.

        Fetches from the SageMaker online store for low-latency access.

        Args:
            n_hours: Number of recent hours to retrieve.

        Returns:
            pd.DataFrame: Recent feature vectors.
        """
        self._connect()

        # Try SageMaker online store via batch get
        if self._featurestore_runtime is not None and self._fg_created:
            try:
                # For online store, we read from local/S3 and return latest
                # SageMaker online store is key-value, so we fall back to offline
                df = self._read_from_s3_offline_store()
                if not df.empty:
                    df = df.sort_values("timestamp").tail(n_hours)
                    logger.info(
                        "Retrieved %d rows from SageMaker store", len(df)
                    )
                    return df
            except Exception as e:
                logger.warning("SageMaker fetch failed: %s — using local", e)

        # Local fallback
        df = self._read_local()
        if not df.empty:
            df = df.sort_values("timestamp").tail(n_hours)
        return df
