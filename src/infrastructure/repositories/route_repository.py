"""Route repository implementation."""
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.sql import text, func
from sqlalchemy import cast, Float

from src.domain.entities.route import Route, RouteMetadata, RouteStatus
from src.domain.interfaces.repositories.route_repository import RouteRepository as RouteRepositoryInterface
from src.domain.interfaces.exceptions.repository_errors import EntityNotFoundError
from src.domain.value_objects import Location, EmptyDriving
from src.infrastructure.database import get_db
from src.infrastructure.logging import get_logger
from src.infrastructure.models import Route as RouteModel


class RouteRepository(RouteRepositoryInterface):
    """Repository for managing route entities."""

    def __init__(self):
        """Initialize repository."""
        self.db = get_db()

    def create(self, entity: Route) -> Route:
        """Create a new route."""
        db_route = RouteModel(
            id=str(entity.id),
            origin=entity.origin,  
            destination=entity.destination,  
            pickup_time=entity.pickup_time.astimezone(timezone.utc),
            delivery_time=entity.delivery_time.astimezone(timezone.utc),
            transport_type=entity.transport_type,
            cargo_id=str(entity.cargo_id) if entity.cargo_id else None,
            distance_km=entity.distance_km,
            duration_hours=entity.duration_hours,
            empty_driving=entity.empty_driving.model_dump() if entity.empty_driving else None,
            is_feasible=entity.is_feasible,
            status=entity.status,
            is_active=entity.is_active,
            extra_data={
                "version": entity.metadata.version,
                "tags": entity.metadata.tags,
                "notes": entity.metadata.notes
            } if entity.metadata else {}
        )
        
        self.db.add(db_route)
        self.db.commit()
        self.db.refresh(db_route)
        
        return self._to_entity(db_route)

    def get(self, id: UUID) -> Optional[Route]:
        """Get route by ID."""
        db_route = self.db.query(RouteModel).filter(RouteModel.id == str(id)).first()
        return self._to_entity(db_route) if db_route else None

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Route]:
        """Get all routes with pagination."""
        db_routes = self.db.query(RouteModel).offset(skip).limit(limit).all()
        return [self._to_entity(db_route) for db_route in db_routes]

    def update(self, id: UUID, entity: Route) -> Optional[Route]:
        """Update a route."""
        db_route = self.db.query(RouteModel).filter(RouteModel.id == str(id)).first()
        if not db_route:
            return None

        update_data = {
            "origin": entity.origin,  
            "destination": entity.destination,  
            "pickup_time": entity.pickup_time.astimezone(timezone.utc),
            "delivery_time": entity.delivery_time.astimezone(timezone.utc),
            "transport_type": entity.transport_type,
            "cargo_id": str(entity.cargo_id) if entity.cargo_id else None,
            "distance_km": entity.distance_km,
            "duration_hours": entity.duration_hours,
            "empty_driving": entity.empty_driving.model_dump() if entity.empty_driving else None,
            "is_feasible": entity.is_feasible,
            "status": entity.status,
            "is_active": entity.is_active,
            "extra_data": {
                "version": entity.metadata.version,
                "tags": entity.metadata.tags,
                "notes": entity.metadata.notes
            } if entity.metadata else {}
        }

        for key, value in update_data.items():
            setattr(db_route, key, value)

        self.db.commit()
        self.db.refresh(db_route)
        return self._to_entity(db_route)

    def delete(self, id: UUID) -> bool:
        """Delete a route."""
        db_route = self.db.query(RouteModel).filter(RouteModel.id == str(id)).first()
        if not db_route:
            return False

        self.db.delete(db_route)
        self.db.commit()
        return True

    def get_by_id(self, route_id: UUID) -> Optional[Route]:
        """Get route by ID."""
        route = self.db.query(RouteModel).filter(RouteModel.id == str(route_id)).first()
        if route is None:
            return None
        return self._to_entity(route)

    def find_by_criteria(
        self,
        origin_location: Optional[Location] = None,
        destination_location: Optional[Location] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        transport_type: Optional[str] = None,
        is_feasible: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Route]:
        """Find routes by various criteria."""
        query = self.db.query(RouteModel)

        # Apply filters
        if origin_location:
            query = query.filter(
                cast(RouteModel.origin['latitude'], Float) == origin_location.latitude,
                cast(RouteModel.origin['longitude'], Float) == origin_location.longitude
            )

        if destination_location:
            query = query.filter(
                cast(RouteModel.destination['latitude'], Float) == destination_location.latitude,
                cast(RouteModel.destination['longitude'], Float) == destination_location.longitude
            )

        if start_date:
            query = query.filter(RouteModel.pickup_time >= start_date)

        if end_date:
            query = query.filter(RouteModel.delivery_time <= end_date)

        if transport_type:
            query = query.filter(RouteModel.transport_type == transport_type)

        if is_feasible is not None:
            query = query.filter(RouteModel.is_feasible == is_feasible)

        # Apply pagination
        routes = query.offset(skip).limit(limit).all()
        return [self._to_entity(route) for route in routes]

    def find_routes(
        self,
        origin: Optional[Location] = None,
        destination: Optional[Location] = None,
        vehicle_type: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        per_page: int = 10
    ) -> List[Route]:
        """Find routes matching criteria."""
        query = self.db.query(RouteModel)
        skip = (page - 1) * per_page

        # Apply filters
        if origin:
            query = query.filter(
                cast(RouteModel.origin['latitude'], Float) == origin.latitude,
                cast(RouteModel.origin['longitude'], Float) == origin.longitude
            )

        if destination:
            query = query.filter(
                cast(RouteModel.destination['latitude'], Float) == destination.latitude,
                cast(RouteModel.destination['longitude'], Float) == destination.longitude
            )

        if vehicle_type:
            query = query.filter(RouteModel.transport_type == vehicle_type)

        if status:
            query = query.filter(RouteModel.status == status)

        # Apply pagination
        routes = query.offset(skip).limit(per_page).all()
        return [self._to_entity(route) for route in routes]

    def get_route_history(self, route_id: UUID) -> List[Dict]:
        """Get history of route changes."""
        # For now, we don't track history
        # This would require a separate RouteHistory table
        return []

    def get_active_routes(self, page: int = 1, per_page: int = 10) -> List[Route]:
        """Get currently active routes."""
        skip = (page - 1) * per_page
        query = self.db.query(RouteModel).filter(RouteModel.is_active == True)
        routes = query.offset(skip).limit(per_page).all()
        return [self._to_entity(route) for route in routes]

    def update_route_status(self, route_id: UUID, status: str, reason: Optional[str] = None) -> Optional[Route]:
        """Update route status."""
        db_route = self.db.query(RouteModel).filter(RouteModel.id == str(route_id)).first()
        if not db_route:
            raise EntityNotFoundError(f"Route {route_id} not found")

        db_route.status = status
        # In a real implementation, we would also store the reason in a history table
        
        self.db.commit()
        self.db.refresh(db_route)
        return self._to_entity(db_route)

    def get_route_metadata(self, route_id: UUID) -> Optional[Dict]:
        """Get route metadata."""
        db_route = self.db.query(RouteModel).filter(RouteModel.id == str(route_id)).first()
        if not db_route:
            raise EntityNotFoundError(f"Route {route_id} not found")
        
        return db_route.extra_data or {}

    def count(self) -> int:
        """Get total count of routes."""
        return self.db.query(func.count(RouteModel.id)).scalar()

    def _to_entity(self, model: RouteModel) -> Route:
        """Convert database model to domain entity."""
        if not model:
            return None

        # Create EmptyDriving if present
        empty_driving = None
        if model.empty_driving:
            origin_data = model.empty_driving.get("origin", {})
            empty_driving = EmptyDriving(
                distance_km=model.empty_driving.get("distance_km", 0),
                duration_hours=model.empty_driving.get("duration_hours", 0),
                origin=Location(**origin_data)
            )
        
        # Create RouteMetadata if present
        metadata = None
        if model.extra_data:
            metadata = RouteMetadata(
                version=model.extra_data.get("version", ""),
                tags=model.extra_data.get("tags", []),
                notes=model.extra_data.get("notes", "")
            )
        
        return Route(
            id=UUID(model.id),
            origin=model.origin,
            destination=model.destination,
            pickup_time=model.pickup_time,
            delivery_time=model.delivery_time,
            transport_type=model.transport_type,
            cargo_id=UUID(model.cargo_id) if model.cargo_id else None,
            distance_km=model.distance_km,
            duration_hours=model.duration_hours,
            empty_driving=empty_driving,
            is_feasible=model.is_feasible,
            status=model.status,
            is_active=model.is_active,
            metadata=metadata
        )
