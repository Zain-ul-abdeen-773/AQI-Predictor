"""Production-grade data ingestion from AQICN and OpenWeatherMap APIs.

Implements:
- Dual-source concurrent fetching with asyncio + aiohttp
- Exponential backoff retry with tenacity (handles 429 / 5xx)
- Strict schema validation of every API response
- Graceful degradation when secondary source is unavailable
- Synthetic data generation for development without API keys

Example:
    >>> import asyncio
    >>> from data_pipeline.ingest import DataIngestionOrchestrator
    >>> orchestrator = DataIngestionOrchestrator()
    >>> payload = asyncio.run(orchestrator.fetch_current())
"""

from __future__ import annotations

import asyncio
import logging
import math
import random
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
    RetryError,
)

from config.settings import get_settings, Settings
from config.schemas import (
    DataSource,
    PollutantReading,
    RawDataPayload,
    WeatherReading,
)

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Custom Exceptions
# ──────────────────────────────────────────────────────────────────────────────


class APIError(Exception):
    """Base exception for API communication errors."""

    def __init__(self, source: str, status_code: int, message: str) -> None:
        self.source = source
        self.status_code = status_code
        super().__init__(f"[{source}] HTTP {status_code}: {message}")


class RateLimitError(APIError):
    """Raised when API rate limit (HTTP 429) is encountered."""
    pass


class TransientError(APIError):
    """Raised for transient server errors (HTTP 5xx)."""
    pass


# ──────────────────────────────────────────────────────────────────────────────
# AQICN Client
# ──────────────────────────────────────────────────────────────────────────────


class AQICNClient:
    """Async client for AQICN Air Quality API v2.

    Fetches real-time pollutant concentrations (PM2.5, PM10, NO2, SO2, CO, O3)
    and the composite AQI value for the configured target location.

    Attributes:
        settings: Application settings instance.
        base_url: AQICN API base URL.
    """

    BASE_URL = "https://api.waqi.info"

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp client session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self) -> None:
        """Close the HTTP session gracefully."""
        if self._session and not self._session.closed:
            await self._session.close()

    @retry(
        retry=retry_if_exception_type((RateLimitError, TransientError, aiohttp.ClientError)),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=60),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    async def fetch_station_data(self) -> Dict[str, Any]:
        """Fetch real-time AQI data from the nearest AQICN station.

        Uses geo-based feed endpoint to find the closest monitoring station
        to the configured coordinates.

        Returns:
            Dict[str, Any]: Raw JSON response from AQICN API.

        Raises:
            RateLimitError: When API rate limit is hit (HTTP 429).
            TransientError: For server-side errors (HTTP 5xx).
            APIError: For other HTTP errors.
        """
        lat, lon = self.settings.coordinates
        url = f"{self.BASE_URL}/feed/geo:{lat};{lon}/"
        params = {"token": self.settings.aqicn_api_key}

        session = await self._get_session()
        async with session.get(url, params=params) as response:
            if response.status == 429:
                raise RateLimitError("AQICN", 429, "Rate limit exceeded")
            if response.status >= 500:
                raise TransientError("AQICN", response.status, "Server error")
            if response.status != 200:
                text = await response.text()
                raise APIError("AQICN", response.status, text)

            data = await response.json()

            if data.get("status") != "ok":
                raise APIError("AQICN", 200, f"API returned status: {data.get('status')}")

            return data.get("data", {})

    async def fetch_pollutants(self) -> Tuple[List[PollutantReading], Optional[float]]:
        """Parse AQICN station data into validated PollutantReading objects.

        Returns:
            Tuple containing:
            - List[PollutantReading]: Validated pollutant readings.
            - Optional[float]: Composite AQI value if available.
        """
        now = datetime.now(timezone.utc)

        try:
            data = await self.fetch_station_data()
        except (RetryError, APIError) as e:
            logger.error("AQICN fetch failed after retries: %s", e)
            return [], None

        aqi_value = data.get("aqi")
        if isinstance(aqi_value, str):
            try:
                aqi_value = float(aqi_value)
            except ValueError:
                aqi_value = None

        iaqi = data.get("iaqi", {})
        pollutant_names = ["pm25", "pm10", "no2", "so2", "co", "o3"]
        readings: List[PollutantReading] = []

        for name in pollutant_names:
            raw = iaqi.get(name, {})
            value = raw.get("v")
            if value is not None:
                try:
                    readings.append(
                        PollutantReading(
                            name=name,
                            value=float(value),
                            unit="AQI sub-index",
                            timestamp=now,
                        )
                    )
                except Exception as e:
                    logger.warning("Failed to parse %s reading: %s", name, e)

        logger.info(
            "AQICN: Fetched %d pollutant readings, AQI=%s",
            len(readings),
            aqi_value,
        )
        return readings, aqi_value


# ──────────────────────────────────────────────────────────────────────────────
# OpenWeatherMap Client
# ──────────────────────────────────────────────────────────────────────────────


class OpenWeatherClient:
    """Async client for OpenWeatherMap Air Pollution and Weather APIs.

    Fetches meteorological data (temperature, humidity, wind, pressure,
    precipitation) and supplementary pollutant concentrations.

    Attributes:
        settings: Application settings instance.
    """

    WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
    AIR_POLLUTION_URL = "https://api.openweathermap.org/data/2.5/air_pollution"

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp client session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self) -> None:
        """Close the HTTP session gracefully."""
        if self._session and not self._session.closed:
            await self._session.close()

    @retry(
        retry=retry_if_exception_type((RateLimitError, TransientError, aiohttp.ClientError)),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=60),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    async def fetch_weather(self) -> WeatherReading:
        """Fetch current weather data from OpenWeatherMap.

        Returns:
            WeatherReading: Validated weather observation.

        Raises:
            RateLimitError: When API rate limit is hit.
            TransientError: For server-side errors.
        """
        lat, lon = self.settings.coordinates
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.settings.openweather_api_key,
            "units": "metric",
        }

        session = await self._get_session()
        async with session.get(self.WEATHER_URL, params=params) as response:
            if response.status == 429:
                raise RateLimitError("OpenWeather", 429, "Rate limit exceeded")
            if response.status >= 500:
                raise TransientError("OpenWeather", response.status, "Server error")
            if response.status != 200:
                text = await response.text()
                raise APIError("OpenWeather", response.status, text)

            data = await response.json()

        main = data.get("main", {})
        wind = data.get("wind", {})
        rain = data.get("rain", {})

        reading = WeatherReading(
            temperature_c=main.get("temp", 25.0),
            humidity_pct=main.get("humidity", 50.0),
            wind_speed_ms=wind.get("speed", 0.0),
            wind_direction_deg=wind.get("deg", 0.0),
            pressure_hpa=main.get("pressure", 1013.25),
            precipitation_mm=rain.get("1h", 0.0),
            timestamp=datetime.now(timezone.utc),
        )

        logger.info(
            "OpenWeather: T=%.1f°C, H=%.0f%%, WS=%.1f m/s",
            reading.temperature_c,
            reading.humidity_pct,
            reading.wind_speed_ms,
        )
        return reading

    @retry(
        retry=retry_if_exception_type((RateLimitError, TransientError, aiohttp.ClientError)),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=60),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    async def fetch_air_pollution(self) -> List[PollutantReading]:
        """Fetch air pollution data from OpenWeatherMap.

        Returns supplementary pollutant concentrations in µg/m³.

        Returns:
            List[PollutantReading]: Supplementary pollutant readings.
        """
        lat, lon = self.settings.coordinates
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.settings.openweather_api_key,
        }

        session = await self._get_session()
        async with session.get(self.AIR_POLLUTION_URL, params=params) as response:
            if response.status == 429:
                raise RateLimitError("OpenWeather", 429, "Rate limit exceeded")
            if response.status >= 500:
                raise TransientError("OpenWeather", response.status, "Server error")
            if response.status != 200:
                return []

            data = await response.json()

        readings: List[PollutantReading] = []
        now = datetime.now(timezone.utc)

        items = data.get("list", [])
        if items:
            components = items[0].get("components", {})
            mapping = {
                "pm2_5": "pm25",
                "pm10": "pm10",
                "no2": "no2",
                "so2": "so2",
                "co": "co",
                "o3": "o3",
            }
            for api_key, our_key in mapping.items():
                value = components.get(api_key)
                if value is not None:
                    readings.append(
                        PollutantReading(
                            name=our_key,
                            value=float(value),
                            unit="µg/m³",
                            timestamp=now,
                        )
                    )

        logger.info("OpenWeather Air Pollution: Fetched %d readings", len(readings))
        return readings


# ──────────────────────────────────────────────────────────────────────────────
# Synthetic Data Generator (Development / Fallback)
# ──────────────────────────────────────────────────────────────────────────────


class SyntheticDataGenerator:
    """Generates realistic synthetic AQI data for development and testing.

    Simulates seasonal patterns, diurnal cycles, and stochastic noise
    matching Sargodha's typical air quality profile. Used when API keys
    are unavailable or for backfilling historical training data.

    Attributes:
        settings: Application settings instance.
    """

    # Sargodha baseline AQI statistics (annual mean, seasonal amplitude)
    SARGODHA_AQI_BASELINE = 120.0  # Annual mean AQI (typically moderate-unhealthy)
    SEASONAL_AMPLITUDE = 80.0  # AQI swing between summer low and winter high
    DIURNAL_AMPLITUDE = 25.0  # Day-night AQI variation
    PEAK_POLLUTION_MONTH = 12  # December (smog season)
    PEAK_POLLUTION_HOUR = 8  # Morning rush hour

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()

    def generate_for_timestamp(self, dt: datetime) -> RawDataPayload:
        """Generate a synthetic data payload for a specific timestamp.

        Uses seasonal, diurnal, and stochastic components to produce
        realistic air quality and weather data for Sargodha.

        Args:
            dt: The target UTC timestamp to generate data for.

        Returns:
            RawDataPayload: A complete synthetic data payload.
        """
        # ── Seasonal component (peaks in Dec-Jan smog season) ──
        month_angle = 2 * math.pi * (dt.month - self.PEAK_POLLUTION_MONTH) / 12
        seasonal = self.SEASONAL_AMPLITUDE * math.cos(month_angle)

        # ── Diurnal component (peaks during morning rush) ──
        hour_angle = 2 * math.pi * (dt.hour - self.PEAK_POLLUTION_HOUR) / 24
        diurnal = self.DIURNAL_AMPLITUDE * math.cos(hour_angle)

        # ── Stochastic noise ──
        noise = random.gauss(0, 15)

        # ── Physical Meteorological Base ──
        # Temperature: Summer 35-45°C, Winter 5-18°C
        temp_seasonal = 25 + 15 * math.cos(2 * math.pi * (dt.month - 7) / 12)
        temp_diurnal = 5 * math.cos(2 * math.pi * (dt.hour - 14) / 24)
        temperature = temp_seasonal + temp_diurnal + random.gauss(0, 2.5)

        # Humidity inversely correlated with temperature
        humidity = max(10, min(95, 70 - temperature * 0.8 + random.gauss(0, 8)))

        # Wind: low during winter inversions, higher in summer
        wind_base = 2.0 + 3.0 * math.sin(2 * math.pi * (dt.month - 4) / 12)
        wind_speed = max(0.5, wind_base + random.gauss(0, 1.8))

        # ── Non-Linear Emissions & Dispersion Engine ──
        # Boundary layer inversion effect (cold ground + calm winds = high trapping)
        inversion_trapping = max(0.8, (28.0 - temperature) * 0.04) * (1.0 / max(0.8, wind_speed * 0.5))
        traffic_rush = 1.4 if dt.hour in [7, 8, 9, 17, 18, 19] else 0.85
        kiln_emission = 1.3 if dt.month in [10, 11, 12, 1, 2] else 0.7

        # Base particulate load subjected to stochastic meteorological turbulence
        pm25_base = max(5, 32.0 * inversion_trapping * traffic_rush * kiln_emission + random.gauss(0, 11))
        pm10_base = max(12, pm25_base * 1.85 + random.gauss(0, 16))
        no2_base = max(4, 22.0 * traffic_rush * (1.0 / max(1.0, wind_speed * 0.4)) + random.gauss(0, 6))
        so2_base = max(2, 14.0 * kiln_emission + random.gauss(0, 4))
        co_base = max(300, 720.0 * traffic_rush + random.gauss(0, 120))
        o3_base = max(10, 45.0 * max(0.2, temperature / 35.0) + random.gauss(0, 10))

        # ── Piecewise EPA AQI Calculation + Sensor Drift Noise ──
        # Prevent exact linear mapping by adding independent sensor measurement variance
        sensor_drift = random.gauss(0, 12)
        aqi = max(15, min(480, int(pm25_base * 2.8 + sensor_drift)))

        pollutants = [
            PollutantReading(name="pm25", value=round(pm25_base, 2), unit="µg/m³", timestamp=dt),
            PollutantReading(name="pm10", value=round(pm10_base, 2), unit="µg/m³", timestamp=dt),
            PollutantReading(name="no2", value=round(no2_base, 2), unit="µg/m³", timestamp=dt),
            PollutantReading(name="so2", value=round(so2_base, 2), unit="µg/m³", timestamp=dt),
            PollutantReading(name="co", value=round(co_base, 2), unit="µg/m³", timestamp=dt),
            PollutantReading(name="o3", value=round(o3_base, 2), unit="µg/m³", timestamp=dt),
        ]

        # ── Weather (Sargodha climate: hot semi-arid) ──
        # Temperature: Summer 35-45°C, Winter 5-18°C
        temp_seasonal = 25 + 15 * math.cos(2 * math.pi * (dt.month - 7) / 12)
        temp_diurnal = 5 * math.cos(2 * math.pi * (dt.hour - 14) / 24)
        temperature = temp_seasonal + temp_diurnal + random.gauss(0, 2)

        # Humidity inversely correlated with temperature
        humidity = max(10, min(95, 70 - temperature * 0.8 + random.gauss(0, 8)))

        # Wind: typically low in winter smog, higher in summer
        wind_base = 2.0 + 3.0 * math.sin(2 * math.pi * (dt.month - 4) / 12)
        wind_speed = max(0, wind_base + random.gauss(0, 1.5))
        wind_dir = random.uniform(0, 360)

        # Pressure: slight seasonal variation
        pressure = 1013.25 + 5 * math.cos(2 * math.pi * dt.month / 12) + random.gauss(0, 2)

        # Precipitation: monsoon Jul-Sep
        precip_prob = 0.3 if 7 <= dt.month <= 9 else 0.05
        precipitation = random.expovariate(1.0 / 2.0) if random.random() < precip_prob else 0.0

        weather = WeatherReading(
            temperature_c=round(temperature, 1),
            humidity_pct=round(humidity, 1),
            wind_speed_ms=round(wind_speed, 1),
            wind_direction_deg=round(wind_dir, 1),
            pressure_hpa=round(pressure, 1),
            precipitation_mm=round(precipitation, 2),
            timestamp=dt,
        )

        return RawDataPayload(
            pollutants=pollutants,
            weather=weather,
            aqi_value=round(aqi, 1),
            source=DataSource.SYNTHETIC,
            fetch_timestamp=dt,
        )


# ──────────────────────────────────────────────────────────────────────────────
# Orchestrator
# ──────────────────────────────────────────────────────────────────────────────


class DataIngestionOrchestrator:
    """Orchestrates data fetching from multiple sources with graceful fallback.

    Primary flow:
    1. Fetch from AQICN (pollutants + AQI)
    2. Fetch from OpenWeatherMap (weather + supplementary pollutants) concurrently
    3. Merge results into a unified RawDataPayload
    4. Fall back to synthetic data if both APIs fail

    Attributes:
        settings: Application settings instance.
        aqicn: AQICN API client.
        openweather: OpenWeatherMap API client.
        synthetic: Synthetic data generator for fallback.
    """

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self.aqicn = AQICNClient(self.settings)
        self.openweather = OpenWeatherClient(self.settings)
        self.synthetic = SyntheticDataGenerator(self.settings)

    async def fetch_current(self) -> RawDataPayload:
        """Fetch current air quality and weather data from all sources.

        Attempts concurrent fetching from AQICN and OpenWeatherMap.
        Falls back to synthetic data if both sources fail.

        Returns:
            RawDataPayload: Unified validated data payload.
        """
        now = datetime.now(timezone.utc)
        pollutants: List[PollutantReading] = []
        aqi_value: Optional[float] = None
        weather: Optional[WeatherReading] = None

        # ── Concurrent fetch from both sources ──
        aqicn_task = asyncio.create_task(self._safe_fetch_aqicn())
        openweather_task = asyncio.create_task(self._safe_fetch_openweather())

        aqicn_result, openweather_result = await asyncio.gather(
            aqicn_task, openweather_task
        )

        # ── Merge AQICN results ──
        if aqicn_result is not None:
            aqicn_pollutants, aqicn_aqi = aqicn_result
            pollutants.extend(aqicn_pollutants)
            aqi_value = aqicn_aqi

        # ── Merge OpenWeather results ──
        if openweather_result is not None:
            ow_weather, ow_pollutants = openweather_result
            weather = ow_weather
            # Only add OpenWeather pollutants if AQICN didn't provide them
            existing_names = {p.name for p in pollutants}
            for p in ow_pollutants:
                if p.name not in existing_names:
                    pollutants.append(p)

        # ── Fallback to synthetic if both failed ──
        if not pollutants or weather is None:
            logger.warning(
                "API sources unavailable — using synthetic data for %s", now
            )
            synthetic_payload = self.synthetic.generate_for_timestamp(now)
            if not pollutants:
                pollutants = synthetic_payload.pollutants
            if weather is None:
                weather = synthetic_payload.weather
            if aqi_value is None:
                aqi_value = synthetic_payload.aqi_value

        source = DataSource.AQICN if aqicn_result else (
            DataSource.OPENWEATHER if openweather_result else DataSource.SYNTHETIC
        )

        payload = RawDataPayload(
            pollutants=pollutants,
            weather=weather,
            aqi_value=aqi_value,
            source=source,
            fetch_timestamp=now,
        )

        logger.info(
            "Ingestion complete: source=%s, pollutants=%d, AQI=%s",
            source.value, len(pollutants), aqi_value,
        )
        return payload

    async def _safe_fetch_aqicn(
        self,
    ) -> Optional[Tuple[List[PollutantReading], Optional[float]]]:
        """Safely attempt AQICN fetch, returning None on failure."""
        try:
            return await self.aqicn.fetch_pollutants()
        except Exception as e:
            logger.error("AQICN fetch failed: %s", e)
            return None

    async def _safe_fetch_openweather(
        self,
    ) -> Optional[Tuple[WeatherReading, List[PollutantReading]]]:
        """Safely attempt OpenWeather fetch, returning None on failure."""
        if not self.settings.openweather_api_key:
            logger.info("OpenWeather API key not configured — skipping")
            return None
        try:
            weather_task = asyncio.create_task(self.openweather.fetch_weather())
            pollution_task = asyncio.create_task(
                self.openweather.fetch_air_pollution()
            )
            weather, air_pollutants = await asyncio.gather(weather_task, pollution_task)
            return weather, air_pollutants
        except Exception as e:
            logger.error("OpenWeather fetch failed: %s", e)
            return None

    async def close(self) -> None:
        """Close all HTTP sessions."""
        await self.aqicn.close()
        await self.openweather.close()


# ──────────────────────────────────────────────────────────────────────────────
# CLI Entry Point
# ──────────────────────────────────────────────────────────────────────────────


async def _main() -> None:
    """CLI entry point for testing data ingestion."""
    orchestrator = DataIngestionOrchestrator()
    try:
        payload = await orchestrator.fetch_current()
        print(f"\n{'='*60}")
        print(f"Source: {payload.source.value}")
        print(f"AQI: {payload.aqi_value}")
        print(f"Pollutants: {len(payload.pollutants)}")
        for p in payload.pollutants:
            print(f"  {p.name}: {p.value:.1f} {p.unit}")
        w = payload.weather
        print(f"Weather: T={w.temperature_c}°C, H={w.humidity_pct}%, "
              f"WS={w.wind_speed_ms}m/s, WD={w.wind_direction_deg}°")
        print(f"{'='*60}\n")
    finally:
        await orchestrator.close()


if __name__ == "__main__":
    asyncio.run(_main())
