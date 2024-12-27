"""Cost-related models for API request/response handling."""
from datetime import datetime
from decimal import Decimal
from typing import Dict, Optional, Any
from pydantic import BaseModel, Field, validator

from .base import ensure_timezone


class CostBreakdown(BaseModel):
    """Cost breakdown model with detailed per-country and component costs."""
    route_id: str
    fuel_costs: Dict[str, Decimal] = Field(..., description="Fuel costs per country")
    toll_costs: Dict[str, Decimal] = Field(..., description="Toll costs per country")
    maintenance_costs: Dict[str, Decimal] = Field(..., description="Maintenance costs per country")
    driver_costs: Dict[str, Decimal] = Field(..., description="Driver costs per country")
    rest_period_costs: Decimal = Field(..., description="Costs for mandatory rest periods")
    loading_unloading_costs: Decimal = Field(..., description="Costs for loading/unloading operations")
    empty_driving_costs: Dict[str, Dict[str, Decimal]] = Field(
        ...,
        description="Empty driving costs per country and type (fuel, toll, driver)"
    )
    cargo_specific_costs: Dict[str, Decimal] = Field(..., description="Costs specific to cargo type")
    overheads: Dict[str, Decimal] = Field(..., description="Overhead costs by category")
    subtotal_distance_based: Decimal = Field(..., description="Total of all distance-based costs")
    subtotal_time_based: Decimal = Field(..., description="Total of all time-based costs")
    subtotal_empty_driving: Decimal = Field(..., description="Total of all empty driving costs")
    total_cost: Decimal = Field(..., description="Total cost including all components")
    currency: str = Field(default="EUR", description="Currency for all monetary values")

    @validator('*')
    def validate_country_costs(cls, v):
        """Validate that all country-specific costs are positive."""
        if isinstance(v, Dict):
            for cost in v.values():
                if isinstance(cost, (int, float, Decimal)) and cost < 0:
                    raise ValueError("Cost values cannot be negative")
        return v

    @validator('empty_driving_costs')
    def validate_empty_driving_costs(cls, v):
        """Validate empty driving costs structure and values."""
        for country_costs in v.values():
            if not isinstance(country_costs, dict):
                raise ValueError("Empty driving costs must be a nested dictionary")
            for cost in country_costs.values():
                if cost < 0:
                    raise ValueError("Empty driving costs cannot be negative")
        return v


class CostSettings(BaseModel):
    """Enhanced cost settings model with detailed rates and factors."""
    fuel_prices: Dict[str, Decimal] = Field(
        ...,
        description="Fuel prices per liter by country"
    )
    toll_rates: Dict[str, Decimal] = Field(
        ...,
        description="Base toll rates per kilometer by country"
    )
    driver_rates: Dict[str, Decimal] = Field(
        ...,
        description="Driver daily rates by country"
    )
    rest_period_rate: Decimal = Field(..., gt=0)
    loading_unloading_rate: Decimal = Field(..., gt=0)
    maintenance_rate_per_km: Decimal = Field(..., gt=0)
    empty_driving_factors: Dict[str, Decimal] = Field(
        ...,
        description="Factors for empty driving costs (fuel, toll, driver)"
    )
    cargo_factors: Dict[str, Dict[str, Decimal]] = Field(
        ...,
        description="Cost factors by cargo type and component"
    )
    overhead_rates: Dict[str, Decimal] = Field(
        ...,
        description="Overhead rates by category"
    )
    version: str = Field(..., description="Settings version")
    is_active: bool = Field(default=True)
    last_modified: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None

    _ensure_modified_timezone = validator('last_modified', allow_reuse=True)(ensure_timezone)

    @validator('*')
    def validate_positive_rates(cls, v):
        """Validate that all rates are positive."""
        if isinstance(v, (int, float, Decimal)) and not isinstance(v, bool):
            if v < 0:
                raise ValueError("Rates cannot be negative")
        return v

    @validator('empty_driving_factors')
    def validate_factors(cls, v):
        """Validate empty driving factors."""
        for factor in v.values():
            if factor < 0 or factor > 2:
                raise ValueError("Empty driving factors must be between 0 and 2")
        return v

    @validator('cargo_factors')
    def validate_cargo_factors(cls, v):
        """Validate cargo-specific factors."""
        for factors in v.values():
            for factor in factors.values():
                if factor < 0 or factor > 5:
                    raise ValueError("Cargo factors must be between 0 and 5")
        return v


class CostHistoryEntry(BaseModel):
    """Cost history entry model."""
    calculation_date: datetime
    route_id: str
    total_cost: Decimal
    currency: str
    calculation_method: str
    version: str
    is_final: bool
    cost_components: Dict[str, Decimal]
    settings_snapshot: Dict[str, Any]

    _ensure_calc_timezone = validator('calculation_date', allow_reuse=True)(ensure_timezone)


class CostSettingsUpdateResponse(BaseModel):
    """Response model for cost settings update."""
    message: str
    updated_at: datetime

    _ensure_updated_timezone = validator('updated_at', allow_reuse=True)(ensure_timezone)
