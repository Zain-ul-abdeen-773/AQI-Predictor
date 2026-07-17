"""Real Historical Data Fetcher using Open-Meteo APIs.

Fetches real hourly air quality and weather data for a given date range.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Optional

import requests
import pandas as pd

from config.settings import get_settings, Settings
from config.schemas import (
    DataSource,
    PollutantReading,
    RawDataPayload,
    WeatherReading,
)

logger = logging.getLogger(__name__)


class RealHistoricalDataFetcher:
    """Fetches real historical AQI and Weather data from Open-Meteo."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()

    def fetch_all(self, start_date: str, end_date: str) -> List[RawDataPayload]:
        """Fetch all data between start_date and end_date and parse into payloads.
        
        Args:
            start_date: YYYY-MM-DD
            end_date: YYYY-MM-DD
            
        Returns:
            List[RawDataPayload]: A list of payloads for each hour.
        """
        lat, lon = self.settings.coordinates
        
        logger.info("Fetching historical Air Quality data from %s to %s...", start_date, end_date)
        aq_url = (
            f"https://air-quality-api.open-meteo.com/v1/air-quality"
            f"?latitude={lat}&longitude={lon}&start_date={start_date}&end_date={end_date}"
            f"&hourly=pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,ozone,us_aqi"
        )
        aq_response = requests.get(aq_url)
        aq_response.raise_for_status()
        aq_data = aq_response.json()["hourly"]

        logger.info("Fetching historical Weather data from %s to %s...", start_date, end_date)
        w_url = (
            f"https://archive-api.open-meteo.com/v1/archive"
            f"?latitude={lat}&longitude={lon}&start_date={start_date}&end_date={end_date}"
            f"&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m,surface_pressure,precipitation"
        )
        w_response = requests.get(w_url)
        w_response.raise_for_status()
        w_data = w_response.json()["hourly"]

        payloads = []
        
        # Merge by index (time arrays are identical for the same date range)
        times = aq_data["time"]
        for i in range(len(times)):
            dt = datetime.fromisoformat(times[i]).replace(tzinfo=timezone.utc)
            
            # Use fallback 0 if missing for any reason
            pm10 = aq_data["pm10"][i] if aq_data["pm10"][i] is not None else 0.0
            pm25 = aq_data["pm2_5"][i] if aq_data["pm2_5"][i] is not None else 0.0
            co = aq_data["carbon_monoxide"][i] if aq_data["carbon_monoxide"][i] is not None else 0.0
            no2 = aq_data["nitrogen_dioxide"][i] if aq_data["nitrogen_dioxide"][i] is not None else 0.0
            so2 = aq_data["sulphur_dioxide"][i] if aq_data["sulphur_dioxide"][i] is not None else 0.0
            o3 = aq_data["ozone"][i] if aq_data["ozone"][i] is not None else 0.0
            aqi_value = aq_data["us_aqi"][i] if aq_data["us_aqi"][i] is not None else 0.0
            
            temp = w_data["temperature_2m"][i] if w_data["temperature_2m"][i] is not None else 0.0
            hum = w_data["relative_humidity_2m"][i] if w_data["relative_humidity_2m"][i] is not None else 0.0
            ws = w_data["wind_speed_10m"][i] if w_data["wind_speed_10m"][i] is not None else 0.0
            wd = w_data["wind_direction_10m"][i] if w_data["wind_direction_10m"][i] is not None else 0.0
            pres = w_data["surface_pressure"][i] if w_data["surface_pressure"][i] is not None else 1013.25
            precip = w_data["precipitation"][i] if w_data["precipitation"][i] is not None else 0.0

            pollutants = [
                PollutantReading(name="pm25", value=float(pm25), unit="µg/m³", timestamp=dt),
                PollutantReading(name="pm10", value=float(pm10), unit="µg/m³", timestamp=dt),
                PollutantReading(name="no2", value=float(no2), unit="µg/m³", timestamp=dt),
                PollutantReading(name="so2", value=float(so2), unit="µg/m³", timestamp=dt),
                PollutantReading(name="co", value=float(co), unit="µg/m³", timestamp=dt),
                PollutantReading(name="o3", value=float(o3), unit="µg/m³", timestamp=dt),
            ]

            weather = WeatherReading(
                temperature_c=float(temp),
                humidity_pct=float(hum),
                wind_speed_ms=float(ws),
                wind_direction_deg=float(wd),
                pressure_hpa=float(pres),
                precipitation_mm=float(precip),
                timestamp=dt,
            )

            payload = RawDataPayload(
                pollutants=pollutants,
                weather=weather,
                aqi_value=float(aqi_value),
                source=DataSource.OPENWEATHER,
                fetch_timestamp=dt,
            )
            payloads.append(payload)

        logger.info("Successfully generated %d payloads.", len(payloads))
        return payloads
