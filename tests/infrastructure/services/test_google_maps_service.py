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
def mock_settings():
    """Mock settings for tests."""
    mock_settings = Mock()
    mock_settings.GOOGLE_MAPS_API_KEY = "AIzaTest123"
    mock_settings.GMAPS_MAX_RETRIES = 3
    mock_settings.GMAPS_RETRY_DELAY = 1.0
    mock_settings.GMAPS_CACHE_TTL = 3600
    return mock_settings


@pytest.fixture
def mock_gmaps_client():
    """Mock Google Maps client."""
    mock_client = Mock()
    mock_client.directions = Mock()
    mock_client.reverse_geocode = Mock()
    with patch('googlemaps.Client', return_value=mock_client):
        yield mock_client


@pytest.fixture
def test_locations():
    """Test location objects."""
    return (
        Location(address="Berlin, Germany", latitude=52.5200, longitude=13.4050),
        Location(address="Warsaw, Poland", latitude=52.2297, longitude=21.0122)
    )


def test_init_with_api_key(mock_settings):
    """Test initialization with explicit API key."""
    with patch('src.settings.get_settings', return_value=mock_settings), \
         patch.dict('os.environ', {'GOOGLE_MAPS_API_KEY': ''}, clear=True), \
         patch('src.settings.Settings') as mock_settings_class:
        mock_settings_class.return_value = mock_settings
        service = GoogleMapsService(api_key='AIzaTest123')
        assert service.api_key == 'AIzaTest123'
        assert service.max_retries == mock_settings.GMAPS_MAX_RETRIES
        assert service.retry_delay == mock_settings.GMAPS_RETRY_DELAY


def test_init_with_settings(mock_settings):
    """Test initialization with settings."""
    with patch('src.settings.get_settings', return_value=mock_settings), \
         patch.dict('os.environ', {'GOOGLE_MAPS_API_KEY': ''}, clear=True), \
         patch('src.settings.Settings') as mock_settings_class:
        mock_settings_class.return_value = mock_settings
        service = GoogleMapsService()
        assert service.api_key == mock_settings.GOOGLE_MAPS_API_KEY
        assert service.max_retries == mock_settings.GMAPS_MAX_RETRIES
        assert service.retry_delay == mock_settings.GMAPS_RETRY_DELAY


def test_init_without_api_key(mock_settings):
    """Test initialization fails without API key."""
    mock_settings.GOOGLE_MAPS_API_KEY = None
    with patch('src.settings.get_settings', return_value=mock_settings), \
         patch.dict('os.environ', {'GOOGLE_MAPS_API_KEY': ''}, clear=True), \
         patch('src.settings.Settings') as mock_settings_class:
        mock_settings_class.return_value = mock_settings
        with pytest.raises(LocationServiceError, match="Google Maps API key not found"):
            GoogleMapsService()


def test_get_country_segments_success(mock_settings, mock_gmaps_client, test_locations):
    """Test successful country segments retrieval."""
    origin, dest = test_locations
    mock_gmaps_client.directions.return_value = [{
        'legs': [{
            'steps': [
                {
                    'end_location': {'lat': 52.5, 'lng': 13.4},
                    'distance': {'value': 45720}
                },
                {
                    'end_location': {'lat': 52.2, 'lng': 21.0},
                    'distance': {'value': 45720}
                }
            ]
        }]
    }]

    mock_gmaps_client.reverse_geocode.side_effect = [
        [{'address_components': [{'types': ['country'], 'short_name': 'DE'}]}],
        [{'address_components': [{'types': ['country'], 'short_name': 'PL'}]}]
    ]

    with patch('src.settings.get_settings', return_value=mock_settings), \
         patch.dict('os.environ', {'GOOGLE_MAPS_API_KEY': ''}, clear=True), \
         patch('src.settings.Settings') as mock_settings_class:
        mock_settings_class.return_value = mock_settings
        service = GoogleMapsService()
        segments = service.get_country_segments(origin, dest, transport_type="truck")
        assert len(segments) == 2
        assert isinstance(segments[0], CountrySegment)
        assert segments[0].country_code == "DE"
        assert segments[0].distance == Decimal("45.720")
        assert isinstance(segments[0].toll_rates, dict)
        assert isinstance(segments[1], CountrySegment)
        assert segments[1].country_code == "PL"
        assert segments[1].distance == Decimal("45.720")
        assert isinstance(segments[1].toll_rates, dict)


def test_get_country_segments_no_route(mock_settings, mock_gmaps_client, test_locations):
    """Test handling when no route is found."""
    origin, dest = test_locations
    mock_gmaps_client.directions.return_value = None

    with patch('src.settings.get_settings', return_value=mock_settings), \
         patch.dict('os.environ', {'GOOGLE_MAPS_API_KEY': ''}, clear=True), \
         patch('src.settings.Settings') as mock_settings_class:
        mock_settings_class.return_value = mock_settings
        service = GoogleMapsService()
        with pytest.raises(LocationServiceError, match="No route found"):
            service.get_country_segments(origin, dest, transport_type="truck")


def test_get_country_segments_api_error(mock_settings, mock_gmaps_client, test_locations):
    """Test handling of API errors."""
    origin, dest = test_locations
    mock_gmaps_client.directions.side_effect = googlemaps.exceptions.ApiError("API Error")

    with patch('src.settings.get_settings', return_value=mock_settings), \
         patch.dict('os.environ', {'GOOGLE_MAPS_API_KEY': ''}, clear=True), \
         patch('src.settings.Settings') as mock_settings_class:
        mock_settings_class.return_value = mock_settings
        service = GoogleMapsService()
        with pytest.raises(LocationServiceError, match="Google Maps API error after 3 retries"):
            service.get_country_segments(origin, dest, transport_type="truck")


def test_get_country_segments_geocode_error(mock_settings, mock_gmaps_client, test_locations):
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
    mock_gmaps_client.reverse_geocode.return_value = []

    with patch('src.settings.get_settings', return_value=mock_settings), \
         patch.dict('os.environ', {'GOOGLE_MAPS_API_KEY': ''}, clear=True), \
         patch('src.settings.Settings') as mock_settings_class:
        mock_settings_class.return_value = mock_settings
        service = GoogleMapsService()
        segments = service.get_country_segments(origin, dest, transport_type="truck")
        assert len(segments) == 1
        assert segments[0].country_code == "Unknown"


def test_get_country_segments_invalid_response(mock_settings, mock_gmaps_client, test_locations):
    """Test handling of invalid API responses."""
    origin, dest = test_locations
    mock_gmaps_client.directions.return_value = [{'invalid': 'response'}]

    with patch('src.settings.get_settings', return_value=mock_settings), \
         patch.dict('os.environ', {'GOOGLE_MAPS_API_KEY': ''}, clear=True), \
         patch('src.settings.Settings') as mock_settings_class:
        mock_settings_class.return_value = mock_settings
        service = GoogleMapsService()
        segments = service.get_country_segments(origin, dest, transport_type="truck")
        assert len(segments) == 0


def test_get_country_segments_empty_steps(mock_settings, mock_gmaps_client, test_locations):
    """Test handling of empty steps in route."""
    origin, dest = test_locations
    mock_gmaps_client.directions.return_value = [{
        'legs': [{
            'steps': []
        }]
    }]

    with patch('src.settings.get_settings', return_value=mock_settings), \
         patch.dict('os.environ', {'GOOGLE_MAPS_API_KEY': ''}, clear=True), \
         patch('src.settings.Settings') as mock_settings_class:
        mock_settings_class.return_value = mock_settings
        service = GoogleMapsService()
        segments = service.get_country_segments(origin, dest, transport_type="truck")
        assert len(segments) == 0
