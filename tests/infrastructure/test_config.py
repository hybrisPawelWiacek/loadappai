"""Test configuration management."""
import os
from pathlib import Path
from unittest import mock

import pytest
from pydantic import ValidationError

from src.settings import Settings, get_settings


@pytest.fixture
def clean_env(monkeypatch):
    """Fixture to provide a clean environment."""
    # List of environment variables to clear
    env_vars = [
        "ENV",
        "DATABASE_URL",
        "SQL_ECHO",
        "OPENAI_API_KEY",
        "GOOGLE_MAPS_API_KEY",
        "FLASK_PORT",
        "WEATHER_ENABLED",
        "TRAFFIC_ENABLED",
        "MARKET_DATA_ENABLED",
        "OPENAI_MODEL",
        "OPENAI_MAX_RETRIES",
        "OPENAI_RETRY_DELAY",
        "OPENAI_TIMEOUT",
        "GMAPS_MAX_RETRIES",
        "GMAPS_RETRY_DELAY",
        "GMAPS_CACHE_TTL"
    ]
    
    # Clear all environment variables
    for var in env_vars:
        monkeypatch.delenv(var, raising=False)


def test_settings_loading(clean_env, monkeypatch):
    """Test loading settings from environment variables."""
    # Set environment variables
    monkeypatch.setenv("ENV", "testing")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")
    monkeypatch.setenv("SQL_ECHO", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "test-maps-key")
    monkeypatch.setenv("FLASK_PORT", "5002")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4")
    monkeypatch.setenv("OPENAI_MAX_RETRIES", "5")
    monkeypatch.setenv("GMAPS_CACHE_TTL", "7200")

    settings = Settings(_env_file=None)
    
    # Test main settings
    assert settings.env == "testing"
    assert settings.database_url == "sqlite:///test.db"
    assert settings.sql_echo is True
    assert settings.openai_api_key == "test-key"
    assert settings.google_maps_api_key == "test-maps-key"
    assert settings.flask_port == 5002
    assert settings.openai_model == "gpt-4"
    assert settings.openai_max_retries == 5
    assert settings.gmaps_cache_ttl == 7200
    
    # Test sub-models
    assert settings.database.url == "sqlite:///test.db"
    assert settings.database.echo is True
    
    assert settings.api.openai_api_key.get_secret_value() == "test-key"
    assert settings.api.google_maps_key.get_secret_value() == "test-maps-key"
    assert settings.api.openai_model == "gpt-4"
    assert settings.api.openai_max_retries == 5
    assert settings.api.gmaps_cache_ttl == 7200
    
    assert settings.service.backend_port == 5002
    assert settings.service.backend_host == "localhost"
    assert not settings.service.weather_enabled
    assert not settings.service.traffic_enabled
    assert not settings.service.market_data_enabled


def test_settings_defaults(clean_env, tmp_path):
    """Test default settings values."""
    # Create an empty .env file
    env_file = tmp_path / ".env"
    env_file.write_text("")

    settings = Settings(_env_file=str(env_file))
    
    # Test main settings
    assert settings.env == "development"
    assert settings.database_url == "sqlite:///loadapp.db"
    assert settings.sql_echo is False
    assert settings.openai_api_key is None
    assert settings.google_maps_api_key is None
    assert settings.flask_port == 5001
    assert settings.openai_model == "gpt-4o-mini"
    assert settings.gmaps_cache_ttl == 3600
    
    # Test sub-models
    assert settings.database.url == "sqlite:///loadapp.db"
    assert settings.database.echo is False
    
    assert settings.api.openai_api_key is None
    assert settings.api.google_maps_key is None
    assert settings.api.openai_model == "gpt-4o-mini"
    assert settings.api.gmaps_cache_ttl == 3600
    
    assert settings.service.backend_port == 5001
    assert settings.service.backend_host == "localhost"
    assert not settings.service.weather_enabled
    assert not settings.service.traffic_enabled
    assert not settings.service.market_data_enabled


def test_settings_validation(clean_env, monkeypatch):
    """Test settings validation."""
    # Test invalid port
    monkeypatch.setenv("FLASK_PORT", "invalid")
    monkeypatch.setenv("ENV", "development")  # Set valid environment
    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)
    assert "FLASK_PORT" in str(exc_info.value)
    assert "unable to parse string as an integer" in str(exc_info.value)

    # Test invalid environment
    monkeypatch.setenv("FLASK_PORT", "5001")  # Reset to valid port
    monkeypatch.setenv("ENV", "invalid")
    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)
    assert "ENV" in str(exc_info.value)
    assert "Environment must be one of" in str(exc_info.value)

    # Test invalid API key (empty string)
    monkeypatch.setenv("ENV", "development")  # Reset to valid environment
    monkeypatch.setenv("OPENAI_API_KEY", "   ")
    settings = Settings(_env_file=None)
    assert settings.openai_api_key is None
    assert settings.api.openai_api_key is None


def test_settings_caching(clean_env):
    """Test settings caching."""
    # Clear any cached settings
    get_settings.cache_clear()

    # First call should create new instance
    settings1 = get_settings()
    
    # Second call should return cached instance
    settings2 = get_settings()
    
    # Both should be the same instance
    assert settings1 is settings2

    # Test that modifying environment after caching doesn't affect cached settings
    with mock.patch.dict(os.environ, {"ENV": "testing"}, clear=True):
        settings3 = get_settings()
        assert settings3 is settings1
        assert settings3.env == "development"  # Should still have original value


def test_settings_file_loading(clean_env, tmp_path):
    """Test loading settings from file."""
    # Create a test .env file
    env_file = tmp_path / ".env"
    env_file.write_text("""
    ENV=testing
    DATABASE_URL=sqlite:///test.db
    SQL_ECHO=true
    OPENAI_API_KEY=test-key
    GOOGLE_MAPS_API_KEY=test-maps-key
    FLASK_PORT=5002
    OPENAI_MODEL=gpt-4
    """)

    settings = Settings(_env_file=str(env_file))
    assert settings.env == "testing"
    assert settings.database.url == "sqlite:///test.db"
    assert settings.database.echo is True
    assert settings.api.openai_api_key.get_secret_value() == "test-key"
    assert settings.api.google_maps_key.get_secret_value() == "test-maps-key"
    assert settings.service.backend_port == 5002
    assert settings.api.openai_model == "gpt-4"


def test_feature_flags(clean_env, monkeypatch):
    """Test feature flag settings."""
    monkeypatch.setenv("WEATHER_ENABLED", "true")
    monkeypatch.setenv("TRAFFIC_ENABLED", "true")
    monkeypatch.setenv("MARKET_DATA_ENABLED", "true")

    settings = Settings(_env_file=None)
    assert settings.weather_enabled is True
    assert settings.traffic_enabled is True
    assert settings.market_data_enabled is True
    
    assert settings.service.weather_enabled is True
    assert settings.service.traffic_enabled is True
    assert settings.service.market_data_enabled is True
