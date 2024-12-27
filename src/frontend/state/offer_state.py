"""Offer state management."""
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from src.domain.entities.offer import Offer, OfferHistory
from src.domain.entities.route import Route
from src.domain.services import OfferGenerationService
from src.infrastructure.logging import get_logger

from dataclasses import dataclass, field
from enum import Enum
import streamlit as st
import requests


class OfferStateError(Exception):
    """Base exception for offer state errors."""
    pass


class InvalidStateTransitionError(OfferStateError):
    """Exception for invalid state transitions."""
    pass


class VersionConflictError(OfferStateError):
    """Exception for version conflicts."""
    pass


class OfferAction(Enum):
    """Available actions for offers."""
    CREATE = "create"
    UPDATE = "update"
    ARCHIVE = "archive"
    DELETE = "delete"


@dataclass
class OfferFilters:
    """Filters for offer listing."""
    status: Optional[List[str]] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    created_by: Optional[str] = None
    route_id: Optional[str] = None
    metadata_search: Optional[str] = None
    page: int = 1
    per_page: int = 10


@dataclass
class OfferState:
    """State container for offer management."""
    # Current offer being viewed/edited
    selected_offer_id: Optional[str] = None
    selected_offer: Optional[Offer] = None
    
    # Version management
    current_version: Optional[str] = None
    comparing_versions: bool = False
    version1: Optional[str] = None
    version2: Optional[str] = None
    
    # History
    history_entries: List[OfferHistory] = field(default_factory=list)
    total_history: int = 0
    history_page: int = 1
    history_per_page: int = 10
    
    # List management
    offers: List[Offer] = field(default_factory=list)
    total_offers: int = 0
    current_page: int = 1
    per_page: int = 10
    
    # Filters
    filters: OfferFilters = field(default_factory=OfferFilters)
    
    # Form state
    is_creating: bool = False
    is_editing: bool = False
    form_data: Optional[Dict[str, Any]] = None
    validation_errors: Dict[str, str] = field(default_factory=dict)
    
    # API interaction
    is_loading: bool = False
    error_message: Optional[str] = None
    success_message: Optional[str] = None

    @classmethod
    def get_state(cls) -> 'OfferState':
        """Get or create offer state in session."""
        if 'offer_state' not in st.session_state:
            st.session_state['offer_state'] = cls()
        return st.session_state['offer_state']

    def reset_messages(self) -> None:
        """Reset error and success messages."""
        self.error_message = None
        self.success_message = None

    def set_error(self, message: str) -> None:
        """Set error message."""
        self.error_message = message
        self.success_message = None

    def set_success(self, message: str) -> None:
        """Set success message."""
        self.success_message = message
        self.error_message = None

    def start_loading(self) -> None:
        """Start loading state."""
        self.is_loading = True
        self.reset_messages()

    def stop_loading(self) -> None:
        """Stop loading state."""
        self.is_loading = False

    def reset_form(self) -> None:
        """Reset form state."""
        self.is_creating = False
        self.is_editing = False
        self.form_data = None
        self.validation_errors.clear()

    def validate_form(self) -> bool:
        """Validate form data."""
        self.validation_errors.clear()
        
        if not self.form_data:
            self.validation_errors['form'] = 'No form data provided'
            return False
        
        # Required fields
        required_fields = ['status', 'margin', 'final_price']
        for field in required_fields:
            if field not in self.form_data or not self.form_data[field]:
                self.validation_errors[field] = f'{field.title()} is required'
        
        # Status transitions
        if self.is_editing and self.selected_offer:
            old_status = self.selected_offer.status
            new_status = self.form_data['status']
            
            if not self._is_valid_status_transition(old_status, new_status):
                self.validation_errors['status'] = f'Invalid status transition from {old_status} to {new_status}'
        
        # Version validation
        if self.is_editing and self.selected_offer:
            if self.form_data['version'] <= self.selected_offer.version:
                self.validation_errors['version'] = 'New version must be greater than current version'
        
        return len(self.validation_errors) == 0

    def _is_valid_status_transition(self, old_status: str, new_status: str) -> bool:
        """Check if status transition is valid."""
        # Define valid transitions
        valid_transitions = {
            OfferStatus.DRAFT: [OfferStatus.ACTIVE, OfferStatus.ARCHIVED],
            OfferStatus.ACTIVE: [OfferStatus.ARCHIVED],
            OfferStatus.ARCHIVED: []  # No transitions from archived
        }
        
        old_status_enum = OfferStatus(old_status)
        new_status_enum = OfferStatus(new_status)
        
        return new_status_enum in valid_transitions[old_status_enum]

    async def load_offer(self, offer_id: str) -> None:
        """Load offer and its history."""
        self.start_loading()
        try:
            # Load offer
            response = await self._api_get(f'/api/v1/offers/{offer_id}')
            self.selected_offer = Offer(**response['offer'])
            self.selected_offer_id = offer_id
            
            # Load history
            history_response = await self._api_get(
                f'/api/v1/offers/{offer_id}/history',
                params={
                    'page': self.history_page,
                    'per_page': self.history_per_page
                }
            )
            self.history_entries = [OfferHistory(**h) for h in history_response['history']]
            self.total_history = history_response['total']
            
        except Exception as e:
            self.set_error(f'Failed to load offer: {str(e)}')
        finally:
            self.stop_loading()

    async def load_offers(self) -> None:
        """Load offers with current filters."""
        self.start_loading()
        try:
            params = {
                'page': self.current_page,
                'per_page': self.per_page,
                **self.filters.__dict__
            }
            response = await self._api_get('/api/v1/offers', params=params)
            
            self.offers = [Offer(**o) for o in response['offers']]
            self.total_offers = response['total']
            
        except Exception as e:
            self.set_error(f'Failed to load offers: {str(e)}')
        finally:
            self.stop_loading()

    async def create_offer(self) -> bool:
        """Create new offer."""
        if not self.validate_form():
            return False
            
        self.start_loading()
        try:
            response = await self._api_post('/api/v1/offers', json=self.form_data)
            self.set_success('Offer created successfully')
            self.reset_form()
            await self.load_offers()
            return True
            
        except Exception as e:
            self.set_error(f'Failed to create offer: {str(e)}')
            return False
            
        finally:
            self.stop_loading()

    async def update_offer(self) -> bool:
        """Update existing offer."""
        if not self.validate_form():
            return False
            
        if not self.selected_offer_id:
            self.set_error('No offer selected for update')
            return False
            
        self.start_loading()
        try:
            response = await self._api_put(
                f'/api/v1/offers/{self.selected_offer_id}',
                json=self.form_data
            )
            self.set_success('Offer updated successfully')
            self.reset_form()
            await self.load_offer(self.selected_offer_id)
            return True
            
        except Exception as e:
            self.set_error(f'Failed to update offer: {str(e)}')
            return False
            
        finally:
            self.stop_loading()

    async def archive_offer(self, offer_id: str) -> bool:
        """Archive an offer."""
        self.start_loading()
        try:
            response = await self._api_post(f'/api/v1/offers/{offer_id}/archive')
            self.set_success('Offer archived successfully')
            await self.load_offers()
            return True
            
        except Exception as e:
            self.set_error(f'Failed to archive offer: {str(e)}')
            return False
            
        finally:
            self.stop_loading()

    async def _api_get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make GET request to API."""
        # TODO: Replace with actual API call
        return {}

    async def _api_post(self, endpoint: str, json: Optional[Dict] = None) -> Dict:
        """Make POST request to API."""
        # TODO: Replace with actual API call
        return {}

    async def _api_put(self, endpoint: str, json: Optional[Dict] = None) -> Dict:
        """Make PUT request to API."""
        # TODO: Replace with actual API call
        return {}
