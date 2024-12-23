"""Domain entities for LoadApp.AI."""
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Union, ForwardRef
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

    def calculate_costs(self, cost_settings: "CostSettings") -> "Cost":
        """Calculate costs for the route using provided cost settings."""
        breakdown = {}
        
        # Calculate fuel costs per country
        fuel_cost = Decimal("0")
        for country_code in {seg.country_code for seg in self.country_segments}:
            distance = self.get_country_distance(country_code)
            fuel_price = cost_settings.fuel_prices.get(country_code, Decimal("0"))
            # Assume standard fuel consumption of 0.3L/km if not specified
            consumption_rate = Decimal(str(
                self.vehicle_specs.fuel_consumption_rate if self.vehicle_specs 
                else 0.3
            ))
            fuel_cost += Decimal(str(distance)) * fuel_price * consumption_rate
        breakdown["fuel"] = fuel_cost

        # Calculate empty driving costs
        if self.empty_driving:
            empty_factor = cost_settings.empty_driving_factors.get("fuel", Decimal("0.8"))
            empty_fuel_cost = Decimal("0")
            
            # Get country codes from empty driving segments if available, otherwise use total distance
            if hasattr(self.empty_driving, 'segments') and self.empty_driving.segments:
                for country_code in {seg.country_code for seg in self.empty_driving.segments}:
                    distance = sum(seg.distance for seg in self.empty_driving.segments if seg.country_code == country_code)
                    fuel_price = cost_settings.fuel_prices.get(country_code, Decimal("0"))
                    consumption_rate = Decimal(str(
                        self.vehicle_specs.fuel_consumption_rate * self.vehicle_specs.empty_consumption_factor 
                        if self.vehicle_specs else 0.24  # 0.3 * 0.8 default
                    ))
                    empty_fuel_cost += Decimal(str(distance)) * fuel_price * consumption_rate * empty_factor
            else:
                # Use total empty driving distance if segments are not available
                distance = self.empty_driving.distance_km
                # Use average fuel price if country-specific prices are not available
                avg_fuel_price = (
                    sum(cost_settings.fuel_prices.values()) / len(cost_settings.fuel_prices)
                    if cost_settings.fuel_prices else Decimal("1.5")  # Default average fuel price
                )
                consumption_rate = Decimal(str(
                    self.vehicle_specs.fuel_consumption_rate * self.vehicle_specs.empty_consumption_factor 
                    if self.vehicle_specs else 0.24  # 0.3 * 0.8 default
                ))
                empty_fuel_cost = Decimal(str(distance)) * avg_fuel_price * consumption_rate * empty_factor
            
            breakdown["empty_driving_fuel"] = empty_fuel_cost

        # Calculate toll costs
        toll_cost = Decimal("0")
        for country_code in {seg.country_code for seg in self.country_segments}:
            distance = self.get_country_distance(country_code)
            toll_rate = cost_settings.toll_rates.get(country_code, {}).get("highway", Decimal("0"))
            toll_cost += Decimal(str(distance)) * toll_rate
        breakdown["toll"] = toll_cost

        # Calculate driver costs
        driver_cost = Decimal("0")
        for country_code in {seg.country_code for seg in self.country_segments}:
            duration = self.get_country_duration(country_code)
            driver_rate = cost_settings.driver_rates.get(country_code, Decimal("0"))
            driver_cost += Decimal(str(duration)) * driver_rate
        
        # Add empty driving driver costs
        if self.empty_driving:
            empty_factor = cost_settings.empty_driving_factors.get("driver", Decimal("1.0"))
            for country_code in {seg.country_code for seg in (self.empty_driving.segments or [])}:
                duration = sum(seg.duration_hours for seg in self.empty_driving.segments if seg.country_code == country_code)
                driver_rate = cost_settings.driver_rates.get(country_code, Decimal("0"))
                driver_cost += Decimal(str(duration)) * driver_rate * empty_factor
        
        breakdown["driver"] = driver_cost

        # Calculate maintenance costs
        total_distance = Decimal(str(self.total_distance()))
        maintenance_cost = total_distance * cost_settings.maintenance_rate_per_km
        breakdown["maintenance"] = maintenance_cost

        # Calculate rest period costs
        rest_cost = Decimal("0")
        total_duration = self.total_duration()
        if total_duration > 4.5:  # Standard rest period after 4.5 hours
            rest_periods = int(total_duration / 4.5)
            rest_cost = Decimal(str(rest_periods)) * cost_settings.rest_period_rate
        breakdown["rest"] = rest_cost

        # Calculate loading/unloading costs
        loading_unloading_cost = Decimal("0")
        for window in self.time_windows:
            if window.operation_type in ["pickup", "delivery"]:
                loading_unloading_cost += cost_settings.loading_unloading_rate * Decimal(str(window.duration_hours))
        breakdown["loading_unloading"] = loading_unloading_cost

        # Calculate overhead costs
        overhead_cost = (
            total_distance * cost_settings.overhead_rates.get("distance", Decimal("0.05")) +
            Decimal(str(self.total_duration())) * cost_settings.overhead_rates.get("time", Decimal("10")) +
            cost_settings.overhead_rates.get("fixed", Decimal("100"))
        )
        breakdown["overhead"] = overhead_cost

        # Create and return Cost object
        return Cost(
            route_id=self.id,
            breakdown=CostBreakdown(**breakdown),
            calculation_method="standard",
            is_final=True,
            validity_period=timedelta(hours=24)
        )


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
    """Cost settings entity for pricing configuration."""

    id: UUID = Field(default_factory=uuid4)
    fuel_prices: Dict[str, Decimal] = Field(description="Country code to fuel price mapping")
    driver_rates: Dict[str, Decimal] = Field(description="Country code to driver rate mapping")
    toll_rates: Dict[str, Dict[str, Decimal]] = Field(description="Country code to toll rates mapping (highway and national)")
    maintenance_rate_per_km: Decimal = Field(gt=0)
    rest_period_rate: Decimal = Field(gt=0)
    loading_unloading_rate: Decimal = Field(gt=0)
    empty_driving_factors: Dict[str, Decimal] = Field(
        description="Factor type (fuel, toll, driver) to multiplier mapping"
    )
    cargo_factors: Dict[str, Dict[str, Decimal]] = Field(
        description="Cargo type to factor mapping (weight, volume, temperature)"
    )
    overhead_rates: Dict[str, Decimal] = Field(
        description="Overhead type (distance, time, fixed) to rate mapping"
    )
    last_modified: datetime = Field(default_factory=utc_now)
    extra_data: Optional[Dict] = None
    version: str = "1.0"
    is_active: bool = Field(default=True)

    def get_fuel_price(self, country_code: str) -> Decimal:
        """Get fuel price for a specific country."""
        return self.fuel_prices.get(country_code, Decimal("0"))

    def get_driver_rate(self, country_code: str) -> Decimal:
        """Get driver rate for a specific country."""
        return self.driver_rates.get(country_code, Decimal("0"))

    def get_toll_rate(self, country_code: str) -> Decimal:
        """Get toll rate for a specific country."""
        return self.toll_rates.get(country_code, {}).get("highway", Decimal("0"))

    def get_cargo_factors(self, cargo_type: str) -> Dict[str, Decimal]:
        """Get cargo factors for a specific cargo type."""
        return self.cargo_factors.get(cargo_type, {})

    @classmethod
    def get_default(cls) -> "CostSettings":
        """Get default cost settings."""
        return cls(
            fuel_prices={
                "PL": Decimal("1.50"),  # EUR per liter
                "DE": Decimal("1.70"),
                "CZ": Decimal("1.45"),
                "SK": Decimal("1.55"),
                "HU": Decimal("1.40"),
                "AT": Decimal("1.65")
            },
            driver_rates={
                "PL": Decimal("25.00"),  # EUR per hour
                "DE": Decimal("35.00"),
                "CZ": Decimal("22.00"),
                "SK": Decimal("23.00"),
                "HU": Decimal("21.00"),
                "AT": Decimal("32.00")
            },
            toll_rates={
                "PL": {"highway": Decimal("0.15"), "national": Decimal("0.10")},  # EUR per km
                "DE": {"highway": Decimal("0.20"), "national": Decimal("0.15")},
                "CZ": {"highway": Decimal("0.18"), "national": Decimal("0.12")},
                "SK": {"highway": Decimal("0.17"), "national": Decimal("0.11")},
                "HU": {"highway": Decimal("0.16"), "national": Decimal("0.10")},
                "AT": {"highway": Decimal("0.22"), "national": Decimal("0.18")}
            },
            maintenance_rate_per_km=Decimal("0.10"),
            rest_period_rate=Decimal("30.00"),  # EUR per hour
            loading_unloading_rate=Decimal("50.00"),  # EUR per operation
            empty_driving_factors={
                "fuel": Decimal("0.8"),  # 80% of loaded fuel consumption
                "toll": Decimal("1.0"),  # Same toll rates
                "driver": Decimal("1.0")  # Same driver rates
            },
            cargo_factors={
                "standard": {
                    "weight": Decimal("0.001"),  # EUR per kg per km
                    "volume": Decimal("0.05"),   # EUR per m3 per km
                    "temperature": Decimal("0.0") # No temperature control
                },
                "refrigerated": {
                    "weight": Decimal("0.002"),
                    "volume": Decimal("0.08"),
                    "temperature": Decimal("0.15") # EUR per hour for cooling
                },
                "hazmat": {
                    "weight": Decimal("0.003"),
                    "volume": Decimal("0.10"),
                    "temperature": Decimal("0.0")
                }
            },
            overhead_rates={
                "distance": Decimal("0.05"),  # EUR per km
                "time": Decimal("5.00"),      # EUR per hour
                "fixed": Decimal("100.00")    # EUR per route
            }
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
