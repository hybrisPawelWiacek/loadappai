"""Tests for Driver domain entity."""

from datetime import datetime, timedelta
from uuid import UUID
from freezegun import freeze_time
import pytest
from pydantic import ValidationError
from pytz import UTC

from src.domain.entities.driver import Driver
from src.domain.utils.datetime import utc_now


@pytest.fixture
def valid_driver_data():
    """Fixture providing valid driver data."""
    return {
        "first_name": "John",
        "last_name": "Doe",
        "license_number": "DL123456",
        "license_type": "Class A CDL",
        "license_expiry": utc_now() + timedelta(days=365),
        "contact_number": "+1234567890",
        "email": "john.doe@example.com",
        "years_experience": 5
    }


def test_driver_creation(valid_driver_data):
    """Test driver creation with valid data."""
    with freeze_time("2024-01-01 12:00:00"):
        driver = Driver(**valid_driver_data)
        
        # Test basic attributes
        assert driver.first_name == "John"
        assert driver.last_name == "Doe"
        assert driver.license_number == "DL123456"
        assert driver.license_type == "Class A CDL"
        assert driver.contact_number == "+1234567890"
        assert driver.email == "john.doe@example.com"
        assert driver.years_experience == 5
        assert driver.is_active is True
        
        # Test generated fields
        assert isinstance(driver.id, UUID)
        assert isinstance(driver.created_at, datetime)
        assert isinstance(driver.updated_at, datetime)
        assert driver.created_at.tzinfo == UTC
        assert driver.updated_at.tzinfo == UTC
        assert driver.created_at.isoformat() == "2024-01-01T12:00:00+00:00"
        assert driver.updated_at.isoformat() == "2024-01-01T12:00:00+00:00"


def test_driver_field_constraints(valid_driver_data):
    """Test field validation constraints."""
    # Test first name constraints
    with pytest.raises(ValidationError):
        data = valid_driver_data.copy()
        data["first_name"] = ""  # Empty string
        Driver(**data)
    
    with pytest.raises(ValidationError):
        data = valid_driver_data.copy()
        data["first_name"] = "A" * 51  # Too long
        Driver(**data)
    
    # Test last name constraints
    with pytest.raises(ValidationError):
        data = valid_driver_data.copy()
        data["last_name"] = ""  # Empty string
        Driver(**data)
    
    with pytest.raises(ValidationError):
        data = valid_driver_data.copy()
        data["last_name"] = "A" * 51  # Too long
        Driver(**data)
    
    # Test license number constraints
    with pytest.raises(ValidationError):
        data = valid_driver_data.copy()
        data["license_number"] = "1234"  # Too short
        Driver(**data)
    
    with pytest.raises(ValidationError):
        data = valid_driver_data.copy()
        data["license_number"] = "A" * 51  # Too long
        Driver(**data)
    
    # Test license type constraints
    with pytest.raises(ValidationError):
        data = valid_driver_data.copy()
        data["license_type"] = ""  # Empty string
        Driver(**data)
    
    with pytest.raises(ValidationError):
        data = valid_driver_data.copy()
        data["license_type"] = "A" * 21  # Too long
        Driver(**data)
    
    # Test contact number constraints
    with pytest.raises(ValidationError):
        data = valid_driver_data.copy()
        data["contact_number"] = "1234"  # Too short
        Driver(**data)
    
    with pytest.raises(ValidationError):
        data = valid_driver_data.copy()
        data["contact_number"] = "1" * 21  # Too long
        Driver(**data)
    
    # Test email validation
    with pytest.raises(ValidationError):
        data = valid_driver_data.copy()
        data["email"] = "invalid-email"  # Invalid email format
        Driver(**data)
    
    # Test years experience constraint
    with pytest.raises(ValidationError):
        data = valid_driver_data.copy()
        data["years_experience"] = -1  # Negative years
        Driver(**data)


def test_driver_update(valid_driver_data):
    """Test driver update functionality."""
    with freeze_time("2024-01-01 12:00:00"):
        driver = Driver(**valid_driver_data)
        initial_id = driver.id
        initial_created_at = driver.created_at
        
        # Move time forward
        with freeze_time("2024-01-02 12:00:00"):
            # Update multiple fields
            driver.update(
                first_name="Jane",
                last_name="Smith",
                contact_number="+9876543210",
                email="jane.smith@example.com",
                years_experience=6
            )
            
            # Check updated fields
            assert driver.first_name == "Jane"
            assert driver.last_name == "Smith"
            assert driver.contact_number == "+9876543210"
            assert driver.email == "jane.smith@example.com"
            assert driver.years_experience == 6
            
            # Check unchanged fields
            assert driver.id == initial_id
            assert driver.created_at == initial_created_at
            
            # Check updated_at was updated
            assert driver.updated_at.isoformat() == "2024-01-02T12:00:00+00:00"


def test_driver_properties(valid_driver_data):
    """Test driver property methods."""
    with freeze_time("2024-01-01 12:00:00"):
        # Test full_name property
        driver = Driver(**valid_driver_data)
        assert driver.full_name == "John Doe"
        
        # Test is_license_valid property with valid license
        assert driver.is_license_valid is True
        
        # Test is_license_valid property with expired license
        expired_data = valid_driver_data.copy()
        expired_data["license_expiry"] = utc_now() - timedelta(days=1)
        driver_expired = Driver(**expired_data)
        assert driver_expired.is_license_valid is False


def test_optional_fields(valid_driver_data):
    """Test optional fields handling."""
    # Test without email
    data = valid_driver_data.copy()
    data.pop("email")
    driver = Driver(**data)
    assert driver.email is None
    
    # Test with explicit None email
    data = valid_driver_data.copy()
    data["email"] = None
    driver = Driver(**data)
    assert driver.email is None
