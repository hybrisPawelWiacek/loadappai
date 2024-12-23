"""Value objects for the domain layer."""
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Optional, List

from pydantic import BaseModel, Field, confloat, constr, field_validator
from pydantic import computed_field, ValidationInfo


class Location(BaseModel):
    """Location value object with address and coordinates."""

    address: str = Field(..., description="Full address of the location")
    latitude: confloat(ge=-90, le=90) = Field(..., description="Latitude in decimal degrees")
    longitude: confloat(ge=-180, le=180) = Field(..., description="Longitude in decimal degrees")
    country: str = Field(default="Unknown")

    @field_validator("latitude")
    def validate_latitude(cls, v: float) -> float:
        """Validate latitude."""
        if not -90 <= v <= 90:
            raise ValueError("Latitude must be between -90 and 90 degrees")
        return v

    @field_validator("longitude")
    def validate_longitude(cls, v: float) -> float:
        """Validate longitude."""
        if not -180 <= v <= 180:
            raise ValueError("Longitude must be between -180 and 180 degrees")
        return v

    class Config:
        """Pydantic model configuration."""

        frozen = True


class RouteMetadata(BaseModel):
    """Metadata for route entities with extension points."""

    weather_data: Optional[Dict] = Field(None, description="Weather conditions along the route")
    traffic_data: Optional[Dict] = Field(None, description="Traffic conditions and incidents")
    compliance_data: Optional[Dict] = Field(None, description="Regulatory compliance information")
    optimization_data: Optional[Dict] = Field(None, description="Route optimization metadata")

    class Config:
        """Pydantic model configuration."""

        frozen = True


class CountrySegment(BaseModel):
    """Country segment of a route with distance and duration."""

    country_code: str = Field(..., description="ISO country code")
    distance: Decimal = Field(..., description="Distance in kilometers", gt=0)
    duration_hours: Decimal = Field(..., description="Duration in hours", gt=0)
    toll_rates: Dict[str, Decimal] = Field(
        default_factory=lambda: {"highway": Decimal("0.15"), "national": Decimal("0.10")}
    )

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

    class Config:
        """Pydantic model configuration."""
        frozen = True


class CostBreakdown(BaseModel):
    """Cost breakdown for a route."""

    fuel_costs: Dict[str, Decimal] = Field(default_factory=dict)
    toll_costs: Dict[str, Decimal] = Field(default_factory=dict)
    maintenance_costs: Dict[str, Decimal] = Field(default_factory=dict)
    driver_costs: Dict[str, Decimal] = Field(default_factory=dict)
    rest_period_costs: Decimal = Field(default=Decimal("0"))
    loading_unloading_costs: Decimal = Field(default=Decimal("0"))
    empty_driving_costs: Dict[str, Dict[str, Decimal]] = Field(default_factory=dict)
    cargo_specific_costs: Dict[str, Decimal] = Field(default_factory=dict)
    equipment_costs: Decimal = Field(default=Decimal("0"))
    overheads: Dict[str, Decimal] = Field(default_factory=dict)
    subtotal_distance_based: Decimal = Field(default=Decimal("0"))
    subtotal_time_based: Decimal = Field(default=Decimal("0"))
    subtotal_empty_driving: Decimal = Field(default=Decimal("0"))
    total_cost: Decimal = Field(default=Decimal("0"))
    currency: str = Field(default="EUR")

    @computed_field
    @property
    def total(self) -> Decimal:
        """Alias for total_cost for backward compatibility."""
        return self.total_cost

    @computed_field
    @property
    def fuel_cost(self) -> Decimal:
        """Sum of all fuel costs."""
        return sum(self.fuel_costs.values())

    @computed_field
    @property
    def toll_cost(self) -> Decimal:
        """Sum of all toll costs."""
        return sum(self.toll_costs.values())

    @computed_field
    @property
    def driver_cost(self) -> Decimal:
        """Sum of all driver costs."""
        return sum(self.driver_costs.values())

    class Config:
        """Pydantic model configuration."""
        frozen = False  # Allow modification of fields after creation


class EmptyDriving(BaseModel):
    """Value object representing empty driving segments."""

    distance_km: float = Field(description="Distance in kilometers", gt=0)
    duration_hours: float = Field(description="Duration in hours", gt=0)
    origin: Optional[Location] = Field(None, description="Starting location of empty driving")
    destination: Optional[Location] = Field(None, description="Ending location of empty driving")
    segments: List[CountrySegment] = Field(default_factory=list, description="List of country segments for empty driving")

    class Config:
        """Pydantic model configuration."""
        frozen = True


class RouteSegment(BaseModel):
    """Value object representing a segment of a route."""

    start_location: Location
    end_location: Location
    distance_km: float = Field(gt=0, description="Distance in kilometers")
    duration_hours: float = Field(gt=0, description="Duration in hours")
    country: str = Field(description="Country code for this segment")
    is_empty_driving: bool = Field(default=False, description="Whether this is an empty driving segment")
    timeline_event: Optional[str] = Field(None, description="Type of timeline event (pickup, delivery, rest)")

    class Config:
        """Pydantic model configuration."""
        frozen = True

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


class Currency(BaseModel):
    """Currency value object."""

    code: constr(min_length=3, max_length=3) = Field(..., description="ISO 4217 currency code")
    symbol: str = Field(..., description="Currency symbol")
    exchange_rate: Optional[Decimal] = Field(None, description="Exchange rate to base currency (EUR)")

    class Config:
        """Pydantic model configuration."""

        frozen = True


class DistanceMatrix(BaseModel):
    """Value object representing a distance matrix between locations."""

    origins: List[Location]
    destinations: List[Location]
    distances: List[List[float]] = Field(description="Matrix of distances in kilometers")
    durations: List[List[float]] = Field(description="Matrix of durations in hours")
    countries: List[List[str]] = Field(description="Matrix of country codes for each segment")
    status: str = Field(default="OK")
    error_message: Optional[str] = None

    class Config:
        """Pydantic model configuration."""
        frozen = True

    @field_validator("distances")
    def validate_distances(cls, v: List[List[float]], info: ValidationInfo) -> List[List[float]]:
        """Validate distances matrix dimensions."""
        if not v:
            raise ValueError("Distances matrix cannot be empty")
        n_origins = len(info.data.get("origins", []))
        n_destinations = len(info.data.get("destinations", []))
        if len(v) != n_origins or any(len(row) != n_destinations for row in v):
            raise ValueError(
                f"Distances matrix dimensions must match: {n_origins}x{n_destinations}"
            )
        return v

    @field_validator("durations")
    def validate_durations(cls, v: List[List[float]], info: ValidationInfo) -> List[List[float]]:
        """Validate durations matrix dimensions."""
        if not v:
            raise ValueError("Durations matrix cannot be empty")
        n_origins = len(info.data.get("origins", []))
        n_destinations = len(info.data.get("destinations", []))
        if len(v) != n_origins or any(len(row) != n_destinations for row in v):
            raise ValueError(
                f"Durations matrix dimensions must match: {n_origins}x{n_destinations}"
            )
        return v

    @field_validator("countries")
    def validate_countries(cls, v: List[List[str]], info: ValidationInfo) -> List[List[str]]:
        """Validate countries matrix dimensions."""
        if not v:
            raise ValueError("Countries matrix cannot be empty")
        n_origins = len(info.data.get("origins", []))
        n_destinations = len(info.data.get("destinations", []))
        if len(v) != n_origins or any(len(row) != n_destinations for row in v):
            raise ValueError(
                f"Countries matrix dimensions must match: {n_origins}x{n_destinations}"
            )
        return v

    def get_distance(self, origin_idx: int, destination_idx: int) -> float:
        """Get distance between origin and destination indices."""
        return self.distances[origin_idx][destination_idx]

    def get_duration(self, origin_idx: int, destination_idx: int) -> float:
        """Get duration between origin and destination indices."""
        return self.durations[origin_idx][destination_idx]

    def get_country(self, origin_idx: int, destination_idx: int) -> str:
        """Get country code for route between origin and destination indices."""
        return self.countries[origin_idx][destination_idx]


class Cost(BaseModel):
    """Value object representing a cost component."""

    amount: Decimal = Field(ge=0)
    currency: str = Field(default="EUR")
    description: Optional[str] = None
    category: Optional[str] = None
    metadata: Optional[Dict] = None

    class Config:
        """Pydantic model configuration."""
        frozen = True

    @field_validator("amount")
    def validate_amount(cls, v: Decimal) -> Decimal:
        """Validate amount is non-negative."""
        if v < 0:
            raise ValueError("Amount must be non-negative")
        return v

    @field_validator("currency")
    def validate_currency(cls, v: str) -> str:
        """Validate currency code."""
        if len(v) != 3:
            raise ValueError("Currency code must be 3 characters")
        return v.upper()


class RouteOptimizationResult(BaseModel):
    """Value object representing the result of route optimization."""

    optimized_route: List[Location]
    total_distance_km: float = Field(gt=0)
    total_duration_hours: float = Field(gt=0)
    segments: List[RouteSegment]
    empty_driving: Optional[EmptyDriving] = None
    metadata: Optional[Dict] = None

    class Config:
        """Pydantic model configuration."""
        frozen = True

    @field_validator("total_distance_km", "total_duration_hours")
    def validate_positive(cls, v: float) -> float:
        """Validate that values are positive."""
        if v <= 0:
            raise ValueError("Value must be positive")
        return v


class OfferGenerationResult(BaseModel):
    """Value object representing the result of offer generation."""

    offer: "Offer"
    route: "Route"
    cost_breakdown: CostBreakdown
    fun_fact: Optional[str] = None
    metadata: Optional[Dict] = None

    class Config:
        """Pydantic model configuration."""
        frozen = True
