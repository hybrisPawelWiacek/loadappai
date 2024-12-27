"""Cost-related domain entities."""

from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, Optional, Set
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, ValidationInfo
from pytz import UTC


def utc_now() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(UTC)


class CostSettingsVersion(str, Enum):
    """Cost settings version enum."""
    V1_0 = "1.0"
    V2_0 = "2.0"
    V2_1 = "2.1"
    V3_0 = "3.0"


class CostComponent(BaseModel):
    """Individual cost component with detailed breakdown."""

    type: str = Field(description="Cost component type (fuel, toll, driver, etc.)")
    amount: Decimal = Field(gt=0)
    currency: str = Field(default="EUR")
    country: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("type")
    def validate_type(cls, v: str) -> str:
        """Validate cost component type."""
        valid_types = {"fuel", "toll", "maintenance", "driver", "rest_period", "loading_unloading", "empty_driving", "cargo_specific", "overheads"}
        if v not in valid_types:
            raise ValueError(f"Invalid cost component type: {v}")
        return v

    @field_validator("amount")
    def validate_amount(cls, v: Decimal) -> Decimal:
        """Validate amount is positive."""
        if v <= 0:
            raise ValueError("Input should be greater than 0")
        return v

    @field_validator("currency")
    def validate_currency(cls, v: str) -> str:
        """Validate currency code."""
        if len(v) != 3:
            raise ValueError("Currency must be a 3-letter ISO code")
        return v.upper()


class CostBreakdown(BaseModel):
    """Cost breakdown for a route."""

    id: UUID = Field(default_factory=uuid4)
    route_id: UUID
    fuel_costs: Dict[str, Decimal] = Field(
        default_factory=dict,
        description="Country code to fuel cost mapping"
    )
    toll_costs: Dict[str, Decimal] = Field(
        default_factory=dict,
        description="Country code to toll cost mapping"
    )
    maintenance_costs: Dict[str, Decimal] = Field(
        default_factory=dict,
        description="Vehicle type to maintenance cost mapping"
    )
    driver_costs: Dict[str, Decimal] = Field(
        default_factory=dict,
        description="Country code to driver cost mapping"
    )
    rest_period_costs: Decimal = Field(
        default=Decimal('0'),
        description="Costs for mandatory rest periods"
    )
    loading_unloading_costs: Decimal = Field(
        default=Decimal('0'),
        description="Costs for loading and unloading operations"
    )
    empty_driving_costs: Dict[str, Dict[str, Decimal]] = Field(
        default_factory=dict,
        description="Empty driving costs by country and cost type"
    )
    cargo_specific_costs: Dict[str, Decimal] = Field(
        default_factory=dict,
        description="Additional costs specific to cargo type"
    )
    overheads: Dict[str, Decimal] = Field(
        default_factory=dict,
        description="Fixed and variable overhead costs"
    )
    subtotal_distance_based: Decimal = Field(
        default=Decimal('0'),
        description="Subtotal of distance-based costs"
    )
    subtotal_time_based: Decimal = Field(
        default=Decimal('0'),
        description="Subtotal of time-based costs"
    )
    subtotal_empty_driving: Decimal = Field(
        default=Decimal('0'),
        description="Subtotal of empty driving costs"
    )
    total_cost: Decimal = Field(
        default=Decimal('0'),
        description="Total cost including all components"
    )
    currency: str = Field(
        default="EUR",
        description="Currency for all cost values"
    )


class Cost(BaseModel):
    """Cost record for a route."""

    id: UUID = Field(default_factory=uuid4)
    route_id: UUID
    breakdown: CostBreakdown
    calculated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: Optional[Dict] = None
    version: str = "2.0"
    is_final: bool = False
    last_updated: datetime = Field(default_factory=utc_now)
    calculation_method: str = Field(description="standard, detailed, or estimated")
    validity_period: Optional[timedelta] = None
    total_cost: Decimal = Field(default=Decimal('0'))

    @field_validator("calculation_method")
    def validate_calculation_method(cls, v: str, info: ValidationInfo) -> str:
        """Validate calculation method."""
        valid_methods = {"standard", "detailed", "estimated"}
        if v not in valid_methods:
            raise ValueError(f"Invalid calculation method: {v}")
        return v

    def total(self) -> Decimal:
        """Get total cost."""
        if not self.breakdown:
            return Decimal('0')
        
        # Return the pre-calculated total from the breakdown
        self.total_cost = self.breakdown.total_cost
        return self.total_cost

    def is_valid(self) -> bool:
        """Check if the cost calculation is still valid."""
        if not self.validity_period:
            return True
        return (datetime.now(UTC) - self.calculated_at) <= self.validity_period

    def recalculate_needed(self) -> bool:
        """Check if recalculation is needed based on validity and version."""
        return not self.is_valid() or self.version != "2.0"


class CostSettings(BaseModel):
    """Cost settings for a specific route."""

    id: UUID = Field(default_factory=uuid4)
    route_id: UUID
    fuel_rates: Dict[str, Decimal] = Field(
        description="Country code to fuel price mapping",
        default_factory=dict
    )
    toll_rates: Dict[str, Dict[str, Decimal]] = Field(
        description="Country code to toll rates mapping (by vehicle type)",
        default_factory=dict
    )
    driver_rates: Dict[str, Decimal] = Field(
        description="Country code to driver rate mapping",
        default_factory=dict
    )
    overhead_rates: Dict[str, Decimal] = Field(
        description="Fixed overheads",
        default_factory=dict
    )
    maintenance_rates: Dict[str, Decimal] = Field(
        description="Maintenance rates by vehicle type",
        default_factory=dict
    )
    enabled_components: Set[str] = Field(
        description="Which cost components are enabled",
        default_factory=lambda: {"fuel", "toll", "driver"}
    )
    version: CostSettingsVersion = CostSettingsVersion.V1_0
    created_at: datetime = Field(default_factory=utc_now)
    modified_at: datetime = Field(default_factory=utc_now)
    created_by: Optional[str] = None
    modified_by: Optional[str] = None

    @field_validator("enabled_components")
    def validate_enabled_components(cls, v: Set[str]) -> Set[str]:
        """Validate that enabled components are valid."""
        valid_components = {"fuel", "toll", "driver", "maintenance", "overhead"}
        invalid = v - valid_components
        if invalid:
            raise ValueError("Invalid cost components")
        return v

    @field_validator("fuel_rates")
    def validate_fuel_rates(cls, v: Dict[str, Decimal]) -> Dict[str, Decimal]:
        """Validate fuel rates."""
        for country, rate in v.items():
            if rate <= 0:
                raise ValueError("Input should be greater than 0")
        return v

    @field_validator("toll_rates")
    def validate_toll_rates(cls, v: Dict[str, Dict[str, Decimal]]) -> Dict[str, Dict[str, Decimal]]:
        """Validate toll rates."""
        for country, rates in v.items():
            for vehicle_type, rate in rates.items():
                if rate <= 0:
                    raise ValueError("Input should be greater than 0")
        return v

    @field_validator("driver_rates")
    def validate_driver_rates(cls, v: Dict[str, Decimal]) -> Dict[str, Decimal]:
        """Validate driver rates."""
        for country, rate in v.items():
            if rate <= 0:
                raise ValueError("Input should be greater than 0")
        return v

    @field_validator("maintenance_rates")
    def validate_maintenance_rates(cls, v: Dict[str, Decimal]) -> Dict[str, Decimal]:
        """Validate maintenance rates."""
        for vehicle_type, rate in v.items():
            if rate <= 0:
                raise ValueError("Input should be greater than 0")
        return v

    @classmethod
    def get_default(cls, route_id: UUID) -> "CostSettings":
        """Get default cost settings for a route."""
        return cls(
            route_id=route_id,
            fuel_rates={"default": Decimal("1.5")},
            toll_rates={"default": {"truck": Decimal("0.2")}},
            driver_rates={"default": Decimal("30.0")},
            overhead_rates={
                "fixed": Decimal("50.0"),
                "variable": Decimal("0.1"),
                "distance": Decimal("0.05"),
                "time": Decimal("10.0")
            },
            maintenance_rates={"truck": Decimal("0.15")},
            enabled_components={"fuel", "toll", "driver", "maintenance", "overhead"}
        )


class CostHistoryEntry(BaseModel):
    """Cost history entry entity for tracking cost calculations."""

    id: UUID = Field(default_factory=uuid4)
    route_id: UUID
    calculation_date: datetime = Field(default_factory=utc_now)
    total_cost: Decimal = Field(gt=0)
    currency: str = Field(default="EUR")
    calculation_method: str = Field(description="standard, detailed, or estimated")
    version: str
    is_final: bool = Field(default=False)
    cost_components: Dict[str, Decimal] = Field(description="Breakdown of cost components")
    settings_snapshot: Dict = Field(description="Snapshot of settings used for calculation")

    @field_validator("cost_components")
    def validate_cost_components(cls, value: Dict[str, Decimal], info: ValidationInfo) -> Dict[str, Decimal]:
        """Validate that all cost components are positive."""
        for component, amount in value.items():
            if amount <= 0:
                raise ValueError("Input should be greater than 0")
        return value

    @field_validator("calculation_method")
    def validate_calculation_method(cls, value: str, info: ValidationInfo) -> str:
        """Validate calculation method."""
        valid_methods = {"standard", "detailed", "estimated"}
        if value not in valid_methods:
            raise ValueError(f"Invalid calculation method: {value}")
        return value

    @field_validator("settings_snapshot")
    def validate_settings_snapshot(cls, value: Dict, info: ValidationInfo) -> Dict:
        """Validate settings snapshot."""
        if "fuel_rates" in value:
            for country, rate in value["fuel_rates"].items():
                if rate <= 0:
                    raise ValueError("Input should be greater than 0")
        if "toll_rates" in value:
            for country, rates in value["toll_rates"].items():
                for vehicle_type, rate in rates.items():
                    if rate <= 0:
                        raise ValueError("Input should be greater than 0")
        if "driver_rates" in value:
            for country, rate in value["driver_rates"].items():
                if rate <= 0:
                    raise ValueError("Input should be greater than 0")
        if "maintenance_rates" in value:
            for vehicle_type, rate in value["maintenance_rates"].items():
                if rate <= 0:
                    raise ValueError("Input should be greater than 0")
        return value
