"""Offer repository implementation."""
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
import uuid

from sqlalchemy import and_, cast, Float, func
from sqlalchemy.orm import Session

from src.domain.entities import Offer as OfferEntity
from src.infrastructure.models import Offer as OfferModel
from src.infrastructure.repositories.base import Repository


class OfferRepository(Repository[OfferEntity]):
    """Repository for managing offer entities."""

    def create(self, entity: OfferEntity) -> OfferEntity:
        """Create a new offer."""
        db_offer = OfferModel(
            id=str(entity.id),
            route_id=str(entity.route_id),
            total_cost=float(entity.final_price),  # Using final_price as total_cost
            margin=float(entity.margin),
            final_price=float(entity.final_price),
            fun_fact=entity.fun_fact,
            created_at=entity.created_at.astimezone(timezone.utc),
            extra_data=entity.metadata if entity.metadata else None,
        )
        self.db.add(db_offer)
        self.db.commit()
        self.db.refresh(db_offer)
        return self._to_entity(db_offer)

    def get(self, id: str) -> Optional[OfferEntity]:
        """Get offer by ID."""
        db_offer = self.db.query(OfferModel).filter(OfferModel.id == id).first()
        return self._to_entity(db_offer) if db_offer else None

    def get_all(self, skip: int = 0, limit: int = 100) -> List[OfferEntity]:
        """Get all offers with pagination."""
        db_offers = self.db.query(OfferModel).offset(skip).limit(limit).all()
        return [self._to_entity(db_offer) for db_offer in db_offers]

    def update(self, id: str, entity: OfferEntity) -> Optional[OfferEntity]:
        """Update an offer."""
        db_offer = self.db.query(OfferModel).filter(OfferModel.id == id).first()
        if not db_offer:
            return None

        update_data = {
            "route_id": str(entity.route_id),
            "total_cost": float(entity.final_price),  # Using final_price as total_cost
            "margin": float(entity.margin),
            "final_price": float(entity.final_price),
            "fun_fact": entity.fun_fact,
            "extra_data": entity.metadata if entity.metadata else None,
        }

        for key, value in update_data.items():
            setattr(db_offer, key, value)

        self.db.commit()
        self.db.refresh(db_offer)
        return self._to_entity(db_offer)

    def delete(self, id: str) -> bool:
        """Delete an offer."""
        db_offer = self.db.query(OfferModel).filter(OfferModel.id == id).first()
        if not db_offer:
            return False

        self.db.delete(db_offer)
        self.db.commit()
        return True

    def find_by_criteria(
        self,
        route_id: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[OfferEntity]:
        """Find offers by various criteria."""
        query = self.db.query(OfferModel)

        # Build filter conditions
        conditions = []
        if route_id:
            conditions.append(OfferModel.route_id == route_id)
        if min_price is not None:
            conditions.append(OfferModel.final_price >= min_price)
        if max_price is not None:
            conditions.append(OfferModel.final_price <= max_price)
        if start_date:
            conditions.append(OfferModel.created_at >= start_date.astimezone(timezone.utc))
        if end_date:
            conditions.append(OfferModel.created_at <= end_date.astimezone(timezone.utc))

        if conditions:
            query = query.filter(and_(*conditions))

        db_offers = query.offset(skip).limit(limit).all()
        return [self._to_entity(db_offer) for db_offer in db_offers]

    def _to_entity(self, db_offer: OfferModel) -> Optional[OfferEntity]:
        """Convert database model to domain entity."""
        if not db_offer:
            return None

        return OfferEntity(
            id=db_offer.id,
            route_id=db_offer.route_id,
            cost_id=str(uuid.uuid4()),  # Generate a new UUID for cost_id
            margin=Decimal(str(db_offer.margin)),
            final_price=Decimal(str(db_offer.final_price)),
            fun_fact=db_offer.fun_fact,
            created_at=db_offer.created_at.replace(tzinfo=timezone.utc),
            metadata=db_offer.extra_data,
        )
