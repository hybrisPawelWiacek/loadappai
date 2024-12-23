"""
Tests for the offer state management
"""
import pytest
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import Mock, patch

import streamlit as st

from src.domain.entities import Offer, OfferHistory
from src.domain.enums import OfferStatus
from src.frontend.state.offer_state import (
    OfferState,
    OfferFilters,
    OfferStateError,
    InvalidStateTransitionError,
    VersionConflictError
)


@pytest.fixture
def sample_offer():
    """Create a sample offer for testing."""
    return Offer(
        id="test-offer-1",
        status=OfferStatus.DRAFT,
        version="1.0",
        final_price=Decimal("1000.00"),
        margin=Decimal("10.0"),
        created_at=datetime.now(timezone.utc),
        modified_at=datetime.now(timezone.utc),
        created_by="test-user",
        modified_by="test-user",
        additional_services=["service1", "service2"],
        notes="Test notes",
        fun_fact="Test fun fact",
        metadata={"key": "value"}
    )


@pytest.fixture
def sample_history_entry(sample_offer):
    """Create a sample history entry for testing."""
    return OfferHistory(
        id="test-history-1",
        offer_id=sample_offer.id,
        version="1.0",
        change_reason="Initial creation",
        changed_by="test-user",
        changed_at=datetime.now(timezone.utc),
        offer_data=sample_offer.__dict__
    )


@pytest.fixture
def offer_state():
    """Create offer state for testing."""
    # Clear session state before each test
    if 'offer_state' in st.session_state:
        del st.session_state['offer_state']
    return OfferState.get_state()


def test_get_state():
    """Test getting state from session."""
    # First call creates new state
    state1 = OfferState.get_state()
    assert isinstance(state1, OfferState)
    
    # Second call returns same state
    state2 = OfferState.get_state()
    assert state1 is state2


def test_reset_messages(offer_state):
    """Test resetting error and success messages."""
    offer_state.error_message = "Test error"
    offer_state.success_message = "Test success"
    
    offer_state.reset_messages()
    
    assert offer_state.error_message is None
    assert offer_state.success_message is None


def test_set_error(offer_state):
    """Test setting error message."""
    offer_state.success_message = "Test success"
    
    offer_state.set_error("Test error")
    
    assert offer_state.error_message == "Test error"
    assert offer_state.success_message is None


def test_set_success(offer_state):
    """Test setting success message."""
    offer_state.error_message = "Test error"
    
    offer_state.set_success("Test success")
    
    assert offer_state.success_message == "Test success"
    assert offer_state.error_message is None


def test_loading_state(offer_state):
    """Test loading state management."""
    offer_state.error_message = "Test error"
    offer_state.success_message = "Test success"
    
    offer_state.start_loading()
    assert offer_state.is_loading is True
    assert offer_state.error_message is None
    assert offer_state.success_message is None
    
    offer_state.stop_loading()
    assert offer_state.is_loading is False


def test_reset_form(offer_state):
    """Test form state reset."""
    offer_state.is_creating = True
    offer_state.is_editing = True
    offer_state.form_data = {"test": "data"}
    offer_state.validation_errors = {"test": "error"}
    
    offer_state.reset_form()
    
    assert offer_state.is_creating is False
    assert offer_state.is_editing is False
    assert offer_state.form_data is None
    assert len(offer_state.validation_errors) == 0


def test_validate_form_required_fields(offer_state):
    """Test form validation with required fields."""
    offer_state.form_data = {
        "status": OfferStatus.DRAFT,
        "margin": None,  # Missing required field
        "final_price": Decimal("1000.00")
    }
    
    assert offer_state.validate_form() is False
    assert "margin" in offer_state.validation_errors


def test_validate_form_status_transition(offer_state, sample_offer):
    """Test form validation with status transitions."""
    # Set up editing state
    offer_state.is_editing = True
    offer_state.selected_offer = sample_offer
    
    # Try invalid transition from DRAFT to ARCHIVED
    offer_state.form_data = {
        "status": OfferStatus.ARCHIVED,
        "margin": Decimal("10.0"),
        "final_price": Decimal("1000.00"),
        "version": "1.1"
    }
    
    assert offer_state.validate_form() is False
    assert "status" in offer_state.validation_errors


def test_validate_form_version_conflict(offer_state, sample_offer):
    """Test form validation with version conflicts."""
    # Set up editing state
    offer_state.is_editing = True
    offer_state.selected_offer = sample_offer
    
    # Try same version number
    offer_state.form_data = {
        "status": OfferStatus.DRAFT,
        "margin": Decimal("10.0"),
        "final_price": Decimal("1000.00"),
        "version": "1.0"  # Same as current version
    }
    
    assert offer_state.validate_form() is False
    assert "version" in offer_state.validation_errors


@pytest.mark.asyncio
async def test_load_offer_success(offer_state, sample_offer, sample_history_entry):
    """Test successful offer loading."""
    with patch.object(offer_state, '_api_get') as mock_api_get:
        # Mock API responses
        mock_api_get.side_effect = [
            {'offer': sample_offer.__dict__},
            {'history': [sample_history_entry.__dict__], 'total': 1}
        ]
        
        await offer_state.load_offer("test-offer-1")
        
        assert offer_state.selected_offer_id == "test-offer-1"
        assert offer_state.selected_offer.id == sample_offer.id
        assert len(offer_state.history_entries) == 1
        assert offer_state.total_history == 1
        assert not offer_state.is_loading
        assert not offer_state.error_message


@pytest.mark.asyncio
async def test_load_offer_error(offer_state):
    """Test offer loading with error."""
    with patch.object(offer_state, '_api_get') as mock_api_get:
        mock_api_get.side_effect = Exception("API error")
        
        await offer_state.load_offer("test-offer-1")
        
        assert not offer_state.is_loading
        assert offer_state.error_message == "Failed to load offer: API error"


@pytest.mark.asyncio
async def test_load_offers_success(offer_state, sample_offer):
    """Test successful offers loading."""
    with patch.object(offer_state, '_api_get') as mock_api_get:
        mock_api_get.return_value = {
            'offers': [sample_offer.__dict__],
            'total': 1
        }
        
        await offer_state.load_offers()
        
        assert len(offer_state.offers) == 1
        assert offer_state.total_offers == 1
        assert not offer_state.is_loading
        assert not offer_state.error_message


@pytest.mark.asyncio
async def test_create_offer_success(offer_state):
    """Test successful offer creation."""
    with patch.object(offer_state, '_api_post') as mock_api_post, \
         patch.object(offer_state, 'load_offers') as mock_load_offers:
        
        offer_state.form_data = {
            "status": OfferStatus.DRAFT,
            "margin": Decimal("10.0"),
            "final_price": Decimal("1000.00")
        }
        
        success = await offer_state.create_offer()
        
        assert success is True
        assert offer_state.success_message == "Offer created successfully"
        assert not offer_state.is_loading
        mock_load_offers.assert_called_once()


@pytest.mark.asyncio
async def test_update_offer_success(offer_state, sample_offer):
    """Test successful offer update."""
    with patch.object(offer_state, '_api_put') as mock_api_put, \
         patch.object(offer_state, 'load_offer') as mock_load_offer:
        
        offer_state.selected_offer_id = sample_offer.id
        offer_state.form_data = {
            "status": OfferStatus.ACTIVE,
            "margin": Decimal("15.0"),
            "final_price": Decimal("1500.00"),
            "version": "1.1"
        }
        
        success = await offer_state.update_offer()
        
        assert success is True
        assert offer_state.success_message == "Offer updated successfully"
        assert not offer_state.is_loading
        mock_load_offer.assert_called_once_with(sample_offer.id)


@pytest.mark.asyncio
async def test_archive_offer_success(offer_state):
    """Test successful offer archival."""
    with patch.object(offer_state, '_api_post') as mock_api_post, \
         patch.object(offer_state, 'load_offers') as mock_load_offers:
        
        success = await offer_state.archive_offer("test-offer-1")
        
        assert success is True
        assert offer_state.success_message == "Offer archived successfully"
        assert not offer_state.is_loading
        mock_load_offers.assert_called_once()
