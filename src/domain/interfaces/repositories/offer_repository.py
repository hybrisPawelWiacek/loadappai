"""Offer repository interface.

This module defines the interface for offer data persistence.
The OfferRepository interface provides methods for:
- Managing offer entities
- Offer status tracking
- Offer history management
- Offer search and filtering

Implementation Requirements:
1. Offer Management:
   - Must handle offer lifecycle
   - Should track versions
   - Must manage status
   - Should store metadata

2. History:
   - Must track all changes
   - Should store reasons
   - Must maintain audit trail
   - Should handle versions
"""
from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from src.domain.entities.offer import Offer, OfferHistory
from src.domain.interfaces.repositories.base import Repository
from src.domain.value_objects.offer import OfferStatus


class OfferRepository(Repository, ABC):
    """Interface for offer data persistence.
    
    This interface defines the contract for offer data access and
    management. It extends the base Repository interface with
    offer-specific operations.
    """

    @abstractmethod
    def find_offers(
        self,
        route_id: Optional[UUID] = None,
        status: Optional[str] = None,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
        page: int = 1,
        per_page: int = 10
    ) -> Tuple[List[Offer], int]:
        """Find offers matching criteria.
        
        Args:
            route_id: Optional route ID filter
            status: Optional status filter
            min_price: Optional minimum price
            max_price: Optional maximum price
            page: Page number
            per_page: Results per page
            
        Returns:
            Tuple of (matching offers, total count)
            
        Implementation Notes:
            - Must support partial matches
            - Should optimize common queries
            - Must handle pagination
            - Should cache results
        """
        pass

    @abstractmethod
    def get_offer_history(self, offer_id: UUID) -> List[OfferHistory]:
        """Get history of offer changes.
        
        Args:
            offer_id: ID of the offer
            
        Returns:
            List of historical changes
            
        Raises:
            EntityNotFoundError: If offer not found
            
        Implementation Notes:
            - Must track all changes
            - Should include timestamps
            - Must store change reasons
            - Should handle versions
        """
        pass

    @abstractmethod
    def get_active_offers(self, page: int = 1, per_page: int = 10) -> List[Offer]:
        """Get currently active offers.
        
        Args:
            page: Page number
            per_page: Results per page
            
        Returns:
            List of active offers
            
        Implementation Notes:
            - Must filter by status
            - Should order by expiry
            - Must handle pagination
            - Should cache results
        """
        pass

    @abstractmethod
    def update_offer_status(
        self,
        offer_id: UUID,
        status: OfferStatus,
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
            EntityNotFoundError: If offer not found
            
        Implementation Notes:
            - Must validate status
            - Should track change reason
            - Must update timestamp
            - Should notify listeners
        """
        pass

    @abstractmethod
    def extend_validity(
        self,
        offer_id: UUID,
        new_validity_date: datetime,
        reason: str = "Validity extended"
    ) -> Offer:
        """Extend offer validity period.
        
        Args:
            offer_id: ID of the offer
            new_validity_date: New validity date
            reason: Optional reason for extension
            
        Returns:
            Updated offer
            
        Raises:
            EntityNotFoundError: If offer not found
            
        Implementation Notes:
            - Must validate extension
            - Should track change reason
            - Must update expiry
            - Should notify listeners
        """
        pass

    @abstractmethod
    def get_offer_metadata(self, offer_id: UUID) -> Dict:
        """Get offer metadata.
        
        Args:
            offer_id: ID of the offer
            
        Returns:
            Offer metadata
            
        Raises:
            EntityNotFoundError: If offer not found
            
        Implementation Notes:
            - Must handle missing data
            - Should parse formats
            - Must validate schema
            - Should cache results
        """
        pass

    @abstractmethod
    def get_version(self, offer_id: UUID, version: str) -> Optional[Offer]:
        """Get specific version of an offer.
        
        Args:
            offer_id: ID of the offer
            version: Version string
            
        Returns:
            Offer at specified version or None if not found
            
        Implementation Notes:
            - Must validate version format
            - Should handle missing versions
            - Must reconstruct state
            - Should cache results
        """
        pass

    @abstractmethod
    def compare_versions(
        self,
        offer_id: UUID,
        version1: str,
        version2: str
    ) -> Tuple[Optional[Offer], Optional[Offer]]:
        """Compare two versions of an offer.
        
        Args:
            offer_id: ID of the offer
            version1: First version to compare
            version2: Second version to compare
            
        Returns:
            Tuple of (version1 offer, version2 offer)
            If a version doesn't exist, that tuple element will be None
            
        Implementation Notes:
            - Must validate versions
            - Should optimize retrieval
            - Must handle missing versions
            - Should cache results
        """
        pass
