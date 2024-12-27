"""Tests for configuration management."""
import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from src.settings import Settings, get_settings


def test_settings_defaults():
    """Test default settings values."""
    with patch.dict(os.environ, {}, clear=True):
        settings = Settings(_env_file=None)  # Disable .env file loading
        assert settings.OPENAI_API_KEY == ""
        assert settings.GOOGLE_MAPS_API_KEY == ""
        assert settings.OPENAI_MODEL == "gpt-3.5-turbo"
        assert settings.ENV == "development"


def test_settings_from_env():
    """Test loading settings from environment variables."""
    env_vars = {
        "OPENAI_API_KEY": "test_openai_key",
        "GOOGLE_MAPS_API_KEY": "test_gmaps_key",
        "ENV": "production",
        "OPENAI_MODEL": "custom-model"
    }
    
    with patch.dict(os.environ, env_vars, clear=True):
        settings = Settings()
        assert settings.OPENAI_API_KEY == "test_openai_key"
        assert settings.GOOGLE_MAPS_API_KEY == "test_gmaps_key"
        assert settings.ENV == "production"
        assert settings.OPENAI_MODEL == "custom-model"


def test_settings_cache():
    """Test settings caching behavior."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "first_key"}):
        settings1 = get_settings()
        
    with patch.dict(os.environ, {"OPENAI_API_KEY": "second_key"}):
        settings2 = get_settings()
    
    # Due to caching, both instances should have the first key
    assert settings1.OPENAI_API_KEY == settings2.OPENAI_API_KEY == "first_key"


def test_settings_validation():
    """Test settings validation."""
    with patch.dict(os.environ, {"OPENAI_MAX_RETRIES": "-1"}):
        with pytest.raises(ValidationError):
            Settings()

    with patch.dict(os.environ, {"GMAPS_CACHE_TTL": "invalid"}):
        with pytest.raises(ValidationError):
            Settings()
