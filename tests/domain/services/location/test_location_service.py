"""Tests for LocationIntegrationService."""
import pytest
from decimal import Decimal
from unittest.mock import Mock, patch

from src.domain.services.location.location_service import LocationIntegrationService
from src.domain.value_objects import Location, CountrySegment
from src.infrastructure.services.google_maps_service import GoogleMapsService
from src.infrastructure.services.toll_rate_service import DefaultTollRateService


@pytest.fixture
def location_service():
    """Create LocationIntegrationService instance for testing."""
    return LocationIntegrationService()


@pytest.fixture
def mock_maps_client():
    """Create mock GoogleMapsService."""
    return Mock(spec=GoogleMapsService)


@pytest.fixture
def mock_toll_rate_service():
    """Create mock TollRateService."""
    return Mock(spec=DefaultTollRateService)


@pytest.fixture
def mock_cache_service():
    """Create mock CacheService."""
    return Mock()


@pytest.fixture
def sample_locations():
    """Create sample locations for testing."""
    return {
        'berlin': Location(
            address="Alexanderplatz 1, 10178 Berlin, Germany",
            latitude=52.5200,
            longitude=13.4050,
            country="DE"
        ),
        'warsaw': Location(
            address="plac Defilad 1, 00-901 Warsaw, Poland",
            latitude=52.2297,
            longitude=21.0122,
            country="PL"
        ),
        'paris': Location(
            address="16 Place de la Concorde, 75008 Paris, France",
            latitude=48.8566,
            longitude=2.3522,
            country="FR"
        )
    }


def test_validate_location_valid(location_service, sample_locations):
    """Test location validation with valid location."""
    assert location_service.validate_location(sample_locations['berlin']) is True


def test_validate_location_invalid_latitude(location_service):
    """Test location validation with invalid latitude."""
    try:
        invalid_location = Location(
            address="Invalid Address",
            latitude=91.0,  # Invalid latitude
            longitude=13.4050,
            country="DE"
        )
        assert False, "Should have raised validation error"
    except ValueError:
        # Pydantic validation prevents creation of invalid location
        pass


def test_validate_location_invalid_longitude(location_service):
    """Test location validation with invalid longitude."""
    try:
        invalid_location = Location(
            address="Invalid Address",
            latitude=52.5200,
            longitude=181.0,  # Invalid longitude
            country="DE"
        )
        assert False, "Should have raised validation error"
    except ValueError:
        # Pydantic validation prevents creation of invalid location
        pass


def test_validate_location_invalid_country(location_service):
    """Test location validation with invalid country code."""
    invalid_location = Location(
        address="Invalid Address",
        latitude=52.5200,
        longitude=13.4050,
        country="DEU"  # Invalid country code (should be 2 chars)
    )
    assert location_service.validate_location(invalid_location) is False


def test_validate_location_with_maps_client(
    location_service,
    mock_maps_client,
    sample_locations
):
    """Test location validation using maps client."""
    # Setup
    location_service._maps_client = mock_maps_client
    mock_maps_client.validate_location.return_value = True
    
    # Execute
    result = location_service.validate_location(sample_locations['berlin'])
    
    # Verify
    assert result is True
    mock_maps_client.validate_location.assert_called_once_with(
        sample_locations['berlin']
    )


def test_calculate_distance_with_maps_client(
    location_service,
    mock_maps_client,
    sample_locations
):
    """Test distance calculation using maps client."""
    # Setup
    location_service._maps_client = mock_maps_client
    expected_distance = Decimal('500.0')
    mock_maps_client.calculate_distance.return_value = expected_distance
    
    # Execute
    distance = location_service.calculate_distance(
        sample_locations['berlin'],
        sample_locations['warsaw']
    )
    
    # Verify
    assert distance == expected_distance
    mock_maps_client.calculate_distance.assert_called_once_with(
        sample_locations['berlin'],
        sample_locations['warsaw'],
        avoid_tolls=False
    )


def test_calculate_distance_fallback(location_service, sample_locations):
    """Test distance calculation fallback when no maps client."""
    distance = location_service.calculate_distance(
        sample_locations['berlin'],
        sample_locations['warsaw']
    )
    # Distance should be approximately 517km (straight line)
    assert 515 <= float(distance) <= 520


def test_calculate_distance_with_cache(
    location_service,
    mock_cache_service,
    sample_locations
):
    """Test distance calculation with caching."""
    # Setup
    location_service._cache_service = mock_cache_service
    cached_distance = '500.0'
    mock_cache_service.get.return_value = cached_distance
    
    # Execute
    distance = location_service.calculate_distance(
        sample_locations['berlin'],
        sample_locations['warsaw']
    )
    
    # Verify
    assert distance == Decimal(cached_distance)
    mock_cache_service.get.assert_called_once()
    mock_cache_service.set.assert_not_called()


def test_calculate_duration_with_maps_client(
    location_service,
    mock_maps_client,
    sample_locations
):
    """Test duration calculation using maps client."""
    # Setup
    location_service._maps_client = mock_maps_client
    expected_duration = Decimal('5.5')  # 5.5 hours
    mock_maps_client.calculate_duration.return_value = expected_duration
    
    # Execute
    duration = location_service.calculate_duration(
        sample_locations['berlin'],
        sample_locations['warsaw'],
        departure_time='2024-12-25T10:00:00Z'
    )
    
    # Verify
    assert duration == expected_duration
    mock_maps_client.calculate_duration.assert_called_once_with(
        sample_locations['berlin'],
        sample_locations['warsaw'],
        departure_time='2024-12-25T10:00:00Z'
    )


def test_calculate_duration_fallback(location_service, sample_locations):
    """Test duration calculation fallback when no maps client."""
    duration = location_service.calculate_duration(
        sample_locations['berlin'],
        sample_locations['warsaw']
    )
    # Verify - should be approximately 8.7 hours (524km / 60km/h)
    assert 8.5 <= float(duration) <= 9.0


def test_get_route_segments_with_maps_client(
    location_service,
    mock_maps_client,
    mock_toll_rate_service,
    sample_locations
):
    """Test route segments calculation with maps client."""
    # Mock the maps client
    mock_maps_client.get_route_segments.return_value = [
        CountrySegment(
            country_code="DE",
            distance=Decimal("258.58597193485735"),
            duration_hours=Decimal("4.309766198914289")
        ),
        CountrySegment(
            country_code="PL",
            distance=Decimal("258.58597193485735"),
            duration_hours=Decimal("4.309766198914289")
        )
    ]

    # Mock toll rate service
    mock_toll_rate_service.get_toll_rates.return_value = {
        "highway": Decimal("0.15"),
        "national": Decimal("0.10")
    }
    
    # Configure location service with mocks
    location_service._maps_client = mock_maps_client
    location_service._toll_rate_service = mock_toll_rate_service
    
    # Calculate segments
    segments = location_service.get_route_segments(
        origin=sample_locations["berlin"],
        destination=sample_locations["warsaw"],
        include_tolls=True,
        vehicle_type="truck"
    )
    
    # Verify segments
    assert len(segments) == 2
    assert segments[0].country_code == "DE"
    assert segments[0].distance == Decimal("258.58597193485735")
    assert segments[0].duration_hours == Decimal("4.309766198914289")
    assert segments[0].toll_rates == {
        "highway": Decimal("0.15"),
        "national": Decimal("0.10")
    }
    assert segments[1].country_code == "PL"
    assert segments[1].distance == Decimal("258.58597193485735")
    assert segments[1].duration_hours == Decimal("4.309766198914289")
    assert segments[1].toll_rates == {
        "highway": Decimal("0.15"),
        "national": Decimal("0.10")
    }

    # Verify maps client was called
    mock_maps_client.get_route_segments.assert_called_once_with(
        origin=sample_locations["berlin"],
        destination=sample_locations["warsaw"]
    )

    # Verify toll rate service was called
    mock_toll_rate_service.get_toll_rates.assert_any_call(
        country="DE",
        vehicle_type="truck"
    )
    mock_toll_rate_service.get_toll_rates.assert_any_call(
        country="PL",
        vehicle_type="truck"
    )


def test_get_route_segments_fallback(
    location_service,
    mock_toll_rate_service,
    sample_locations
):
    """Test route segments calculation fallback when no maps client."""
    # Create location service without maps client
    location_service._maps_client = None
    location_service._toll_rate_service = mock_toll_rate_service

    # Mock toll rate service
    mock_toll_rate_service.get_toll_rates.side_effect = lambda country, vehicle_type: {
        "highway": Decimal("0.15"),
        "national": Decimal("0.12")
    }
    
    # Calculate segments
    segments = location_service.get_route_segments(
        origin=sample_locations["berlin"],
        destination=sample_locations["warsaw"],
        include_tolls=True,
        vehicle_type="truck"
    )

    # Verify segments
    assert len(segments) == 2
    assert segments[0].country_code == "DE"
    assert segments[0].distance == Decimal("258.58597193485735")
    assert segments[0].duration_hours == Decimal("4.309766198914289")
    assert segments[0].toll_rates == {
        "highway": Decimal("0.15"),
        "national": Decimal("0.12")
    }
    assert segments[1].country_code == "PL"
    assert segments[1].distance == Decimal("258.58597193485735")
    assert segments[1].duration_hours == Decimal("4.309766198914289")
    assert segments[1].toll_rates == {
        "highway": Decimal("0.15"),
        "national": Decimal("0.12")
    }

    # Verify toll rate service was called
    mock_toll_rate_service.get_toll_rates.assert_any_call(
        country="DE",
        vehicle_type="truck"
    )
    mock_toll_rate_service.get_toll_rates.assert_any_call(
        country="PL",
        vehicle_type="truck"
    )


def test_address_validation(location_service):
    """Test address validation for different countries."""
    # Test valid addresses
    valid_location = Location(
        address="Alexanderplatz 1, 10178 Berlin",
        latitude=52.5200,
        longitude=13.4050,
        country="DE"
    )
    assert location_service.validate_location(valid_location) is True
    
    # Test empty address
    invalid_location = Location(
        address="",  # Empty address
        latitude=52.5200,
        longitude=13.4050,
        country="DE"
    )
    assert location_service.validate_location(invalid_location) is False
    
    # Test whitespace-only address
    invalid_location = Location(
        address="   ",  # Whitespace only
        latitude=52.5200,
        longitude=13.4050,
        country="DE"
    )
    assert location_service.validate_location(invalid_location) is False
