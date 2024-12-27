"""Test Google Maps service implementation."""
from unittest.mock import Mock, patch
import googlemaps
from decimal import Decimal
import pytest
import os

from src.domain.interfaces import LocationServiceError
from src.domain.value_objects import Location, CountrySegment
from src.infrastructure.services.google_maps_service import GoogleMapsService
from src.settings import Settings, get_settings


@pytest.fixture(autouse=True)
def clear_settings_cache():
    """Clear settings cache before each test."""
    get_settings.cache_clear()
    yield


@pytest.fixture
def mock_settings(monkeypatch):
    """Mock settings for tests."""
    class MockSettings:
        def __init__(self):
            self.google_maps_api_key = "test_key"
            self.api = Mock()
            self.api.gmaps_max_retries = 3
            self.api.gmaps_retry_delay = 1.0
            self.api.gmaps_cache_ttl = 3600
            self.api.google_maps_key = "test_key"
    
    mock_settings = MockSettings()
    
    def mock_get_settings():
        return mock_settings
    
    monkeypatch.setattr("src.infrastructure.services.google_maps_service.get_settings", mock_get_settings)
    return mock_settings


@pytest.fixture
def mock_gmaps_client():
    """Mock Google Maps client."""
    mock_client = Mock()
    mock_client.distance_matrix.return_value = {
        'rows': [{'elements': [{'status': 'OK', 'distance': {'value': 1000}, 'duration': {'value': 3600}}]}]
    }
    mock_client.directions.return_value = [{
        'legs': [{
            'steps': [{
                'distance': {'value': 1000},
                'duration': {'value': 3600},
                'html_instructions': 'Drive',
                'start_location': {'lat': 52.52, 'lng': 13.405},
                'end_location': {'lat': 52.2297, 'lng': 21.0122}
            }]
        }]
    }]
    mock_client.reverse_geocode.return_value = [{'address_components': [{'types': ['country'], 'long_name': 'Poland', 'short_name': 'PL'}]}]
    return mock_client


@pytest.fixture
def mock_toll_rate_service():
    """Mock toll rate service."""
    service = Mock()
    service.get_toll_rate_for_segment.return_value = Decimal('10.00')
    service.has_toll_roads.return_value = True
    return service


@pytest.fixture
def test_locations():
    """Test location objects."""
    return (
        Location(address="Berlin, Germany", latitude=52.5200, longitude=13.4050),
        Location(address="Warsaw, Poland", latitude=52.2297, longitude=21.0122)
    )


def test_init_with_api_key(mock_settings, mock_gmaps_client):
    """Test initialization with explicit API key."""
    with patch('googlemaps.Client', return_value=mock_gmaps_client):
        service = GoogleMapsService(api_key='test_key')
        assert service.api_key == 'test_key'
        assert service.max_retries == mock_settings.api.gmaps_max_retries
        assert service.retry_delay == mock_settings.api.gmaps_retry_delay


def test_init_with_settings(mock_settings, mock_gmaps_client):
    """Test initialization with settings."""
    with patch('googlemaps.Client', return_value=mock_gmaps_client):
        service = GoogleMapsService()
        assert service.api_key == mock_settings.google_maps_api_key
        assert service.max_retries == mock_settings.api.gmaps_max_retries
        assert service.retry_delay == mock_settings.api.gmaps_retry_delay


def test_init_without_api_key(mock_settings):
    """Test initialization fails without API key."""
    mock_settings.google_maps_api_key = None
    with pytest.raises(LocationServiceError, match="Google Maps API key not found"):
        GoogleMapsService()


def test_get_route_segments_success(mock_settings, mock_gmaps_client, test_locations, mock_toll_rate_service):
    """Test getting route segments successfully."""
    origin, dest = test_locations
    mock_toll_rate_service.get_toll_rate_for_segment.return_value = Decimal('10.00')

    with patch('googlemaps.Client', return_value=mock_gmaps_client), \
         patch('src.infrastructure.services.toll_rate_service.DefaultTollRateService', return_value=mock_toll_rate_service):
        service = GoogleMapsService(toll_rate_service=mock_toll_rate_service)
        segments = service.get_route_segments(origin, dest, include_tolls=True)
        assert len(segments) == 1
        assert segments[0].distance == Decimal('1.000')  # 1000 meters = 1.000 km
        assert segments[0].duration_hours == Decimal('1.000')  # 3600 seconds = 1.000 hour
        assert segments[0].country_code == 'PL'  # Poland
        assert segments[0].has_tolls == True


def test_get_route_segments_no_route(mock_settings, mock_gmaps_client, test_locations):
    """Test getting route segments when no route is found."""
    origin, dest = test_locations
    mock_gmaps_client.directions.return_value = []
    mock_gmaps_client.distance_matrix.return_value = {
        'rows': [{'elements': [{'status': 'ZERO_RESULTS'}]}]
    }

    with patch('googlemaps.Client', return_value=mock_gmaps_client):
        service = GoogleMapsService()
        with pytest.raises(LocationServiceError, match="No route found"):
            service.get_route_segments(origin, dest)


def test_get_route_segments_invalid_response(mock_settings, mock_gmaps_client, test_locations):
    """Test getting route segments with invalid response."""
    origin, dest = test_locations
    mock_gmaps_client.directions.return_value = [{}]  # Invalid response
    mock_gmaps_client.distance_matrix.return_value = {
        'rows': [{'elements': [{'status': 'OK', 'distance': {'value': 1000}, 'duration': {'value': 3600}}]}]
    }

    with patch('googlemaps.Client', return_value=mock_gmaps_client):
        service = GoogleMapsService()
        with pytest.raises(LocationServiceError, match="Invalid route data"):
            service.get_route_segments(origin, dest)


def test_get_route_segments_empty_steps(mock_settings, mock_gmaps_client, test_locations):
    """Test getting route segments with empty steps."""
    origin, dest = test_locations
    mock_gmaps_client.directions.return_value = [{
        'legs': [{'steps': []}]
    }]
    mock_gmaps_client.distance_matrix.return_value = {
        'rows': [{'elements': [{'status': 'OK', 'distance': {'value': 1000}, 'duration': {'value': 3600}}]}]
    }

    with patch('googlemaps.Client', return_value=mock_gmaps_client):
        service = GoogleMapsService()
        segments = service.get_route_segments(origin, dest)
        assert len(segments) == 0  # Should return empty list for empty steps


def test_get_route_segments_api_error(mock_settings, mock_gmaps_client, test_locations):
    """Test handling of API errors."""
    origin, dest = test_locations
    mock_gmaps_client.directions.side_effect = googlemaps.exceptions.ApiError("API Error")

    with patch('googlemaps.Client', return_value=mock_gmaps_client):
        service = GoogleMapsService()
        with pytest.raises(LocationServiceError, match="Failed to get route segments"):
            service.get_route_segments(origin, dest)


def test_get_route_segments_geocode_error(mock_settings, mock_gmaps_client, test_locations):
    """Test handling of geocoding errors."""
    origin, dest = test_locations
    mock_gmaps_client.directions.return_value = [{
        'legs': [{
            'steps': [
                {
                    'end_location': {'lat': 52.5, 'lng': 13.4},
                    'distance': {'value': 45720}
                }
            ]
        }]
    }]
    mock_gmaps_client.reverse_geocode.side_effect = googlemaps.exceptions.ApiError("Geocoding Error")

    with patch('googlemaps.Client', return_value=mock_gmaps_client):
        service = GoogleMapsService()
        with pytest.raises(LocationServiceError, match="Failed to get route segments"):
            service.get_route_segments(origin, dest)


def test_get_route_segments_invalid_response(mock_settings, mock_gmaps_client, test_locations):
    """Test handling of invalid API responses."""
    origin, dest = test_locations
    mock_gmaps_client.directions.return_value = [{}]  # Invalid response

    with patch('googlemaps.Client', return_value=mock_gmaps_client):
        service = GoogleMapsService()
        with pytest.raises(LocationServiceError, match="Invalid route data"):
            service.get_route_segments(origin, dest)
