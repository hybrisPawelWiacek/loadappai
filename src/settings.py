"""Application settings module following clean architecture principles."""

from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional, Union
import os

from pydantic import Field, field_validator, BaseModel, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseModel):
    """Database-specific settings."""
    url: str = Field(
        default="sqlite:///loadapp.db",
        description="Database connection URL"
    )
    echo: bool = Field(
        default=False,
        description="Enable SQL query logging"
    )


class APISettings(BaseModel):
    """External API settings."""
    openai_key: Optional[SecretStr] = Field(
        default=None,
        description="OpenAI API key for AI services"
    )
    openai_model: str = Field(
        default="gpt-4-mini",
        description="OpenAI model to use"
    )
    openai_max_retries: int = Field(
        default=3,
        description="Maximum number of retries for OpenAI API calls"
    )
    openai_retry_delay: float = Field(
        default=1.0,
        description="Delay between retries for OpenAI API calls"
    )
    google_maps_key: Optional[SecretStr] = Field(
        default=None,
        description="Google Maps API key for location services"
    )
    gmaps_max_retries: int = Field(
        default=3,
        description="Maximum number of retries for Google Maps API calls"
    )
    gmaps_retry_delay: float = Field(
        default=1.0,
        description="Delay between retries for Google Maps API calls"
    )
    gmaps_cache_ttl: int = Field(
        default=3600,
        description="TTL for Google Maps API cache in seconds"
    )


class ServiceSettings(BaseModel):
    """Service-specific settings."""
    backend_host: str = Field(
        default="localhost",
        description="Host for backend service"
    )
    backend_port: int = Field(
        default=5001,
        description="Port for Flask backend service"
    )
    weather_enabled: bool = Field(
        default=False,
        description="Enable weather service integration"
    )
    traffic_enabled: bool = Field(
        default=False,
        description="Enable traffic service integration"
    )
    market_data_enabled: bool = Field(
        default=False,
        description="Enable market data service integration"
    )


class Settings(BaseSettings):
    """Application settings following clean architecture principles."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        env_prefix="",
        extra="ignore"
    )

    # Environment
    env: str = Field(
        default="development",
        alias="ENV",
        description="Application environment"
    )

    # Database settings
    database_url: str = Field(
        default="sqlite:///loadapp.db",
        alias="DATABASE_URL",
        description="Database connection URL"
    )
    sql_echo: bool = Field(
        default=False,
        alias="SQL_ECHO",
        description="Enable SQL query logging"
    )

    # API settings
    openai_api_key: Optional[str] = Field(
        default=None,
        alias="OPENAI_API_KEY",
        description="OpenAI API key"
    )
    google_maps_api_key: Optional[str] = Field(
        default=None,
        alias="GOOGLE_MAPS_API_KEY",
        description="Google Maps API key"
    )

    # Service settings
    flask_port: int = Field(
        default=5001,
        alias="FLASK_PORT",
        description="Flask backend port"
    )
    weather_enabled: bool = Field(
        default=False,
        alias="WEATHER_ENABLED",
        description="Enable weather service"
    )
    traffic_enabled: bool = Field(
        default=False,
        alias="TRAFFIC_ENABLED",
        description="Enable traffic service"
    )
    market_data_enabled: bool = Field(
        default=False,
        alias="MARKET_DATA_ENABLED",
        description="Enable market data"
    )

    @property
    def database(self) -> DatabaseSettings:
        """Get database settings."""
        return DatabaseSettings(
            url=self.database_url,
            echo=self.sql_echo
        )

    @property
    def api(self) -> APISettings:
        """Get API settings."""
        openai_key = None
        if self.openai_api_key and self.openai_api_key.strip():
            openai_key = SecretStr(self.openai_api_key)

        google_maps_key = None
        if self.google_maps_api_key and self.google_maps_api_key.strip():
            google_maps_key = SecretStr(self.google_maps_api_key)

        return APISettings(
            openai_key=openai_key,
            google_maps_key=google_maps_key
        )

    @property
    def service(self) -> ServiceSettings:
        """Get service settings."""
        return ServiceSettings(
            backend_host="localhost",
            backend_port=self.flask_port,
            weather_enabled=self.weather_enabled,
            traffic_enabled=self.traffic_enabled,
            market_data_enabled=self.market_data_enabled
        )

    @field_validator("env")
    def validate_env(cls, v: str) -> str:
        """Validate environment setting."""
        allowed = {"development", "testing", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"Environment must be one of: {allowed}")
        return v

    @field_validator("openai_api_key", "google_maps_api_key")
    def validate_api_keys(cls, v: Optional[str]) -> Optional[str]:
        """Validate API keys."""
        if v is None or not v.strip():
            return None
        return v

    def __init__(self, **kwargs):
        """Initialize settings with environment variables and .env file."""
        # If _env_file is provided, ensure it exists
        env_file = kwargs.get("_env_file")
        if env_file and not os.path.exists(env_file):
            # If the file doesn't exist, remove it from kwargs to use defaults
            kwargs.pop("_env_file")

        super().__init__(**kwargs)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Export settings instance
settings = get_settings()
