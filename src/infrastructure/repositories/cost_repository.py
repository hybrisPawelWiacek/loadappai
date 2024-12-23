"""Cost repository implementation."""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from src.domain.entities import Cost as CostEntity
from src.infrastructure.database import Database
from src.infrastructure.models import CostHistory as CostModel
from src.infrastructure.repositories.base import Repository


class CostRepository(Repository[CostEntity]):
    """Repository for managing cost entities."""

    def __init__(self, db: Database):
        """Initialize repository with database connection."""
        self.db = db

    def create(self, entity: CostEntity) -> CostEntity:
        """Create a new cost entity."""
        with self.db.session() as session:
            model = CostModel(
                id=str(entity.id),
                route_id=str(entity.route_id),
                calculation_date=entity.calculated_at,
                total_cost=float(entity.total()),
                currency=entity.metadata.get("currency", "EUR") if entity.metadata else "EUR",
                calculation_method=entity.calculation_method,
                version=entity.version,
                is_final=entity.is_final,
                cost_components=entity.breakdown,
                settings_snapshot=entity.metadata or {}
            )
            session.add(model)
            session.commit()
            session.refresh(model)
            return self._to_entity(model)

    def get(self, id: str) -> Optional[CostEntity]:
        """Get cost entity by ID."""
        with self.db.session() as session:
            model = session.query(CostModel).filter_by(id=id).first()
            return self._to_entity(model) if model else None

    def get_all(self, skip: int = 0, limit: int = 100) -> List[CostEntity]:
        """Get all cost entities with pagination."""
        with self.db.session() as session:
            models = session.query(CostModel).offset(skip).limit(limit).all()
            return [self._to_entity(model) for model in models]

    def update(self, id: str, entity: CostEntity) -> Optional[CostEntity]:
        """Update a cost entity."""
        with self.db.session() as session:
            model = session.query(CostModel).filter_by(id=id).first()
            if not model:
                return None
            
            # Update fields
            model.total_cost = float(entity.total())
            model.currency = entity.metadata.get("currency", "EUR") if entity.metadata else "EUR"
            model.calculation_method = entity.calculation_method
            model.version = entity.version
            model.is_final = entity.is_final
            model.cost_components = entity.breakdown
            model.settings_snapshot = entity.metadata or {}
            
            session.add(model)
            session.commit()
            session.refresh(model)
            return self._to_entity(model)

    def delete(self, id: str) -> bool:
        """Delete a cost entity."""
        with self.db.session() as session:
            model = session.query(CostModel).filter_by(id=id).first()
            if not model:
                return False
            session.delete(model)
            session.commit()
            return True

    def get_latest_for_route(self, route_id: str) -> Optional[CostEntity]:
        """Get the latest cost calculation for a route."""
        with self.db.session() as session:
            model = (
                session.query(CostModel)
                .filter_by(route_id=route_id)
                .order_by(CostModel.calculation_date.desc())
                .first()
            )
            return self._to_entity(model) if model else None

    def get_all_for_route(self, route_id: str) -> List[CostEntity]:
        """Get all cost calculations for a route."""
        with self.db.session() as session:
            models = (
                session.query(CostModel)
                .filter_by(route_id=route_id)
                .order_by(CostModel.calculation_date.desc())
                .all()
            )
            return [self._to_entity(model) for model in models]

    def _to_entity(self, model: CostModel) -> CostEntity:
        """Convert database model to domain entity."""
        if not model:
            return None
        
        return CostEntity(
            id=UUID(model.id),
            route_id=UUID(model.route_id),
            breakdown=model.cost_components,
            calculated_at=model.calculation_date,
            metadata=model.settings_snapshot,
            version=model.version,
            is_final=model.is_final,
            calculation_method=model.calculation_method
        )
