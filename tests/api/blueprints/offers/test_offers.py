"""Tests for the offers blueprint."""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from uuid import uuid4

from src.domain.models import Offer, OfferHistory
from src.domain.responses import OfferResponse, OfferHistoryResponse

@pytest.fixture
def mock_offer():
    """Fixture for mock offer."""
    return Offer(
        id=uuid4(),
        route_id=uuid4(),
        status='DRAFT',
        margin=0.15,
        total_cost=1000.0,
        offer_price=1150.0,
        currency='EUR',
        version=1,
        created_at=datetime.utcnow(),
        modified_at=datetime.utcnow(),
        metadata={'key': 'value'}
    )

@pytest.fixture
def mock_offer_history():
    """Fixture for mock offer history."""
    return [
        OfferHistory(
            id=uuid4(),
            offer_id=uuid4(),
            version=1,
            status='DRAFT',
            margin=0.15,
            total_cost=1000.0,
            offer_price=1150.0,
            modified_at=datetime.utcnow(),
            modified_by='user1',
            change_reason='Initial creation'
        ),
        OfferHistory(
            id=uuid4(),
            offer_id=uuid4(),
            version=2,
            status='SENT',
            margin=0.18,
            total_cost=1000.0,
            offer_price=1180.0,
            modified_at=datetime.utcnow(),
            modified_by='user2',
            change_reason='Price adjustment'
        )
    ]

def test_get_offer(client, mock_offer):
    """Test getting an offer by ID."""
    with patch('src.api.blueprints.offers.offers.OfferRepository') as mock_repo:
        mock_repo.return_value.get_by_id.return_value = mock_offer
        
        response = client.get(f'/api/offers/{mock_offer.id}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['id'] == str(mock_offer.id)
        assert data['status'] == 'DRAFT'
        assert data['margin'] == 0.15
        assert data['total_cost'] == 1000.0

def test_get_offer_with_history(client, mock_offer, mock_offer_history):
    """Test getting an offer with version history."""
    with patch('src.api.blueprints.offers.offers.OfferRepository') as mock_repo:
        mock_repo.return_value.get_by_id.return_value = mock_offer
        mock_repo.return_value.get_history.return_value = mock_offer_history
        
        response = client.get(f'/api/offers/{mock_offer.id}?include_history=true')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['id'] == str(mock_offer.id)
        assert len(data['history']) == 2
        assert data['history'][0]['version'] == 1
        assert data['history'][1]['version'] == 2

def test_get_offer_specific_version(client, mock_offer):
    """Test getting a specific version of an offer."""
    with patch('src.api.blueprints.offers.offers.OfferRepository') as mock_repo:
        mock_repo.return_value.get_version.return_value = mock_offer
        
        response = client.get(f'/api/offers/{mock_offer.id}?version=1')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['id'] == str(mock_offer.id)
        assert data['version'] == 1

def test_get_offer_not_found(client):
    """Test getting a non-existent offer."""
    with patch('src.api.blueprints.offers.offers.OfferRepository') as mock_repo:
        mock_repo.return_value.get_by_id.return_value = None
        
        response = client.get(f'/api/offers/{uuid4()}')
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['code'] == 'NOT_FOUND'

def test_update_offer(client, mock_offer):
    """Test updating an offer."""
    with patch('src.api.blueprints.offers.offers.OfferRepository') as mock_repo:
        mock_repo.return_value.get_by_id.return_value = mock_offer
        mock_repo.return_value.update.return_value = mock_offer
        
        update_data = {
            'margin': 0.18,
            'status': 'SENT',
            'modified_by': 'user2',
            'change_reason': 'Price adjustment'
        }
        
        response = client.put(f'/api/offers/{mock_offer.id}', json=update_data)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['id'] == str(mock_offer.id)
        assert data['version'] == 1

def test_archive_offer(client, mock_offer):
    """Test archiving an offer."""
    with patch('src.api.blueprints.offers.offers.OfferRepository') as mock_repo:
        mock_repo.return_value.get_by_id.return_value = mock_offer
        mock_repo.return_value.update.return_value = mock_offer
        
        archive_data = {
            'archived_by': 'user1',
            'archive_reason': 'No longer needed'
        }
        
        response = client.post(f'/api/offers/{mock_offer.id}/archive', json=archive_data)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['id'] == str(mock_offer.id)

def test_list_offers(client, mock_offer):
    """Test listing offers with filtering and pagination."""
    with patch('src.api.blueprints.offers.offers.OfferRepository') as mock_repo:
        mock_repo.return_value.list_offers.return_value = [mock_offer]
        
        response = client.get('/api/offers?status=DRAFT&page=1&per_page=10')
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['items']) == 1
        assert data['pagination']['page'] == 1
        assert data['pagination']['per_page'] == 10

def test_validation_error_handling(client, mock_offer):
    """Test handling of validation errors in offer updates."""
    with patch('src.api.blueprints.offers.offers.OfferRepository') as mock_repo:
        mock_repo.return_value.get_by_id.return_value = mock_offer
        
        invalid_data = {
            'margin': -0.1,  # Invalid: negative margin
            'status': 'INVALID_STATUS'  # Invalid: unknown status
        }
        
        response = client.put(f'/api/offers/{mock_offer.id}', json=invalid_data)
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['code'] == 'VALIDATION_ERROR'

def test_internal_error_handling(client):
    """Test handling of internal errors."""
    with patch('src.api.blueprints.offers.offers.OfferRepository') as mock_repo:
        mock_repo.return_value.get_by_id.side_effect = Exception('Database error')
        
        response = client.get(f'/api/offers/{uuid4()}')
        
        assert response.status_code == 500
        data = response.get_json()
        assert data['code'] == 'INTERNAL_ERROR'
