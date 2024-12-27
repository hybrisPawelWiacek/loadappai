"""Cost-related value objects."""

from decimal import Decimal
from typing import Dict, Optional
from uuid import UUID, uuid4
from pydantic import Field, constr, field_validator

from .common import BaseValueObject


class Currency(BaseValueObject):
    """Currency value object."""

    code: constr(min_length=3, max_length=3) = Field(
        ..., description="ISO 4217 currency code"
    )
    symbol: str = Field(..., description="Currency symbol")
    exchange_rate: Optional[Decimal] = Field(
        None, description="Exchange rate to base currency (EUR)"
    )


class CountrySettings(BaseValueObject):
    """Country-specific cost settings."""

    country_code: constr(min_length=2, max_length=2) = Field(
        ..., description="ISO 3166-1 alpha-2 country code"
    )
    currency: str = Field(default="EUR")
    fuel_cost_per_km: Decimal = Field(default=Decimal("0"), ge=0)
    toll_cost_per_km: Decimal = Field(default=Decimal("0"), ge=0)
    driver_cost_per_hour: Decimal = Field(default=Decimal("0"), ge=0)
    rest_period_cost: Decimal = Field(default=Decimal("0"), ge=0)
    loading_unloading_cost: Decimal = Field(default=Decimal("0"), ge=0)
    empty_driving_multiplier: Decimal = Field(default=Decimal("1"), ge=0)
    maintenance_cost_per_km: Decimal = Field(default=Decimal("0"), ge=0)
    overhead_percentage: Decimal = Field(default=Decimal("0"), ge=0)

    @field_validator("country_code")
    def validate_country_code(cls, v: str) -> str:
        """Validate country code is uppercase."""
        return v.upper()

    @field_validator("currency")
    def validate_currency(cls, v: str) -> str:
        """Validate currency code."""
        if len(v) != 3:
            raise ValueError("Currency code must be 3 characters")
        return v.upper()


class Cost(BaseValueObject):
    """Value object representing a cost component."""

    amount: Decimal = Field(ge=0)
    currency: str = Field(default="EUR")
    description: Optional[str] = None
    category: Optional[str] = None

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


class CostBreakdown(BaseValueObject):
    """Cost breakdown for a route."""

    id: UUID = Field(default_factory=uuid4)
    route_id: UUID
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

    class Config:
        """Pydantic model configuration."""
        frozen = False  # Allow updates for cost calculations

    @property
    def total(self) -> Decimal:
        """Alias for total_cost for backward compatibility."""
        return self.total_cost

    @property
    def fuel_cost(self) -> Decimal:
        """Sum of all fuel costs."""
        return sum(self.fuel_costs.values())

    @property
    def toll_cost(self) -> Decimal:
        """Sum of all toll costs."""
        return sum(self.toll_costs.values())

    @property
    def driver_cost(self) -> Decimal:
        """Sum of all driver costs."""
        return sum(self.driver_costs.values())
