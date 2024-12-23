"""Configuration management for LoadApp.AI."""
from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
    )

    # API Keys
    OPENAI_API_KEY: str = Field(default="")
    GOOGLE_MAPS_API_KEY: str = Field(default="")

    # Backend Settings
    BACKEND_URL: str = Field(default="http://localhost:5000")

    # OpenAI Settings
    OPENAI_MODEL: str = Field(default="gpt-3.5-turbo")
    OPENAI_MAX_RETRIES: int = Field(default=3, gt=0)
    OPENAI_RETRY_DELAY: float = Field(default=1.0, gt=0)

    # Google Maps Settings
    GMAPS_MAX_RETRIES: int = Field(default=2, gt=0)
    GMAPS_RETRY_DELAY: float = Field(default=0.1, gt=0)
    GMAPS_CACHE_TTL: int = Field(default=3600, gt=0)

    # Environment
    ENV: str = Field(default="development")


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
