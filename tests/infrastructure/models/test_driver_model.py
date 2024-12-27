"""Tests for the Driver SQLAlchemy model."""

import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.exc import IntegrityError

from src.infrastructure.models import Driver, Vehicle


@pytest.fixture
def driver_data():
    """Create test driver data."""
    return {
        "first_name": "John",
        "last_name": "Doe",
        "license_number": "DL123456",
        "license_type": "CE",
        "license_expiry": datetime.now(timezone.utc) + timedelta(days=365),
        "contact_number": "+1234567890",
        "email": "john.doe@example.com",
        "years_experience": 5
    }


@pytest.fixture
def vehicle_data():
    """Create test vehicle data."""
    return {
        "vehicle_type": "truck",
        "fuel_consumption_rate": 25.0,
        "empty_consumption_factor": 0.8,
        "maintenance_rate_per_km": 0.15,
        "toll_class": "Euro6",
        "has_special_equipment": True,
        "equipment_costs": {
            "refrigeration": 50.0,
            "lift": 30.0
        }
    }


def test_create_driver(db_session, driver_data):
    """Test creating a new driver."""
    driver = Driver(**driver_data)
    db_session.add(driver)
    db_session.commit()

    assert driver.id is not None
    assert driver.first_name == driver_data["first_name"]
    assert driver.last_name == driver_data["last_name"]
    assert driver.license_number == driver_data["license_number"]
    assert driver.license_type == driver_data["license_type"]
    assert driver.license_expiry == driver_data["license_expiry"]
    assert driver.contact_number == driver_data["contact_number"]
    assert driver.email == driver_data["email"]
    assert driver.years_experience == driver_data["years_experience"]
    assert driver.is_active is True
    assert driver.created_at is not None
    assert driver.created_at.tzinfo is not None  # Ensure timezone info is present
    assert driver.updated_at is not None
    assert driver.updated_at.tzinfo is not None  # Ensure timezone info is present
    assert len(driver.vehicles) == 0


def test_unique_license_number(db_session, driver_data):
    """Test unique constraint on license number."""
    # Create first driver
    driver1 = Driver(**driver_data)
    db_session.add(driver1)
    db_session.commit()

    # Try to create second driver with same license
    driver2 = Driver(**driver_data)
    db_session.add(driver2)
    
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Create second driver with different license
    driver_data["license_number"] = "DL789012"
    driver2 = Driver(**driver_data)
    db_session.add(driver2)
    db_session.commit()

    assert driver2.id is not None
    assert driver2.license_number != driver1.license_number


def test_driver_vehicle_relationship(db_session, driver_data, vehicle_data):
    """Test driver-vehicle relationship."""
    # Create driver
    driver = Driver(**driver_data)
    db_session.add(driver)
    db_session.commit()

    # Create and assign vehicle
    vehicle = Vehicle(**vehicle_data, driver_id=driver.id)
    db_session.add(vehicle)
    db_session.commit()

    # Test relationship from driver to vehicle
    assert len(driver.vehicles) == 1
    assert driver.vehicles[0].id == vehicle.id
    assert driver.vehicles[0].vehicle_type == vehicle_data["vehicle_type"]

    # Test relationship from vehicle to driver
    assert vehicle.driver_id == driver.id
    assert vehicle.driver.first_name == driver_data["first_name"]


def test_driver_timestamps(db_session, driver_data):
    """Test that timestamps are set correctly."""
    driver = Driver(**driver_data)
    db_session.add(driver)
    db_session.commit()

    created_at = driver.created_at
    updated_at = driver.updated_at

    assert created_at is not None
    assert updated_at is not None
    assert created_at.tzinfo is not None  # Ensure timezone info is present
    assert updated_at.tzinfo is not None  # Ensure timezone info is present
    assert abs(created_at - datetime.now(timezone.utc)) < timedelta(seconds=10)
    assert abs(updated_at - datetime.now(timezone.utc)) < timedelta(seconds=10)
    assert abs(created_at - updated_at) < timedelta(seconds=1)  # Should be very close

    # Test that updated_at changes on update
    original_updated_at = driver.updated_at
    driver.years_experience = 6
    db_session.commit()

    assert driver.created_at == created_at  # Created time should not change
    assert driver.updated_at != original_updated_at  # Updated time should change
    assert driver.updated_at > original_updated_at  # New updated time should be later
    assert abs(driver.updated_at - datetime.now(timezone.utc)) < timedelta(seconds=10)  # Should be recent


def test_driver_active_status(db_session, driver_data):
    """Test driver active status field."""
    # Create active driver
    driver = Driver(**driver_data)
    db_session.add(driver)
    db_session.commit()
    assert driver.is_active is True

    # Deactivate driver
    driver.is_active = False
    db_session.commit()
    assert driver.is_active is False

    # Reactivate driver
    driver.is_active = True
    db_session.commit()
    assert driver.is_active is True


def test_driver_null_constraints(db_session):
    """Test driver null constraints."""
    # Try to create driver without required fields
    driver = Driver()
    db_session.add(driver)

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Email is optional
    driver = Driver(
        first_name="John",
        last_name="Doe",
        license_number="DL123456",
        license_type="CE",
        license_expiry=datetime.now(timezone.utc) + timedelta(days=365),
        contact_number="+1234567890",
        years_experience=5
    )
    db_session.add(driver)
    db_session.commit()

    assert driver.id is not None
    assert driver.email is None


def test_driver_license_expiry(db_session, driver_data):
    """Test driver license expiry field."""
    # Set license expiry to past date
    driver_data["license_expiry"] = datetime.now(timezone.utc) - timedelta(days=1)
    driver = Driver(**driver_data)
    db_session.add(driver)
    db_session.commit()

    assert driver.license_expiry < datetime.now(timezone.utc)

    # Update license expiry to future date
    new_expiry = datetime.now(timezone.utc) + timedelta(days=365)
    driver.license_expiry = new_expiry
    db_session.commit()

    assert driver.license_expiry == new_expiry


def test_cascade_delete_vehicles(db_session, driver_data, vehicle_data):
    """Test that deleting a driver does not cascade delete vehicles."""
    # Create driver and vehicle
    driver = Driver(**driver_data)
    db_session.add(driver)
    db_session.commit()

    vehicle = Vehicle(**vehicle_data, driver_id=driver.id)
    db_session.add(vehicle)
    db_session.commit()

    # Delete driver and verify vehicle still exists with null driver_id
    db_session.delete(driver)
    db_session.commit()

    vehicle = db_session.query(Vehicle).filter_by(id=vehicle.id).first()
    assert vehicle is not None
    assert vehicle.driver_id is None
