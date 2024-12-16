"""Domain entities for LoadApp.AI."""
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator

from src.domain.value_objects import (
    CostBreakdown,
    EmptyDriving,
    Location,
    RouteMetadata,
)


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
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[RouteMetadata] = None

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
    """Cost entity representing transport costs."""

    route_id: UUID
    breakdown: CostBreakdown
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict] = None

    @property
    def total(self) -> Decimal:
        """Get total cost."""
        return self.breakdown.total


class Offer(BaseModel):
    """Offer entity representing a commercial offer."""

    id: UUID = Field(default_factory=uuid4)
    route_id: UUID
    total_cost: Decimal = Field(ge=0)
    margin: float = Field(ge=0, le=1)
    final_price: Decimal = Field(ge=0)
    fun_fact: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict] = None

    @validator("final_price")
    def validate_final_price(cls, v: Decimal, values: Dict) -> Decimal:
        """Validate that final price matches total cost plus margin."""
        if "total_cost" in values and "margin" in values:
            expected = values["total_cost"] * (Decimal("1") + Decimal(str(values["margin"])))
            if abs(v - expected) > Decimal("0.01"):  # Allow small rounding differences
                raise ValueError("final_price must equal total_cost * (1 + margin)")
        return v


class TransportType(BaseModel):
    """Transport type entity representing a type of truck."""

    id: str
    name: str
    capacity: float = Field(gt=0)
    emissions_class: str
    fuel_consumption_empty: float = Field(gt=0)
    fuel_consumption_loaded: float = Field(gt=0)
    metadata: Optional[Dict] = None

    def calculate_fuel_consumption(self, distance: float, is_loaded: bool) -> float:
        """Calculate fuel consumption for given distance."""
        consumption_rate = self.fuel_consumption_loaded if is_loaded else self.fuel_consumption_empty
        return (consumption_rate * distance) / 100  # L/100km to total liters


class Cargo(BaseModel):
    """Cargo entity representing goods being transported."""

    id: str
    weight: float = Field(gt=0)
    value: Decimal = Field(ge=0)
    special_requirements: Optional[Dict] = None
    hazmat: bool = False
    metadata: Optional[Dict] = None

    def validate_transport_type(self, transport_type: TransportType) -> bool:
        """Validate if cargo can be transported by given transport type."""
        if self.weight > transport_type.capacity:
            return False
        if self.special_requirements and self.special_requirements.get("temperature_controlled"):
            return "refrigerated" in transport_type.id.lower()
        return True


class CostSettings(BaseModel):
    """Cost settings entity for pricing configuration."""

    id: UUID = Field(default_factory=uuid4)
    fuel_price_per_liter: Decimal = Field(gt=0)
    driver_daily_salary: Decimal = Field(gt=0)
    toll_rates: Dict[str, Decimal]  # Country code to rate mapping
    overheads: Dict[str, Decimal]  # Overhead type to amount mapping
    cargo_factors: Dict[str, Decimal]  # Factor type to amount mapping
    last_modified: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict] = None

    def calculate_toll_cost(self, country_distances: Dict[str, float]) -> Decimal:
        """Calculate toll costs based on country distances."""
        total = Decimal("0")
        for country, distance in country_distances.items():
            if country in self.toll_rates:
                total += self.toll_rates[country] * Decimal(str(distance))
        return total
