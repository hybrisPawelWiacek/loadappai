"""Test suite for routes blueprint."""
import json
from datetime import datetime
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from flask import url_for

from src.domain.models import Route, RouteSegment
from src.domain.responses import RouteResponse, ErrorResponse

@pytest.fixture
def mock_route():
    """Fixture for mock route."""
    return Route(
        id=uuid4(),
        origin='Warsaw, Poland',
        destination='Berlin, Germany',
        distance=575.0,
        duration=6.5,
        segments=[
            RouteSegment(
                start_address='Warsaw, Poland',
                end_address='Poznan, Poland',
                distance=310.0,
                duration=3.5,
                type='LOADED'
            ),
            RouteSegment(
                start_address='Poznan, Poland',
                end_address='Berlin, Germany',
                distance=265.0,
                duration=3.0,
                type='LOADED'
            )
        ],
        created_at=datetime.utcnow(),
        modified_at=datetime.utcnow(),
        metadata={
            'cargo_weight': 1000,
            'cargo_volume': 500
        }
    )

def test_create_route(client):
    """Test creating a new route."""
    with patch('src.api.blueprints.routes.routes.RouteRepository') as mock_repo, \
         patch('src.api.blueprints.routes.routes.GoogleMapsService') as mock_maps:
        
        # Mock the route creation
        mock_route_id = uuid4()
        mock_repo.return_value.create.return_value = Route(
            id=mock_route_id,
            origin='Warsaw, Poland',
            destination='Berlin, Germany',
            distance=575.0,
            duration=6.5,
            created_at=datetime.utcnow(),
            modified_at=datetime.utcnow()
        )
        
        # Mock the geocoding
        mock_maps.return_value.geocode.side_effect = [
            {'lat': 52.2297, 'lng': 21.0122},  # Warsaw
            {'lat': 52.5200, 'lng': 13.4050}   # Berlin
        ]
        
        data = {
            'origin': 'Warsaw, Poland',
            'destination': 'Berlin, Germany',
            'cargo_weight': 1000,
            'cargo_volume': 500
        }
        
        response = client.post('/api/routes', json=data)
        assert response.status_code == 201
        
        route_data = json.loads(response.data)
        assert route_data['origin'] == data['origin']
        assert route_data['destination'] == data['destination']
        assert 'id' in route_data
        assert 'distance' in route_data
        assert 'duration' in route_data

def test_get_route(client, mock_route):
    """Test retrieving a route."""
    with patch('src.api.blueprints.routes.routes.RouteRepository') as mock_repo:
        mock_repo.return_value.get_by_id.return_value = mock_route
        
        response = client.get(f'/api/routes/{mock_route.id}')
        assert response.status_code == 200
        
        route_data = json.loads(response.data)
        assert route_data['id'] == str(mock_route.id)
        assert route_data['origin'] == mock_route.origin
        assert route_data['destination'] == mock_route.destination
        assert len(route_data['segments']) == 2

def test_get_route_not_found(client):
    """Test retrieving a non-existent route."""
    with patch('src.api.blueprints.routes.routes.RouteRepository') as mock_repo:
        mock_repo.return_value.get_by_id.return_value = None
        
        response = client.get(f'/api/routes/{uuid4()}')
        assert response.status_code == 404
        
        error_data = json.loads(response.data)
        assert error_data['code'] == 'NOT_FOUND'

def test_delete_route(client, mock_route):
    """Test deleting a route."""
    with patch('src.api.blueprints.routes.routes.RouteRepository') as mock_repo:
        mock_repo.return_value.get_by_id.return_value = mock_route
        mock_repo.return_value.delete.return_value = True
        
        response = client.delete(f'/api/routes/{mock_route.id}')
        assert response.status_code == 200
        
        # Verify repository calls
        mock_repo.return_value.delete.assert_called_once_with(mock_route.id)

def test_update_route(client, mock_route):
    """Test updating a route."""
    with patch('src.api.blueprints.routes.routes.RouteRepository') as mock_repo, \
         patch('src.api.blueprints.routes.routes.GoogleMapsService') as mock_maps:
        
        mock_repo.return_value.get_by_id.return_value = mock_route
        mock_repo.return_value.update.return_value = mock_route
        
        # Mock the geocoding
        mock_maps.return_value.geocode.side_effect = [
            {'lat': 52.2297, 'lng': 21.0122},  # Warsaw
            {'lat': 50.1109, 'lng': 8.6821}    # Frankfurt
        ]
        
        update_data = {
            'destination': 'Frankfurt, Germany',
            'cargo_weight': 1200
        }
        
        response = client.put(f'/api/routes/{mock_route.id}', json=update_data)
        assert response.status_code == 200
        
        route_data = json.loads(response.data)
        assert route_data['id'] == str(mock_route.id)
        assert 'metadata' in route_data

def test_list_routes(client, mock_route):
    """Test listing routes with filtering."""
    with patch('src.api.blueprints.routes.routes.RouteRepository') as mock_repo:
        mock_repo.return_value.list_routes.return_value = [mock_route]
        
        response = client.get('/api/routes?origin=Warsaw')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data['items']) == 1
        assert data['pagination']['page'] == 1

def test_calculate_empty_driving(client, mock_route):
    """Test calculating empty driving for a route."""
    with patch('src.api.blueprints.routes.routes.RouteRepository') as mock_repo, \
         patch('src.api.blueprints.routes.routes.EmptyDrivingService') as mock_service:
        
        mock_repo.return_value.get_by_id.return_value = mock_route
        mock_service.return_value.calculate.return_value = mock_route.segments
        
        response = client.post(f'/api/routes/{mock_route.id}/empty-driving')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data['segments']) == 2

def test_validation_error_handling(client):
    """Test handling of validation errors."""
    data = {
        'origin': '',  # Invalid: empty origin
        'destination': 'Berlin, Germany'
    }
    
    response = client.post('/api/routes', json=data)
    assert response.status_code == 400
    
    error_data = json.loads(response.data)
    assert error_data['code'] == 'VALIDATION_ERROR'

def test_geocoding_error_handling(client):
    """Test handling of geocoding errors."""
    with patch('src.api.blueprints.routes.routes.GoogleMapsService') as mock_maps:
        mock_maps.return_value.geocode.side_effect = Exception('Geocoding failed')
        
        data = {
            'origin': 'Invalid Address',
            'destination': 'Berlin, Germany'
        }
        
        response = client.post('/api/routes', json=data)
        assert response.status_code == 400
        
        error_data = json.loads(response.data)
        assert error_data['code'] == 'GEOCODING_ERROR'

def test_internal_error_handling(client):
    """Test handling of internal errors."""
    with patch('src.api.blueprints.routes.routes.RouteRepository') as mock_repo:
        mock_repo.return_value.list_routes.side_effect = Exception('Database error')
        
        response = client.get('/api/routes')
        assert response.status_code == 500
        
        error_data = json.loads(response.data)
        assert error_data['code'] == 'INTERNAL_ERROR'
