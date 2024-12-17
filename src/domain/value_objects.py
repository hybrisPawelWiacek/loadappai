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


class CountrySegment(BaseModel):
    """Value object representing a segment of the route in a specific country."""

    country_code: str = Field(description="ISO country code")
    distance: Decimal = Field(ge=0, description="Distance in kilometers")
    toll_rates: Dict[str, Decimal] = Field(default_factory=dict, description="Toll rates by category")

    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "country_code": "DE",
                "distance": Decimal("150.5"),
                "toll_rates": {
                    "highway": Decimal("25.50"),
                    "national": Decimal("10.20")
                }
            }
        }


class CostBreakdown(BaseModel):
    """Cost breakdown for a route."""

    fuel_cost: Decimal = Field(ge=0)
    toll_cost: Decimal = Field(ge=0)
    driver_cost: Decimal = Field(ge=0)
    overheads: Decimal = Field(ge=0)
    cargo_specific_costs: Dict[str, Decimal] = Field(default_factory=dict)
    total: Decimal = Field(ge=0)

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
            total=self.total + other.total,
        )

    class Config:
        """Pydantic model configuration."""

        frozen = True


class EmptyDriving(BaseModel):
    """Value object representing empty driving segments."""

    distance_km: float = Field(description="Distance in kilometers", gt=0)
    duration_hours: float = Field(description="Duration in hours", gt=0)

    model_config = {"frozen": True}


class Currency(BaseModel):
    """Currency value object."""

    code: constr(min_length=3, max_length=3) = Field(..., description="ISO 4217 currency code")
    symbol: str = Field(..., description="Currency symbol")
    exchange_rate: Optional[Decimal] = Field(None, description="Exchange rate to base currency (EUR)")

    class Config:
        """Pydantic model configuration."""

        frozen = True
