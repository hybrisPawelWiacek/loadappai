"""Domain entities for LoadApp.AI."""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID, uuid4
from pytz import UTC

from pydantic import BaseModel, Field, validator

from src.domain.value_objects import (
    CostBreakdown,
    EmptyDriving,
    Location,
    RouteMetadata,
    CountrySegment
)


def utc_now() -> datetime:
    return datetime.now(UTC)


class Route(BaseModel):
    """Route entity representing a transport route with empty driving."""

    id: UUID = Field(default_factory=uuid4)
    origin: Location
    destination: Location
    pickup_time: datetime
    delivery_time: datetime
    transport_type: str
    cargo_id: Optional[str] = None
    distance_km: float = Field(gt=0)
    duration_hours: float = Field(gt=0)
    empty_driving: EmptyDriving
    is_feasible: bool = True
    created_at: datetime = Field(default_factory=utc_now)
    metadata: Optional[RouteMetadata] = None
    country_segments: List[CountrySegment] = Field(default_factory=list)

    @validator("delivery_time")
    def delivery_after_pickup(cls, v: datetime, values: Dict) -> datetime:
        """Validate that delivery time is after pickup time."""
        if "pickup_time" in values and v <= values["pickup_time"]:
            raise ValueError("delivery_time must be after pickup_time")
        return v

    @property
    def total_distance(self) -> float:
        """Calculate total distance including empty driving."""
        return self.distance_km + self.empty_driving.distance_km

    @property
    def total_duration(self) -> float:
        """Calculate total duration including empty driving."""
        return self.duration_hours + self.empty_driving.duration_hours


class Cost(BaseModel):
    """
    Cost record for a route.
    """
    id: UUID = Field(default_factory=uuid4)
    route_id: UUID
    breakdown: CostBreakdown
    calculated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: Optional[Dict] = None

    @property
    def total(self) -> Decimal:
        """Get total cost."""
        return self.breakdown.total


class Offer(BaseModel):
    """Offer entity representing a commercial offer for a route."""

    id: UUID = Field(default_factory=uuid4)
    route_id: UUID
    cost_id: UUID
    margin: Decimal
    final_price: Decimal
    fun_fact: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
    metadata: Optional[Dict] = None

    @property
    def price(self) -> Decimal:
        """Get the final price."""
        return self.final_price


class TransportType(BaseModel):
    """Transport type entity representing a type of vehicle."""

    id: str
    name: str
    capacity: float = Field(gt=0)
    fuel_consumption_empty: Decimal = Field(gt=0)
    fuel_consumption_loaded: Decimal = Field(gt=0)
    emissions_class: str
    cargo_restrictions: List[str] = Field(default_factory=list)
    metadata: Optional[Dict] = None

    def calculate_fuel_consumption(self, distance: float, is_loaded: bool) -> float:
        """Calculate fuel consumption for given distance."""
        consumption_rate = self.fuel_consumption_loaded if is_loaded else self.fuel_consumption_empty
        return (consumption_rate * distance) / 100  # L/100km to total liters


class Cargo(BaseModel):
    """Cargo entity representing goods to be transported."""

    id: str
    weight: float = Field(gt=0)
    value: Decimal = Field(ge=0)
    type: str
    special_requirements: Dict[str, str] = Field(default_factory=dict)
    hazmat: bool = False
    metadata: Optional[Dict] = None


class CostSettings(BaseModel):
    """Cost settings entity for pricing configuration."""

    id: UUID = Field(default_factory=uuid4)
    fuel_price_per_liter: Decimal = Field(gt=0)
    driver_daily_salary: Decimal = Field(gt=0)
    toll_rates: Dict[str, Decimal]  # Country code to rate mapping
    overheads: Dict[str, Decimal]  # Overhead type to amount mapping
    cargo_factors: Dict[str, Decimal]  # Factor type to amount mapping
    last_modified: datetime = Field(default_factory=utc_now)
    metadata: Optional[Dict] = None

    def calculate_toll_cost(self, country_distances: Dict[str, float]) -> Decimal:
        """Calculate toll costs based on country distances."""
        total = Decimal("0")
        for country, distance in country_distances.items():
            if country in self.toll_rates:
                total += self.toll_rates[country] * Decimal(str(distance))
        return total
