"""Offer repository implementation."""
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Dict, Any, Tuple
import uuid

from sqlalchemy import and_, cast, Float, func, desc, or_
from sqlalchemy.orm import Session

from src.domain.entities import Offer as OfferEntity, OfferHistory as OfferHistoryEntity
from src.infrastructure.models import Offer as OfferModel, OfferHistory as OfferHistoryModel
from src.infrastructure.repositories.base import Repository


class OfferRepository(Repository[OfferEntity]):
    """Repository for managing offer entities with version tracking and history."""

    def create(self, entity: OfferEntity) -> OfferEntity:
        """Create a new offer with initial version."""
        db_offer = OfferModel(
            id=str(entity.id),
            route_id=str(entity.route_id),
            cost_id=str(entity.cost_id),
            total_cost=float(entity.total_cost),
            margin=float(entity.margin),
            final_price=float(entity.final_price),
            fun_fact=entity.fun_fact,
            status=entity.status,
            version=entity.version or "1.0",
            is_active=entity.is_active,
            created_at=entity.created_at.astimezone(timezone.utc),
            modified_at=entity.modified_at.astimezone(timezone.utc),
            created_by=entity.created_by,
            modified_by=entity.modified_by,
            extra_data=entity.metadata if entity.metadata else None,
        )
        self.db.add(db_offer)
        self.db.commit()
        self.db.refresh(db_offer)
        
        # Create initial history entry
        self.add_history(
            offer_id=str(entity.id),
            version=entity.version or "1.0",
            status=entity.status,
            margin=float(entity.margin),
            final_price=float(entity.final_price),
            fun_fact=entity.fun_fact,
            metadata=entity.metadata,
            changed_by=entity.created_by,
            change_reason="Initial offer creation"
        )
        
        return self._to_entity(db_offer)

    def get_by_id(self, id: str) -> Optional[OfferEntity]:
        """Get current version of an offer by ID."""
        db_offer = self.db.query(OfferModel).filter(OfferModel.id == id).first()
        return self._to_entity(db_offer) if db_offer else None

    def get_version(self, id: str, version: str) -> Optional[OfferEntity]:
        """Get specific version of an offer."""
        db_history = (
            self.db.query(OfferHistoryModel)
            .filter(
                and_(
                    OfferHistoryModel.offer_id == id,
                    OfferHistoryModel.version == version
                )
            )
            .first()
        )
        return self._history_to_entity(db_history) if db_history else None

    def list_with_filters(
        self,
        page: int = 1,
        per_page: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[OfferEntity], int]:
        """
        List offers with pagination and advanced filtering.
        
        Args:
            page: Page number (1-based)
            per_page: Items per page
            filters: Dictionary of filters:
                - status: Offer status
                - route_id: Route ID
                - created_by: Creator's identifier
                - created_after: Creation date lower bound
                - created_before: Creation date upper bound
                - min_price: Minimum price
                - max_price: Maximum price
                - metadata_search: Search within metadata
        
        Returns:
            Tuple of (list of offers, total count)
        """
        query = self.db.query(OfferModel)
        
        # Apply filters
        if filters:
            if filters.get('status'):
                query = query.filter(OfferModel.status == filters['status'])
            
            if filters.get('route_id'):
                query = query.filter(OfferModel.route_id == filters['route_id'])
            
            if filters.get('created_by'):
                query = query.filter(OfferModel.created_by == filters['created_by'])
            
            if filters.get('created_after'):
                query = query.filter(OfferModel.created_at >= filters['created_after'])
            
            if filters.get('created_before'):
                query = query.filter(OfferModel.created_at <= filters['created_before'])
            
            if filters.get('min_price'):
                query = query.filter(OfferModel.final_price >= filters['min_price'])
            
            if filters.get('max_price'):
                query = query.filter(OfferModel.final_price <= filters['max_price'])
            
            if filters.get('metadata_search'):
                query = query.filter(OfferModel.extra_data.contains(filters['metadata_search']))
        
        # Get total count before pagination
        total = query.count()
        
        # Apply pagination
        query = query.order_by(desc(OfferModel.created_at))
        query = query.offset((page - 1) * per_page).limit(per_page)
        
        # Execute query
        offers = query.all()
        return [self._to_entity(offer) for offer in offers], total

    def update(self, entity: OfferEntity) -> OfferEntity:
        """Update an offer and create history entry."""
        db_offer = self.db.query(OfferModel).filter(OfferModel.id == str(entity.id)).first()
        if not db_offer:
            return None

        # Create history entry before update
        self.add_history(
            offer_id=str(entity.id),
            version=db_offer.version,
            status=db_offer.status,
            margin=float(db_offer.margin),
            final_price=float(db_offer.final_price),
            fun_fact=db_offer.fun_fact,
            metadata=db_offer.extra_data,
            changed_by=entity.modified_by,
            change_reason=entity.metadata.get('change_reason', 'Offer updated')
        )

        # Update offer
        update_data = {
            "route_id": str(entity.route_id),
            "cost_id": str(entity.cost_id),
            "total_cost": float(entity.total_cost),
            "margin": float(entity.margin),
            "final_price": float(entity.final_price),
            "fun_fact": entity.fun_fact,
            "status": entity.status,
            "version": entity.version,
            "is_active": entity.is_active,
            "modified_at": entity.modified_at.astimezone(timezone.utc),
            "modified_by": entity.modified_by,
            "extra_data": entity.metadata if entity.metadata else None,
        }

        for key, value in update_data.items():
            setattr(db_offer, key, value)

        self.db.commit()
        self.db.refresh(db_offer)
        return self._to_entity(db_offer)

    def add_history(
        self,
        offer_id: str,
        version: str,
        status: str,
        margin: float,
        final_price: float,
        fun_fact: Optional[str],
        metadata: Optional[Dict],
        changed_by: Optional[str],
        change_reason: Optional[str]
    ) -> OfferHistoryEntity:
        """Add a history entry for an offer."""
        history_entry = OfferHistoryModel(
            id=str(uuid.uuid4()),
            offer_id=offer_id,
            version=version,
            status=status,
            margin=margin,
            final_price=final_price,
            fun_fact=fun_fact,
            extra_data=metadata,
            changed_at=datetime.now(timezone.utc),
            changed_by=changed_by,
            change_reason=change_reason
        )
        self.db.add(history_entry)
        self.db.commit()
        self.db.refresh(history_entry)
        return self._history_to_entity(history_entry)

    def get_history(
        self,
        offer_id: str,
        page: int = 1,
        per_page: int = 10,
        include_metadata: bool = False
    ) -> Tuple[List[OfferHistoryEntity], int]:
        """
        Get paginated history entries for an offer.
        
        Args:
            offer_id: Offer ID
            page: Page number (1-based)
            per_page: Items per page
            include_metadata: Whether to include metadata in results
            
        Returns:
            Tuple of (list of history entries, total count)
        """
        query = (
            self.db.query(OfferHistoryModel)
            .filter(OfferHistoryModel.offer_id == offer_id)
            .order_by(desc(OfferHistoryModel.changed_at))
        )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        query = query.offset((page - 1) * per_page).limit(per_page)
        
        # Execute query
        history_entries = query.all()
        return [self._history_to_entity(entry) for entry in history_entries], total

    def compare_versions(
        self,
        offer_id: str,
        version1: str,
        version2: str
    ) -> Tuple[Optional[OfferHistoryEntity], Optional[OfferHistoryEntity]]:
        """
        Compare two versions of an offer.
        
        Args:
            offer_id: Offer ID
            version1: First version to compare
            version2: Second version to compare
            
        Returns:
            Tuple of (version1 entry, version2 entry)
        """
        entries = (
            self.db.query(OfferHistoryModel)
            .filter(
                and_(
                    OfferHistoryModel.offer_id == offer_id,
                    or_(
                        OfferHistoryModel.version == version1,
                        OfferHistoryModel.version == version2
                    )
                )
            )
            .order_by(OfferHistoryModel.version)
            .all()
        )
        
        if len(entries) != 2:
            return None, None
            
        return (
            self._history_to_entity(entries[0]),
            self._history_to_entity(entries[1])
        )

    def get(self, id: str) -> Optional[OfferEntity]:
        """Get entity by ID."""
        return self.get_by_id(id)

    def get_all(self, skip: int = 0, limit: int = 100) -> List[OfferEntity]:
        """Get all entities with pagination."""
        db_offers = (
            self.db.query(OfferModel)
            .order_by(desc(OfferModel.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [self._to_entity(offer) for offer in db_offers]

    def delete(self, id: str) -> bool:
        """Delete an entity."""
        db_offer = self.db.query(OfferModel).filter(OfferModel.id == id).first()
        if db_offer:
            self.db.delete(db_offer)
            self.db.commit()
            return True
        return False

    def _to_entity(self, db_offer: OfferModel) -> OfferEntity:
        """Convert database model to domain entity."""
        if not db_offer:
            return None
            
        return OfferEntity(
            id=uuid.UUID(db_offer.id),
            route_id=uuid.UUID(db_offer.route_id),
            cost_id=uuid.UUID(db_offer.cost_id),
            total_cost=Decimal(str(db_offer.total_cost)),
            margin=Decimal(str(db_offer.margin)),
            final_price=Decimal(str(db_offer.final_price)),
            fun_fact=db_offer.fun_fact,
            status=db_offer.status,
            version=db_offer.version,
            is_active=db_offer.is_active,
            created_at=db_offer.created_at.replace(tzinfo=timezone.utc),
            modified_at=db_offer.modified_at.replace(tzinfo=timezone.utc),
            created_by=db_offer.created_by,
            modified_by=db_offer.modified_by,
            metadata=db_offer.extra_data
        )

    def _history_to_entity(self, db_history: OfferHistoryModel) -> OfferHistoryEntity:
        """Convert history model to domain entity."""
        if not db_history:
            return None
            
        return OfferHistoryEntity(
            id=uuid.UUID(db_history.id),
            offer_id=uuid.UUID(db_history.offer_id),
            version=db_history.version,
            status=db_history.status,
            margin=Decimal(str(db_history.margin)),
            final_price=Decimal(str(db_history.final_price)),
            fun_fact=db_history.fun_fact,
            metadata=db_history.extra_data,
            changed_at=db_history.changed_at.replace(tzinfo=timezone.utc),
            changed_by=db_history.changed_by,
            change_reason=db_history.change_reason
        )
