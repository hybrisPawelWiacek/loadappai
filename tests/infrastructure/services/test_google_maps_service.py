"""Tests for GoogleMapsService."""
import os
from unittest.mock import Mock, patch

import pytest
from googlemaps.exceptions import ApiError, Timeout, TransportError

from src.domain.interfaces import LocationServiceError
from src.domain.value_objects import Location, CountrySegment
from src.infrastructure.services import GoogleMapsService


@pytest.fixture
def mock_gmaps_client():
    """Create a mock Google Maps client."""
    with patch('googlemaps.Client') as mock_client:
        # Configure the mock to not validate API key
        mock_client.return_value = Mock()
        yield mock_client.return_value


@pytest.fixture
def service(mock_gmaps_client):
    """Create a GoogleMapsService instance with mocked client."""
    with patch.dict(os.environ, {'GOOGLE_MAPS_API_KEY': 'test_key'}):
        with patch('googlemaps.Client') as mock_client:
            # Configure the mock to not validate API key
            mock_client.return_value = mock_gmaps_client
            return GoogleMapsService()


def test_init_with_api_key():
    """Test initialization with explicit API key."""
    with patch('googlemaps.Client') as mock_client:
        # Configure the mock to not validate API key
        mock_client.return_value = Mock()
        service = GoogleMapsService(api_key='test_key')
        assert service.api_key == 'test_key'


def test_init_with_env_var():
    """Test initialization with API key from environment variable."""
    with patch.dict(os.environ, {'GOOGLE_MAPS_API_KEY': 'test_key'}):
        with patch('googlemaps.Client') as mock_client:
            # Configure the mock to not validate API key
            mock_client.return_value = Mock()
            service = GoogleMapsService()
            assert service.api_key == 'test_key'


def test_init_without_api_key():
    """Test initialization fails without API key."""
    with patch.dict(os.environ, clear=True):
        with pytest.raises(LocationServiceError, match="Google Maps API key not found"):
            GoogleMapsService()


def test_calculate_distance_success(service, mock_gmaps_client):
    """Test successful distance calculation."""
    # Mock response from Google Maps API
    mock_gmaps_client.distance_matrix.return_value = {
        'rows': [{
            'elements': [{
                'status': 'OK',
                'distance': {'value': 100000}  # 100 km in meters
            }]
        }]
    }
    
    origin = Location(latitude=52.5200, longitude=13.4050, address="Berlin, Germany")
    dest = Location(latitude=52.2297, longitude=21.0122, address="Warsaw, Poland")
    
    distance = service.calculate_distance(origin, dest)
    assert distance == 100.0  # Should convert meters to kilometers
    
    # Verify API call
    mock_gmaps_client.distance_matrix.assert_called_once_with(
        origins=[(52.5200, 13.4050)],
        destinations=[(52.2297, 21.0122)],
        mode="driving",
        units="metric"
    )


def test_calculate_distance_api_error(service, mock_gmaps_client):
    """Test handling of API error in distance calculation."""
    mock_gmaps_client.distance_matrix.side_effect = ApiError("API Error")
    
    origin = Location(latitude=52.5200, longitude=13.4050, address="Berlin, Germany")
    dest = Location(latitude=52.2297, longitude=21.0122, address="Warsaw, Poland")
    
    with pytest.raises(LocationServiceError, match="Google Maps API error: API Error"):
        service.calculate_distance(origin, dest)


def test_calculate_duration_success(service, mock_gmaps_client):
    """Test successful duration calculation."""
    # Mock response from Google Maps API
    mock_gmaps_client.distance_matrix.return_value = {
        'rows': [{
            'elements': [{
                'status': 'OK',
                'duration': {'value': 7200}  # 2 hours in seconds
            }]
        }]
    }
    
    origin = Location(latitude=52.5200, longitude=13.4050, address="Berlin, Germany")
    dest = Location(latitude=52.2297, longitude=21.0122, address="Warsaw, Poland")
    
    duration = service.calculate_duration(origin, dest)
    assert duration == 2.0  # Should convert seconds to hours
    
    # Verify API call
    mock_gmaps_client.distance_matrix.assert_called_once_with(
        origins=[(52.5200, 13.4050)],
        destinations=[(52.2297, 21.0122)],
        mode="driving",
        units="metric"
    )


def test_get_country_segments_success(service, mock_gmaps_client):
    """Test successful country segments retrieval."""
    # Mock responses
    mock_gmaps_client.directions.return_value = [{
        'legs': [{
            'steps': [{
                'end_location': {'lat': 52.5200, 'lng': 13.4050},
                'distance': {'value': 50000}  # 50 km in meters
            }, {
                'end_location': {'lat': 52.2297, 'lng': 21.0122},
                'distance': {'value': 50000}  # 50 km in meters
            }]
        }]
    }]
    
    # Mock geocoding responses for the two points
    mock_gmaps_client.reverse_geocode.side_effect = [
        [{'address_components': [{'types': ['country'], 'short_name': 'DE'}]}],
        [{'address_components': [{'types': ['country'], 'short_name': 'PL'}]}]
    ]
    
    origin = Location(latitude=52.5200, longitude=13.4050, address="Berlin, Germany")
    dest = Location(latitude=52.2297, longitude=21.0122, address="Warsaw, Poland")
    
    segments = service.get_country_segments(origin, dest, "truck")
    assert len(segments) == 2
    assert segments[0].country_code == "DE"
    assert segments[1].country_code == "PL"
    assert segments[0].distance == 50.0
    assert segments[1].distance == 50.0
    assert "highway" in segments[0].toll_rates
    assert "national" in segments[0].toll_rates


def test_get_country_segments_api_error(service, mock_gmaps_client):
    """Test handling of API error in country segments retrieval."""
    mock_gmaps_client.directions.side_effect = ApiError("API Error")
    
    origin = Location(latitude=52.5200, longitude=13.4050, address="Berlin, Germany")
    dest = Location(latitude=52.2297, longitude=21.0122, address="Warsaw, Poland")
    
    with pytest.raises(LocationServiceError, match="Google Maps API error: API Error"):
        service.get_country_segments(origin, dest, "truck")


def test_error_handling_timeout(service, mock_gmaps_client):
    """Test handling of timeout errors."""
    mock_gmaps_client.distance_matrix.side_effect = Timeout("Timeout")
    
    origin = Location(latitude=52.5200, longitude=13.4050, address="Berlin, Germany")
    dest = Location(latitude=52.2297, longitude=21.0122, address="Warsaw, Poland")
    
    with pytest.raises(LocationServiceError, match="Google Maps API error: Timeout"):
        service.calculate_distance(origin, dest)


def test_error_handling_transport_error(service, mock_gmaps_client):
    """Test handling of transport errors."""
    mock_gmaps_client.distance_matrix.side_effect = TransportError("Transport Error")
    
    origin = Location(latitude=52.5200, longitude=13.4050, address="Berlin, Germany")
    dest = Location(latitude=52.2297, longitude=21.0122, address="Warsaw, Poland")
    
    with pytest.raises(LocationServiceError, match="Google Maps API error: Transport Error"):
        service.calculate_distance(origin, dest)
