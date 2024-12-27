"""Tests for the Vehicle SQLAlchemy model."""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from src.domain.entities.vehicle import VehicleSpecification
from src.infrastructure.models import Vehicle, Driver


@pytest.fixture
def driver_data():
    """Create test driver data."""
    return {
        "first_name": "John",
        "last_name": "Doe",
        "license_number": "DL123456",
        "license_type": "CE",
        "license_expiry": datetime.utcnow() + timedelta(days=365),
        "contact_number": "+1234567890",
        "email": "john.doe@example.com",
        "years_experience": 5
    }


@pytest.fixture
def driver(db_session, driver_data):
    """Create a test driver."""
    driver = Driver(**driver_data)
    db_session.add(driver)
    db_session.commit()
    return driver


@pytest.fixture
def vehicle_data():
    """Create test vehicle data."""
    return {
        "vehicle_type": "truck",
        "fuel_consumption_rate": 25.0,  # L/100km
        "empty_consumption_factor": 0.8,  # 80% of full consumption when empty
        "maintenance_rate_per_km": 0.15,  # EUR/km
        "toll_class": "Euro6",
        "has_special_equipment": True,
        "equipment_costs": {
            "refrigeration": 50.0,
            "lift": 30.0
        }
    }


@pytest.fixture
def domain_vehicle_spec():
    """Create a domain vehicle specification."""
    return VehicleSpecification(
        vehicle_type="truck",
        fuel_consumption_rate=25.0,
        empty_consumption_factor=0.8,
        maintenance_rate_per_km=Decimal("0.15"),
        toll_class="Euro6",
        has_special_equipment=True,
        equipment_costs={
            "refrigeration": Decimal("50.0"),
            "lift": Decimal("30.0")
        }
    )


def test_create_vehicle(db_session, vehicle_data):
    """Test creating a new vehicle."""
    vehicle = Vehicle(**vehicle_data)
    db_session.add(vehicle)
    db_session.commit()

    assert vehicle.id is not None
    assert vehicle.vehicle_type == vehicle_data["vehicle_type"]
    assert vehicle.fuel_consumption_rate == vehicle_data["fuel_consumption_rate"]
    assert vehicle.empty_consumption_factor == vehicle_data["empty_consumption_factor"]
    assert vehicle.maintenance_rate_per_km == vehicle_data["maintenance_rate_per_km"]
    assert vehicle.toll_class == vehicle_data["toll_class"]
    assert vehicle.has_special_equipment == vehicle_data["has_special_equipment"]
    assert vehicle.equipment_costs == vehicle_data["equipment_costs"]
    assert vehicle.is_active is True
    assert vehicle.created_at is not None
    assert vehicle.updated_at is not None
    assert vehicle.driver_id is None


def test_vehicle_driver_relationship(db_session, vehicle_data, driver):
    """Test vehicle-driver relationship."""
    # Create vehicle with driver
    vehicle = Vehicle(**vehicle_data, driver_id=driver.id)
    db_session.add(vehicle)
    db_session.commit()

    # Test relationship from vehicle to driver
    assert vehicle.driver_id == driver.id
    assert vehicle.driver == driver
    assert vehicle in driver.vehicles

    # Test updating driver
    new_driver = Driver(
        first_name="Jane",
        last_name="Smith",
        license_number="DL789012",
        license_type="CE",
        license_expiry=datetime.utcnow() + timedelta(days=365),
        contact_number="+0987654321",
        email="jane.smith@example.com"
    )
    db_session.add(new_driver)
    db_session.commit()

    vehicle.driver = new_driver
    db_session.commit()

    assert vehicle.driver_id == new_driver.id
    assert vehicle.driver == new_driver
    assert vehicle in new_driver.vehicles
    assert vehicle not in driver.vehicles


def test_vehicle_equipment_costs(db_session, vehicle_data):
    """Test vehicle equipment costs JSON field."""
    vehicle = Vehicle(**vehicle_data)
    db_session.add(vehicle)
    db_session.commit()

    # Test reading JSON field
    assert vehicle.equipment_costs == vehicle_data["equipment_costs"]
    assert "refrigeration" in vehicle.equipment_costs
    assert vehicle.equipment_costs["refrigeration"] == 50.0

    # Test updating JSON field
    new_equipment = {
        "refrigeration": 60.0,
        "lift": 35.0,
        "gps": 20.0
    }
    vehicle.equipment_costs = new_equipment
    db_session.commit()

    db_session.refresh(vehicle)
    assert vehicle.equipment_costs == new_equipment
    assert vehicle.equipment_costs["gps"] == 20.0


def test_vehicle_timestamps(db_session, vehicle_data):
    """Test vehicle timestamp fields."""
    # Create vehicle and check initial timestamps
    vehicle = Vehicle(**vehicle_data)
    db_session.add(vehicle)
    db_session.commit()

    created_at = vehicle.created_at
    updated_at = vehicle.updated_at
    assert created_at is not None
    assert updated_at is not None
    assert abs((created_at - updated_at).total_seconds()) < 0.1  # Allow small difference

    # Update vehicle and check timestamps
    db_session.expire(vehicle)
    vehicle.fuel_consumption_rate = 30.0
    db_session.commit()

    assert vehicle.created_at == created_at
    assert vehicle.updated_at > updated_at


def test_vehicle_active_status(db_session, vehicle_data):
    """Test vehicle active status field."""
    # Create active vehicle
    vehicle = Vehicle(**vehicle_data)
    db_session.add(vehicle)
    db_session.commit()

    assert vehicle.is_active is True

    # Test querying active vehicles
    active_vehicles = db_session.query(Vehicle).filter(Vehicle.is_active.is_(True)).all()
    assert vehicle in active_vehicles

    # Deactivate vehicle
    vehicle.is_active = False
    db_session.commit()

    # Test querying inactive vehicles
    inactive_vehicles = db_session.query(Vehicle).filter(Vehicle.is_active.is_(False)).all()
    assert vehicle in inactive_vehicles
    assert vehicle not in db_session.query(Vehicle).filter(Vehicle.is_active.is_(True)).all()


def test_vehicle_null_constraints(db_session):
    """Test vehicle null constraints."""
    # Test required fields
    vehicle = Vehicle()
    db_session.add(vehicle)
    
    with pytest.raises(Exception) as exc_info:
        db_session.commit()
    db_session.rollback()
    
    # Create minimal valid vehicle
    vehicle = Vehicle(
        vehicle_type="van",
        fuel_consumption_rate=20.0,
        empty_consumption_factor=0.75,
        maintenance_rate_per_km=0.12,
        toll_class="Euro5"
    )
    db_session.add(vehicle)
    db_session.commit()

    assert vehicle.id is not None


def test_multiple_vehicles_per_driver(db_session, driver, vehicle_data):
    """Test assigning multiple vehicles to a driver."""
    # Create first vehicle
    vehicle1 = Vehicle(**vehicle_data, driver_id=driver.id)
    db_session.add(vehicle1)

    # Create second vehicle with different specs
    vehicle2_data = vehicle_data.copy()
    vehicle2_data.update({
        "vehicle_type": "van",
        "fuel_consumption_rate": 18.0,
        "empty_consumption_factor": 0.75
    })
    vehicle2 = Vehicle(**vehicle2_data, driver_id=driver.id)
    db_session.add(vehicle2)

    db_session.commit()

    # Check both vehicles are assigned to the driver
    assert len(driver.vehicles) == 2
    assert vehicle1 in driver.vehicles
    assert vehicle2 in driver.vehicles

    # Verify each vehicle has correct specs
    assert vehicle1.vehicle_type == "truck"
    assert vehicle2.vehicle_type == "van"
    assert vehicle1.fuel_consumption_rate == 25.0
    assert vehicle2.fuel_consumption_rate == 18.0


def test_to_domain_conversion(db_session, vehicle_data):
    """Test conversion from SQLAlchemy model to domain entity."""
    # Create and save vehicle
    vehicle = Vehicle(**vehicle_data)
    db_session.add(vehicle)
    db_session.commit()

    # Convert to domain entity
    domain_spec = vehicle.to_domain()

    # Verify conversion accuracy
    assert isinstance(domain_spec, VehicleSpecification)
    assert domain_spec.vehicle_type == vehicle.vehicle_type
    assert domain_spec.fuel_consumption_rate == vehicle.fuel_consumption_rate
    assert domain_spec.empty_consumption_factor == vehicle.empty_consumption_factor
    assert domain_spec.maintenance_rate_per_km == Decimal(str(vehicle.maintenance_rate_per_km))
    assert domain_spec.toll_class == vehicle.toll_class
    assert domain_spec.has_special_equipment == vehicle.has_special_equipment

    # Check equipment costs conversion to Decimal
    assert all(isinstance(cost, Decimal) for cost in domain_spec.equipment_costs.values())
    assert domain_spec.equipment_costs["refrigeration"] == Decimal(str(vehicle.equipment_costs["refrigeration"]))
    assert domain_spec.equipment_costs["lift"] == Decimal(str(vehicle.equipment_costs["lift"]))


def test_from_domain_conversion(db_session, domain_vehicle_spec):
    """Test creation of SQLAlchemy model from domain entity."""
    # Create model from domain entity
    vehicle = Vehicle.from_domain(domain_vehicle_spec)
    db_session.add(vehicle)
    db_session.commit()

    # Verify conversion accuracy
    assert vehicle.vehicle_type == domain_vehicle_spec.vehicle_type
    assert vehicle.fuel_consumption_rate == float(domain_vehicle_spec.fuel_consumption_rate)
    assert vehicle.empty_consumption_factor == float(domain_vehicle_spec.empty_consumption_factor)
    assert vehicle.maintenance_rate_per_km == float(domain_vehicle_spec.maintenance_rate_per_km)
    assert vehicle.toll_class == domain_vehicle_spec.toll_class
    assert vehicle.has_special_equipment == domain_vehicle_spec.has_special_equipment

    # Check equipment costs conversion to float
    assert all(isinstance(cost, float) for cost in vehicle.equipment_costs.values())
    assert vehicle.equipment_costs["refrigeration"] == float(domain_vehicle_spec.equipment_costs["refrigeration"])
    assert vehicle.equipment_costs["lift"] == float(domain_vehicle_spec.equipment_costs["lift"])


def test_decimal_float_handling(db_session, domain_vehicle_spec):
    """Test proper handling of Decimal/float conversions."""
    # Test precise decimal values
    domain_spec = domain_vehicle_spec
    domain_spec.maintenance_rate_per_km = Decimal("0.155555555")
    domain_spec.equipment_costs["precision_test"] = Decimal("123.456789")

    # Convert to SQLAlchemy model (decimals to floats)
    vehicle = Vehicle.from_domain(domain_spec)
    db_session.add(vehicle)
    db_session.commit()

    # Convert back to domain entity (floats to decimals)
    converted_spec = vehicle.to_domain()

    # Verify precision maintained through conversions
    assert str(converted_spec.maintenance_rate_per_km) == str(Decimal(str(vehicle.maintenance_rate_per_km)))
    assert str(converted_spec.equipment_costs["precision_test"]) == str(Decimal(str(vehicle.equipment_costs["precision_test"])))
