"""ClearML Dataset integration and management.

Handles programmatic dataset creation, data ingestion,
and offline store operations using ClearML Datasets.

Example:
    >>> from feature_pipeline.register import FeatureStoreManager
    >>> manager = FeatureStoreManager()
    >>> manager.insert_features(df)
"""

from __future__ import annotations

import logging
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from config.settings import Settings, get_settings

logger = logging.getLogger(__name__)


class FeatureStoreManager:
    """Manages ClearML Dataset operations.

    Handles dataset creation, data insertion
    and data retrieval for training and inference pipelines.

    Attributes:
        settings: Application settings instance.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._cache: pd.DataFrame | None = None
        self._cache_ts: float = 0.0
        self._cache_ttl: float = float(self.settings.cache_ttl_seconds)

    def insert_features(
        self,
        df: pd.DataFrame,
        write_options: dict[str, Any] | None = None,
    ) -> None:
        """Insert feature data into the ClearML dataset.

        Args:
            df: DataFrame with feature data.
            write_options: Optional write options.
        """
        if df.empty:
            logger.warning("Empty DataFrame - skipping insertion")
            return

        try:
            from clearml import Dataset

            # Ensure timestamp is correct type
            if "timestamp" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                if df["timestamp"].dt.tz is not None:
                    df["timestamp"] = df["timestamp"].dt.tz_localize(None)

            # Forward-fill then use column median for remaining NaNs
            # Avoids the misleading fillna(0) pattern
            numeric_cols = df.select_dtypes(include=["number"]).columns
            df[numeric_cols] = df[numeric_cols].ffill()
            col_medians = df[numeric_cols].median()
            df[numeric_cols] = df[numeric_cols].fillna(col_medians)

            # Save locally to temp file
            with tempfile.TemporaryDirectory() as tmpdir:
                csv_path = Path(tmpdir) / "features.csv"

                # If dataset exists, pull old data to append
                try:
                    old_dataset = Dataset.get(
                        dataset_project=self.settings.clearml_project_name,
                        dataset_name=self.settings.clearml_dataset_name,
                    )
                    local_path = old_dataset.get_local_copy()
                    old_csv = Path(local_path) / "features.csv"
                    if old_csv.exists():
                        old_df = pd.read_csv(old_csv)
                        if "timestamp" in old_df.columns:
                            old_df["timestamp"] = pd.to_datetime(old_df["timestamp"])

                        # Concatenate and drop duplicates
                        df = pd.concat([old_df, df]).drop_duplicates(
                            subset=["timestamp"], keep="last"
                        )
                except ValueError:
                    # Dataset doesn't exist yet, we will create a new one
                    pass

                df.sort_values("timestamp", inplace=True)
                df.to_csv(csv_path, index=False)

                # Create new dataset version
                dataset = Dataset.create(
                    dataset_project=self.settings.clearml_project_name,
                    dataset_name=self.settings.clearml_dataset_name,
                    description="Sargodha AQI features including pollutant concentrations, meteorological data, and lag features.",
                )

                dataset.add_files(str(csv_path))
                dataset.upload()
                dataset.finalize()

            # Invalidate local cache after new insert
            self._cache = None
            self._cache_ts = 0.0

            logger.info("Inserted %d total rows into ClearML dataset", len(df))
        except ImportError:
            logger.error("ClearML package not installed.")
        except Exception as e:
            logger.error("ClearML dataset insertion failed: %s", e)

    def get_training_data(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> pd.DataFrame:
        """Retrieve feature data for model training.

        Args:
            start_date: Start of training window (inclusive).
            end_date: End of training window (inclusive).

        Returns:
            pd.DataFrame: Training feature DataFrame.
        """
        try:
            from clearml import Dataset

            dataset = Dataset.get(
                dataset_project=self.settings.clearml_project_name,
                dataset_name=self.settings.clearml_dataset_name,
            )
            local_path = dataset.get_local_copy()
            csv_path = Path(local_path) / "features.csv"

            if not csv_path.exists():
                logger.warning("features.csv not found in ClearML dataset")
                return pd.DataFrame()

            df = pd.read_csv(csv_path)

            if not df.empty and "timestamp" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"], format="ISO8601", utc=True)
                if start_date:
                    if start_date.tzinfo is not None:
                        start_date = start_date.replace(tzinfo=None)
                    df = df[df["timestamp"] >= start_date]
                if end_date:
                    if end_date.tzinfo is not None:
                        end_date = end_date.replace(tzinfo=None)
                    df = df[df["timestamp"] <= end_date]
                df.sort_values("timestamp", inplace=True)

            logger.info("Retrieved %d rows from ClearML dataset", len(df))
            return df
        except ValueError as e:
            logger.warning("ClearML Dataset Error: %s", e)
        except Exception as e:
            logger.error("Failed to read from ClearML dataset: %s", e)

        return pd.DataFrame()

    def get_latest_features(self, n_hours: int = 72) -> pd.DataFrame:
        """Retrieve the most recent N hours of features for inference.

        Uses an in-memory cache with TTL to avoid downloading
        the full dataset from ClearML on every request. Cache refresh
        is atomic to prevent concurrent requests from triggering
        duplicate downloads.

        Args:
            n_hours: Number of recent hours to retrieve.

        Returns:
            pd.DataFrame: Recent feature vectors.
        """
        import threading

        now = time.time()
        cache_expired = (now - self._cache_ts) > self._cache_ttl

        if self._cache is None or cache_expired:
            # Atomic refresh: only one thread fetches at a time
            if not hasattr(self, "_refresh_lock"):
                self._refresh_lock = threading.Lock()
            if self._refresh_lock.acquire(blocking=False):
                try:
                    new_data = self.get_training_data()
                    # Atomic swap — assign only after successful fetch
                    self._cache = new_data
                    self._cache_ts = time.time()
                    if not self._cache.empty:
                        logger.info("Feature cache refreshed: %d total rows", len(self._cache))
                finally:
                    self._refresh_lock.release()

        if self._cache is not None and not self._cache.empty:
            return self._cache.sort_values("timestamp").tail(n_hours).copy()
        return pd.DataFrame()
