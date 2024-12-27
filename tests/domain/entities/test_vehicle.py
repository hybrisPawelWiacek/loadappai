"""Tests for vehicle and settings-related domain entities."""

from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4
from freezegun import freeze_time
import pytest
from pytz import UTC

from src.domain.entities.vehicle import (
    VehicleSpecification,
    SystemSettings,
    utc_now
)


def test_utc_now():
    """Test UTC now helper function."""
    with freeze_time("2024-01-01 12:00:00"):
        now = utc_now()
        assert isinstance(now, datetime)
        assert now.tzinfo == UTC
        assert now.year == 2024
        assert now.month == 1
        assert now.day == 1
        assert now.hour == 12


@pytest.fixture
def valid_vehicle_spec():
    """Create a valid vehicle specification for testing."""
    return {
        "vehicle_type": "truck",
        "fuel_consumption_rate": 30.0,
        "empty_consumption_factor": 0.8,
        "maintenance_rate_per_km": Decimal("0.15"),
        "toll_class": "heavy",
        "has_special_equipment": True,
        "equipment_costs": {
            "refrigeration": Decimal("50.00"),
            "lift": Decimal("25.50"),
            "gps": Decimal("10.00")
        }
    }


class TestVehicleSpecification:
    """Test VehicleSpecification entity."""

    def test_valid_specification(self, valid_vehicle_spec):
        """Test creating a valid vehicle specification."""
        spec = VehicleSpecification(**valid_vehicle_spec)
        assert spec.vehicle_type == valid_vehicle_spec["vehicle_type"]
        assert spec.fuel_consumption_rate == valid_vehicle_spec["fuel_consumption_rate"]
        assert spec.empty_consumption_factor == valid_vehicle_spec["empty_consumption_factor"]
        assert spec.maintenance_rate_per_km == valid_vehicle_spec["maintenance_rate_per_km"]
        assert spec.toll_class == valid_vehicle_spec["toll_class"]
        assert spec.has_special_equipment == valid_vehicle_spec["has_special_equipment"]
        assert spec.equipment_costs == valid_vehicle_spec["equipment_costs"]

    def test_decimal_precision(self, valid_vehicle_spec):
        """Test handling of decimal precision."""
        data = valid_vehicle_spec.copy()
        data["maintenance_rate_per_km"] = Decimal("0.15555")
        spec = VehicleSpecification(**data)
        assert isinstance(spec.maintenance_rate_per_km, Decimal)
        assert spec.maintenance_rate_per_km == Decimal("0.15555")

    def test_equipment_costs(self, valid_vehicle_spec):
        """Test equipment costs dictionary handling."""
        spec = VehicleSpecification(**valid_vehicle_spec)
        assert len(spec.equipment_costs) == 3
        assert all(isinstance(cost, Decimal) for cost in spec.equipment_costs.values())
        assert spec.equipment_costs["refrigeration"] == Decimal("50.00")
        assert spec.equipment_costs["lift"] == Decimal("25.50")
        assert spec.equipment_costs["gps"] == Decimal("10.00")

    def test_invalid_fuel_consumption(self, valid_vehicle_spec):
        """Test validation of fuel consumption rate."""
        data = valid_vehicle_spec.copy()
        data["fuel_consumption_rate"] = 0
        with pytest.raises(ValueError, match="greater than 0"):
            VehicleSpecification(**data)

        data["fuel_consumption_rate"] = -1
        with pytest.raises(ValueError, match="greater than 0"):
            VehicleSpecification(**data)

    def test_invalid_consumption_factor(self, valid_vehicle_spec):
        """Test validation of empty consumption factor."""
        data = valid_vehicle_spec.copy()
        data["empty_consumption_factor"] = 1.5
        with pytest.raises(ValueError, match="less than or equal to 1"):
            VehicleSpecification(**data)

        data["empty_consumption_factor"] = -0.1
        with pytest.raises(ValueError, match="greater than 0"):
            VehicleSpecification(**data)


@pytest.fixture
def valid_system_settings():
    """Create valid system settings for testing."""
    return {
        "api_url": "http://localhost:5001",
        "api_version": "v1",
        "request_timeout_seconds": 30,
        "default_currency": "EUR",
        "default_language": "en",
        "enable_cost_history": True,
        "enable_route_optimization": True,
        "enable_real_time_tracking": False,
        "maps_provider": "google",
        "geocoding_provider": "google",
        "min_margin_percent": Decimal("5"),
        "max_margin_percent": Decimal("50"),
        "price_rounding_decimals": 2,
        "max_route_duration": timedelta(days=5)
    }


class TestSystemSettings:
    """Test SystemSettings entity."""

    def test_valid_settings(self, valid_system_settings):
        """Test creating valid system settings."""
        settings = SystemSettings(**valid_system_settings)
        assert isinstance(settings.id, UUID)
        assert settings.api_url == valid_system_settings["api_url"]
        assert settings.api_version == valid_system_settings["api_version"]
        assert settings.request_timeout_seconds == valid_system_settings["request_timeout_seconds"]
        assert settings.default_currency == valid_system_settings["default_currency"]
        assert settings.min_margin_percent == valid_system_settings["min_margin_percent"]
        assert settings.max_margin_percent == valid_system_settings["max_margin_percent"]
        assert settings.is_active is True

    def test_uuid_generation(self, valid_system_settings):
        """Test UUID generation for system settings."""
        settings1 = SystemSettings(**valid_system_settings)
        settings2 = SystemSettings(**valid_system_settings)
        assert isinstance(settings1.id, UUID)
        assert isinstance(settings2.id, UUID)
        assert settings1.id != settings2.id

    def test_timestamp_generation(self, valid_system_settings):
        """Test timestamp generation and timezone handling."""
        with freeze_time("2024-01-01 12:00:00"):
            settings = SystemSettings(**valid_system_settings)
            assert isinstance(settings.last_modified, datetime)
            assert settings.last_modified.tzinfo == UTC
            assert settings.last_modified.isoformat() == "2024-01-01T12:00:00+00:00"

    def test_margin_validation(self, valid_system_settings):
        """Test margin percentage validation."""
        data = valid_system_settings.copy()

        # Test invalid max margin
        data["max_margin_percent"] = Decimal("101")
        with pytest.raises(ValueError, match="less than or equal to 100"):
            SystemSettings(**data)

        # Test invalid min margin
        data = valid_system_settings.copy()
        data["min_margin_percent"] = Decimal("-1")
        with pytest.raises(ValueError, match="greater than or equal to 0"):
            SystemSettings(**data)

        # Test min margin greater than max margin
        data = valid_system_settings.copy()
        data["min_margin_percent"] = Decimal("60")
        data["max_margin_percent"] = Decimal("50")
        with pytest.raises(ValueError):
            SystemSettings(**data)

    def test_request_timeout_validation(self, valid_system_settings):
        """Test request timeout validation."""
        data = valid_system_settings.copy()
        data["request_timeout_seconds"] = 0
        with pytest.raises(ValueError, match="greater than 0"):
            SystemSettings(**data)

    def test_default_settings(self):
        """Test default system settings generation."""
        settings = SystemSettings.get_default()
        assert isinstance(settings.id, UUID)
        assert isinstance(settings.last_modified, datetime)
        assert settings.last_modified.tzinfo == UTC
        assert settings.api_url == "http://localhost:5001"
        assert settings.api_version == "v1"
        assert settings.request_timeout_seconds == 30
        assert settings.default_currency == "EUR"
        assert settings.default_language == "en"
        assert settings.enable_cost_history is True
        assert settings.enable_route_optimization is True
        assert settings.enable_real_time_tracking is False
        assert settings.maps_provider == "google"
        assert settings.geocoding_provider == "google"
        assert settings.min_margin_percent == Decimal("5")
        assert settings.max_margin_percent == Decimal("50")
        assert settings.price_rounding_decimals == 2
        assert settings.max_route_duration == timedelta(days=5)
        assert settings.is_active is True
