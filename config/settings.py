"""Centralized configuration management using Pydantic BaseSettings.

All environment variables, API keys, thresholds, and application-wide
constants are defined here with strict type validation and sensible defaults.
Loads from .env file automatically for local development.
"""

from __future__ import annotations

import logging
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent
"""Absolute path to the project root directory."""


class AQICategory(str, Enum):
    """EPA AQI breakpoint categories with associated color codes."""

    GOOD = "Good"
    MODERATE = "Moderate"
    UNHEALTHY_SENSITIVE = "Unhealthy for Sensitive Groups"
    UNHEALTHY = "Unhealthy"
    VERY_UNHEALTHY = "Very Unhealthy"
    HAZARDOUS = "Hazardous"


AQI_BREAKPOINTS: dict[str, dict] = {
    AQICategory.GOOD: {"range": (0, 50), "color": "#2ECC71", "hex_bg": "#1B4332"},
    AQICategory.MODERATE: {"range": (51, 100), "color": "#F1C40F", "hex_bg": "#7C6F1B"},
    AQICategory.UNHEALTHY_SENSITIVE: {"range": (101, 150), "color": "#E67E22", "hex_bg": "#784212"},
    AQICategory.UNHEALTHY: {"range": (151, 200), "color": "#E74C3C", "hex_bg": "#78281F"},
    AQICategory.VERY_UNHEALTHY: {"range": (201, 300), "color": "#8E44AD", "hex_bg": "#4A235A"},
    AQICategory.HAZARDOUS: {"range": (301, 500), "color": "#7B241C", "hex_bg": "#4A0E0E"},
}
"""AQI category breakpoints with color coding for dashboard rendering."""


# ──────────────────────────────────────────────────────────────────────────────
# Settings
# ──────────────────────────────────────────────────────────────────────────────


class Settings(BaseSettings):
    """Application-wide settings loaded from environment variables.

    All sensitive keys are loaded from environment or .env file.
    Non-sensitive defaults are provided inline.

    Attributes:
        aqicn_api_key: API token for AQICN (https://aqicn.org/data-platform/token/).
        openweather_api_key: API key for OpenWeatherMap APIs.
        aws_region: AWS region for SageMaker and other services.
        sagemaker_role_arn: IAM role ARN for SageMaker operations.
        s3_feature_store_bucket: S3 bucket for feature store offline storage.
        target_city: The city being monitored.
        target_latitude: Latitude of the target location.
        target_longitude: Longitude of the target location.
        target_timezone: IANA timezone string for the target city.
        feature_group_name: SageMaker Feature Group name.
        feature_group_version: Feature group version.
        model_registry_name: SageMaker Model Package Group name.
        backfill_years: Number of years of historical data to backfill.
        backfill_batch_size: Rows per batch during backfill writes.
        api_retry_max_attempts: Maximum retry attempts for API calls.
        api_retry_wait_seconds: Base wait time for exponential backoff.
        api_rate_limit_per_minute: Maximum API calls per minute.
        forecast_horizon_hours: Hours into the future to predict.
        lookback_window_hours: Hours of historical data for LSTM input.
        aqi_alert_threshold: AQI value triggering hazardous alerts.
        lstm_hidden_size: Hidden dimension for Bi-LSTM layers.
        lstm_num_layers: Number of stacked LSTM layers.
        lstm_dropout: Dropout probability in LSTM.
        lstm_learning_rate: Initial learning rate for AdamW.
        lstm_epochs: Maximum training epochs.
        lstm_batch_size: Training batch size.
        optuna_n_trials: Number of Bayesian optimization trials for LightGBM.
        cv_n_splits: Number of TimeSeriesSplit folds.
        cache_ttl_seconds: TTL for API response caching.
        log_level: Application log level.
        fastapi_host: FastAPI server host.
        fastapi_port: FastAPI server port.
        news_rss_feeds: RSS feed URLs for regional news.
        news_keywords: Keywords for filtering relevant news.
    """

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── API Keys ──────────────────────────────────────────────────────────
    aqicn_api_key: str = Field(default="demo", description="AQICN API token")
    openweather_api_key: str = Field(default="", description="OpenWeatherMap API key")

    # ── ClearML Configuration ─────────────────────────────────────────────
    clearml_project_name: str = Field(default="AQI Predictor", description="ClearML Project Name")
    clearml_dataset_name: str = Field(default="Sargodha Features", description="ClearML Dataset Name")

    # ── Target Location ───────────────────────────────────────────────────
    target_city: str = Field(default="Sargodha", description="Target city name")
    target_latitude: float = Field(default=32.0836, description="Target latitude")
    target_longitude: float = Field(default=72.6711, description="Target longitude")
    target_timezone: str = Field(default="Asia/Karachi", description="IANA timezone")

    # ── SageMaker Feature Store & Model Registry ────────────────────────
    feature_group_name: str = Field(default="sargodha_aqi_features")
    feature_group_version: int = Field(default=1, ge=1)
    model_registry_name: str = Field(default="sargodha-aqi-forecast-model")

    # ── Data Pipeline ─────────────────────────────────────────────────────
    backfill_years: int = Field(default=5, ge=1, le=10)
    backfill_batch_size: int = Field(default=10_000, ge=100)
    api_retry_max_attempts: int = Field(default=5, ge=1, le=20)
    api_retry_wait_seconds: float = Field(default=1.0, ge=0.1)
    api_rate_limit_per_minute: int = Field(default=60, ge=1)

    # ── Model Architecture ────────────────────────────────────────────────
    forecast_horizon_hours: int = Field(default=72, ge=1, description="3 days = 72 hours")
    lookback_window_hours: int = Field(default=72, ge=1, description="Input sequence length")
    aqi_alert_threshold: int = Field(default=150, ge=50)

    # ── LSTM Hyperparameters ──────────────────────────────────────────────
    lstm_hidden_size: int = Field(default=128, ge=16)
    lstm_num_layers: int = Field(default=2, ge=1)
    lstm_dropout: float = Field(default=0.3, ge=0.0, le=0.8)
    lstm_learning_rate: float = Field(default=1e-3, gt=0.0)
    lstm_epochs: int = Field(default=100, ge=1)
    lstm_batch_size: int = Field(default=64, ge=8)

    # ── Advanced Training ─────────────────────────────────────────────────
    grad_accumulation_steps: int = Field(default=4, ge=1)
    lr_scheduler_type: str = Field(default="cosine_warm_restarts")
    mixed_precision: bool = Field(default=True)
    early_stopping_patience: int = Field(default=15, ge=1)
    early_stopping_min_delta: float = Field(default=1e-4, ge=0.0)

    # ── LightGBM Tuning ──────────────────────────────────────────────────
    optuna_n_trials: int = Field(default=50, ge=5)

    # ── Evaluation ────────────────────────────────────────────────────────
    cv_n_splits: int = Field(default=5, ge=2)

    # ── Caching & Performance ─────────────────────────────────────────────
    cache_ttl_seconds: int = Field(default=300, ge=60, description="5-minute default TTL")

    # ── Logging ───────────────────────────────────────────────────────────
    log_level: str = Field(default="INFO")

    # ── FastAPI ───────────────────────────────────────────────────────────
    fastapi_host: str = Field(default="0.0.0.0")
    fastapi_port: int = Field(default=8000, ge=1024, le=65535)

    # ── News Pipeline ─────────────────────────────────────────────────────
    news_rss_feeds: List[str] = Field(
        default=[
            "https://www.dawn.com/feeds/home",
            "https://tribune.com.pk/feed/home",
            "https://www.geo.tv/rss/1/1",
        ]
    )
    news_keywords: List[str] = Field(
        default=[
            "Sargodha",
            "smog",
            "pollution",
            "crop burning",
            "factory emissions",
            "air quality",
            "haze",
            "respiratory",
        ]
    )

    # ── Validators ────────────────────────────────────────────────────────

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Ensure log_level is a valid Python logging level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}, got '{v}'")
        return upper

    # ── Derived Properties ────────────────────────────────────────────────

    @property
    def coordinates(self) -> tuple[float, float]:
        """Return (latitude, longitude) tuple."""
        return (self.target_latitude, self.target_longitude)

    @property
    def project_root(self) -> Path:
        """Absolute path to the project root."""
        return PROJECT_ROOT

    @property
    def data_dir(self) -> Path:
        """Absolute path to data storage directory."""
        path = PROJECT_ROOT / "data"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def models_dir(self) -> Path:
        """Absolute path to trained models directory."""
        path = PROJECT_ROOT / "models"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def logs_dir(self) -> Path:
        """Absolute path to application logs directory."""
        path = PROJECT_ROOT / "logs"
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton Settings instance.

    Uses functools.lru_cache to ensure the settings are only parsed once
    during the application lifecycle. Thread-safe for concurrent access.

    Returns:
        Settings: The validated application settings.
    """
    settings = Settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format="%(asctime)s | %(name)-30s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger.info("Settings loaded successfully for target: %s", settings.target_city)
    return settings
