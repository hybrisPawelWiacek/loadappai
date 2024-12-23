"""
Integration tests for the LoadApp.AI frontend
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

from src.frontend.components.route_form import RouteFormData, Location, TransportType
from src.frontend.components.map_visualization import RouteSegment, TimelineEventType
from src.frontend.components.cost_calculation import EnhancedCostBreakdown
from src.frontend.integration import (
    convert_form_to_request,
    convert_response_to_segments,
    handle_route_submission
)
from src.frontend.api_client import ValidationError

@pytest.fixture
def sample_form_data():
    """Create sample form data for testing."""
    # Use fixed datetime for consistent testing
    base_time = datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc)
    return RouteFormData(
        origin=Location(
            address="Berlin, Germany",
            latitude=52.52,
            longitude=13.405,
            country="DE"
        ),
        destination=Location(
            address="Prague, Czech Republic",
            latitude=50.075,
            longitude=14.437,
            country="CZ"
        ),
        pickup_time=base_time + timedelta(hours=1),
        delivery_time=base_time + timedelta(hours=24),
        transport_type=TransportType.TRUCK,
        cargo_specs={
            'weight_kg': 1000,
            'volume_m3': 20,
            'cargo_type': "General",
            'temperature_controlled': False,
            'hazmat_class': None,
            'required_temp_celsius': None
        }
    )

@pytest.fixture
def sample_api_response():
    """Create sample API response for testing."""
    # Use fixed datetime for consistent testing
    base_time = datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc)
    return {
        'id': 'test-route-1',
        'origin': {
            'address': "Berlin, Germany",
            'latitude': 52.52,
            'longitude': 13.405,
            'country': "DE"
        },
        'destination': {
            'address': "Prague, Czech Republic",
            'latitude': 50.075,
            'longitude': 14.437,
            'country': "CZ"
        },
        'pickup_time': (base_time + timedelta(hours=1)).isoformat(),
        'delivery_time': (base_time + timedelta(hours=24)).isoformat(),
        'segments': [
            {
                'start_location': {
                    'address': "Berlin, Germany",
                    'latitude': 52.52,
                    'longitude': 13.405,
                    'country': "DE"
                },
                'end_location': {
                    'address': "Dresden, Germany",
                    'latitude': 51.050,
                    'longitude': 13.737,
                    'country': "DE"
                },
                'distance_km': 200,
                'duration_hours': 2.5,
                'country': "DE",
                'is_empty_driving': False,
                'timeline_event': "pickup"
            },
            {
                'start_location': {
                    'address': "Dresden, Germany",
                    'latitude': 51.050,
                    'longitude': 13.737,
                    'country': "DE"
                },
                'end_location': {
                    'address': "Prague, Czech Republic",
                    'latitude': 50.075,
                    'longitude': 14.437,
                    'country': "CZ"
                },
                'distance_km': 150,
                'duration_hours': 2.0,
                'country': "CZ",
                'is_empty_driving': False,
                'timeline_event': "delivery"
            }
        ]
    }

def test_convert_form_to_request(sample_form_data):
    """Test conversion of form data to API request format."""
    request_data = convert_form_to_request(sample_form_data)
    
    assert request_data['origin']['address'] == "Berlin, Germany"
    assert request_data['destination']['address'] == "Prague, Czech Republic"
    assert request_data['transport_type'] == TransportType.TRUCK.value
    assert isinstance(request_data['pickup_time'], str)
    assert isinstance(request_data['delivery_time'], str)
    assert request_data['cargo_specs']['weight_kg'] == 1000
    assert request_data['cargo_specs']['volume_m3'] == 20

def test_convert_response_to_segments(sample_api_response):
    """Test conversion of API response to route segments."""
    segments, pickup_time = convert_response_to_segments(sample_api_response)
    
    assert len(segments) == 2
    assert isinstance(segments[0], RouteSegment)
    assert segments[0].start_location.address == "Berlin, Germany"
    assert segments[0].timeline_event == TimelineEventType.PICKUP
    assert segments[1].timeline_event == TimelineEventType.DELIVERY
    assert isinstance(pickup_time, datetime)

@patch('src.frontend.integration.init_api_client')
def test_handle_route_submission_success(mock_init_client, sample_form_data, sample_api_response):
    """Test successful route submission handling."""
    # Mock API client
    mock_client = Mock()
    mock_client.create_route.return_value = sample_api_response
    mock_init_client.return_value = mock_client
    
    # Handle submission
    result = handle_route_submission(sample_form_data)
    
    assert result is not None
    segments, pickup_time = result
    assert len(segments) == 2
    assert isinstance(pickup_time, datetime)
    mock_client.create_route.assert_called_once()

@patch('src.frontend.integration.init_api_client')
def test_handle_route_submission_validation_error(mock_init_client, sample_form_data):
    """Test route submission with validation error."""
    # Mock API client
    mock_client = Mock()
    mock_client.create_route.side_effect = ValidationError(
        message="Validation failed",
        status_code=400,
        response_data={'errors': {'pickup_time': ['Must be in the future']}}
    )
    mock_init_client.return_value = mock_client
    
    # Handle submission
    with patch('streamlit.error') as mock_st_error:
        result = handle_route_submission(sample_form_data)
    
    assert result is None
    mock_st_error.assert_called()
    mock_client.create_route.assert_called_once()
