"""
State management hooks for frontend components.
"""
from datetime import datetime
from decimal import Decimal
from typing import Tuple, Optional, Dict, Any
from uuid import UUID

import streamlit as st

from src.domain.entities.offer import Offer, OfferHistory
from src.frontend.state.offer_state import OfferState, OfferFilters


def use_offer_list() -> Tuple[OfferState, Dict[str, Any]]:
    """
    Hook for offer list management.
    
    Returns:
        Tuple of (state, actions)
    """
    state = OfferState.get_state()
    
    async def load_page(page: int) -> None:
        """Load specific page of offers."""
        state.current_page = page
        await state.load_offers()
    
    async def apply_filters(filters: OfferFilters) -> None:
        """Apply new filters and reload offers."""
        state.filters = filters
        state.current_page = 1
        await state.load_offers()
    
    async def refresh() -> None:
        """Refresh current page."""
        await state.load_offers()
    
    return state, {
        'load_page': load_page,
        'apply_filters': apply_filters,
        'refresh': refresh
    }


def use_offer_details(offer_id: Optional[str] = None) -> Tuple[OfferState, Dict[str, Any]]:
    """
    Hook for offer details management.
    
    Args:
        offer_id: Optional offer ID to load
        
    Returns:
        Tuple of (state, actions)
    """
    state = OfferState.get_state()
    
    async def load() -> None:
        """Load offer details."""
        if offer_id:
            await state.load_offer(offer_id)
    
    async def start_edit() -> None:
        """Start editing current offer."""
        state.is_editing = True
        state.form_data = state.selected_offer.__dict__ if state.selected_offer else None
    
    async def cancel_edit() -> None:
        """Cancel editing."""
        state.reset_form()
    
    async def save() -> bool:
        """Save changes to current offer."""
        return await state.update_offer()
    
    async def archive() -> bool:
        """Archive current offer."""
        if offer_id:
            return await state.archive_offer(offer_id)
        return False
    
    return state, {
        'load': load,
        'start_edit': start_edit,
        'cancel_edit': cancel_edit,
        'save': save,
        'archive': archive
    }


def use_offer_form() -> Tuple[OfferState, Dict[str, Any]]:
    """
    Hook for offer form management.
    
    Returns:
        Tuple of (state, actions)
    """
    state = OfferState.get_state()
    
    def update_form(field: str, value: Any) -> None:
        """Update form field."""
        if not state.form_data:
            state.form_data = {}
        state.form_data[field] = value
    
    def validate() -> bool:
        """Validate form data."""
        return state.validate_form()
    
    async def submit() -> bool:
        """Submit form data."""
        if state.is_editing:
            return await state.update_offer()
        else:
            return await state.create_offer()
    
    def reset() -> None:
        """Reset form state."""
        state.reset_form()
    
    return state, {
        'update_form': update_form,
        'validate': validate,
        'submit': submit,
        'reset': reset
    }


def use_offer_history() -> Tuple[OfferState, Dict[str, Any]]:
    """
    Hook for offer history management.
    
    Returns:
        Tuple of (state, actions)
    """
    state = OfferState.get_state()
    
    async def load_page(page: int) -> None:
        """Load specific page of history."""
        state.history_page = page
        if state.selected_offer_id:
            await state.load_offer(state.selected_offer_id)
    
    def start_compare() -> None:
        """Start version comparison."""
        state.comparing_versions = True
        state.version1 = None
        state.version2 = None
    
    def select_versions(v1: str, v2: str) -> None:
        """Select versions for comparison."""
        state.version1 = v1
        state.version2 = v2
    
    def cancel_compare() -> None:
        """Cancel version comparison."""
        state.comparing_versions = False
        state.version1 = None
        state.version2 = None
    
    return state, {
        'load_page': load_page,
        'start_compare': start_compare,
        'select_versions': select_versions,
        'cancel_compare': cancel_compare
    }
