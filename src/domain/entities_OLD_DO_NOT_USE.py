"""Domain entities for LoadApp.AI."""
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Union, Set, ForwardRef, Any
from uuid import UUID, uuid4
from pytz import UTC

from pydantic import BaseModel, Field, validator, field_validator, ValidationInfo

from src.domain.value_objects import (
    Location,
    CountrySegment,
    EmptyDriving,
    CostBreakdown,
    RouteMetadata,
    RouteSegment
)

def utc_now() -> datetime:
    return datetime.now(UTC)


class TransportType(str, Enum):
    """Transport type enum."""

    TRUCK = "truck"
    VAN = "van"
    TRAILER = "trailer"
    FLATBED_TRUCK = "flatbed_truck"


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


class CargoSpecification(BaseModel):
    """Cargo specifications affecting cost calculations."""

    cargo_type: str
    weight_kg: float = Field(gt=0)
    volume_m3: float = Field(gt=0)
    temperature_controlled: bool = False
    required_temp_celsius: Optional[float] = None
    special_handling: List[str] = Field(default_factory=list)
    hazmat_class: Optional[str] = None


class VehicleSpecification(BaseModel):
    """Vehicle specifications affecting cost calculations."""

    vehicle_type: str
    fuel_consumption_rate: float = Field(gt=0)
    empty_consumption_factor: float = Field(gt=0, le=1.0)
    maintenance_rate_per_km: Decimal = Field(gt=0)
    toll_class: str
    has_special_equipment: bool = False
    equipment_costs: Dict[str, Decimal] = Field(default_factory=dict)


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
    transport_type: str
    distance_km: float = Field(gt=0)
    duration_hours: float = Field(gt=0)
    empty_driving: Optional[EmptyDriving] = None
    is_feasible: bool = True
    created_at: datetime = Field(default_factory=utc_now)
    route_metadata: Optional[RouteMetadata] = None
    country_segments: List[CountrySegment] = Field(default_factory=list)
    cargo_specs: Optional[CargoSpecification] = None
    vehicle_specs: Optional[VehicleSpecification] = None
    time_windows: List[TimeWindow] = Field(default_factory=list)
    segments: List[RouteSegment] = Field(default_factory=list)
    feasibility_notes: Optional[str] = None

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
            return TransportType(value)
        except ValueError:
            raise ValueError(f"Invalid transport type: {value}")

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
        total = sum(seg.distance for seg in self.country_segments if seg.country_code == country_code)
        if self.empty_driving and self.empty_driving.segments:
            total += sum(seg.distance for seg in self.empty_driving.segments if seg.country_code == country_code)
        return float(total)

    def get_country_duration(self, country_code: str) -> float:
        """Get total duration for a specific country."""
        total = sum(seg.duration_hours for seg in self.country_segments if seg.country_code == country_code)
        if self.empty_driving and self.empty_driving.segments:
            total += sum(seg.duration_hours for seg in self.empty_driving.segments if seg.country_code == country_code)
        return float(total)



class Cargo(BaseModel):
    """Cargo entity."""

    id: UUID = Field(default_factory=uuid4)
    weight: float = Field(gt=0)
    volume: float = Field(gt=0)
    value: Decimal = Field(ge=0)
    type: str
    hazmat: bool = False
    refrigerated: bool = False
    fragile: bool = False
    stackable: bool = True
    special_requirements: Optional[Dict[str, str]] = None
    metadata: Optional[Dict] = None


class CostBreakdown(BaseModel):
    """Cost breakdown for a route."""

    id: UUID = Field(default_factory=uuid4)
    route_id: UUID
    fuel_costs: Dict[str, Decimal] = Field(default_factory=dict)
    toll_costs: Dict[str, Decimal] = Field(default_factory=dict)
    maintenance_costs: Dict[str, Decimal] = Field(default_factory=dict)
    driver_costs: Dict[str, Decimal] = Field(default_factory=dict)
    rest_period_costs: Decimal = Decimal('0')
    loading_unloading_costs: Decimal = Decimal('0')
    empty_driving_costs: Dict[str, Dict[str, Decimal]] = Field(default_factory=dict)
    cargo_specific_costs: Dict[str, Decimal] = Field(default_factory=dict)
    overheads: Dict[str, Decimal] = Field(default_factory=dict)
    subtotal_distance_based: Decimal = Decimal('0')
    subtotal_time_based: Decimal = Decimal('0')
    subtotal_empty_driving: Decimal = Decimal('0')
    total_cost: Decimal = Decimal('0')
    currency: str = "EUR"


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
        valid_types = {"fuel", "toll", "driver", "maintenance", "overhead"}
        if v not in valid_types:
            raise ValueError(f"Invalid cost component type: {v}")
        return v
    
    @field_validator("amount")
    def validate_amount(cls, v: Decimal) -> Decimal:
        """Validate amount is positive."""
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v

    @field_validator("currency")
    def validate_currency(cls, v: str) -> str:
        """Validate currency code."""
        if len(v) != 3:
            raise ValueError("Currency must be a 3-letter ISO code")
        return v.upper()


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

    @property
    def total(self) -> Decimal:
        """Get total cost."""
        return self.breakdown.total_cost

    @property
    def total_cost(self) -> Decimal:
        """Get total cost (alias for total)."""
        return self.total

    def is_valid(self) -> bool:
        """Check if the cost calculation is still valid."""
        if not self.validity_period:
            return True
        return datetime.now(UTC) < self.calculated_at + self.validity_period

    def recalculate_needed(self) -> bool:
        """Check if recalculation is needed based on validity and version."""
        return not self.is_valid() or self.version != "2.0"

    def dict(self, *args, **kwargs) -> Dict:
        """Convert to dictionary with proper handling of special types."""
        d = super().dict(*args, **kwargs)
        d["total_cost"] = str(self.total_cost)
        return d


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
    version: str = "1.0"
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
            raise ValueError(f"Invalid cost components: {invalid}")
        return v

    @field_validator("fuel_rates", "driver_rates")
    def validate_country_rates(cls, v: Dict[str, Decimal]) -> Dict[str, Decimal]:
        """Validate that rates are positive."""
        for country, rate in v.items():
            if rate <= 0:
                raise ValueError(f"Rate for {country} must be positive")
        return v

    @field_validator("toll_rates")
    def validate_toll_rates(cls, v: Dict[str, Dict[str, Decimal]]) -> Dict[str, Dict[str, Decimal]]:
        """Validate that toll rates are positive."""
        for country, rates in v.items():
            for vehicle_type, rate in rates.items():
                if rate <= 0:
                    raise ValueError(f"Toll rate for {country}/{vehicle_type} must be positive")
        return v

    @classmethod
    def get_default(cls, route_id: UUID) -> "CostSettings":
        """Get default cost settings for a route."""
        return cls(
            route_id=route_id,
            fuel_rates={"DE": Decimal("1.8"), "PL": Decimal("1.6"), "CZ": Decimal("1.7")},
            toll_rates={
                "DE": {"truck": Decimal("0.20"), "van": Decimal("0.10")},
                "PL": {"truck": Decimal("0.15"), "van": Decimal("0.08")},
                "CZ": {"truck": Decimal("0.18"), "van": Decimal("0.09")}
            },
            driver_rates={"DE": Decimal("35"), "PL": Decimal("25"), "CZ": Decimal("28")},
            overhead_rates={"fixed": Decimal("100"), "variable": Decimal("50")},
            maintenance_rates={"truck": Decimal("0.15"), "van": Decimal("0.10")}
        )


class OfferStatus(str, Enum):
    """Offer status enum."""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class Offer(ExtensibleEntity):
    """Offer entity representing a commercial offer for a route."""

    id: UUID = Field(default_factory=uuid4)
    route_id: UUID
    cost_id: UUID
    total_cost: Decimal
    margin: Decimal
    final_price: Decimal
    fun_fact: Optional[str] = None
    status: OfferStatus = Field(default=OfferStatus.DRAFT)
    is_active: bool = Field(default=True)
    
    @property
    def price(self) -> Decimal:
        """Get the final price."""
        return self.final_price


class OfferHistory(BaseModel):
    """Offer history entity for tracking changes."""
    
    id: UUID = Field(default_factory=uuid4)
    offer_id: UUID
    version: str
    status: OfferStatus
    margin: Decimal
    final_price: Decimal
    fun_fact: Optional[str] = None
    metadata: Optional[Dict] = None
    changed_at: datetime = Field(default_factory=utc_now)
    changed_by: Optional[str] = None
    change_reason: Optional[str] = None


class TransportSettings(BaseModel):
    """Transport settings entity for vehicle and cargo configuration."""

    id: UUID = Field(default_factory=uuid4)
    vehicle_types: List[str] = Field(description="Available vehicle types")
    equipment_types: List[str] = Field(description="Available equipment types")
    cargo_types: List[str] = Field(description="Supported cargo types")
    loading_time_minutes: int = Field(gt=0)
    unloading_time_minutes: int = Field(gt=0)
    max_driving_hours: float = Field(gt=0)
    required_rest_hours: float = Field(gt=0)
    max_working_days: int = Field(gt=0)
    speed_limits: Dict[str, int] = Field(description="Speed limits by road type")
    is_active: bool = Field(default=True)
    last_modified: datetime = Field(default_factory=utc_now)

    @classmethod
    def get_default(cls) -> "TransportSettings":
        """Get default transport settings."""
        return cls(
            vehicle_types=["truck", "van", "trailer", "flatbed_truck"],
            equipment_types=["refrigeration", "tail_lift", "gps_tracking"],
            cargo_types=["standard", "refrigerated", "hazmat", "fragile"],
            loading_time_minutes=30,
            unloading_time_minutes=30,
            max_driving_hours=9.0,
            required_rest_hours=11.0,
            max_working_days=5,
            speed_limits={
                "highway": 90,
                "rural": 70,
                "urban": 50
            }
        )


class SystemSettings(BaseModel):
    """System settings entity for global configuration."""

    id: UUID = Field(default_factory=uuid4)
    api_url: str = Field(description="Base URL for API")
    api_version: str = Field(description="API version")
    request_timeout_seconds: int = Field(gt=0)
    default_currency: str = Field(default="EUR")
    default_language: str = Field(default="en")
    enable_cost_history: bool = Field(default=True)
    enable_route_optimization: bool = Field(default=True)
    enable_real_time_tracking: bool = Field(default=False)
    maps_provider: str = Field(default="google")
    geocoding_provider: str = Field(default="google")
    min_margin_percent: Decimal = Field(ge=0, le=100)
    max_margin_percent: Decimal = Field(ge=0, le=100)
    price_rounding_decimals: int = Field(default=2)
    max_route_duration: timedelta = Field(default=timedelta(days=5))
    is_active: bool = Field(default=True)
    last_modified: datetime = Field(default_factory=utc_now)

    @classmethod
    def get_default(cls) -> "SystemSettings":
        """Get default system settings."""
        return cls(
            api_url="http://localhost:8000",
            api_version="v1",
            request_timeout_seconds=30,
            default_currency="EUR",
            default_language="en",
            enable_cost_history=True,
            enable_route_optimization=True,
            enable_real_time_tracking=False,
            maps_provider="google",
            geocoding_provider="google",
            min_margin_percent=Decimal("5"),
            max_margin_percent=Decimal("25"),
            price_rounding_decimals=2
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
            if amount < 0:
                raise ValueError(f"Cost component {component} cannot be negative")
        return value

    @field_validator("calculation_method")
    def validate_calculation_method(cls, value: str, info: ValidationInfo) -> str:
        """Validate calculation method."""
        valid_methods = {"standard", "detailed", "estimated"}
        if value not in valid_methods:
            raise ValueError(f"Invalid calculation method. Must be one of: {valid_methods}")
        return value
