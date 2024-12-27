"""Offer repository implementation."""
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal, getcontext
from typing import Dict, List, Optional, Tuple, Union
from uuid import UUID, uuid4

from sqlalchemy import MetaData, or_, desc
from sqlalchemy.orm import Session

from src.domain.entities.offer import Offer, OfferHistory
from src.domain.interfaces.exceptions.repository_errors import OfferNotFoundError
from src.domain.interfaces.repositories.offer_repository import OfferRepository as IOfferRepository
from src.domain.value_objects.offer import OfferStatus
from src.infrastructure.models import Offer as OfferModel, OfferHistory as OfferHistoryModel
from src.infrastructure.database import get_db
from src.infrastructure.logging import get_logger


class OfferRepository(IOfferRepository):
    """Repository for managing offer entities with version tracking and history."""

    def __init__(self, db: Session):
        """Initialize the repository with a database session."""
        self.db = db
        self.db_session = db  # Alias for db for compatibility

    def create(self, offer: Offer) -> Offer:
        """Create a new offer."""
        model = OfferModel(
            id=str(offer.id),
            route_id=str(offer.route_id),
            cost_history_id=str(offer.cost_id),
            total_cost=float(offer.total_cost),
            margin=float(offer.margin),
            final_price=float(offer.final_price),
            fun_fact=offer.fun_fact,
            status=offer.status.value,
            is_active=offer.is_active,
            valid_until=offer.valid_until,
            version="1.0",
            extra_data=offer.metadata or {},
            created_at=datetime.now(timezone.utc),
            modified_at=datetime.now(timezone.utc)
        )
        self.db.add(model)
        self.db.flush()

        # Create initial history entry
        history = self._create_history_entry(
            offer_id=model.id,
            version="1.0",
            status=model.status,
            margin=float(offer.margin),
            final_price=float(offer.final_price),
            fun_fact=model.fun_fact,
            metadata=model.extra_data,
            reason="Initial creation"
        )
        self.db.add(history)
        self.db.commit()

        return self._to_entity(model)

    def get(self, id: UUID) -> Optional[Offer]:
        """Get an offer by ID."""
        return self.get_by_id(str(id))

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Offer]:
        """Get all offers with pagination."""
        models = self.db.query(OfferModel).offset(skip).limit(limit).all()
        return [self._to_entity(m) for m in models]

    def count(self) -> int:
        """Get total number of offers."""
        return self.db.query(OfferModel).count()

    def get_by_id(self, id: str) -> Optional[Offer]:
        """Get an offer by ID."""
        db_offer = self.db.query(OfferModel).filter(OfferModel.id == str(id)).first()
        if not db_offer:
            return None
        return self._to_entity(db_offer)

    def get_version(self, offer_id: UUID, version: str) -> Optional[Offer]:
        """Get specific version of an offer."""
        # Get the offer first to get all required fields
        offer = self.db.query(OfferModel).filter(OfferModel.id == str(offer_id)).first()
        if not offer:
            raise OfferNotFoundError(f"Offer with id {offer_id} not found")

        # Get the history entry for the specific version
        history = self.db.query(OfferHistoryModel).filter(
            OfferHistoryModel.offer_id == str(offer_id),
            OfferHistoryModel.version == version
        ).first()

        if not history:
            return None

        # Create an offer with the historical data
        return Offer(
            id=UUID(history.offer_id),
            route_id=UUID(offer.route_id),
            cost_id=UUID(offer.cost_history_id) if offer.cost_history_id else None,
            total_cost=Decimal(str(offer.total_cost)).quantize(Decimal('0.01')),
            status=OfferStatus(history.status),
            margin=Decimal(str(history.margin)).quantize(Decimal('0.0001')),
            final_price=Decimal(str(history.final_price)).quantize(Decimal('0.01')),
            fun_fact=history.fun_fact,
            metadata=history.extra_data or {},
            version=history.version,
            created_at=offer.created_at,
            modified_at=history.changed_at,
            valid_until=offer.valid_until,
            is_active=offer.is_active
        )

    def update(self, offer: Offer) -> Offer:
        """Update an existing offer."""
        db_offer = self.db.query(OfferModel).filter(OfferModel.id == str(offer.id)).first()
        if not db_offer:
            raise OfferNotFoundError(f"Offer with id {offer.id} not found")

        # Update version
        db_offer.version = self._increment_version(db_offer.version)
        db_offer.modified_at = datetime.now(timezone.utc)

        # Update fields
        db_offer.status = offer.status.value
        db_offer.margin = float(offer.margin)
        db_offer.final_price = float(offer.final_price)
        db_offer.fun_fact = offer.fun_fact
        db_offer.extra_data = offer.metadata or {}
        db_offer.is_active = offer.is_active
        db_offer.valid_until = offer.valid_until

        # Create history entry
        history = self._create_history_entry(
            offer_id=offer.id,
            version=db_offer.version,
            status=offer.status.value,
            margin=float(offer.margin),
            final_price=float(offer.final_price),
            fun_fact=offer.fun_fact,
            metadata=offer.metadata or {},
            reason="Offer updated"
        )
        self.db.add(history)
        self.db.commit()

        return self._to_entity(db_offer)

    def delete(self, id: str) -> bool:
        """Delete an offer by ID."""
        db_offer = self.db.query(OfferModel).filter(OfferModel.id == str(id)).first()
        if not db_offer:
            return False
        self.db.delete(db_offer)
        self.db.commit()
        return True

    def find_offers(
        self,
        route_id: Optional[UUID] = None,
        status: Optional[str] = None,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
        page: int = 1,
        per_page: int = 10
    ) -> Tuple[List[Offer], int]:
        """Find offers matching criteria."""
        filters = {}
        if route_id:
            filters['route_id'] = str(route_id)
        if status:
            filters['status'] = status
        if min_price:
            filters['min_price'] = float(min_price)
        if max_price:
            filters['max_price'] = float(max_price)
            
        return self.list_with_filters(page=page, per_page=per_page, filters=filters)

    def get_offer_history(self, offer_id: UUID) -> List[OfferHistory]:
        """Get history of an offer."""
        history_models = self.db.query(OfferHistoryModel).filter(
            OfferHistoryModel.offer_id == str(offer_id)
        ).order_by(OfferHistoryModel.changed_at.desc()).all()

        return [self._to_history_entity(h) for h in history_models]

    def get_active_offers(self) -> List[Offer]:
        """Get all active offers."""
        now = datetime.now(timezone.utc)
        models = self.db.query(OfferModel).filter(
            OfferModel.is_active == True,  # noqa
            OfferModel.status == OfferStatus.ACTIVE.value,
            or_(
                OfferModel.valid_until.is_(None),
                OfferModel.valid_until > now
            )
        ).all()

        return [self._to_entity(m) for m in models]

    def update_offer_status(
        self,
        offer_id: UUID,
        status: OfferStatus,
        reason: Optional[str] = None
    ) -> Offer:
        """Update offer status."""
        model = self.db.query(OfferModel).filter(OfferModel.id == str(offer_id)).first()
        if not model:
            raise OfferNotFoundError(f"Offer with id {offer_id} not found")

        # Update model
        model.status = status.value
        model.version = self._increment_version(model.version)
        model.modified_at = datetime.now(timezone.utc)

        # Create history entry
        history = self._create_history_entry(
            offer_id=offer_id,
            version=model.version,
            status=status.value,
            margin=float(model.margin),
            final_price=float(model.final_price),
            fun_fact=model.fun_fact,
            metadata=model.extra_data or {},
            reason=reason or f"Status updated to {status.value}"
        )
        self.db.add(history)
        self.db.commit()

        return self._to_entity(model)

    def extend_validity(
        self,
        offer_id: UUID,
        new_validity_date: datetime,
        reason: str = "Validity extended"
    ) -> Offer:
        """Extend offer validity."""
        model = self.db.query(OfferModel).filter(OfferModel.id == str(offer_id)).first()
        if not model:
            raise OfferNotFoundError(f"Offer with id {offer_id} not found")

        # Ensure new_validity_date has timezone info
        if new_validity_date.tzinfo is None:
            new_validity_date = new_validity_date.replace(tzinfo=timezone.utc)

        # Update the version and validity date
        model.version = self._increment_version(model.version)
        model.valid_until = new_validity_date
        model.modified_at = datetime.now(timezone.utc)

        # Create history entry with detailed reason
        history = self._create_history_entry(
            offer_id=offer_id,
            version=model.version,
            status=model.status,
            margin=float(model.margin),
            final_price=float(model.final_price),
            fun_fact=model.fun_fact,
            metadata=model.extra_data or {},
            reason=f"{reason} - Valid until: {new_validity_date.isoformat()}"
        )
        self.db.add(history)
        self.db.commit()

        return self._to_entity(model)

    def get_offer_metadata(self, offer_id: UUID) -> Dict:
        """Get offer metadata."""
        db_offer = self._get_offer(offer_id)
        if not db_offer:
            raise OfferNotFoundError(f"Offer with ID {offer_id} not found")
        return db_offer.extra_data if db_offer.extra_data else {}

    def compare_versions(
        self,
        offer_id: UUID,
        version1: str,
        version2: str
    ) -> Tuple[Optional[Offer], Optional[Offer]]:
        """Compare two versions of an offer."""
        v1 = self.get_version(offer_id, version1)
        v2 = self.get_version(offer_id, version2)
        return v1, v2

    def list_with_filters(
        self,
        page: int = 1,
        per_page: int = 10,
        filters: Optional[Dict] = None
    ) -> Tuple[List[Offer], int]:
        """List offers with filters."""
        query = self.db.query(OfferModel)

        if filters:
            if 'route_id' in filters:
                query = query.filter(OfferModel.route_id == filters['route_id'])
            if 'status' in filters:
                query = query.filter(OfferModel.status == filters['status'])
            if 'min_price' in filters:
                query = query.filter(OfferModel.final_price >= filters['min_price'])
            if 'max_price' in filters:
                query = query.filter(OfferModel.final_price <= filters['max_price'])

        # Get total count before pagination
        total = query.count()

        # Apply pagination
        query = query.offset((page - 1) * per_page).limit(per_page)

        # Execute query and convert to entities
        models = query.all()
        offers = [self._to_entity(m) for m in models]

        return offers, total

    def _get_by_id(self, offer_id: UUID) -> Optional[OfferModel]:
        """Get offer by ID."""
        return self.db.query(OfferModel).filter(OfferModel.id == str(offer_id)).first()

    def _get_offer(self, offer_id: UUID) -> Optional[OfferModel]:
        """Get offer by ID."""
        return self.db.query(OfferModel).filter(OfferModel.id == str(offer_id)).first()

    def _to_entity(self, model: OfferModel) -> Offer:
        """Convert model to entity."""
        # Ensure all datetime fields have timezone info
        valid_until = model.valid_until.replace(tzinfo=timezone.utc) if model.valid_until else None
        created_at = model.created_at.replace(tzinfo=timezone.utc) if model.created_at else None
        modified_at = model.modified_at.replace(tzinfo=timezone.utc) if model.modified_at else None

        return Offer(
            id=UUID(model.id),
            route_id=UUID(model.route_id),
            cost_id=UUID(model.cost_history_id) if model.cost_history_id else None,
            total_cost=Decimal(str(model.total_cost)).quantize(Decimal('0.01')),
            margin=Decimal(str(model.margin)).quantize(Decimal('0.0001')),
            final_price=Decimal(str(model.final_price)).quantize(Decimal('0.01')),
            fun_fact=model.fun_fact,
            status=OfferStatus(model.status),
            is_active=model.is_active,
            valid_until=valid_until,
            version=model.version,
            metadata=model.extra_data or {},
            created_at=created_at,
            modified_at=modified_at
        )

    def _to_history_entity(self, model: OfferHistoryModel) -> OfferHistory:
        """Convert history model to domain entity."""
        if not model:
            return None
            
        # Ensure datetime fields have timezone info
        changed_at = model.changed_at.replace(tzinfo=timezone.utc) if model.changed_at else None

        return OfferHistory(
            id=UUID(model.id),
            offer_id=UUID(model.offer_id),
            version=model.version,
            status=OfferStatus(model.status),
            margin=Decimal(str(model.margin)).quantize(Decimal('0.0001')),
            final_price=Decimal(str(model.final_price)).quantize(Decimal('0.01')),
            fun_fact=model.fun_fact,
            metadata=model.extra_data or {},
            changed_at=changed_at,
            changed_by=model.changed_by,
            change_reason=model.change_reason
        )

    def _create_history_entry(
        self,
        offer_id: UUID,
        version: str,
        status: str,
        margin: float,
        final_price: float,
        fun_fact: str,
        metadata: Dict,
        reason: str
    ) -> OfferHistoryModel:
        """Create a history entry."""
        # Ensure metadata is JSON serializable
        safe_metadata = {}
        if metadata and not isinstance(metadata, MetaData):  # Skip if it's a SQLAlchemy MetaData
            for key, value in metadata.items():
                if isinstance(value, (str, int, float, bool, list, dict)):
                    safe_metadata[key] = value

        return OfferHistoryModel(
            id=str(uuid4()),
            offer_id=str(offer_id),
            version=version,
            status=status,
            margin=margin,
            final_price=final_price,
            fun_fact=fun_fact,
            extra_data=safe_metadata,
            changed_at=datetime.now(timezone.utc),
            changed_by="system",
            change_reason=reason
        )

    def _increment_version(self, current_version: str) -> str:
        """Increment version number with fixed precision."""
        version_num = float(current_version)
        return f"{version_num + 0.1:.1f}"
