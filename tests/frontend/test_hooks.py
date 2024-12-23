"""
Tests for the frontend state management hooks
"""
import pytest
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import Mock, patch

import streamlit as st

from src.domain.entities import Offer, OfferHistory
from src.domain.enums import OfferStatus
from src.frontend.state.hooks import (
    use_offer_list,
    use_offer_details,
    use_offer_form,
    use_offer_history
)
from src.frontend.state.offer_state import OfferState, OfferFilters


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
def offer_state(sample_offer):
    """Create offer state for testing."""
    if 'offer_state' in st.session_state:
        del st.session_state['offer_state']
    state = OfferState.get_state()
    state.selected_offer = sample_offer
    state.selected_offer_id = sample_offer.id
    return state


@pytest.mark.asyncio
async def test_use_offer_list():
    """Test offer list hook."""
    # Get state and actions
    state, actions = use_offer_list()
    assert isinstance(state, OfferState)
    assert set(actions.keys()) == {'load_page', 'apply_filters', 'refresh'}
    
    # Test load_page
    with patch.object(state, 'load_offers') as mock_load:
        await actions['load_page'](2)
        assert state.current_page == 2
        mock_load.assert_called_once()
    
    # Test apply_filters
    with patch.object(state, 'load_offers') as mock_load:
        filters = OfferFilters(status=['DRAFT'])
        await actions['apply_filters'](filters)
        assert state.filters == filters
        assert state.current_page == 1
        mock_load.assert_called_once()
    
    # Test refresh
    with patch.object(state, 'load_offers') as mock_load:
        await actions['refresh']()
        mock_load.assert_called_once()


@pytest.mark.asyncio
async def test_use_offer_details(offer_state):
    """Test offer details hook."""
    # Get state and actions
    state, actions = use_offer_details("test-offer-1")
    assert isinstance(state, OfferState)
    assert set(actions.keys()) == {'load', 'start_edit', 'cancel_edit', 'save', 'archive'}
    
    # Test load
    with patch.object(state, 'load_offer') as mock_load:
        await actions['load']()
        mock_load.assert_called_once_with("test-offer-1")
    
    # Test start_edit
    await actions['start_edit']()
    assert state.is_editing is True
    assert state.form_data == offer_state.selected_offer.__dict__
    
    # Test cancel_edit
    await actions['cancel_edit']()
    assert state.is_editing is False
    assert state.form_data is None
    
    # Test save
    with patch.object(state, 'update_offer') as mock_update:
        mock_update.return_value = True
        result = await actions['save']()
        assert result is True
        mock_update.assert_called_once()
    
    # Test archive
    with patch.object(state, 'archive_offer') as mock_archive:
        mock_archive.return_value = True
        result = await actions['archive']()
        assert result is True
        mock_archive.assert_called_once_with("test-offer-1")


def test_use_offer_form():
    """Test offer form hook."""
    # Get state and actions
    state, actions = use_offer_form()
    assert isinstance(state, OfferState)
    assert set(actions.keys()) == {'update_form', 'validate', 'submit', 'reset'}
    
    # Test update_form
    actions['update_form']('test_field', 'test_value')
    assert state.form_data == {'test_field': 'test_value'}
    
    # Test validate
    with patch.object(state, 'validate_form') as mock_validate:
        mock_validate.return_value = True
        result = actions['validate']()
        assert result is True
        mock_validate.assert_called_once()
    
    # Test reset
    actions['reset']()
    assert state.is_creating is False
    assert state.is_editing is False
    assert state.form_data is None
    assert len(state.validation_errors) == 0


@pytest.mark.asyncio
async def test_use_offer_history():
    """Test offer history hook."""
    # Get state and actions
    state, actions = use_offer_history()
    assert isinstance(state, OfferState)
    assert set(actions.keys()) == {'load_page', 'start_compare', 'select_versions', 'cancel_compare'}
    
    # Test load_page
    state.selected_offer_id = "test-offer-1"
    with patch.object(state, 'load_offer') as mock_load:
        await actions['load_page'](2)
        assert state.history_page == 2
        mock_load.assert_called_once_with("test-offer-1")
    
    # Test start_compare
    actions['start_compare']()
    assert state.comparing_versions is True
    assert state.version1 is None
    assert state.version2 is None
    
    # Test select_versions
    actions['select_versions']("1.0", "1.1")
    assert state.version1 == "1.0"
    assert state.version2 == "1.1"
    
    # Test cancel_compare
    actions['cancel_compare']()
    assert state.comparing_versions is False
    assert state.version1 is None
    assert state.version2 is None
