"""Route-related value objects."""

from decimal import Decimal
from typing import Dict, List, Optional
from pydantic import Field, field_validator

from .common import BaseValueObject
from .location import Location


class CountrySegment(BaseValueObject):
    """Country segment of a route with distance and duration."""

    country_code: str = Field(..., description="ISO country code", min_length=1)
    distance: Decimal = Field(..., description="Distance in kilometers", gt=0)
    duration_hours: Decimal = Field(..., description="Duration in hours", gt=0)
    toll_rates: Dict[str, Decimal] = Field(
        default_factory=lambda: {"highway": Decimal("0.15"), "national": Decimal("0.10")}
    )

    @field_validator("country_code")
    def validate_country_code(cls, v: str) -> str:
        """Validate country code."""
        if not v.strip():
            raise ValueError("Country code cannot be empty")
        return v.upper()

    @field_validator("distance")
    def validate_distance(cls, v: Decimal) -> Decimal:
        """Validate distance."""
        if v <= 0:
            raise ValueError("Distance must be positive")
        return v

    @field_validator("duration_hours")
    def validate_duration(cls, v: Decimal) -> Decimal:
        """Validate duration."""
        if v <= 0:
            raise ValueError("Duration must be positive")
        return v

    @field_validator("toll_rates")
    def validate_toll_rates(cls, v: Dict[str, Decimal]) -> Dict[str, Decimal]:
        """Validate toll rates."""
        for rate_type, rate in v.items():
            if rate <= 0:
                raise ValueError(f"Toll rate for {rate_type} must be positive")
        return v


class RouteMetadata(BaseValueObject):
    """Metadata for route entities with extension points."""

    version: str = Field(default="1.0", description="Version of the route metadata")
    tags: List[str] = Field(default_factory=list, description="Tags for categorizing the route")
    notes: Optional[str] = Field(None, description="Additional notes about the route")
    weather_data: Optional[Dict] = Field(
        None, description="Weather conditions along the route"
    )
    traffic_data: Optional[Dict] = Field(
        None, description="Traffic conditions and incidents"
    )
    compliance_data: Optional[Dict] = Field(
        None, description="Regulatory compliance information"
    )
    optimization_data: Optional[Dict] = Field(
        None, description="Route optimization metadata"
    )


class RouteSegment(BaseValueObject):
    """Value object representing a segment of a route."""

    start_location: Location
    end_location: Location
    distance_km: float = Field(gt=0, description="Distance in kilometers")
    duration_hours: float = Field(gt=0, description="Duration in hours")
    country: str = Field(description="Country code for this segment")
    is_empty_driving: bool = Field(
        default=False, description="Whether this is an empty driving segment"
    )
    timeline_event: Optional[str] = Field(
        None, description="Type of timeline event (pickup, delivery, rest)"
    )

    @field_validator("duration_hours")
    def validate_duration(cls, v: float) -> float:
        """Validate duration is positive."""
        if v <= 0:
            raise ValueError("Duration must be positive")
        return v

    @field_validator("distance_km")
    def validate_distance(cls, v: float) -> float:
        """Validate distance is positive."""
        if v <= 0:
            raise ValueError("Distance must be positive")
        return v


class EmptyDriving(BaseValueObject):
    """Value object representing empty driving segments."""

    distance_km: float = Field(description="Distance in kilometers", gt=0)
    duration_hours: float = Field(description="Duration in hours", gt=0)
    origin: Optional[Location] = Field(
        None, description="Starting location of empty driving"
    )
    destination: Optional[Location] = Field(
        None, description="Ending location of empty driving"
    )
    segments: List[CountrySegment] = Field(
        default_factory=list,
        description="List of segments for empty driving"
    )


class RouteOptimizationResult(BaseValueObject):
    """Value object representing the result of route optimization."""

    optimized_route: List[Location]
    total_distance_km: float = Field(gt=0)
    total_duration_hours: float = Field(gt=0)
    segments: List[RouteSegment]
    empty_driving: Optional[EmptyDriving] = None

    @field_validator("total_distance_km", "total_duration_hours")
    def validate_positive(cls, v: float) -> float:
        """Validate that values are positive."""
        if v <= 0:
            raise ValueError("Value must be positive")
        return v
