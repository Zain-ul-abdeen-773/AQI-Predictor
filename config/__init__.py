"""Configuration module for the Pearls AQI Predictor.

Provides centralized configuration management using Pydantic BaseSettings,
validation schemas, and type-safe configuration access.
"""

from config.settings import get_settings, Settings

__all__ = ["get_settings", "Settings"]
