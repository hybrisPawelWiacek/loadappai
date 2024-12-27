"""Tests for transport-related domain entities."""

import pytest
from datetime import datetime
from typing import Dict
from uuid import UUID

from src.domain.entities.transport import (
    VehicleType,
    EquipmentType,
    CargoTypeConfig,
    SpeedLimit,
    TransportSettings,
    utc_now
)


@pytest.fixture
def valid_vehicle_type() -> Dict:
    """Create valid vehicle type data."""
    return {
        "name": "40t Truck",
        "capacity_kg": 40000,
        "volume_m3": 90,
        "length_m": 13.6,
        "width_m": 2.4,
        "height_m": 2.6,
        "emissions_class": "EURO6",
        "fuel_consumption_empty": 25.0,
        "fuel_consumption_loaded": 32.0,
        "equipment_requirements": ["tail_lift"],
        "metadata": {"manufacturer": "Volvo"}
    }


@pytest.fixture
def valid_equipment_type() -> Dict:
    """Create valid equipment type data."""
    return {
        "name": "Tail Lift",
        "description": "Hydraulic lift for loading/unloading",
        "weight_kg": 500,
        "compatible_vehicles": ["truck_40t"],
        "compatible_cargo_types": ["pallets", "machinery"],
        "metadata": {"power_source": "hydraulic"}
    }


@pytest.fixture
def valid_cargo_type() -> Dict:
    """Create valid cargo type data."""
    return {
        "name": "Frozen Food",
        "description": "Temperature controlled frozen food",
        "requires_temperature_control": True,
        "default_temp_range": {"min": -20, "max": -18},
        "special_handling_requirements": ["quick_loading"],
        "compatible_vehicles": ["reefer_truck"],
        "required_equipment": ["temp_monitor"],
        "metadata": {"packaging": "cardboard"}
    }


@pytest.fixture
def valid_speed_limit() -> Dict:
    """Create valid speed limit data."""
    return {
        "country": "EU",
        "highway_kmh": 90,
        "rural_kmh": 80,
        "urban_kmh": 50,
        "vehicle_specific": {
            "truck_40t": {
                "highway": 80,
                "rural": 70,
                "urban": 50
            }
        }
    }


class TestVehicleType:
    """Test VehicleType validation and behavior."""

    def test_valid_vehicle_type(self, valid_vehicle_type):
        """Test creating a valid vehicle type."""
        vehicle = VehicleType(**valid_vehicle_type)
        assert vehicle.name == valid_vehicle_type["name"]
        assert vehicle.capacity_kg == valid_vehicle_type["capacity_kg"]
        assert vehicle.metadata == valid_vehicle_type["metadata"]

    def test_invalid_dimensions(self, valid_vehicle_type):
        """Test validation of vehicle dimensions."""
        # Test zero dimensions
        for dim in ["length_m", "width_m", "height_m"]:
            invalid_data = valid_vehicle_type.copy()
            invalid_data[dim] = 0
            with pytest.raises(ValueError, match="greater than 0"):
                VehicleType(**invalid_data)

        # Test negative dimensions
        invalid_data = valid_vehicle_type.copy()
        invalid_data["volume_m3"] = -1
        with pytest.raises(ValueError, match="greater than 0"):
            VehicleType(**invalid_data)

    def test_invalid_consumption(self, valid_vehicle_type):
        """Test validation of fuel consumption values."""
        invalid_data = valid_vehicle_type.copy()
        invalid_data["fuel_consumption_empty"] = -1
        with pytest.raises(ValueError, match="greater than 0"):
            VehicleType(**invalid_data)

        invalid_data["fuel_consumption_loaded"] = 0
        with pytest.raises(ValueError, match="greater than 0"):
            VehicleType(**invalid_data)


class TestEquipmentType:
    """Test EquipmentType validation and behavior."""

    def test_valid_equipment(self, valid_equipment_type):
        """Test creating valid equipment."""
        equipment = EquipmentType(**valid_equipment_type)
        assert equipment.name == valid_equipment_type["name"]
        assert equipment.weight_kg == valid_equipment_type["weight_kg"]
        assert equipment.compatible_vehicles == valid_equipment_type["compatible_vehicles"]

    def test_invalid_weight(self, valid_equipment_type):
        """Test validation of equipment weight."""
        invalid_data = valid_equipment_type.copy()
        invalid_data["weight_kg"] = -1
        with pytest.raises(ValueError, match="greater than or equal to 0"):
            EquipmentType(**invalid_data)

    def test_empty_compatibility_lists(self, valid_equipment_type):
        """Test equipment with empty compatibility lists."""
        data = valid_equipment_type.copy()
        data["compatible_vehicles"] = []
        data["compatible_cargo_types"] = []
        equipment = EquipmentType(**data)
        assert equipment.compatible_vehicles == []
        assert equipment.compatible_cargo_types == []


class TestCargoTypeConfig:
    """Test CargoTypeConfig validation and behavior."""

    def test_valid_cargo_type(self, valid_cargo_type):
        """Test creating valid cargo type."""
        cargo = CargoTypeConfig(**valid_cargo_type)
        assert cargo.name == valid_cargo_type["name"]
        assert cargo.requires_temperature_control == valid_cargo_type["requires_temperature_control"]
        assert cargo.default_temp_range == valid_cargo_type["default_temp_range"]

    def test_temperature_control_validation(self, valid_cargo_type):
        """Test temperature control validation."""
        # Test missing temp range when required
        invalid_data = valid_cargo_type.copy()
        invalid_data["requires_temperature_control"] = True
        invalid_data["default_temp_range"] = None
        with pytest.raises(ValueError, match="Temperature range must be specified"):
            CargoTypeConfig(**invalid_data)

        # Test invalid temperature range
        invalid_data["default_temp_range"] = {"min": 0, "max": -5}
        with pytest.raises(ValueError, match="Minimum temperature must be less than maximum"):
            CargoTypeConfig(**invalid_data)

    def test_non_temperature_controlled(self, valid_cargo_type):
        """Test non-temperature controlled cargo."""
        data = valid_cargo_type.copy()
        data["requires_temperature_control"] = False
        data["default_temp_range"] = None
        cargo = CargoTypeConfig(**data)
        assert cargo.default_temp_range is None


class TestSpeedLimit:
    """Test SpeedLimit validation and behavior."""

    def test_valid_speed_limit(self, valid_speed_limit):
        """Test creating valid speed limit."""
        speed_limit = SpeedLimit(**valid_speed_limit)
        assert speed_limit.country == valid_speed_limit["country"]
        assert speed_limit.highway_kmh == valid_speed_limit["highway_kmh"]
        assert speed_limit.vehicle_specific == valid_speed_limit["vehicle_specific"]

    def test_invalid_speeds(self, valid_speed_limit):
        """Test validation of speed values."""
        for field in ["highway_kmh", "rural_kmh", "urban_kmh"]:
            invalid_data = valid_speed_limit.copy()
            invalid_data[field] = 0
            with pytest.raises(ValueError, match="greater than 0"):
                SpeedLimit(**invalid_data)

    def test_vehicle_specific_speeds(self, valid_speed_limit):
        """Test vehicle-specific speed limits."""
        speed_limit = SpeedLimit(**valid_speed_limit)
        assert speed_limit.vehicle_specific["truck_40t"]["highway"] == 80
        assert speed_limit.vehicle_specific["truck_40t"]["urban"] == 50


class TestTransportSettings:
    """Test TransportSettings validation and behavior."""

    def test_valid_transport_settings(self, valid_vehicle_type, valid_equipment_type,
                                    valid_cargo_type, valid_speed_limit):
        """Test creating valid transport settings."""
        settings = TransportSettings(
            vehicle_types={"truck_40t": VehicleType(**valid_vehicle_type)},
            equipment_types={"tail_lift": EquipmentType(**valid_equipment_type)},
            cargo_types={"frozen": CargoTypeConfig(**valid_cargo_type)},
            loading_time_minutes=45,
            unloading_time_minutes=45,
            max_driving_hours=9.0,
            required_rest_hours=11.0,
            max_working_days=5,
            speed_limits={"EU": SpeedLimit(**valid_speed_limit)}
        )
        assert isinstance(settings.id, UUID)
        assert len(settings.vehicle_types) == 1
        assert len(settings.speed_limits) == 1
        assert settings.is_active is True

    def test_driving_hours_validation(self, valid_vehicle_type, valid_equipment_type,
                                    valid_cargo_type, valid_speed_limit):
        """Test validation of driving and rest hours."""
        # Test excessive driving hours
        with pytest.raises(ValueError, match="Maximum driving hours cannot exceed 24"):
            TransportSettings(
                vehicle_types={"truck_40t": VehicleType(**valid_vehicle_type)},
                equipment_types={"tail_lift": EquipmentType(**valid_equipment_type)},
                cargo_types={"frozen": CargoTypeConfig(**valid_cargo_type)},
                loading_time_minutes=45,
                unloading_time_minutes=45,
                max_driving_hours=25.0,  # Invalid
                required_rest_hours=8.0,
                max_working_days=5,
                speed_limits={"EU": SpeedLimit(**valid_speed_limit)}
            )

        # Test invalid combination of driving and rest hours
        with pytest.raises(ValueError, match="Sum of driving and rest hours cannot exceed 24"):
            TransportSettings(
                vehicle_types={"truck_40t": VehicleType(**valid_vehicle_type)},
                equipment_types={"tail_lift": EquipmentType(**valid_equipment_type)},
                cargo_types={"frozen": CargoTypeConfig(**valid_cargo_type)},
                loading_time_minutes=45,
                unloading_time_minutes=45,
                max_driving_hours=14.0,
                required_rest_hours=12.0,  # Invalid combination
                max_working_days=5,
                speed_limits={"EU": SpeedLimit(**valid_speed_limit)}
            )

    def test_empty_collections_validation(self, valid_vehicle_type, valid_equipment_type,
                                        valid_cargo_type, valid_speed_limit):
        """Test validation of required collections."""
        base_settings = {
            "loading_time_minutes": 45,
            "unloading_time_minutes": 45,
            "max_driving_hours": 9.0,
            "required_rest_hours": 11.0,
            "max_working_days": 5,
        }

        # Test empty vehicle types
        with pytest.raises(ValueError, match="At least one vehicle type must be defined"):
            TransportSettings(
                **base_settings,
                vehicle_types={},
                equipment_types={"tail_lift": EquipmentType(**valid_equipment_type)},
                cargo_types={"frozen": CargoTypeConfig(**valid_cargo_type)},
                speed_limits={"EU": SpeedLimit(**valid_speed_limit)}
            )

        # Test empty cargo types
        with pytest.raises(ValueError, match="At least one cargo type must be defined"):
            TransportSettings(
                **base_settings,
                vehicle_types={"truck_40t": VehicleType(**valid_vehicle_type)},
                equipment_types={"tail_lift": EquipmentType(**valid_equipment_type)},
                cargo_types={},
                speed_limits={"EU": SpeedLimit(**valid_speed_limit)}
            )

        # Test empty speed limits
        with pytest.raises(ValueError, match="At least one country speed limit must be defined"):
            TransportSettings(
                **base_settings,
                vehicle_types={"truck_40t": VehicleType(**valid_vehicle_type)},
                equipment_types={"tail_lift": EquipmentType(**valid_equipment_type)},
                cargo_types={"frozen": CargoTypeConfig(**valid_cargo_type)},
                speed_limits={}
            )

    def test_default_settings(self):
        """Test default transport settings generation."""
        settings = TransportSettings.get_default()
        assert isinstance(settings, TransportSettings)
        assert "truck_40t" in settings.vehicle_types
        assert "tail_lift" in settings.equipment_types
        assert "general" in settings.cargo_types
        assert "EU" in settings.speed_limits
        assert settings.max_driving_hours == 9.0
        assert settings.required_rest_hours == 11.0
        assert settings.max_working_days == 5

    def test_business_rules(self, valid_vehicle_type, valid_equipment_type,
                           valid_cargo_type, valid_speed_limit):
        """Test business rule validation."""
        # Create initial valid settings
        settings_data = {
            "vehicle_types": {"truck_40t": VehicleType(**valid_vehicle_type)},
            "equipment_types": {"tail_lift": EquipmentType(**valid_equipment_type)},
            "cargo_types": {"frozen": CargoTypeConfig(**valid_cargo_type)},
            "loading_time_minutes": 45,
            "unloading_time_minutes": 45,
            "max_driving_hours": 9.0,
            "required_rest_hours": 11.0,
            "max_working_days": 5,
            "speed_limits": {"EU": SpeedLimit(**valid_speed_limit)}
        }

        # Test working days limit
        invalid_settings = settings_data.copy()
        invalid_settings["max_working_days"] = 8
        with pytest.raises(ValueError, match="Input should be less than or equal to 7"):
            TransportSettings(**invalid_settings)

        # Test loading time validation
        invalid_settings = settings_data.copy()
        invalid_settings["loading_time_minutes"] = 0
        with pytest.raises(ValueError, match="Input should be greater than 0"):
            TransportSettings(**invalid_settings)

        # Test unloading time validation
        invalid_settings = settings_data.copy()
        invalid_settings["unloading_time_minutes"] = -1
        with pytest.raises(ValueError, match="Input should be greater than 0"):
            TransportSettings(**invalid_settings)

        # Create valid settings to test last_modified
        settings = TransportSettings(**settings_data)
        assert isinstance(settings.last_modified, datetime)
        assert settings.last_modified.tzinfo is not None  # Ensures timezone-aware
