"""Tests for driver repository implementation."""

import pytest
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from src.domain.entities.driver import Driver
from src.domain.utils.datetime import utc_now
from src.infrastructure.database import Database
from src.infrastructure.repositories.driver_repository import DriverRepository
from src.infrastructure.models import Driver as DriverModel


@pytest.fixture
def driver():
    """Create test driver."""
    return Driver(
        id=uuid4(),
        first_name="John",
        last_name="Doe",
        license_number="DL123456",
        license_type="Class A",
        license_expiry=utc_now() + timedelta(days=365),
        contact_number="+1234567890",
        email="john.doe@example.com",
        years_experience=5,
        is_active=True
    )


@pytest.fixture
def repository(db_session):
    """Create test repository."""
    return DriverRepository(db_session)


def test_create(repository, driver):
    """Test creating a new driver."""
    # Test creating
    created = repository.create(driver)
    assert created.id == driver.id
    assert created.first_name == driver.first_name
    assert created.last_name == driver.last_name
    assert created.license_number == driver.license_number
    assert created.license_type == driver.license_type
    assert created.license_expiry.replace(tzinfo=None) == driver.license_expiry.replace(tzinfo=None)  # Compare naive datetimes
    assert created.contact_number == driver.contact_number
    assert created.email == driver.email
    assert created.years_experience == driver.years_experience
    assert created.is_active == driver.is_active


def test_get_by_id(repository, driver):
    """Test getting driver by ID."""
    # Save driver first
    saved = repository.create(driver)
    
    # Test retrieving
    retrieved = repository.get_by_id(driver.id)
    assert retrieved is not None
    assert retrieved.id == saved.id
    assert retrieved.first_name == saved.first_name
    assert retrieved.last_name == saved.last_name
    assert retrieved.license_number == saved.license_number
    assert retrieved.license_type == saved.license_type
    assert retrieved.license_expiry.replace(tzinfo=None) == saved.license_expiry.replace(tzinfo=None)  # Compare naive datetimes
    assert retrieved.contact_number == saved.contact_number
    assert retrieved.email == saved.email
    assert retrieved.years_experience == saved.years_experience
    assert retrieved.is_active == saved.is_active
    
    # Test getting non-existent driver
    assert repository.get_by_id(UUID('00000000-0000-0000-0000-000000000000')) is None


def test_get_all(repository, driver):
    """Test getting all drivers."""
    # Create multiple drivers
    driver1 = repository.create(driver)
    
    driver2 = Driver(
        id=uuid4(),  # Add explicit UUID
        first_name="Jane",
        last_name="Smith",
        license_number="DL789012",
        license_type="Class B",
        license_expiry=utc_now() + timedelta(days=180),
        contact_number="+0987654321",
        email="jane.smith@example.com",
        years_experience=3,
        is_active=True
    )
    driver2 = repository.create(driver2)
    
    # Get all drivers
    drivers = repository.get_all()
    assert len(drivers) == 2
    assert any(d.id == driver1.id for d in drivers)
    assert any(d.id == driver2.id for d in drivers)


def test_update(repository, driver):
    """Test updating existing driver."""
    # Create initial driver
    created = repository.create(driver)
    
    # Update driver
    created.first_name = "Jonathan"
    created.years_experience = 6
    created.is_active = False
    
    updated = repository.update(created)
    assert updated is not None
    assert updated.first_name == "Jonathan"
    assert updated.years_experience == 6
    assert not updated.is_active
    
    # Test updating non-existent driver
    non_existent = Driver(
        id=UUID('00000000-0000-0000-0000-000000000000'),
        first_name="Non",
        last_name="Existent",
        license_number="DL000000",
        license_type="None",
        license_expiry=utc_now(),
        contact_number="+0000000000",
        email="non.existent@example.com",
        years_experience=0,
        is_active=False
    )
    assert repository.update(non_existent) is None


def test_delete(repository, driver):
    """Test deleting driver."""
    # Create driver
    created = repository.create(driver)
    
    # Test successful deletion
    assert repository.delete(created.id) is True
    assert repository.get_by_id(created.id) is None
    
    # Test deleting non-existent driver
    assert repository.delete(UUID('00000000-0000-0000-0000-000000000000')) is False


def test_inactive_driver(repository, driver):
    """Test handling inactive drivers."""
    # Create inactive driver
    driver.is_active = False
    inactive = repository.create(driver)
    
    # Verify inactive status is preserved
    retrieved = repository.get_by_id(inactive.id)
    assert retrieved is not None
    assert not retrieved.is_active


def test_license_expiry(repository, driver):
    """Test handling license expiry."""
    # Create driver with expired license
    driver.license_expiry = utc_now() - timedelta(days=1)
    expired = repository.create(driver)
    
    # Verify expiry is preserved
    retrieved = repository.get_by_id(expired.id)
    assert retrieved is not None
    assert retrieved.license_expiry.replace(tzinfo=None) < utc_now().replace(tzinfo=None)  # Compare naive datetimes
    assert not retrieved.is_license_valid
