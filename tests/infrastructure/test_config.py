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

    settings = Settings(_env_file=None)
    assert settings.env == "testing"
    assert settings.database.url == "sqlite:///test.db"
    assert settings.database.echo is True
    assert settings.api.openai_key.get_secret_value() == "test-key"
    assert settings.api.google_maps_key.get_secret_value() == "test-maps-key"
    assert settings.service.backend_port == 5002


def test_settings_defaults(clean_env, tmp_path):
    """Test default settings values."""
    # Create an empty .env file
    env_file = tmp_path / ".env"
    env_file.write_text("")

    settings = Settings(_env_file=str(env_file))
    assert settings.env == "development"
    assert settings.database.url == "sqlite:///loadapp.db"
    assert settings.database.echo is False
    assert settings.api.openai_key is None
    assert settings.api.google_maps_key is None
    assert settings.service.backend_port == 5001
    assert settings.api.openai_model == "gpt-4-mini"
    assert settings.api.gmaps_cache_ttl == 3600


def test_settings_validation(clean_env, monkeypatch):
    """Test settings validation."""
    # Test invalid port
    monkeypatch.setenv("FLASK_PORT", "invalid")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)

    # Test invalid environment
    monkeypatch.setenv("ENV", "invalid")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


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
    # Create a temporary .env file
    env_content = """
    ENV=testing
    DATABASE_URL=sqlite:///test_file.db
    SQL_ECHO=true
    OPENAI_API_KEY=test-key-from-file
    GOOGLE_MAPS_API_KEY=test-maps-key-from-file
    FLASK_PORT=5003
    """
    env_file = tmp_path / ".env"
    env_file.write_text(env_content.strip())

    settings = Settings(_env_file=str(env_file))
    assert settings.env == "testing"
    assert settings.database.url == "sqlite:///test_file.db"
    assert settings.database.echo is True
    assert settings.api.openai_key.get_secret_value() == "test-key-from-file"
    assert settings.api.google_maps_key.get_secret_value() == "test-maps-key-from-file"
    assert settings.service.backend_port == 5003


def test_feature_flags(clean_env, monkeypatch):
    """Test feature flag settings."""
    monkeypatch.setenv("WEATHER_ENABLED", "true")
    monkeypatch.setenv("TRAFFIC_ENABLED", "true")
    monkeypatch.setenv("MARKET_DATA_ENABLED", "true")

    settings = Settings(_env_file=None)
    assert settings.service.weather_enabled is True
    assert settings.service.traffic_enabled is True
    assert settings.service.market_data_enabled is True
