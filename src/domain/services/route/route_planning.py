"""Route planning service implementation.

This module implements the route planning service interface.
It provides functionality for:
- Creating and validating routes
- Calculating distances and durations
- Managing empty driving
- Handling route metadata
"""
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from src.domain.entities.route import Route, RouteStatus, TransportType
from src.domain.interfaces.services.location_service import LocationService
from src.domain.services.common.base import BaseService
from src.domain.value_objects import (
    Location, EmptyDriving, RouteMetadata, RouteSegment
)

class RoutePlanningService(BaseService):
    """Service for planning and validating transport routes.
    
    This service is responsible for:
    - Creating and validating routes
    - Calculating distances and durations
    - Managing empty driving calculations
    - Handling route metadata
    """
    
    def __init__(
        self,
        location_service: LocationService,
        cost_service: Optional['CostCalculationService'] = None
    ):
        """Initialize route planning service.
        
        Args:
            location_service: Service for location operations
            cost_service: Optional service for cost calculations
        """
        super().__init__()
        self.location_service = location_service
        self._cost_service = cost_service
    
    def create_route(
        self,
        origin: Location,
        destination: Location,
        pickup_time: datetime,
        delivery_time: datetime,
        transport_type: Optional[TransportType] = None,
        cargo_id: Optional[UUID] = None,
        metadata: Optional[Dict] = None
    ) -> Route:
        """Create a route with empty driving calculation.
        
        Args:
            origin: Starting location
            destination: Ending location
            pickup_time: Time of pickup
            delivery_time: Time of delivery
            transport_type: Optional type of transport
            cargo_id: Optional ID of cargo
            metadata: Optional route metadata
            
        Returns:
            Created route
            
        Raises:
            ValueError: If inputs are invalid
        """
        self._log_entry(
            "create_route",
            origin=origin,
            destination=destination,
            pickup_time=pickup_time,
            delivery_time=delivery_time,
            transport_type=transport_type
        )
        
        try:
            # Validate inputs
            self._validate_required(origin, "origin")
            self._validate_required(destination, "destination")
            self._validate_required(pickup_time, "pickup_time")
            self._validate_required(delivery_time, "delivery_time")
            
            # Calculate main route
            distance = self.location_service.calculate_distance(origin, destination)
            duration = self.location_service.calculate_duration(origin, destination)
            
            # Get country segments
            self.logger.info("Getting country segments")
            country_segments = self.location_service.get_country_segments(
                origin,
                destination
            )
            
            # Calculate empty driving if needed
            empty_driving = None
            if origin != destination:
                self.logger.info("Calculating empty driving")
                empty_distance = self.location_service.calculate_distance(
                    destination,
                    origin
                )
                empty_duration = self.location_service.calculate_duration(
                    destination,
                    origin
                )
                empty_driving = EmptyDriving(
                    distance_km=empty_distance,
                    duration_hours=empty_duration,
                    origin=origin.dict(),
                    destination=destination.dict()
                )
            
            # Create route metadata
            route_metadata = RouteMetadata(
                country_segments=country_segments,
                empty_driving=empty_driving,
                **metadata or {}
            )
            
            # Create route
            route = Route(
                origin=origin.dict(),
                destination=destination.dict(),
                pickup_time=pickup_time,
                delivery_time=delivery_time,
                transport_type=transport_type or TransportType.TRUCK,
                distance_km=distance,
                duration_hours=duration,
                status=RouteStatus.DRAFT,
                metadata=route_metadata.dict(),
                cargo_id=cargo_id
            )
            
            self._log_exit("create_route", route)
            return route
            
        except Exception as e:
            self._log_error("create_route", e)
            raise ValueError(f"Failed to create route: {str(e)}")
    
    def validate_route(self, route: Route) -> bool:
        """Validate route configuration.
        
        Args:
            route: Route to validate
            
        Returns:
            True if route is valid
            
        Raises:
            ValueError: If route is invalid
        """
        self._log_entry("validate_route", route=route)
        
        try:
            # Validate required fields
            self._validate_required(route.origin, "origin")
            self._validate_required(route.destination, "destination")
            self._validate_required(route.pickup_time, "pickup_time")
            self._validate_required(route.delivery_time, "delivery_time")
            
            # Validate times
            if route.pickup_time >= route.delivery_time:
                raise ValueError("Pickup time must be before delivery time")
            
            # Validate distance and duration
            if route.distance_km <= 0:
                raise ValueError("Distance must be positive")
            if route.duration_hours <= 0:
                raise ValueError("Duration must be positive")
            
            # Validate metadata
            if route.metadata:
                if "country_segments" not in route.metadata:
                    raise ValueError("Missing country segments in metadata")
                
                segments = route.metadata["country_segments"]
                if not segments:
                    raise ValueError("Country segments cannot be empty")
                
                # Validate segment chain
                for i in range(len(segments) - 1):
                    if segments[i]["exit_point"] != segments[i + 1]["entry_point"]:
                        raise ValueError("Invalid segment chain")
            
            self._log_exit("validate_route", True)
            return True
            
        except Exception as e:
            self._log_error("validate_route", e)
            return False
    
    def update_route_status(
        self,
        route: Route,
        new_status: RouteStatus,
        reason: Optional[str] = None
    ) -> Route:
        """Update route status.
        
        Args:
            route: Route to update
            new_status: New status
            reason: Optional reason for change
            
        Returns:
            Updated route
            
        Raises:
            ValueError: If status transition is invalid
        """
        self._log_entry(
            "update_route_status",
            route=route,
            new_status=new_status,
            reason=reason
        )
        
        try:
            # Validate status transition
            if not self._is_valid_status_transition(route.status, new_status):
                raise ValueError(
                    f"Invalid status transition from {route.status} to {new_status}"
                )
            
            # Update status
            route.status = new_status
            
            # Add status change to metadata
            if not route.metadata:
                route.metadata = {}
            
            if "status_history" not in route.metadata:
                route.metadata["status_history"] = []
            
            route.metadata["status_history"].append({
                "from_status": route.status,
                "to_status": new_status,
                "timestamp": datetime.utcnow().isoformat(),
                "reason": reason
            })
            
            self._log_exit("update_route_status", route)
            return route
            
        except Exception as e:
            self._log_error("update_route_status", e)
            raise ValueError(f"Failed to update route status: {str(e)}")
    
    def _is_valid_status_transition(
        self,
        current_status: RouteStatus,
        new_status: RouteStatus
    ) -> bool:
        """Check if status transition is valid.
        
        Args:
            current_status: Current route status
            new_status: Proposed new status
            
        Returns:
            True if transition is valid
        """
        # Define valid transitions
        valid_transitions = {
            RouteStatus.DRAFT: {
                RouteStatus.ACTIVE,
                RouteStatus.CANCELLED
            },
            RouteStatus.ACTIVE: {
                RouteStatus.COMPLETED,
                RouteStatus.CANCELLED
            },
            RouteStatus.COMPLETED: set(),  # Terminal state
            RouteStatus.CANCELLED: set()   # Terminal state
        }
        
        return new_status in valid_transitions.get(current_status, set())
