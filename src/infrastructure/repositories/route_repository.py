"""Route repository implementation."""
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import and_, cast, Float, func, JSON, or_
from sqlalchemy.orm import Session

from src.domain.entities import Route as RouteEntity
from src.domain.value_objects import EmptyDriving, Location, RouteMetadata
from src.infrastructure.models import Route as RouteModel
from src.infrastructure.repositories.base import Repository


class RouteRepository(Repository[RouteEntity]):
    """Repository for managing route entities."""

    def create(self, entity: RouteEntity) -> RouteEntity:
        """Create a new route."""
        db_route = RouteModel(
            id=str(entity.id),
            origin=entity.origin.model_dump(),
            destination=entity.destination.model_dump(),
            pickup_time=entity.pickup_time.astimezone(timezone.utc),
            delivery_time=entity.delivery_time.astimezone(timezone.utc),
            transport_type=entity.transport_type,
            cargo_id=entity.cargo_id,
            distance_km=entity.distance_km,
            duration_hours=entity.duration_hours,
            empty_driving=entity.empty_driving.model_dump() if entity.empty_driving else None,
            is_feasible=entity.is_feasible,
            extra_data=entity.metadata.model_dump() if entity.metadata else None,
        )
        self.db.add(db_route)
        self.db.commit()
        self.db.refresh(db_route)
        return self._to_entity(db_route)

    def get(self, id: str) -> Optional[RouteEntity]:
        """Get route by ID."""
        db_route = self.db.query(RouteModel).filter(RouteModel.id == id).first()
        return self._to_entity(db_route) if db_route else None

    def get_all(self, skip: int = 0, limit: int = 100) -> List[RouteEntity]:
        """Get all routes with pagination."""
        db_routes = self.db.query(RouteModel).offset(skip).limit(limit).all()
        return [self._to_entity(db_route) for db_route in db_routes]

    def update(self, id: str, entity: RouteEntity) -> Optional[RouteEntity]:
        """Update a route."""
        db_route = self.db.query(RouteModel).filter(RouteModel.id == id).first()
        if not db_route:
            return None

        update_data = {
            "origin": entity.origin.model_dump(),
            "destination": entity.destination.model_dump(),
            "pickup_time": entity.pickup_time.astimezone(timezone.utc),
            "delivery_time": entity.delivery_time.astimezone(timezone.utc),
            "transport_type": entity.transport_type,
            "cargo_id": entity.cargo_id,
            "distance_km": entity.distance_km,
            "duration_hours": entity.duration_hours,
            "empty_driving": entity.empty_driving.model_dump() if entity.empty_driving else None,
            "is_feasible": entity.is_feasible,
            "extra_data": entity.metadata.model_dump() if entity.metadata else None,
        }

        for key, value in update_data.items():
            setattr(db_route, key, value)

        self.db.commit()
        self.db.refresh(db_route)
        return self._to_entity(db_route)

    def delete(self, id: str) -> bool:
        """Delete a route."""
        db_route = self.db.query(RouteModel).filter(RouteModel.id == id).first()
        if not db_route:
            return False

        self.db.delete(db_route)
        self.db.commit()
        return True

    def find_by_criteria(
        self,
        origin_location: Optional[Location] = None,
        destination_location: Optional[Location] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        transport_type: Optional[str] = None,
        is_feasible: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[RouteEntity]:
        """Find routes by various criteria."""
        query = self.db.query(RouteModel)

        # Build filter conditions
        conditions = []
        if origin_location:
            # Use SQLite's json_extract function
            conditions.append(
                cast(
                    func.json_extract(RouteModel.origin, "$.latitude"),
                    Float
                ) == origin_location.latitude
            )
            conditions.append(
                cast(
                    func.json_extract(RouteModel.origin, "$.longitude"),
                    Float
                ) == origin_location.longitude
            )
        if destination_location:
            conditions.append(
                cast(
                    func.json_extract(RouteModel.destination, "$.latitude"),
                    Float
                ) == destination_location.latitude
            )
            conditions.append(
                cast(
                    func.json_extract(RouteModel.destination, "$.longitude"),
                    Float
                ) == destination_location.longitude
            )
        if start_date:
            conditions.append(RouteModel.pickup_time >= start_date.astimezone(timezone.utc))
        if end_date:
            conditions.append(RouteModel.delivery_time <= end_date.astimezone(timezone.utc))
        if transport_type:
            conditions.append(RouteModel.transport_type == transport_type)
        if is_feasible is not None:
            conditions.append(RouteModel.is_feasible == is_feasible)

        if conditions:
            query = query.filter(and_(*conditions))

        db_routes = query.offset(skip).limit(limit).all()
        return [self._to_entity(db_route) for db_route in db_routes]

    def _to_entity(self, db_route: RouteModel) -> Optional[RouteEntity]:
        """Convert database model to domain entity."""
        if not db_route:
            return None

        return RouteEntity(
            id=db_route.id,
            origin=Location(**db_route.origin),
            destination=Location(**db_route.destination),
            pickup_time=db_route.pickup_time.replace(tzinfo=timezone.utc),
            delivery_time=db_route.delivery_time.replace(tzinfo=timezone.utc),
            transport_type=db_route.transport_type,
            cargo_id=db_route.cargo_id,
            distance_km=db_route.distance_km,
            duration_hours=db_route.duration_hours,
            empty_driving=EmptyDriving(**db_route.empty_driving) if db_route.empty_driving else None,
            is_feasible=db_route.is_feasible,
            metadata=RouteMetadata(**db_route.extra_data) if db_route.extra_data else None,
        )
