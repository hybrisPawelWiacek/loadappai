"""Application configuration."""
import json
import os
from functools import lru_cache
from typing import Dict, Optional, Union

from pydantic import PostgresDsn, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=os.getenv("ENV_FILE", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # Database
    DATABASE_URL: str = "sqlite:///loadapp.db"
    SQL_ECHO: bool = False

    # API Keys
    GOOGLE_MAPS_API_KEY: Optional[Union[SecretStr, str]] = None
    OPENAI_API_KEY: Optional[Union[SecretStr, str]] = None

    # Environment
    ENV: str = "development"

    # OpenAI Configuration
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_MAX_RETRIES: int = 3
    OPENAI_RETRY_DELAY: float = 1.0

    # Google Maps Configuration
    GMAPS_MAX_RETRIES: int = 3
    GMAPS_RETRY_DELAY: float = 1.0
    GMAPS_CACHE_TTL: int = 3600

    # CrewAI Configuration (Optional)
    CREWAI_BASE_URL: Optional[str] = None
    CREWAI_BEARER_TOKEN: Optional[str] = None

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

    @field_validator("DEFAULT_TOLL_RATES", mode="before")
    @classmethod
    def parse_toll_rates(cls, v):
        """Parse toll rates from string if needed."""
        if isinstance(v, str):
            return json.loads(v)
        return v


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
