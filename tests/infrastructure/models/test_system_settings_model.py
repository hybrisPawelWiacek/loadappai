"""Tests for the SystemSettings SQLAlchemy model."""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

from src.domain.entities.vehicle import SystemSettings as DomainSystemSettings
from src.infrastructure.models import SystemSettings


@pytest.fixture
def system_settings_data():
    """Create test system settings data."""
    return {
        "api_url": "http://api.example.com",
        "api_version": "v2",
        "request_timeout_seconds": 60,
        "default_currency": "EUR",
        "default_language": "en",
        "enable_cost_history": True,
        "enable_route_optimization": True,
        "enable_real_time_tracking": False,
        "maps_provider": "google",
        "geocoding_provider": "google",
        "min_margin_percent": 5.0,
        "max_margin_percent": 50.0,
        "price_rounding_decimals": 2,
        "max_route_duration": "7 days",
        "is_active": True
    }


@pytest.fixture
def domain_system_settings():
    """Create a domain system settings entity."""
    return DomainSystemSettings(
        id=uuid4(),
        api_url="http://api.example.com",
        api_version="v2",
        request_timeout_seconds=60,
        default_currency="EUR",
        default_language="en",
        enable_cost_history=True,
        enable_route_optimization=True,
        enable_real_time_tracking=False,
        maps_provider="google",
        geocoding_provider="google",
        min_margin_percent=Decimal("5.0"),
        max_margin_percent=Decimal("50.0"),
        price_rounding_decimals=2,
        max_route_duration=timedelta(days=7),
        is_active=True,
        last_modified=datetime.utcnow()
    )


def test_create_system_settings(db_session, system_settings_data):
    """Test creating system settings."""
    settings = SystemSettings(**system_settings_data)
    db_session.add(settings)
    db_session.commit()

    assert settings.id is not None
    assert settings.api_url == system_settings_data["api_url"]
    assert settings.api_version == system_settings_data["api_version"]
    assert settings.request_timeout_seconds == system_settings_data["request_timeout_seconds"]
    assert settings.default_currency == system_settings_data["default_currency"]
    assert settings.default_language == system_settings_data["default_language"]
    assert settings.enable_cost_history == system_settings_data["enable_cost_history"]
    assert settings.enable_route_optimization == system_settings_data["enable_route_optimization"]
    assert settings.enable_real_time_tracking == system_settings_data["enable_real_time_tracking"]
    assert settings.maps_provider == system_settings_data["maps_provider"]
    assert settings.geocoding_provider == system_settings_data["geocoding_provider"]
    assert settings.min_margin_percent == system_settings_data["min_margin_percent"]
    assert settings.max_margin_percent == system_settings_data["max_margin_percent"]
    assert settings.price_rounding_decimals == system_settings_data["price_rounding_decimals"]
    assert settings.max_route_duration == system_settings_data["max_route_duration"]
    assert settings.is_active == system_settings_data["is_active"]
    assert settings.last_modified is not None


def test_to_domain_conversion(db_session, system_settings_data):
    """Test conversion from SQLAlchemy model to domain entity."""
    # Create and save settings
    settings = SystemSettings(**system_settings_data)
    db_session.add(settings)
    db_session.commit()

    # Convert to domain entity
    domain_settings = settings.to_domain()

    # Verify conversion accuracy
    assert isinstance(domain_settings, DomainSystemSettings)
    assert isinstance(domain_settings.id, UUID)
    assert domain_settings.id == UUID(settings.id)
    assert domain_settings.api_url == settings.api_url
    assert domain_settings.api_version == settings.api_version
    assert domain_settings.request_timeout_seconds == settings.request_timeout_seconds
    assert domain_settings.default_currency == settings.default_currency
    assert domain_settings.default_language == settings.default_language
    assert domain_settings.enable_cost_history == settings.enable_cost_history
    assert domain_settings.enable_route_optimization == settings.enable_route_optimization
    assert domain_settings.enable_real_time_tracking == settings.enable_real_time_tracking
    assert domain_settings.maps_provider == settings.maps_provider
    assert domain_settings.geocoding_provider == settings.geocoding_provider
    assert domain_settings.min_margin_percent == Decimal(str(settings.min_margin_percent))
    assert domain_settings.max_margin_percent == Decimal(str(settings.max_margin_percent))
    assert domain_settings.price_rounding_decimals == settings.price_rounding_decimals
    assert domain_settings.max_route_duration == timedelta(days=int(settings.max_route_duration.split()[0]))
    assert domain_settings.is_active == settings.is_active
    assert isinstance(domain_settings.last_modified, datetime)


def test_from_domain_conversion(db_session, domain_system_settings):
    """Test creation of SQLAlchemy model from domain entity."""
    # Create model from domain entity
    settings = SystemSettings.from_domain(domain_system_settings)
    db_session.add(settings)
    db_session.commit()

    # Verify conversion accuracy
    assert str(domain_system_settings.id) == settings.id
    assert domain_system_settings.api_url == settings.api_url
    assert domain_system_settings.api_version == settings.api_version
    assert domain_system_settings.request_timeout_seconds == settings.request_timeout_seconds
    assert domain_system_settings.default_currency == settings.default_currency
    assert domain_system_settings.default_language == settings.default_language
    assert domain_system_settings.enable_cost_history == settings.enable_cost_history
    assert domain_system_settings.enable_route_optimization == settings.enable_route_optimization
    assert domain_system_settings.enable_real_time_tracking == settings.enable_real_time_tracking
    assert domain_system_settings.maps_provider == settings.maps_provider
    assert domain_system_settings.geocoding_provider == settings.geocoding_provider
    assert float(domain_system_settings.min_margin_percent) == settings.min_margin_percent
    assert float(domain_system_settings.max_margin_percent) == settings.max_margin_percent
    assert domain_system_settings.price_rounding_decimals == settings.price_rounding_decimals
    assert f"{domain_system_settings.max_route_duration.days} days" == settings.max_route_duration
    assert domain_system_settings.is_active == settings.is_active


def test_timedelta_string_conversions(db_session):
    """Test conversion between timedelta and string representations."""
    # Test various duration formats
    test_cases = [
        ("1 days", timedelta(days=1)),
        ("7 days", timedelta(days=7)),
        ("30 days", timedelta(days=30)),
        ("365 days", timedelta(days=365))
    ]

    for duration_str, duration_td in test_cases:
        # Create settings with string duration
        settings = SystemSettings(
            api_url="http://test.com",
            api_version="v1",
            request_timeout_seconds=30,
            max_route_duration=duration_str,
            min_margin_percent=5.0,
            max_margin_percent=50.0
        )
        db_session.add(settings)
        db_session.commit()

        # Convert to domain and verify timedelta
        domain_settings = settings.to_domain()
        assert domain_settings.max_route_duration == duration_td

        # Convert back and verify string format
        model_settings = SystemSettings.from_domain(domain_settings)
        assert model_settings.max_route_duration == duration_str


def test_uuid_handling(db_session, domain_system_settings):
    """Test proper handling of UUIDs."""
    # Test with predefined UUID
    settings = SystemSettings.from_domain(domain_system_settings)
    db_session.add(settings)
    db_session.commit()

    assert settings.id == str(domain_system_settings.id)
    
    # Test with auto-generated UUID
    new_settings = SystemSettings(
        api_url="http://test.com",
        api_version="v1",
        request_timeout_seconds=30,
        max_route_duration="5 days",
        min_margin_percent=5.0,
        max_margin_percent=50.0
    )
    db_session.add(new_settings)
    db_session.commit()

    assert new_settings.id is not None
    # Verify it's a valid UUID string
    uuid_obj = UUID(new_settings.id)
    assert isinstance(uuid_obj, UUID)

    # Convert to domain and back
    domain_obj = new_settings.to_domain()
    assert isinstance(domain_obj.id, UUID)
    assert str(domain_obj.id) == new_settings.id

    model_obj = SystemSettings.from_domain(domain_obj)
    assert model_obj.id == new_settings.id


def test_null_constraints(db_session):
    """Test null constraints on required fields."""
    # Test required fields
    settings = SystemSettings()
    db_session.add(settings)
    
    with pytest.raises(Exception) as exc_info:
        db_session.commit()
    db_session.rollback()

    # Create minimal valid settings
    settings = SystemSettings(
        api_url="http://test.com",
        api_version="v1",
        request_timeout_seconds=30,
        max_route_duration="5 days",
        min_margin_percent=5.0,
        max_margin_percent=50.0
    )
    db_session.add(settings)
    db_session.commit()

    assert settings.id is not None


def test_active_state_management(db_session, system_settings_data):
    """Test active state management."""
    # Create active settings
    settings = SystemSettings(**system_settings_data)
    db_session.add(settings)
    db_session.commit()

    assert settings.is_active is True

    # Test querying active settings
    active_settings = db_session.query(SystemSettings).filter(SystemSettings.is_active.is_(True)).all()
    assert settings in active_settings

    # Deactivate settings
    settings.is_active = False
    db_session.commit()

    # Test querying inactive settings
    inactive_settings = db_session.query(SystemSettings).filter(SystemSettings.is_active.is_(False)).all()
    assert settings in inactive_settings
    assert settings not in db_session.query(SystemSettings).filter(SystemSettings.is_active.is_(True)).all()
