"""Route-related domain entities."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, ValidationInfo
from pytz import UTC

from src.domain.value_objects import (
    Location,
    CountrySegment,
    EmptyDriving,
    RouteMetadata,
    RouteSegment
)


def utc_now() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(UTC)


class TransportType(str, Enum):
    """Transport type enum."""
    TRUCK = "truck"
    VAN = "van"
    TRAILER = "trailer"
    FLATBED_TRUCK = "flatbed_truck"


class RouteStatus(str, Enum):
    """Route status enum."""
    DRAFT = "draft"
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TimelineEventType(str, Enum):
    """Timeline event type enum."""
    PICKUP = "pickup"
    DELIVERY = "delivery"
    REST = "rest"
    EMPTY_DRIVING = "empty_driving"
    LOADED_DRIVING = "loaded_driving"


class TimeWindow(BaseModel):
    """Time window constraints for route segments."""
    location: Location
    earliest: datetime
    latest: datetime
    operation_type: str = Field(description="pickup, delivery, or rest")
    duration_hours: float = Field(gt=0)

    @field_validator("latest")
    def latest_after_earliest(cls, value: datetime, info: ValidationInfo) -> datetime:
        """Validate that latest time is after earliest time."""
        if "earliest" in info.data and value <= info.data["earliest"]:
            raise ValueError("Latest time must be after earliest time")
        return value


class ExtensibleEntity(BaseModel):
    """Base class for entities with version tracking and metadata."""
    version: str = "1.0"
    metadata: Optional[Dict] = None
    created_at: datetime = Field(default_factory=utc_now)
    modified_at: datetime = Field(default_factory=utc_now)
    created_by: Optional[str] = None
    modified_by: Optional[str] = None


class Route(ExtensibleEntity):
    """Route entity representing a transport route with empty driving."""
    id: UUID = Field(default_factory=uuid4)
    cargo_id: Optional[UUID] = None
    origin: Dict = Field(description="Location dictionary")
    destination: Dict = Field(description="Location dictionary")
    pickup_time: datetime
    delivery_time: datetime
    transport_type: str = Field(default=TransportType.TRUCK.value)
    distance_km: float = Field(gt=0)
    duration_hours: float = Field(gt=0)
    segments: List[RouteSegment] = Field(default_factory=list)
    country_segments: List[CountrySegment] = Field(default_factory=list)
    empty_driving: Optional[EmptyDriving] = None
    time_windows: List[TimeWindow] = Field(default_factory=list)
    metadata: RouteMetadata = Field(default_factory=RouteMetadata)
    is_optimized: bool = False
    is_active: bool = True
    is_feasible: bool = True
    feasibility_notes: Optional[str] = None
    status: str = Field(default=RouteStatus.DRAFT.value)

    @field_validator("delivery_time")
    def delivery_after_pickup(cls, value: datetime, info: ValidationInfo) -> datetime:
        """Validate that delivery time is after pickup time."""
        if "pickup_time" in info.data and value <= info.data["pickup_time"]:
            raise ValueError("Delivery time must be after pickup time")
        return value

    @field_validator("transport_type")
    def validate_transport_type(cls, value: str) -> str:
        """Validate transport type."""
        try:
            TransportType(value)
            return value
        except ValueError:
            raise ValueError(f"Invalid transport type: {value}")

    @field_validator("status")
    def validate_status(cls, value: str) -> str:
        """Validate route status."""
        try:
            RouteStatus(value)
            return value
        except ValueError:
            raise ValueError(f"Invalid route status: {value}")

    @field_validator("distance_km", "duration_hours")
    def validate_positive(cls, value: float) -> float:
        """Validate that numeric values are positive."""
        if value <= 0:
            raise ValueError("Value must be positive")
        return value

    def total_distance(self) -> float:
        """Calculate total distance including empty driving."""
        total = self.distance_km
        if self.empty_driving:
            total += self.empty_driving.distance_km
        return total

    def total_duration(self) -> float:
        """Calculate total duration including empty driving."""
        total = self.duration_hours
        if self.empty_driving:
            total += self.empty_driving.duration_hours
        return total

    def get_country_distance(self, country_code: str) -> float:
        """Get total distance for a specific country."""
        total = sum(
            segment.distance_km
            for segment in self.country_segments
            if segment.country_code == country_code
        )
        if self.empty_driving and self.empty_driving.segments:
            total += sum(
                segment.distance_km
                for segment in self.empty_driving.segments
                if segment.country_code == country_code
            )
        return total

    def get_country_duration(self, country_code: str) -> float:
        """Get total duration for a specific country."""
        total = sum(
            segment.duration_hours
            for segment in self.country_segments
            if segment.country_code == country_code
        )
        if self.empty_driving and self.empty_driving.segments:
            total += sum(
                segment.duration_hours
                for segment in self.empty_driving.segments
                if segment.country_code == country_code
            )
        return total
