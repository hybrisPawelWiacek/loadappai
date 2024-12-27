"""Tests for location-related value objects."""

import pytest
from pydantic import ValidationError

from src.domain.value_objects.location import Location, DistanceMatrix, Address


def test_address_creation():
    """Test creating a valid Address."""
    address = Address(
        street="123 Main St",
        city="New York",
        postal_code="10001",
        country="US",
        state="NY",
        formatted="123 Main St, New York, NY 10001, US"
    )
    assert address.street == "123 Main St"
    assert address.city == "New York"
    assert address.postal_code == "10001"
    assert address.country == "US"
    assert address.state == "NY"
    assert address.formatted == "123 Main St, New York, NY 10001, US"


def test_address_optional_fields():
    """Test Address with optional fields."""
    address = Address(
        street="123 Main St",
        city="London",
        postal_code="SW1A 1AA",
        country="GB"
    )
    assert address.state is None
    assert address.formatted is None


def test_address_immutability():
    """Test that Address is immutable."""
    address = Address(
        street="123 Main St",
        city="New York",
        postal_code="10001",
        country="US"
    )
    
    with pytest.raises(ValidationError) as exc_info:
        address.street = "456 Main St"  # type: ignore
    assert "frozen_instance" in str(exc_info.value)


def test_location_creation():
    """Test creating a valid Location."""
    location = Location(
        address="123 Main St, City",
        latitude=40.7128,
        longitude=-74.0060,
        country="US"
    )
    assert location.address == "123 Main St, City"
    assert location.latitude == 40.7128
    assert location.longitude == -74.0060
    assert location.country == "US"


def test_location_validation():
    """Test Location validation."""
    # Test invalid latitude
    with pytest.raises(ValidationError) as exc_info:
        Location(
            address="123 Main St",
            latitude=100,  # Invalid latitude
            longitude=-74.0060,
            _validation_mode="all",
        )
    assert "Input should be less than or equal to 90" in str(exc_info.value)

    # Test invalid longitude
    with pytest.raises(ValidationError) as exc_info:
        Location(
            address="123 Main St",
            latitude=40.7128,
            longitude=200,  # Invalid longitude
            _validation_mode="all",
        )
    assert "Input should be less than or equal to 180" in str(exc_info.value)


def test_location_immutability():
    """Test that Location is immutable."""
    location = Location(
        address="123 Main St",
        latitude=40.7128,
        longitude=-74.0060,
    )
    
    with pytest.raises(ValidationError) as exc_info:
        location.address = "456 Main St"  # type: ignore
    assert "frozen_instance" in str(exc_info.value)


def test_distance_matrix_creation():
    """Test creating a valid DistanceMatrix."""
    origins = [
        Location(address="Origin1", latitude=40.0, longitude=-74.0),
        Location(address="Origin2", latitude=41.0, longitude=-75.0),
    ]
    destinations = [
        Location(address="Dest1", latitude=42.0, longitude=-76.0),
        Location(address="Dest2", latitude=43.0, longitude=-77.0),
    ]
    
    matrix = DistanceMatrix(
        origins=origins,
        destinations=destinations,
        distances=[[100.0, 200.0], [150.0, 250.0]],
        durations=[[2.0, 4.0], [3.0, 5.0]],
        countries=[["US", "US"], ["US", "US"]],
    )
    
    assert len(matrix.origins) == 2
    assert len(matrix.destinations) == 2
    assert matrix.get_distance(0, 1) == 200.0
    assert matrix.get_duration(1, 0) == 3.0
    assert matrix.get_country(0, 0) == "US"


def test_distance_matrix_validation():
    """Test DistanceMatrix validation."""
    origins = [Location(address="Origin", latitude=40.0, longitude=-74.0)]
    destinations = [
        Location(address="Dest1", latitude=41.0, longitude=-75.0),
        Location(address="Dest2", latitude=42.0, longitude=-76.0),
    ]
    
    # Test invalid matrix dimensions for distances
    with pytest.raises(ValidationError) as exc_info:
        DistanceMatrix(
            origins=origins,
            destinations=destinations,
            distances=[[100.0]],  # Should be 1x2
            durations=[[2.0, 4.0]],
            countries=[["US", "US"]],
            _validation_mode="all",
        )
    assert "Distances matrix must be" in str(exc_info.value)

    # Test invalid matrix dimensions for durations
    with pytest.raises(ValidationError) as exc_info:
        DistanceMatrix(
            origins=origins,
            destinations=destinations,
            distances=[[100.0, 200.0]],
            durations=[[2.0]],  # Should be 1x2
            countries=[["US", "US"]],
            _validation_mode="all",
        )
    assert "Durations matrix must be" in str(exc_info.value)

    # Test invalid matrix dimensions for countries
    with pytest.raises(ValidationError) as exc_info:
        DistanceMatrix(
            origins=origins,
            destinations=destinations,
            distances=[[100.0, 200.0]],
            durations=[[2.0, 4.0]],
            countries=[["US"]],  # Should be 1x2
            _validation_mode="all",
        )
    assert "Countries matrix must be" in str(exc_info.value)


def test_distance_matrix_immutability():
    """Test that DistanceMatrix is immutable."""
    matrix = DistanceMatrix(
        origins=[Location(address="Origin", latitude=40.0, longitude=-74.0)],
        destinations=[Location(address="Dest", latitude=41.0, longitude=-75.0)],
        distances=[[100.0]],
        durations=[[2.0]],
        countries=[["US"]],
    )
    
    with pytest.raises(ValidationError) as exc_info:
        matrix.distances = [[200.0]]  # type: ignore
    assert "frozen_instance" in str(exc_info.value)


def test_distance_matrix_helper_methods():
    """Test DistanceMatrix helper methods with invalid indices."""
    matrix = DistanceMatrix(
        origins=[Location(address="Origin", latitude=40.0, longitude=-74.0)],
        destinations=[Location(address="Dest", latitude=41.0, longitude=-75.0)],
        distances=[[100.0]],
        durations=[[2.0]],
        countries=[["US"]],
    )
    
    with pytest.raises(IndexError):
        matrix.get_distance(1, 0)  # Invalid origin index
    
    with pytest.raises(IndexError):
        matrix.get_duration(0, 1)  # Invalid destination index
    
    with pytest.raises(IndexError):
        matrix.get_country(1, 1)  # Both indices invalid
