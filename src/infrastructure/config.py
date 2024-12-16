"""Application configuration."""
from functools import lru_cache
from typing import Dict, Optional

from pydantic import PostgresDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=True)

    # Database
    DATABASE_URL: str = "sqlite:///loadapp.db"
    SQL_ECHO: bool = False

    # API Keys
    GOOGLE_MAPS_API_KEY: SecretStr
    OPENAI_API_KEY: SecretStr

    # Feature Flags
    WEATHER_ENABLED: bool = False
    TRAFFIC_ENABLED: bool = False
    MARKET_DATA_ENABLED: bool = False

    # Server
    BACKEND_HOST: str = "localhost"
    BACKEND_PORT: int = 5000

    # Cost Settings Defaults
    DEFAULT_FUEL_PRICE: float = 1.50
    DEFAULT_DRIVER_SALARY: float = 138.0
    DEFAULT_TOLL_RATES: Dict[str, float] = {
        "DE": 0.10,
        "FR": 0.12,
    }


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
