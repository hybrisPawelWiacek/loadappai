"""Offer service interface.

This module defines the interface for offer management services.
The OfferService interface provides methods for:
- Creating and managing offers
- Offer validation and pricing
- Offer status tracking
- History management

Implementation Requirements:
1. Offer Creation:
   - Must validate all inputs
   - Should calculate pricing
   - Must generate unique IDs
   - Should track creation time

2. Offer Management:
   - Must handle status changes
   - Should track modifications
   - Must maintain history
   - Should handle versioning

3. Validation:
   - Must check all required fields
   - Should validate pricing
   - Must verify route exists
   - Should check business rules

4. History:
   - Must track all changes
   - Should store change reasons
   - Must maintain audit trail
   - Should handle versioning

Example Usage:
    ```python
    # Create new offer
    offer = offer_service.create_offer(
        route_id="123",
        price=Decimal("450.00"),
        validity_hours=24
    )
    
    # Update offer status
    updated = offer_service.update_status(
        offer_id="456",
        status="accepted",
        reason="Customer confirmed"
    )
    ```
"""
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from src.domain.entities.offer import Offer
from src.domain.interfaces.exceptions.service_errors import ServiceError

class OfferServiceError(ServiceError):
    """Exception raised for errors in the offer service.
    
    This includes:
    - Invalid offer data
    - Status transition errors
    - Validation failures
    - History tracking errors
    """
    pass

class OfferService(ABC):
    """Interface for offer management services.
    
    This interface defines the contract for offer-related operations
    including creation, validation, status management, and history
    tracking.
    """

    @abstractmethod
    def create_offer(
        self,
        route_id: UUID,
        price: Decimal,
        validity_hours: int,
        metadata: Optional[Dict] = None
    ) -> Offer:
        """Create a new offer.
        
        Args:
            route_id: ID of the route
            price: Offer price
            validity_hours: Offer validity period
            metadata: Optional additional data
            
        Returns:
            Created offer
            
        Raises:
            OfferServiceError: If creation fails
            
        Implementation Notes:
            - Must validate all inputs
            - Should calculate final price
            - Must set expiration time
            - Should handle metadata
        """
        pass

    @abstractmethod
    def update_status(
        self,
        offer_id: UUID,
        status: str,
        reason: Optional[str] = None
    ) -> Offer:
        """Update offer status.
        
        Args:
            offer_id: ID of the offer
            status: New status
            reason: Optional reason for change
            
        Returns:
            Updated offer
            
        Raises:
            OfferServiceError: If update fails
            
        Implementation Notes:
            - Must validate status transition
            - Should track change reason
            - Must update timestamp
            - Should notify relevant parties
        """
        pass

    @abstractmethod
    def validate_offer(
        self,
        offer: Offer
    ) -> bool:
        """Validate an offer.
        
        Args:
            offer: Offer to validate
            
        Returns:
            True if offer is valid
            
        Raises:
            OfferServiceError: If validation fails
            
        Implementation Notes:
            - Must check all required fields
            - Should validate pricing
            - Must verify expiration
            - Should check business rules
        """
        pass

    @abstractmethod
    def get_offer_history(
        self,
        offer_id: UUID
    ) -> List[Dict]:
        """Get history of an offer.
        
        Args:
            offer_id: ID of the offer
            
        Returns:
            List of historical changes
            
        Raises:
            OfferServiceError: If history retrieval fails
            
        Implementation Notes:
            - Must track all changes
            - Should include timestamps
            - Must maintain audit trail
            - Should handle versions
        """
        pass

    @abstractmethod
    def extend_validity(
        self,
        offer_id: UUID,
        hours: int,
        reason: Optional[str] = None
    ) -> Offer:
        """Extend offer validity period.
        
        Args:
            offer_id: ID of the offer
            hours: Hours to extend
            reason: Optional reason for extension
            
        Returns:
            Updated offer
            
        Raises:
            OfferServiceError: If extension fails
            
        Implementation Notes:
            - Must validate extension period
            - Should track change reason
            - Must update expiration
            - Should notify relevant parties
        """
        pass
