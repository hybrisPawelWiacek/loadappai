"""Route-related models for API request/response handling."""
from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, validator

from src.domain.entities.route import TransportType as DomainTransportType
from .base import ensure_timezone


class TransportType(str, Enum):
    """Valid transport types."""
    TRUCK = "truck"
    VAN = "van"
    TRAILER = "trailer"


class TimelineEventType(str, Enum):
    """Types of timeline events."""
    PICKUP = "pickup"
    DELIVERY = "delivery"
    EMPTY_DRIVING = "empty_driving"


class Location(BaseModel):
    """Location model with address and coordinates."""
    address: str
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    country: str = Field(..., description="ISO country code")


class EmptyDriving(BaseModel):
    """Empty driving details."""
    distance_km: float
    duration_hours: float
    start_location: Optional[Location] = None
    end_location: Optional[Location] = None


class RouteSegment(BaseModel):
    """Route segment details."""
    start_location: Location
    end_location: Location
    distance_km: float
    duration_hours: float
    country: str
    is_empty_driving: bool
    timeline_event: Optional[TimelineEventType] = None


class RouteCreateRequest(BaseModel):
    """Request model for route creation."""
    cargo_id: Optional[str] = None
    origin: Location
    destination: Location
    transport_type: TransportType
    pickup_time: datetime
    delivery_time: datetime
    cargo_specs: Optional["CargoSpecification"] = None

    _ensure_pickup_timezone = validator('pickup_time', allow_reuse=True)(ensure_timezone)
    _ensure_delivery_timezone = validator('delivery_time', allow_reuse=True)(ensure_timezone)

    @validator('delivery_time')
    def validate_delivery_time(cls, v, values):
        """Validate that delivery time is after pickup time."""
        if 'pickup_time' in values and v <= values['pickup_time']:
            raise ValueError('delivery_time must be after pickup_time')
        return v


class RouteResponse(BaseModel):
    """Response model for route operations."""
    id: str
    cargo_id: Optional[str] = None
    origin: Location
    destination: Location
    transport_type: TransportType
    pickup_time: datetime
    delivery_time: datetime
    cargo_specs: Optional["CargoSpecification"] = None
    distance_km: float
    duration_hours: float
    empty_driving: Optional[EmptyDriving] = None
    segments: List[RouteSegment] = Field(default_factory=list)
    is_feasible: bool = True
    feasibility_notes: Optional[str] = None
    created_at: datetime

    _ensure_pickup_timezone = validator('pickup_time', allow_reuse=True)(ensure_timezone)
    _ensure_delivery_timezone = validator('delivery_time', allow_reuse=True)(ensure_timezone)
    _ensure_created_timezone = validator('created_at', allow_reuse=True)(ensure_timezone)

    @classmethod
    def from_domain(cls, route):
        """Convert domain Route model to API response model."""
        # Convert origin and destination to Location models
        origin = Location(
            address=route.origin["address"],
            latitude=route.origin["latitude"],
            longitude=route.origin["longitude"],
            country=route.origin["country"]
        )
        destination = Location(
            address=route.destination["address"],
            latitude=route.destination["latitude"],
            longitude=route.destination["longitude"],
            country=route.destination["country"]
        )

        # Convert empty driving if present
        empty_driving = None
        if route.empty_driving:
            empty_start = None
            if route.empty_driving.origin:
                empty_start = Location(
                    address=route.empty_driving.origin.address,
                    latitude=route.empty_driving.origin.latitude,
                    longitude=route.empty_driving.origin.longitude,
                    country=route.empty_driving.origin.country
                )
            empty_end = None
            if route.empty_driving.destination:
                empty_end = Location(
                    address=route.empty_driving.destination.address,
                    latitude=route.empty_driving.destination.latitude,
                    longitude=route.empty_driving.destination.longitude,
                    country=route.empty_driving.destination.country
                )
            empty_driving = EmptyDriving(
                distance_km=route.empty_driving.distance_km,
                duration_hours=route.empty_driving.duration_hours,
                start_location=empty_start,
                end_location=empty_end
            )

        # Convert cargo specs if present
        cargo_specs = None
        if route.cargo_specs:
            from .cargo import CargoSpecification
            cargo_specs = CargoSpecification(
                cargo_type=route.cargo_specs.cargo_type,
                weight_kg=route.cargo_specs.weight_kg,
                volume_m3=route.cargo_specs.volume_m3,
                temperature_controlled=route.cargo_specs.temperature_controlled,
                required_temp_celsius=route.cargo_specs.required_temp_celsius,
                hazmat_class=route.cargo_specs.hazmat_class
            )

        # Create route segments
        segments = []
        for segment in route.country_segments:
            start_loc = Location(
                address=segment.start_location["address"],
                latitude=segment.start_location["latitude"],
                longitude=segment.start_location["longitude"],
                country=segment.start_location["country"]
            )
            end_loc = Location(
                address=segment.end_location["address"],
                latitude=segment.end_location["latitude"],
                longitude=segment.end_location["longitude"],
                country=segment.end_location["country"]
            )
            segments.append(RouteSegment(
                start_location=start_loc,
                end_location=end_loc,
                distance_km=float(segment.distance),
                duration_hours=float(segment.duration_hours),
                country=segment.country_code,
                is_empty_driving=False,  # Regular segment
                timeline_event=None  # Can be enhanced with timeline events if needed
            ))

        return cls(
            id=str(route.id),
            cargo_id=str(route.cargo_id) if route.cargo_id else None,
            origin=origin,
            destination=destination,
            transport_type=route.transport_type,
            pickup_time=route.pickup_time,
            delivery_time=route.delivery_time,
            cargo_specs=cargo_specs,
            distance_km=route.distance_km,
            duration_hours=route.duration_hours,
            empty_driving=empty_driving,
            segments=segments,
            is_feasible=route.is_feasible,
            created_at=route.created_at
        )
