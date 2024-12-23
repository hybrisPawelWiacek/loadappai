"""
Tests for the LoadApp.AI frontend API client
"""
import pytest
from unittest.mock import Mock, patch
import requests
from datetime import datetime

from src.frontend.api_client import (
    ApiClient,
    ApiConfig,
    ApiError,
    ValidationError,
    NotFoundError,
    ServerError
)

@pytest.fixture
def mock_session():
    """Mock requests session."""
    with patch('requests.Session') as mock:
        yield mock

@pytest.fixture
def api_client(mock_session):
    """Create API client with mocked session."""
    config = ApiConfig(base_url="http://test.local")
    client = ApiClient(config)
    client.session = mock_session
    return client

def test_create_route_success(api_client, mock_session):
    """Test successful route creation."""
    # Mock response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'id': 'test-route-1',
        'origin': {'address': 'Berlin', 'latitude': 52.52, 'longitude': 13.405, 'country': 'DE'},
        'destination': {'address': 'Prague', 'latitude': 50.075, 'longitude': 14.437, 'country': 'CZ'},
        'segments': [
            {
                'start_location': {'address': 'Berlin', 'latitude': 52.52, 'longitude': 13.405, 'country': 'DE'},
                'end_location': {'address': 'Dresden', 'latitude': 51.050, 'longitude': 13.737, 'country': 'DE'},
                'distance_km': 200,
                'duration_hours': 2.5,
                'country': 'DE',
                'is_empty_driving': False,
                'timeline_event': 'pickup'
            }
        ]
    }
    mock_session.request.return_value = mock_response
    
    # Test data
    route_data = {
        'origin': {'address': 'Berlin', 'latitude': 52.52, 'longitude': 13.405, 'country': 'DE'},
        'destination': {'address': 'Prague', 'latitude': 50.075, 'longitude': 14.437, 'country': 'CZ'},
        'pickup_time': datetime.now().isoformat(),
        'delivery_time': datetime.now().isoformat(),
        'transport_type': 'truck'
    }
    
    # Make request
    response = api_client.create_route(route_data)
    
    # Verify
    assert response['id'] == 'test-route-1'
    mock_session.request.assert_called_once_with(
        method='POST',
        url='http://test.local/api/routes',
        params=None,
        json=route_data,
        timeout=30,
        verify=True
    )

def test_create_route_validation_error(api_client, mock_session):
    """Test route creation with validation error."""
    # Mock response
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.json.return_value = {
        'message': 'Validation failed',
        'errors': {
            'pickup_time': ['Must be in the future']
        }
    }
    mock_session.request.return_value = mock_response
    
    # Test data
    route_data = {
        'origin': {'address': 'Berlin'},  # Missing required fields
        'destination': {'address': 'Prague'}
    }
    
    # Make request and verify error
    with pytest.raises(ValidationError) as exc:
        api_client.create_route(route_data)
    
    assert exc.value.message == 'Validation failed'
    assert exc.value.response_data['errors']['pickup_time'] == ['Must be in the future']

def test_get_route_not_found(api_client, mock_session):
    """Test route retrieval with not found error."""
    # Mock response
    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.json.return_value = {
        'message': 'Route not found'
    }
    mock_session.request.return_value = mock_response
    
    # Make request and verify error
    with pytest.raises(NotFoundError) as exc:
        api_client.get_route('non-existent')
    
    assert exc.value.message == 'Route not found'

def test_server_error(api_client, mock_session):
    """Test handling of server errors."""
    # Mock response
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.json.return_value = {
        'message': 'Internal server error'
    }
    mock_session.request.return_value = mock_response
    
    # Make request and verify error
    with pytest.raises(ServerError) as exc:
        api_client.get_route('test-route')
    
    assert exc.value.message == 'Internal server error'

def test_network_error(api_client, mock_session):
    """Test handling of network errors."""
    # Mock session to raise error
    mock_session.request.side_effect = requests.RequestException('Connection failed')
    
    # Make request and verify error
    with pytest.raises(ApiError) as exc:
        api_client.get_route('test-route')
    
    assert 'Connection failed' in str(exc.value)
