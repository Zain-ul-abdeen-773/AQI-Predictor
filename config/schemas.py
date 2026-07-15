"""Pydantic validation schemas for data flowing through all pipelines.

Every raw API response, processed feature vector, prediction output,
and inter-service payload is validated against these strict schemas
to ensure structural integrity at every boundary.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# ──────────────────────────────────────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────────────────────────────────────


class AQILevel(str, Enum):
    """AQI risk level classification."""

    GOOD = "Good"
    MODERATE = "Moderate"
    UNHEALTHY_SENSITIVE = "Unhealthy for Sensitive Groups"
    UNHEALTHY = "Unhealthy"
    VERY_UNHEALTHY = "Very Unhealthy"
    HAZARDOUS = "Hazardous"


class DataSource(str, Enum):
    """Enumeration of supported data source providers."""

    AQICN = "aqicn"
    OPENWEATHER = "openweather"
    SYNTHETIC = "synthetic"


class ModelType(str, Enum):
    """Supported model architecture types."""

    RIDGE = "ridge"
    ELASTICNET = "elasticnet"
    LIGHTGBM = "lightgbm"
    BILSTM_ATTENTION = "bilstm_attention"
    ENSEMBLE = "ensemble"


# ──────────────────────────────────────────────────────────────────────────────
# Raw API Response Schemas
# ──────────────────────────────────────────────────────────────────────────────


class PollutantReading(BaseModel):
    """Single pollutant concentration reading from any source.

    Attributes:
        name: Pollutant identifier (e.g., 'pm25', 'pm10', 'no2').
        value: Concentration value (µg/m³ or ppm depending on pollutant).
        unit: Measurement unit.
        timestamp: UTC timestamp of the reading.
    """

    name: str = Field(..., description="Pollutant identifier")
    value: float = Field(..., ge=-1.0, description="Concentration value")
    unit: str = Field(default="µg/m³", description="Measurement unit")
    timestamp: datetime = Field(..., description="UTC timestamp")

    @field_validator("name")
    @classmethod
    def normalize_pollutant_name(cls, v: str) -> str:
        """Normalize pollutant names to lowercase standard form."""
        mapping = {
            "pm2.5": "pm25", "pm2_5": "pm25", "PM2.5": "pm25",
            "pm10": "pm10", "PM10": "pm10",
            "no2": "no2", "NO2": "no2",
            "so2": "so2", "SO2": "so2",
            "co": "co", "CO": "co",
            "o3": "o3", "O3": "o3",
        }
        return mapping.get(v, v.lower())


class WeatherReading(BaseModel):
    """Meteorological observation from weather API.

    Attributes:
        temperature_c: Temperature in Celsius.
        humidity_pct: Relative humidity percentage.
        wind_speed_ms: Wind speed in meters per second.
        wind_direction_deg: Wind direction in degrees (0-360).
        pressure_hpa: Barometric pressure in hectopascals.
        precipitation_mm: Precipitation in millimeters (hourly).
        timestamp: UTC timestamp of the observation.
    """

    temperature_c: float = Field(..., ge=-60.0, le=65.0)
    humidity_pct: float = Field(..., ge=0.0, le=100.0)
    wind_speed_ms: float = Field(..., ge=0.0, le=120.0)
    wind_direction_deg: float = Field(..., ge=0.0, le=360.0)
    pressure_hpa: float = Field(..., ge=850.0, le=1090.0)
    precipitation_mm: float = Field(default=0.0, ge=0.0)
    timestamp: datetime = Field(..., description="UTC timestamp")


class RawDataPayload(BaseModel):
    """Combined raw data payload from all sources before feature engineering.

    Attributes:
        pollutants: List of pollutant readings.
        weather: Weather observation.
        aqi_value: Official AQI index value (target variable).
        source: Data source provider.
        fetch_timestamp: When the data was fetched.
    """

    pollutants: List[PollutantReading] = Field(..., min_length=1)
    weather: WeatherReading
    aqi_value: Optional[float] = Field(default=None, ge=0, le=500)
    source: DataSource = Field(default=DataSource.AQICN)
    fetch_timestamp: datetime = Field(default_factory=datetime.utcnow)


# ──────────────────────────────────────────────────────────────────────────────
# Processed Feature Schemas
# ──────────────────────────────────────────────────────────────────────────────


class TemporalFeatures(BaseModel):
    """Cyclical and categorical temporal features.

    Uses sine/cosine encoding for cyclical continuity.

    Attributes:
        hour: Hour of day (0-23).
        day_of_week: Day of week (0-6, Monday=0).
        month: Month (1-12).
        day_of_year: Day of year (1-366).
        hour_sin: sin(2π × hour / 24).
        hour_cos: cos(2π × hour / 24).
        day_sin: sin(2π × day_of_week / 7).
        day_cos: cos(2π × day_of_week / 7).
        month_sin: sin(2π × month / 12).
        month_cos: cos(2π × month / 12).
        is_weekend: Boolean weekend indicator.
    """

    hour: int = Field(..., ge=0, le=23)
    day_of_week: int = Field(..., ge=0, le=6)
    month: int = Field(..., ge=1, le=12)
    day_of_year: int = Field(..., ge=1, le=366)
    hour_sin: float = Field(...)
    hour_cos: float = Field(...)
    day_sin: float = Field(...)
    day_cos: float = Field(...)
    month_sin: float = Field(...)
    month_cos: float = Field(...)
    is_weekend: bool = Field(...)


class DerivedFeatures(BaseModel):
    """Computed environmental interaction features.

    Attributes:
        aqi_change_rate_1h: AQI change rate over 1-hour window.
        aqi_change_rate_3h: AQI change rate over 3-hour window.
        aqi_change_rate_6h: AQI change rate over 6-hour window.
        wind_u_component: Eastward wind component (m/s).
        wind_v_component: Northward wind component (m/s).
        wind_pm25_interaction: Cross-product of wind vector with PM2.5.
        wind_pm10_interaction: Cross-product of wind vector with PM10.
        temperature_humidity_index: THI boundary layer proxy.
        thermal_inversion_flag: Detected atmospheric inversion condition.
        pollution_intensity: Composite pollution intensity index.
    """

    aqi_change_rate_1h: float = Field(default=0.0)
    aqi_change_rate_3h: float = Field(default=0.0)
    aqi_change_rate_6h: float = Field(default=0.0)
    wind_u_component: float = Field(default=0.0)
    wind_v_component: float = Field(default=0.0)
    wind_pm25_interaction: float = Field(default=0.0)
    wind_pm10_interaction: float = Field(default=0.0)
    temperature_humidity_index: float = Field(default=0.0)
    thermal_inversion_flag: bool = Field(default=False)
    pollution_intensity: float = Field(default=0.0)


class LagFeatures(BaseModel):
    """Autoregressive lag features for time-series modeling.

    Attributes:
        aqi_lag_1h: AQI value 1 hour ago.
        aqi_lag_3h: AQI value 3 hours ago.
        aqi_lag_6h: AQI value 6 hours ago.
        aqi_lag_12h: AQI value 12 hours ago.
        aqi_lag_24h: AQI value 24 hours ago.
        pm25_lag_1h: PM2.5 value 1 hour ago.
        pm25_lag_3h: PM2.5 value 3 hours ago.
        pm25_rolling_mean_6h: Rolling 6-hour mean of PM2.5.
        pm25_rolling_std_6h: Rolling 6-hour std of PM2.5.
        pm25_rolling_mean_24h: Rolling 24-hour mean of PM2.5.
    """

    aqi_lag_1h: Optional[float] = Field(default=None)
    aqi_lag_3h: Optional[float] = Field(default=None)
    aqi_lag_6h: Optional[float] = Field(default=None)
    aqi_lag_12h: Optional[float] = Field(default=None)
    aqi_lag_24h: Optional[float] = Field(default=None)
    pm25_lag_1h: Optional[float] = Field(default=None)
    pm25_lag_3h: Optional[float] = Field(default=None)
    pm25_rolling_mean_6h: Optional[float] = Field(default=None)
    pm25_rolling_std_6h: Optional[float] = Field(default=None)
    pm25_rolling_mean_24h: Optional[float] = Field(default=None)


class FeatureVector(BaseModel):
    """Complete feature vector ready for model ingestion.

    Combines raw pollutant/weather values with all engineered features.

    Attributes:
        timestamp: UTC timestamp of the observation.
        year: Year partition key.
        month: Month partition key.
        aqi_value: Target AQI value (None during inference).
        pm25: PM2.5 concentration.
        pm10: PM10 concentration.
        no2: NO2 concentration.
        so2: SO2 concentration.
        co: CO concentration.
        o3: O3 concentration.
        temperature_c: Temperature in Celsius.
        humidity_pct: Relative humidity percentage.
        wind_speed_ms: Wind speed in m/s.
        wind_direction_deg: Wind direction in degrees.
        pressure_hpa: Barometric pressure.
        precipitation_mm: Hourly precipitation.
        temporal: Temporal feature block.
        derived: Derived feature block.
        lags: Lag feature block.
        source: Data source identifier.
    """

    timestamp: datetime
    year: int = Field(..., ge=2015, le=2035)
    month: int = Field(..., ge=1, le=12)

    # Target
    aqi_value: Optional[float] = Field(default=None, ge=0, le=500)

    # Raw pollutants
    pm25: float = Field(default=0.0, ge=0.0)
    pm10: float = Field(default=0.0, ge=0.0)
    no2: float = Field(default=0.0, ge=0.0)
    so2: float = Field(default=0.0, ge=0.0)
    co: float = Field(default=0.0, ge=0.0)
    o3: float = Field(default=0.0, ge=0.0)

    # Raw weather
    temperature_c: float = Field(default=25.0)
    humidity_pct: float = Field(default=50.0)
    wind_speed_ms: float = Field(default=0.0)
    wind_direction_deg: float = Field(default=0.0)
    pressure_hpa: float = Field(default=1013.25)
    precipitation_mm: float = Field(default=0.0)

    # Engineered features
    temporal: TemporalFeatures
    derived: DerivedFeatures
    lags: LagFeatures = Field(default_factory=LagFeatures)

    # Metadata
    source: DataSource = Field(default=DataSource.AQICN)

    def to_flat_dict(self) -> Dict[str, Any]:
        """Flatten nested feature blocks into a single-level dictionary.

        Returns:
            Dict[str, Any]: Flat dictionary suitable for DataFrame construction.
        """
        base = {
            "timestamp": self.timestamp,
            "year": self.year,
            "month": self.month,
            "aqi_value": self.aqi_value,
            "pm25": self.pm25,
            "pm10": self.pm10,
            "no2": self.no2,
            "so2": self.so2,
            "co": self.co,
            "o3": self.o3,
            "temperature_c": self.temperature_c,
            "humidity_pct": self.humidity_pct,
            "wind_speed_ms": self.wind_speed_ms,
            "wind_direction_deg": self.wind_direction_deg,
            "pressure_hpa": self.pressure_hpa,
            "precipitation_mm": self.precipitation_mm,
            "source": self.source.value,
        }
        # Flatten temporal
        base.update(self.temporal.model_dump())
        # Flatten derived
        base.update(self.derived.model_dump())
        # Flatten lags
        base.update(self.lags.model_dump())
        return base


# ──────────────────────────────────────────────────────────────────────────────
# Prediction / Response Schemas
# ──────────────────────────────────────────────────────────────────────────────


class HourlyPrediction(BaseModel):
    """Single hourly AQI prediction with uncertainty bounds.

    Attributes:
        timestamp: Predicted timestamp.
        aqi_predicted: Point prediction of AQI value.
        aqi_lower_80: Lower bound of 80% prediction interval.
        aqi_upper_80: Upper bound of 80% prediction interval.
        aqi_lower_95: Lower bound of 95% prediction interval.
        aqi_upper_95: Upper bound of 95% prediction interval.
        level: Categorized AQI risk level.
    """

    timestamp: datetime
    aqi_predicted: float = Field(..., ge=0)
    aqi_lower_80: Optional[float] = Field(default=None)
    aqi_upper_80: Optional[float] = Field(default=None)
    aqi_lower_95: Optional[float] = Field(default=None)
    aqi_upper_95: Optional[float] = Field(default=None)
    level: AQILevel = Field(default=AQILevel.GOOD)


class ForecastResponse(BaseModel):
    """Complete 3-day AQI forecast response from the /predict endpoint.

    Attributes:
        city: Target city name.
        generated_at: When the forecast was generated.
        model_type: Which model produced the forecast.
        model_version: Model version used.
        current_aqi: Current measured AQI value.
        current_level: Current AQI risk level.
        hourly_predictions: List of hourly predictions for the forecast horizon.
        summary: Human-readable summary of the forecast.
        alert: Whether any predicted values exceed the alert threshold.
    """

    city: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    model_type: ModelType
    model_version: str = Field(default="1.0.0")
    current_aqi: float = Field(..., ge=0)
    current_level: AQILevel
    hourly_predictions: List[HourlyPrediction] = Field(..., min_length=1)
    summary: str = Field(default="")
    alert: bool = Field(default=False)


class SHAPExplanation(BaseModel):
    """SHAP feature contribution explanation for a prediction.

    Attributes:
        feature_name: Name of the input feature.
        shap_value: SHAP contribution value.
        feature_value: Actual value of the feature in the input.
        direction: Whether this feature pushed prediction up or down.
    """

    feature_name: str
    shap_value: float
    feature_value: float
    direction: str = Field(default="neutral")

    @field_validator("direction", mode="before")
    @classmethod
    def compute_direction(cls, v: str, info) -> str:
        """Auto-compute direction from SHAP value if not provided."""
        if v == "neutral" and "shap_value" in info.data:
            shap_val = info.data["shap_value"]
            if shap_val > 0.01:
                return "increase"
            elif shap_val < -0.01:
                return "decrease"
        return v


class ExplainResponse(BaseModel):
    """Response from the /explain endpoint.

    Attributes:
        prediction_aqi: The AQI value being explained.
        base_value: SHAP base/expected value.
        contributions: Ordered list of feature contributions.
        model_type: Which model was explained.
    """

    prediction_aqi: float
    base_value: float
    contributions: List[SHAPExplanation]
    model_type: ModelType


class HealthResponse(BaseModel):
    """Response from the /health endpoint.

    Attributes:
        status: Service health status.
        version: Application version.
        feature_store_connected: SageMaker Feature Store connection status.
        model_loaded: Whether prediction model is loaded.
        uptime_seconds: Time since service start.
    """

    status: str = Field(default="healthy")
    version: str = Field(default="1.0.0")
    feature_store_connected: bool = Field(default=False)
    model_loaded: bool = Field(default=False)
    uptime_seconds: float = Field(default=0.0)


class NewsItem(BaseModel):
    """Regional news article with sentiment analysis.

    Attributes:
        title: Article headline.
        url: Link to the full article.
        source: News outlet name.
        published_at: Publication timestamp.
        sentiment_score: Sentiment analysis score (-1 to 1).
        relevance_keywords: Matched keywords from the article.
        risk_factor: Computed regional risk factor.
    """

    title: str
    url: str = Field(default="")
    source: str = Field(default="unknown")
    published_at: Optional[datetime] = Field(default=None)
    sentiment_score: float = Field(default=0.0, ge=-1.0, le=1.0)
    relevance_keywords: List[str] = Field(default_factory=list)
    risk_factor: str = Field(default="Low")


class AnomalyDetectionResult(BaseModel):
    """Result from the anomaly detection subsystem.

    Attributes:
        timestamp: When the anomaly check was performed.
        is_anomaly: Whether the reading is anomalous.
        anomaly_score: Isolation Forest anomaly score (-1 = anomalous, 1 = normal).
        contributing_features: Features contributing most to anomaly.
    """

    timestamp: datetime
    is_anomaly: bool = Field(default=False)
    anomaly_score: float = Field(default=0.0)
    contributing_features: List[str] = Field(default_factory=list)
