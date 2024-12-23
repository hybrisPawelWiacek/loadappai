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
            origin=entity.origin,  
            destination=entity.destination,  
            pickup_time=entity.pickup_time.astimezone(timezone.utc),
            delivery_time=entity.delivery_time.astimezone(timezone.utc),
            transport_type=entity.transport_type,
            cargo_id=entity.cargo_id,
            distance_km=entity.distance_km,
            duration_hours=entity.duration_hours,
            empty_driving=entity.empty_driving.model_dump() if entity.empty_driving else None,
            is_feasible=entity.is_feasible,
            extra_data=entity.metadata.model_dump() if entity.metadata else None
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
            "origin": entity.origin,  
            "destination": entity.destination,  
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

    def get_by_id(self, route_id: str) -> Optional[RouteEntity]:
        """Get route by ID."""
        route = self.db.query(RouteModel).filter(RouteModel.id == route_id).first()
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
    ) -> List[RouteEntity]:
        """Find routes by various criteria."""
        query = self.db.query(RouteModel)

        # Apply filters
        if origin_location:
            query = query.filter(
                cast(RouteModel.origin[('coordinates', 'lat')], Float) == origin_location.coordinates.lat,
                cast(RouteModel.origin[('coordinates', 'lng')], Float) == origin_location.coordinates.lng
            )

        if destination_location:
            query = query.filter(
                cast(RouteModel.destination[('coordinates', 'lat')], Float) == destination_location.coordinates.lat,
                cast(RouteModel.destination[('coordinates', 'lng')], Float) == destination_location.coordinates.lng
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

    def _to_entity(self, model: RouteModel) -> RouteEntity:
        """Convert database model to domain entity."""
        if not model:
            return None

        # Create Location objects from dictionaries
        origin = Location(**model.origin)
        destination = Location(**model.destination)
        
        # Create EmptyDriving if present
        empty_driving = None
        if model.empty_driving:
            empty_driving = EmptyDriving(**model.empty_driving)
        
        # Create RouteMetadata if present
        metadata = None
        if model.extra_data:
            metadata = RouteMetadata(**model.extra_data)
        
        return RouteEntity(
            id=model.id,
            origin=origin.dict(),  # Convert back to dict
            destination=destination.dict(),  # Convert back to dict
            pickup_time=model.pickup_time,
            delivery_time=model.delivery_time,
            transport_type=model.transport_type,
            cargo_id=model.cargo_id,
            distance_km=model.distance_km,
            duration_hours=model.duration_hours,
            empty_driving=empty_driving,
            is_feasible=model.is_feasible,
            metadata=metadata
        )
