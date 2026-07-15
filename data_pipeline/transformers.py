"""Advanced feature engineering for AQI prediction.

Implements all required and advanced feature transformations:
- Cyclical temporal encoding (sin/cos for hour, day, month)
- AQI change rate (1h, 3h, 6h rolling derivatives)
- Wind-pollutant vector interactions (U/V decomposition)
- Boundary layer proxy (Temperature-Humidity Index)
- Thermal inversion detection
- Lag features (t-1, t-3, t-6, t-12, t-24)
- Rolling statistics (mean, std over 6h and 24h windows)
- Composite pollution intensity index

Example:
    >>> from data_pipeline.transformers import FeatureEngineer
    >>> engineer = FeatureEngineer()
    >>> df = engineer.transform(raw_df)
"""

from __future__ import annotations

import logging
import math
from datetime import datetime, timezone
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from config.settings import get_settings, Settings
from config.schemas import (
    DerivedFeatures,
    FeatureVector,
    LagFeatures,
    RawDataPayload,
    TemporalFeatures,
    DataSource,
)

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """Transforms raw data payloads into feature vectors for ML consumption.

    Applies a comprehensive suite of feature engineering techniques including
    temporal encoding, environmental interaction features, and autoregressive
    lag features for time-series forecasting.

    Attributes:
        settings: Application settings instance.
        _history_buffer: In-memory buffer of recent AQI values for lag computation.
    """

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self._history_buffer: List[Dict] = []

    # ──────────────────────────────────────────────────────────────────────
    # Temporal Features
    # ──────────────────────────────────────────────────────────────────────

    @staticmethod
    def compute_temporal_features(dt: datetime) -> TemporalFeatures:
        """Compute cyclical temporal features from a datetime.

        Uses sine and cosine encoding to maintain cyclical continuity
        at period boundaries (e.g., hour 23 → 0).

        Args:
            dt: UTC datetime to extract temporal features from.

        Returns:
            TemporalFeatures: Complete set of cyclical + categorical features.
        """
        hour = dt.hour
        dow = dt.weekday()  # Monday=0
        month = dt.month
        doy = dt.timetuple().tm_yday

        return TemporalFeatures(
            hour=hour,
            day_of_week=dow,
            month=month,
            day_of_year=doy,
            hour_sin=math.sin(2 * math.pi * hour / 24),
            hour_cos=math.cos(2 * math.pi * hour / 24),
            day_sin=math.sin(2 * math.pi * dow / 7),
            day_cos=math.cos(2 * math.pi * dow / 7),
            month_sin=math.sin(2 * math.pi * month / 12),
            month_cos=math.cos(2 * math.pi * month / 12),
            is_weekend=dow >= 5,
        )

    # ──────────────────────────────────────────────────────────────────────
    # Derived Environmental Features
    # ──────────────────────────────────────────────────────────────────────

    @staticmethod
    def compute_wind_components(
        wind_speed: float, wind_direction_deg: float
    ) -> tuple[float, float]:
        """Decompose wind into eastward (U) and northward (V) components.

        Uses standard meteorological convention where wind direction
        indicates where the wind is coming FROM.

        Args:
            wind_speed: Wind speed in m/s.
            wind_direction_deg: Wind direction in degrees (0-360).

        Returns:
            Tuple of (u_component, v_component) in m/s.
        """
        wind_dir_rad = math.radians(wind_direction_deg)
        u = -wind_speed * math.sin(wind_dir_rad)
        v = -wind_speed * math.cos(wind_dir_rad)
        return round(u, 4), round(v, 4)

    @staticmethod
    def compute_temperature_humidity_index(
        temperature_c: float, humidity_pct: float
    ) -> float:
        """Compute Temperature-Humidity Index (THI) as boundary layer proxy.

        THI serves as a proxy for atmospheric inversion layer conditions.
        High THI with low wind suggests stagnant air trapping pollutants.

        Formula: THI = T - (0.55 - 0.0055 * RH) * (T - 14.5)

        Args:
            temperature_c: Temperature in Celsius.
            humidity_pct: Relative humidity percentage.

        Returns:
            float: Temperature-Humidity Index value.
        """
        thi = temperature_c - (0.55 - 0.0055 * humidity_pct) * (temperature_c - 14.5)
        return round(thi, 4)

    @staticmethod
    def detect_thermal_inversion(
        temperature_c: float,
        humidity_pct: float,
        wind_speed_ms: float,
        hour: int,
    ) -> bool:
        """Detect potential thermal inversion conditions.

        Thermal inversions trap pollutants near the surface. Common conditions:
        - Low wind speed (< 2 m/s)
        - Cool temperatures at night/early morning
        - High humidity

        Args:
            temperature_c: Temperature in Celsius.
            humidity_pct: Relative humidity percentage.
            wind_speed_ms: Wind speed in m/s.
            hour: Hour of day (0-23).

        Returns:
            bool: True if inversion conditions are likely.
        """
        is_night_or_dawn = hour < 8 or hour > 20
        low_wind = wind_speed_ms < 2.0
        high_humidity = humidity_pct > 70.0
        cool_temp = temperature_c < 20.0

        return is_night_or_dawn and low_wind and (high_humidity or cool_temp)

    @staticmethod
    def compute_pollution_intensity(pollutant_dict: Dict[str, float]) -> float:
        """Compute composite pollution intensity index.

        Weighted sum of normalized pollutant concentrations with
        PM2.5 receiving the highest weight due to health impact.

        Args:
            pollutant_dict: Dictionary of pollutant name → concentration.

        Returns:
            float: Composite pollution intensity score (0-500+).
        """
        weights = {
            "pm25": 0.35,
            "pm10": 0.20,
            "no2": 0.15,
            "so2": 0.10,
            "co": 0.10,
            "o3": 0.10,
        }
        intensity = 0.0
        for name, weight in weights.items():
            value = pollutant_dict.get(name, 0.0)
            intensity += weight * value
        return round(intensity, 4)

    def compute_derived_features(
        self,
        weather: Dict[str, float],
        pollutant_dict: Dict[str, float],
        hour: int,
    ) -> DerivedFeatures:
        """Compute all derived environmental features.

        Args:
            weather: Weather observation as dict.
            pollutant_dict: Pollutant concentrations as dict.
            hour: Hour of day.

        Returns:
            DerivedFeatures: Complete derived feature set.
        """
        wind_speed = weather.get("wind_speed_ms", 0.0)
        wind_dir = weather.get("wind_direction_deg", 0.0)
        temp = weather.get("temperature_c", 25.0)
        humidity = weather.get("humidity_pct", 50.0)

        u, v = self.compute_wind_components(wind_speed, wind_dir)
        thi = self.compute_temperature_humidity_index(temp, humidity)
        inversion = self.detect_thermal_inversion(temp, humidity, wind_speed, hour)
        intensity = self.compute_pollution_intensity(pollutant_dict)

        pm25 = pollutant_dict.get("pm25", 0.0)
        pm10 = pollutant_dict.get("pm10", 0.0)
        wind_magnitude = math.sqrt(u ** 2 + v ** 2) if (u or v) else 0.0

        return DerivedFeatures(
            aqi_change_rate_1h=0.0,  # Computed from history buffer
            aqi_change_rate_3h=0.0,
            aqi_change_rate_6h=0.0,
            wind_u_component=u,
            wind_v_component=v,
            wind_pm25_interaction=round(wind_magnitude * pm25, 4),
            wind_pm10_interaction=round(wind_magnitude * pm10, 4),
            temperature_humidity_index=thi,
            thermal_inversion_flag=inversion,
            pollution_intensity=intensity,
        )

    # ──────────────────────────────────────────────────────────────────────
    # Lag Features & History Management
    # ──────────────────────────────────────────────────────────────────────

    def update_history(self, timestamp: datetime, aqi: float, pm25: float) -> None:
        """Add an observation to the history buffer for lag computation.

        Maintains a rolling buffer of the last 24 hourly observations.

        Args:
            timestamp: UTC timestamp of the observation.
            aqi: AQI value.
            pm25: PM2.5 concentration.
        """
        self._history_buffer.append({
            "timestamp": timestamp,
            "aqi": aqi,
            "pm25": pm25,
        })
        # Keep last 48 hours (buffer overhead for rolling windows)
        if len(self._history_buffer) > 48:
            self._history_buffer = self._history_buffer[-48:]

    def compute_lag_features(self) -> LagFeatures:
        """Compute autoregressive lag features from the history buffer.

        Returns lag values at t-1, t-3, t-6, t-12, t-24 and rolling
        statistics (mean, std) over 6h and 24h windows.

        Returns:
            LagFeatures: Computed lag features (None for unavailable lags).
        """
        n = len(self._history_buffer)
        if n == 0:
            return LagFeatures()

        def _get_lag(offset: int, key: str) -> Optional[float]:
            idx = n - offset
            if 0 <= idx < n:
                return self._history_buffer[idx].get(key)
            return None

        # Rolling statistics for PM2.5
        pm25_values = [h["pm25"] for h in self._history_buffer if h.get("pm25") is not None]
        pm25_6h = pm25_values[-6:] if len(pm25_values) >= 6 else pm25_values
        pm25_24h = pm25_values[-24:] if len(pm25_values) >= 24 else pm25_values

        return LagFeatures(
            aqi_lag_1h=_get_lag(1, "aqi"),
            aqi_lag_3h=_get_lag(3, "aqi"),
            aqi_lag_6h=_get_lag(6, "aqi"),
            aqi_lag_12h=_get_lag(12, "aqi"),
            aqi_lag_24h=_get_lag(24, "aqi"),
            pm25_lag_1h=_get_lag(1, "pm25"),
            pm25_lag_3h=_get_lag(3, "pm25"),
            pm25_rolling_mean_6h=round(np.mean(pm25_6h), 4) if pm25_6h else None,
            pm25_rolling_std_6h=round(np.std(pm25_6h), 4) if len(pm25_6h) > 1 else None,
            pm25_rolling_mean_24h=round(np.mean(pm25_24h), 4) if pm25_24h else None,
        )

    def compute_aqi_change_rates(self) -> Dict[str, float]:
        """Compute AQI change rate (first derivative) over rolling windows.

        Delta AQI / Delta t for 1h, 3h, and 6h windows.

        Returns:
            Dict with keys 'rate_1h', 'rate_3h', 'rate_6h'.
        """
        n = len(self._history_buffer)
        rates: Dict[str, float] = {"rate_1h": 0.0, "rate_3h": 0.0, "rate_6h": 0.0}

        if n < 2:
            return rates

        current_aqi = self._history_buffer[-1].get("aqi", 0)

        for window, key in [(1, "rate_1h"), (3, "rate_3h"), (6, "rate_6h")]:
            idx = n - 1 - window
            if 0 <= idx < n:
                past_aqi = self._history_buffer[idx].get("aqi", current_aqi)
                rates[key] = round((current_aqi - past_aqi) / window, 4)

        return rates

    # ──────────────────────────────────────────────────────────────────────
    # Main Transform: RawDataPayload → FeatureVector
    # ──────────────────────────────────────────────────────────────────────

    def transform(self, payload: RawDataPayload) -> FeatureVector:
        """Transform a raw data payload into a complete feature vector.

        Applies all temporal, derived, and lag feature engineering steps.

        Args:
            payload: Validated raw data from ingestion pipeline.

        Returns:
            FeatureVector: Complete feature vector ready for model input.
        """
        dt = payload.fetch_timestamp
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        # ── Extract pollutant values ──
        pollutant_dict: Dict[str, float] = {}
        for p in payload.pollutants:
            pollutant_dict[p.name] = p.value

        # ── Extract weather ──
        w = payload.weather
        weather_dict = {
            "temperature_c": w.temperature_c,
            "humidity_pct": w.humidity_pct,
            "wind_speed_ms": w.wind_speed_ms,
            "wind_direction_deg": w.wind_direction_deg,
            "pressure_hpa": w.pressure_hpa,
            "precipitation_mm": w.precipitation_mm,
        }

        # ── Compute temporal features ──
        temporal = self.compute_temporal_features(dt)

        # ── Update history and compute lags ──
        aqi = payload.aqi_value or 0.0
        pm25 = pollutant_dict.get("pm25", 0.0)
        self.update_history(dt, aqi, pm25)

        lags = self.compute_lag_features()

        # ── Compute derived features ──
        derived = self.compute_derived_features(
            weather_dict, pollutant_dict, dt.hour
        )

        # ── Inject AQI change rates ──
        change_rates = self.compute_aqi_change_rates()
        derived.aqi_change_rate_1h = change_rates["rate_1h"]
        derived.aqi_change_rate_3h = change_rates["rate_3h"]
        derived.aqi_change_rate_6h = change_rates["rate_6h"]

        # ── Assemble feature vector ──
        feature_vector = FeatureVector(
            timestamp=dt,
            year=dt.year,
            month=dt.month,
            aqi_value=payload.aqi_value,
            pm25=pollutant_dict.get("pm25", 0.0),
            pm10=pollutant_dict.get("pm10", 0.0),
            no2=pollutant_dict.get("no2", 0.0),
            so2=pollutant_dict.get("so2", 0.0),
            co=pollutant_dict.get("co", 0.0),
            o3=pollutant_dict.get("o3", 0.0),
            temperature_c=w.temperature_c,
            humidity_pct=w.humidity_pct,
            wind_speed_ms=w.wind_speed_ms,
            wind_direction_deg=w.wind_direction_deg,
            pressure_hpa=w.pressure_hpa,
            precipitation_mm=w.precipitation_mm,
            temporal=temporal,
            derived=derived,
            lags=lags,
            source=payload.source,
        )

        logger.debug(
            "Feature vector generated for %s (AQI=%.1f, %d features)",
            dt.isoformat(), aqi, len(feature_vector.to_flat_dict()),
        )
        return feature_vector

    # ──────────────────────────────────────────────────────────────────────
    # Batch DataFrame Transform
    # ──────────────────────────────────────────────────────────────────────

    def transform_batch(self, payloads: List[RawDataPayload]) -> pd.DataFrame:
        """Transform a list of raw payloads into a feature DataFrame.

        Processes payloads sequentially to maintain temporal ordering
        for lag feature computation.

        Args:
            payloads: List of raw data payloads, sorted by timestamp.

        Returns:
            pd.DataFrame: DataFrame with all features as columns.
        """
        # Sort by timestamp to ensure correct lag computation
        sorted_payloads = sorted(payloads, key=lambda p: p.fetch_timestamp)

        vectors: List[Dict] = []
        for payload in sorted_payloads:
            fv = self.transform(payload)
            vectors.append(fv.to_flat_dict())

        df = pd.DataFrame(vectors)
        logger.info("Batch transform: %d payloads → %d rows × %d cols",
                     len(payloads), len(df), len(df.columns))
        return df

    def impute_missing_lags(self, df: pd.DataFrame) -> pd.DataFrame:
        """Impute missing lag features using forward-fill then backward-fill.

        Applied after batch transform to handle NaN values at the
        beginning of the time series where lag windows aren't available.

        Args:
            df: Feature DataFrame with potential NaN lag values.

        Returns:
            pd.DataFrame: DataFrame with imputed lag features.
        """
        lag_columns = [c for c in df.columns if "lag" in c or "rolling" in c]
        for col in lag_columns:
            if col in df.columns:
                df[col] = df[col].ffill().bfill().fillna(0.0)

        logger.info("Imputed %d lag columns", len(lag_columns))
        return df
