"""Tests for the costs blueprint."""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from uuid import uuid4

from src.domain.models import (
    Route, CostCalculation, CostSettings
)
from src.domain.responses import (
    CostCalculationResponse, CostSettingsResponse
)

@pytest.fixture
def mock_route():
    """Fixture for mock route."""
    return Route(
        id=uuid4(),
        origin='Warsaw, Poland',
        destination='Berlin, Germany',
        distance=575.0,
        duration=6.5,
        created_at=datetime.utcnow(),
        modified_at=datetime.utcnow()
    )

@pytest.fixture
def mock_cost_calculation():
    """Fixture for mock cost calculation."""
    return CostCalculation(
        id=uuid4(),
        route_id=uuid4(),
        total_cost=1000.0,
        fuel_cost=400.0,
        maintenance_cost=150.0,
        driver_cost=450.0,
        currency='EUR',
        created_at=datetime.utcnow(),
        metadata={
            'fuel_consumption': 28.5,
            'total_distance': 575.0,
            'total_duration': 6.5
        }
    )

@pytest.fixture
def mock_cost_settings():
    """Fixture for mock cost settings."""
    return CostSettings(
        route_id=uuid4(),
        fuel_consumption=28.5,
        additional_cost_per_km=0.05,
        custom_driver_cost_per_hour=30.0,
        currency='EUR',
        created_at=datetime.utcnow(),
        modified_at=datetime.utcnow()
    )

def test_calculate_route_costs(client, mock_route, mock_cost_calculation):
    """Test calculating costs for a route."""
    with patch('src.api.blueprints.costs.costs.RouteRepository') as mock_route_repo, \
         patch('src.api.blueprints.costs.costs.CostCalculationService') as mock_cost_service:
        mock_route_repo.return_value.get_by_id.return_value = mock_route
        mock_cost_service.return_value.calculate_costs.return_value = mock_cost_calculation
        
        response = client.post(f'/api/costs/routes/{mock_route.id}/calculate')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['total_cost'] == 1000.0
        assert data['fuel_cost'] == 400.0
        assert data['maintenance_cost'] == 150.0
        assert data['driver_cost'] == 450.0

def test_get_route_costs(client, mock_cost_calculation):
    """Test getting previously calculated costs for a route."""
    with patch('src.api.blueprints.costs.costs.CostCalculationRepository') as mock_repo:
        mock_repo.return_value.get_latest_for_route.return_value = mock_cost_calculation
        
        response = client.get(f'/api/costs/routes/{mock_cost_calculation.route_id}/costs')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['total_cost'] == 1000.0
        assert data['currency'] == 'EUR'
        assert 'metadata' in data

def test_get_route_costs_not_found(client):
    """Test getting costs for a route with no calculations."""
    with patch('src.api.blueprints.costs.costs.CostCalculationRepository') as mock_repo:
        mock_repo.return_value.get_latest_for_route.return_value = None
        
        response = client.get(f'/api/costs/routes/{uuid4()}/costs')
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['code'] == 'NOT_FOUND'

def test_get_route_settings(client, mock_cost_settings):
    """Test getting settings for a route."""
    with patch('src.api.blueprints.costs.costs.CostSettingsRepository') as mock_repo:
        mock_repo.return_value.get_by_route_id.return_value = mock_cost_settings
        
        response = client.get(f'/api/costs/routes/{mock_cost_settings.route_id}/settings')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['fuel_consumption'] == 28.5
        assert data['currency'] == 'EUR'

def test_create_route_settings(client, mock_cost_settings):
    """Test creating settings for a route."""
    with patch('src.api.blueprints.costs.costs.CostSettingsRepository') as mock_repo:
        mock_repo.return_value.create.return_value = mock_cost_settings
        
        settings_data = {
            'fuel_consumption': 28.5,
            'additional_cost_per_km': 0.05,
            'custom_driver_cost_per_hour': 30.0,
            'currency': 'EUR'
        }
        
        response = client.post(
            f'/api/costs/routes/{mock_cost_settings.route_id}/settings',
            json=settings_data
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['fuel_consumption'] == 28.5
        assert data['currency'] == 'EUR'

def test_update_route_settings(client, mock_cost_settings):
    """Test updating settings for a route."""
    with patch('src.api.blueprints.costs.costs.CostSettingsRepository') as mock_repo:
        mock_repo.return_value.get_by_route_id.return_value = mock_cost_settings
        mock_repo.return_value.update.return_value = mock_cost_settings
        
        update_data = {
            'fuel_consumption': 30.0,
            'additional_cost_per_km': 0.06
        }
        
        response = client.put(
            f'/api/costs/routes/{mock_cost_settings.route_id}/settings',
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['fuel_consumption'] == 28.5  # Using mock data
        assert data['currency'] == 'EUR'

def test_update_route_settings_not_found(client):
    """Test updating settings for a non-existent route."""
    with patch('src.api.blueprints.costs.costs.CostSettingsRepository') as mock_repo:
        mock_repo.return_value.get_by_route_id.return_value = None
        
        update_data = {
            'fuel_consumption': 30.0,
            'additional_cost_per_km': 0.06
        }
        
        response = client.put(f'/api/costs/routes/{uuid4()}/settings', json=update_data)
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['code'] == 'NOT_FOUND'

def test_validation_error_handling(client, mock_route):
    """Test handling of validation errors in route settings."""
    invalid_data = {
        'fuel_consumption': -1.0,  # Invalid: negative consumption
        'currency': 'INVALID'  # Invalid: unknown currency
    }
    
    response = client.post(f'/api/costs/routes/{mock_route.id}/settings', json=invalid_data)
    
    assert response.status_code == 400
    data = response.get_json()
    assert data['code'] == 'VALIDATION_ERROR'

def test_internal_error_handling(client):
    """Test handling of internal errors."""
    with patch('src.api.blueprints.costs.costs.CostSettingsRepository') as mock_repo:
        mock_repo.return_value.get_by_route_id.side_effect = Exception('Database error')
        
        response = client.get(f'/api/costs/routes/{uuid4()}/settings')
        
        assert response.status_code == 500
        data = response.get_json()
        assert data['code'] == 'INTERNAL_ERROR'
