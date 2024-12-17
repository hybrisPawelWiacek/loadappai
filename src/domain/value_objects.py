"""Value objects for the domain layer."""
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Optional

from pydantic import BaseModel, Field, confloat, constr
from pydantic import computed_field


class Location(BaseModel):
    """Location value object with address and coordinates."""

    address: str = Field(..., description="Full address of the location")
    latitude: confloat(ge=-90, le=90) = Field(..., description="Latitude in decimal degrees")
    longitude: confloat(ge=-180, le=180) = Field(..., description="Longitude in decimal degrees")

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


@dataclass(frozen=True)
class CountrySegment:
    """Represents a route segment within a specific country."""

    country_code: constr(min_length=2, max_length=2)
    distance: confloat(gt=0)
    toll_rates: Dict[str, Decimal]


class CostBreakdown(BaseModel):
    """Cost breakdown for a route."""

    fuel_cost: Decimal = Field(ge=0)
    toll_cost: Decimal = Field(ge=0)
    driver_cost: Decimal = Field(ge=0)
    overheads: Decimal = Field(ge=0)
    cargo_specific_costs: Dict[str, Decimal] = Field(default_factory=dict)
    total_cost: Decimal = Field(ge=0)

    @computed_field
    @property
    def total(self) -> Decimal:
        """Calculate total cost."""
        return (
            self.fuel_cost
            + self.toll_cost
            + self.driver_cost
            + self.overheads
            + sum(self.cargo_specific_costs.values())
        )

    def __add__(self, other: "CostBreakdown") -> "CostBreakdown":
        """Add two cost breakdowns together."""
        return CostBreakdown(
            fuel_cost=self.fuel_cost + other.fuel_cost,
            toll_cost=self.toll_cost + other.toll_cost,
            driver_cost=self.driver_cost + other.driver_cost,
            overheads=self.overheads + other.overheads,
            cargo_specific_costs={
                k: self.cargo_specific_costs.get(k, Decimal("0"))
                + other.cargo_specific_costs.get(k, Decimal("0"))
                for k in set(self.cargo_specific_costs) | set(other.cargo_specific_costs)
            },
            total_cost=self.total_cost + other.total_cost,
        )

    class Config:
        """Pydantic model configuration."""

        frozen = True


class EmptyDriving(BaseModel):
    """Empty driving details."""

    distance_km: confloat(ge=0) = Field(..., description="Empty driving distance in kilometers")
    duration_hours: confloat(ge=0) = Field(..., description="Empty driving duration in hours")

    class Config:
        """Pydantic model configuration."""

        frozen = True


class Currency(BaseModel):
    """Currency value object."""

    code: constr(min_length=3, max_length=3) = Field(..., description="ISO 4217 currency code")
    symbol: str = Field(..., description="Currency symbol")
    exchange_rate: Optional[Decimal] = Field(None, description="Exchange rate to base currency (EUR)")

    class Config:
        """Pydantic model configuration."""

        frozen = True
