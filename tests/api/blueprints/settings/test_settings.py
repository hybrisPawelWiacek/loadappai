"""Tests for the settings blueprint."""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from uuid import uuid4

from src.domain.models import (
    CostSettings, TransportSettings, SystemSettings,
    CostSettingsUpdateRequest
)
from src.domain.responses import (
    CostSettingsResponse, CostSettingsUpdateResponse
)

@pytest.fixture
def mock_cost_settings():
    """Fixture for mock cost settings."""
    return CostSettings(
        fuel_prices={
            'PL': 1.5,
            'DE': 1.8,
            'FR': 1.7
        },
        maintenance_cost_per_km=0.15,
        driver_cost_per_hour=25.0,
        base_cost_multiplier=1.2,
        currency='EUR'
    )

@pytest.fixture
def mock_transport_settings():
    """Fixture for mock transport settings."""
    return TransportSettings(
        max_driving_time=9,
        max_working_time=13,
        break_duration=0.75,
        daily_rest_duration=11,
        speed_empty=75,
        speed_loaded=68
    )

@pytest.fixture
def mock_system_settings():
    """Fixture for mock system settings."""
    return SystemSettings(
        default_currency='EUR',
        distance_unit='km',
        time_zone='UTC',
        language='en'
    )

def test_get_cost_settings(client, mock_cost_settings):
    """Test getting cost settings."""
    with patch('src.api.blueprints.settings.settings.CostSettingsRepository') as mock_repo:
        mock_repo.return_value.get_current_cost_settings.return_value = mock_cost_settings
        
        response = client.get('/api/settings/cost')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['fuel_prices']['PL'] == 1.5
        assert data['maintenance_cost_per_km'] == 0.15
        assert data['currency'] == 'EUR'

def test_get_cost_settings_not_found(client):
    """Test getting cost settings when none exist."""
    with patch('src.api.blueprints.settings.settings.CostSettingsRepository') as mock_repo:
        mock_repo.return_value.get_current_cost_settings.return_value = None
        
        response = client.get('/api/settings/cost')
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['code'] == 'NOT_FOUND'

def test_create_cost_settings(client, mock_cost_settings):
    """Test creating new cost settings."""
    with patch('src.api.blueprints.settings.settings.CostSettingsRepository') as mock_repo:
        mock_repo.return_value.update.return_value = mock_cost_settings
        
        settings_data = mock_cost_settings.dict()
        response = client.post('/api/settings/cost', json=settings_data)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['settings']['fuel_prices']['PL'] == 1.5
        assert 'updated_at' in data

def test_update_cost_settings(client, mock_cost_settings):
    """Test updating existing cost settings."""
    with patch('src.api.blueprints.settings.settings.CostSettingsRepository') as mock_repo:
        mock_repo.return_value.update.return_value = mock_cost_settings
        
        update_data = CostSettingsUpdateRequest(
            fuel_prices={'PL': 1.6},
            maintenance_cost_per_km=0.16
        ).dict()
        
        response = client.put('/api/settings/cost', json=update_data)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'settings' in data
        assert 'updated_at' in data

def test_get_transport_settings(client, mock_transport_settings):
    """Test getting transport settings."""
    with patch('src.api.blueprints.settings.settings.CostSettingsRepository') as mock_repo:
        mock_repo.return_value.get_transport_settings.return_value = mock_transport_settings
        
        response = client.get('/api/settings/transport')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['max_driving_time'] == 9
        assert data['speed_empty'] == 75
        assert data['speed_loaded'] == 68

def test_update_transport_settings(client, mock_transport_settings):
    """Test updating transport settings."""
    with patch('src.api.blueprints.settings.settings.CostSettingsRepository') as mock_repo:
        mock_repo.return_value.update_transport_settings.return_value = None
        
        settings_data = mock_transport_settings.dict()
        settings_data['speed_empty'] = 80
        
        response = client.put('/api/settings/transport', json=settings_data)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Transport settings updated successfully'
        assert 'updated_at' in data

def test_get_system_settings(client, mock_system_settings):
    """Test getting system settings."""
    with patch('src.api.blueprints.settings.settings.CostSettingsRepository') as mock_repo:
        mock_repo.return_value.get_system_settings.return_value = mock_system_settings
        
        response = client.get('/api/settings/system')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['default_currency'] == 'EUR'
        assert data['distance_unit'] == 'km'
        assert data['time_zone'] == 'UTC'

def test_update_system_settings(client, mock_system_settings):
    """Test updating system settings."""
    with patch('src.api.blueprints.settings.settings.CostSettingsRepository') as mock_repo:
        mock_repo.return_value.update_system_settings.return_value = None
        
        settings_data = mock_system_settings.dict()
        settings_data['language'] = 'pl'
        
        response = client.put('/api/settings/system', json=settings_data)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'System settings updated successfully'
        assert 'updated_at' in data

def test_validation_error_handling(client):
    """Test handling of validation errors."""
    invalid_data = {
        'fuel_prices': {'PL': 'invalid'},  # Should be a number
        'maintenance_cost_per_km': -1  # Should be positive
    }
    
    response = client.post('/api/settings/cost', json=invalid_data)
    
    assert response.status_code == 400
    data = response.get_json()
    assert data['code'] == 'VALIDATION_ERROR'

def test_internal_error_handling(client, mock_cost_settings):
    """Test handling of internal errors."""
    with patch('src.api.blueprints.settings.settings.CostSettingsRepository') as mock_repo:
        mock_repo.return_value.get_current_cost_settings.side_effect = Exception('Database error')
        
        response = client.get('/api/settings/cost')
        
        assert response.status_code == 500
        data = response.get_json()
        assert data['code'] == 'INTERNAL_ERROR'
