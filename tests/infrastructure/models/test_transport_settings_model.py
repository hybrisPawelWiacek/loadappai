"""Tests for the TransportSettings model."""
import pytest
from datetime import datetime
from decimal import Decimal
from uuid import uuid4, UUID
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from src.domain.entities.transport import (
    TransportSettings as DomainTransportSettings,
    VehicleType,
    EquipmentType,
    CargoTypeConfig,
    SpeedLimit
)
from src.infrastructure.models import TransportSettings


@pytest.fixture
def default_vehicle_types():
    """Default test data for vehicle types."""
    return {
        "truck_40t": {
            "name": "40t Truck",
            "capacity_kg": 40000.0,
            "volume_m3": 90.0,
            "length_m": 13.6,
            "width_m": 2.4,
            "height_m": 2.6,
            "emissions_class": "EURO6",
            "fuel_consumption_empty": 25.0,
            "fuel_consumption_loaded": 32.0,
            "equipment_requirements": ["tail_lift"]
        }
    }


@pytest.fixture
def default_equipment_types():
    """Default test data for equipment types."""
    return {
        "tail_lift": {
            "name": "Tail Lift",
            "description": "Hydraulic lift for loading/unloading",
            "weight_kg": 500.0,
            "compatible_vehicles": ["truck_40t"],
            "compatible_cargo_types": ["pallets", "machinery"]
        }
    }


@pytest.fixture
def default_cargo_types():
    """Default test data for cargo types."""
    return {
        "general": {
            "name": "General Cargo",
            "description": "Standard non-temperature controlled cargo",
            "requires_temperature_control": False,
            "compatible_vehicles": ["truck_40t"],
            "required_equipment": []
        },
        "refrigerated": {
            "name": "Refrigerated Cargo",
            "description": "Temperature controlled cargo",
            "requires_temperature_control": True,
            "default_temp_range": {"min": -20.0, "max": -18.0},
            "compatible_vehicles": ["truck_40t"],
            "required_equipment": ["refrigeration_unit"]
        }
    }


@pytest.fixture
def default_speed_limits():
    """Default test data for speed limits."""
    return {
        "EU": {
            "country": "EU",
            "highway_kmh": 90.0,
            "rural_kmh": 80.0,
            "urban_kmh": 50.0,
            "vehicle_specific": {
                "truck_40t": {
                    "highway": 80.0,
                    "rural": 70.0,
                    "urban": 50.0
                }
            }
        }
    }


@pytest.fixture
def default_settings_data(default_vehicle_types, default_equipment_types, 
                         default_cargo_types, default_speed_limits):
    """Default test data for transport settings."""
    return {
        "vehicle_types": default_vehicle_types,
        "equipment_types": default_equipment_types,
        "cargo_types": default_cargo_types,
        "loading_time_minutes": 45,
        "unloading_time_minutes": 45,
        "max_driving_hours": 9.0,
        "required_rest_hours": 11.0,
        "max_working_days": 5,
        "speed_limits": default_speed_limits,
        "is_active": True
    }


def test_create_transport_settings(db_session, default_settings_data):
    """Test creating a new transport settings entry."""
    settings = TransportSettings(**default_settings_data)
    db_session.add(settings)
    db_session.commit()

    assert settings.id is not None
    assert settings.vehicle_types == default_settings_data["vehicle_types"]
    assert settings.equipment_types == default_settings_data["equipment_types"]
    assert settings.cargo_types == default_settings_data["cargo_types"]
    assert settings.loading_time_minutes == default_settings_data["loading_time_minutes"]
    assert settings.unloading_time_minutes == default_settings_data["unloading_time_minutes"]
    assert settings.max_driving_hours == default_settings_data["max_driving_hours"]
    assert settings.required_rest_hours == default_settings_data["required_rest_hours"]
    assert settings.max_working_days == default_settings_data["max_working_days"]
    assert settings.speed_limits == default_settings_data["speed_limits"]
    assert settings.is_active == default_settings_data["is_active"]
    assert settings.last_modified is not None


def test_json_field_validation(db_session, default_settings_data):
    """Test JSON field validation and manipulation."""
    settings = TransportSettings(**default_settings_data)
    db_session.add(settings)
    db_session.commit()

    # Test updating vehicle types
    new_vehicle = {
        "name": "Small Van",
        "capacity_kg": 1500.0,
        "volume_m3": 8.0,
        "length_m": 4.5,
        "width_m": 1.8,
        "height_m": 1.9,
        "emissions_class": "EURO6",
        "fuel_consumption_empty": 8.0,
        "fuel_consumption_loaded": 10.0,
        "equipment_requirements": []
    }
    
    # Deep copy the dictionary to avoid modifying the original
    updated_vehicle_types = settings.vehicle_types.copy()
    updated_vehicle_types["small_van"] = new_vehicle
    settings.vehicle_types = updated_vehicle_types
    
    db_session.commit()
    db_session.refresh(settings)

    assert "small_van" in settings.vehicle_types
    assert settings.vehicle_types["small_van"] == new_vehicle


def test_domain_conversion(db_session, default_settings_data):
    """Test conversion between infrastructure and domain models."""
    # Create infrastructure model
    settings = TransportSettings(**default_settings_data)
    db_session.add(settings)
    db_session.commit()

    # Convert to domain entity
    domain_settings = settings.to_domain()
    assert isinstance(domain_settings, DomainTransportSettings)
    assert domain_settings.id == UUID(settings.id)
    
    # Check nested type conversions
    for key, value in domain_settings.vehicle_types.items():
        assert isinstance(value, VehicleType)
        # Check original data is preserved
        assert value.name == settings.vehicle_types[key]["name"]
        assert value.capacity_kg == settings.vehicle_types[key]["capacity_kg"]
    
    for key, value in domain_settings.equipment_types.items():
        assert isinstance(value, EquipmentType)
        assert value.name == settings.equipment_types[key]["name"]
        assert value.weight_kg == settings.equipment_types[key]["weight_kg"]
    
    for key, value in domain_settings.cargo_types.items():
        assert isinstance(value, CargoTypeConfig)
        assert value.name == settings.cargo_types[key]["name"]
        assert value.requires_temperature_control == settings.cargo_types[key]["requires_temperature_control"]
    
    for key, value in domain_settings.speed_limits.items():
        assert isinstance(value, SpeedLimit)
        assert value.country == key
        assert value.highway_kmh == settings.speed_limits[key]["highway_kmh"]

    # Convert back to infrastructure model
    new_settings = TransportSettings.from_domain(domain_settings)
    assert new_settings.id == settings.id
    
    # Compare only the fields that exist in both models
    for key in settings.vehicle_types:
        assert new_settings.vehicle_types[key]["name"] == settings.vehicle_types[key]["name"]
        assert new_settings.vehicle_types[key]["capacity_kg"] == settings.vehicle_types[key]["capacity_kg"]
    
    for key in settings.equipment_types:
        assert new_settings.equipment_types[key]["name"] == settings.equipment_types[key]["name"]
        assert new_settings.equipment_types[key]["weight_kg"] == settings.equipment_types[key]["weight_kg"]
    
    for key in settings.cargo_types:
        assert new_settings.cargo_types[key]["name"] == settings.cargo_types[key]["name"]
        assert new_settings.cargo_types[key]["requires_temperature_control"] == settings.cargo_types[key]["requires_temperature_control"]
    
    for key in settings.speed_limits:
        assert new_settings.speed_limits[key]["highway_kmh"] == settings.speed_limits[key]["highway_kmh"]
        assert new_settings.speed_limits[key]["rural_kmh"] == settings.speed_limits[key]["rural_kmh"]
        assert new_settings.speed_limits[key]["urban_kmh"] == settings.speed_limits[key]["urban_kmh"]


def test_null_constraints(db_session):
    """Test null constraints on required fields."""
    required_fields = [
        "loading_time_minutes",
        "unloading_time_minutes", 
        "max_driving_hours",
        "required_rest_hours",
        "max_working_days"
    ]

    base_data = {
        "id": str(uuid4()),  
        "vehicle_types": {"test": {"name": "Test", "capacity_kg": 1000.0, "volume_m3": 10.0, 
                                "length_m": 5.0, "width_m": 2.0, "height_m": 2.0,
                                "emissions_class": "EURO6", "fuel_consumption_empty": 10.0,
                                "fuel_consumption_loaded": 15.0}},
        "equipment_types": {"test": {"name": "Test", "description": "Test", "weight_kg": 100.0}},
        "cargo_types": {"test": {"name": "Test", "description": "Test", "requires_temperature_control": False}},
        "loading_time_minutes": 45,
        "unloading_time_minutes": 45,
        "max_driving_hours": 9.0,
        "required_rest_hours": 11.0,
        "max_working_days": 5,
        "speed_limits": {"EU": {"country": "EU", "highway_kmh": 90.0, "rural_kmh": 80.0, "urban_kmh": 50.0}}
    }

    # Test each required field with None value
    for field in required_fields:
        data = base_data.copy()
        data[field] = None

        settings = TransportSettings(**data)
        db_session.add(settings)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
        
        db_session.rollback()

    # Test invalid values (should fail domain validation)
    invalid_values = {
        "loading_time_minutes": 0,  # Must be > 0
        "unloading_time_minutes": -1,  # Must be > 0
        "max_driving_hours": 25,  # Must be <= 24
        "required_rest_hours": 20,  # Would exceed 24 hours with max_driving_hours
        "max_working_days": 8  # Must be <= 7
    }

    for field, invalid_value in invalid_values.items():
        data = base_data.copy()
        data[field] = invalid_value

        settings = TransportSettings(**data)
        with pytest.raises(ValueError):
            settings.to_domain()

    # Test JSON fields with empty values
    json_fields = ["vehicle_types", "equipment_types", "cargo_types", "speed_limits"]
    for field in json_fields:
        data = base_data.copy()
        data[field] = {}  # Empty dict should fail validation

        settings = TransportSettings(**data)
        with pytest.raises(ValueError):
            settings.to_domain()  # Domain conversion should fail with empty dicts


def test_active_state_management(db_session, default_settings_data):
    """Test active state management and querying."""
    # Create multiple settings
    settings1 = TransportSettings(**default_settings_data)
    settings2 = TransportSettings(**default_settings_data)
    settings2.is_active = False
    
    db_session.add_all([settings1, settings2])
    db_session.commit()

    # Query active settings
    active_settings = db_session.query(TransportSettings).filter(
        TransportSettings.is_active == True
    ).all()
    
    assert len(active_settings) == 1
    assert active_settings[0].id == settings1.id

    # Deactivate settings
    settings1.is_active = False
    db_session.commit()

    active_settings = db_session.query(TransportSettings).filter(
        TransportSettings.is_active == True
    ).all()
    assert len(active_settings) == 0


def test_timestamp_handling(db_session, default_settings_data):
    """Test last_modified timestamp handling."""
    settings = TransportSettings(**default_settings_data)
    db_session.add(settings)
    db_session.commit()
    
    original_timestamp = settings.last_modified

    # Wait a moment to ensure timestamp difference
    import time
    time.sleep(0.1)
    
    # Modify settings
    settings.loading_time_minutes = 60
    db_session.commit()
    db_session.refresh(settings)
    
    assert settings.last_modified > original_timestamp


def test_query_performance(db_session, default_settings_data):
    """Test index performance for common queries."""
    # Create multiple settings
    for _ in range(5):
        settings = TransportSettings(**default_settings_data)
        settings.is_active = _ % 2 == 0
        db_session.add(settings)
    db_session.commit()

    # Test query using index
    query = text("""
        EXPLAIN QUERY PLAN 
        SELECT * FROM transport_settings 
        WHERE is_active = 1
    """)
    
    plan = db_session.execute(query).fetchall()
    plan_str = " ".join(str(row[3]) for row in plan).lower()
    
    # Check if the index is used (specific to SQLite)
    assert "index" in plan_str
