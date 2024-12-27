"""API request and response models."""
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field, validator
from decimal import Decimal

from src.domain.entities.offer import OfferHistory, Offer
from src.domain.entities.cargo import CargoSpecification
from src.domain.entities.route import TransportType, TimelineEventType


class TransportType(str, Enum):
    """Valid transport types."""
    TRUCK = "truck"
    VAN = "van"
    TRAILER = "trailer"


class TimelineEventType(str, Enum):
    """Types of timeline events."""
    PICKUP = "pickup"
    DELIVERY = "delivery"
    EMPTY_DRIVING = "empty_driving"


class Location(BaseModel):
    """Location model with address and coordinates."""
    address: str
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    country: str = Field(..., description="ISO country code")


class CargoSpecification(BaseModel):
    """Cargo specifications."""
    weight_kg: float = Field(..., gt=0)
    volume_m3: float = Field(..., gt=0)
    cargo_type: str
    hazmat_class: Optional[str] = None
    temperature_controlled: bool = False
    required_temp_celsius: Optional[float] = None


class EmptyDriving(BaseModel):
    """Empty driving details."""
    distance_km: float
    duration_hours: float
    start_location: Optional[Location] = None
    end_location: Optional[Location] = None


class RouteSegment(BaseModel):
    """Route segment details."""
    start_location: Location
    end_location: Location
    distance_km: float
    duration_hours: float
    country: str
    is_empty_driving: bool
    timeline_event: Optional[TimelineEventType] = None


class RouteCreateRequest(BaseModel):
    """Request model for route creation."""
    cargo_id: Optional[str] = None
    origin: Location
    destination: Location
    transport_type: TransportType
    pickup_time: datetime
    delivery_time: datetime
    cargo_specs: Optional[CargoSpecification] = None

    @validator('pickup_time', 'delivery_time')
    def ensure_timezone(cls, v):
        """Ensure datetime has timezone information."""
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        return v

    @validator('delivery_time')
    def validate_delivery_time(cls, v, values):
        """Validate that delivery time is after pickup time."""
        if 'pickup_time' in values and v <= values['pickup_time']:
            raise ValueError('delivery_time must be after pickup_time')
        return v


class RouteResponse(BaseModel):
    """Response model for route operations."""
    id: str
    cargo_id: Optional[str] = None
    origin: Location
    destination: Location
    transport_type: TransportType
    pickup_time: datetime
    delivery_time: datetime
    cargo_specs: Optional[CargoSpecification] = None
    distance_km: float
    duration_hours: float
    empty_driving: Optional[EmptyDriving] = None
    segments: List[RouteSegment] = Field(default_factory=list)
    is_feasible: bool = True
    feasibility_notes: Optional[str] = None
    created_at: datetime

    @validator('pickup_time', 'delivery_time', 'created_at')
    def ensure_timezone(cls, v):
        """Ensure datetime has timezone information."""
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        return v

    @classmethod
    def from_domain(cls, route):
        """Convert domain Route model to API response model."""
        # Convert origin and destination to Location models
        origin = Location(
            address=route.origin["address"],
            latitude=route.origin["latitude"],
            longitude=route.origin["longitude"],
            country=route.origin["country"]
        )
        destination = Location(
            address=route.destination["address"],
            latitude=route.destination["latitude"],
            longitude=route.destination["longitude"],
            country=route.destination["country"]
        )

        # Convert empty driving if present
        empty_driving = None
        if route.empty_driving:
            empty_start = None
            if route.empty_driving.origin:
                empty_start = Location(
                    address=route.empty_driving.origin.address,
                    latitude=route.empty_driving.origin.latitude,
                    longitude=route.empty_driving.origin.longitude,
                    country=route.empty_driving.origin.country
                )
            empty_end = None
            if route.empty_driving.destination:
                empty_end = Location(
                    address=route.empty_driving.destination.address,
                    latitude=route.empty_driving.destination.latitude,
                    longitude=route.empty_driving.destination.longitude,
                    country=route.empty_driving.destination.country
                )
            empty_driving = EmptyDriving(
                distance_km=route.empty_driving.distance_km,
                duration_hours=route.empty_driving.duration_hours,
                start_location=empty_start,
                end_location=empty_end
            )

        # Convert cargo specs if present
        cargo_specs = None
        if route.cargo_specs:
            cargo_specs = CargoSpecification(
                cargo_type=route.cargo_specs.cargo_type,
                weight_kg=route.cargo_specs.weight_kg,
                volume_m3=route.cargo_specs.volume_m3,
                temperature_controlled=route.cargo_specs.temperature_controlled,
                required_temp_celsius=route.cargo_specs.required_temp_celsius,
                hazmat_class=route.cargo_specs.hazmat_class
            )

        # Create route segments
        segments = []
        for segment in route.country_segments:
            start_loc = Location(
                address=segment.start_location["address"],
                latitude=segment.start_location["latitude"],
                longitude=segment.start_location["longitude"],
                country=segment.start_location["country"]
            )
            end_loc = Location(
                address=segment.end_location["address"],
                latitude=segment.end_location["latitude"],
                longitude=segment.end_location["longitude"],
                country=segment.end_location["country"]
            )
            segments.append(RouteSegment(
                start_location=start_loc,
                end_location=end_loc,
                distance_km=float(segment.distance),
                duration_hours=float(segment.duration_hours),
                country=segment.country_code,
                is_empty_driving=False,  # Regular segment
                timeline_event=None  # Can be enhanced with timeline events if needed
            ))

        return cls(
            id=str(route.id),
            cargo_id=str(route.cargo_id) if route.cargo_id else None,
            origin=origin,
            destination=destination,
            transport_type=route.transport_type,
            pickup_time=route.pickup_time,
            delivery_time=route.delivery_time,
            cargo_specs=cargo_specs,
            distance_km=route.distance_km,
            duration_hours=route.duration_hours,
            empty_driving=empty_driving,
            segments=segments,
            is_feasible=route.is_feasible,
            feasibility_notes=route.route_metadata.get('feasibility_notes') if route.route_metadata else None,
            created_at=route.created_at
        )


class CostBreakdown(BaseModel):
    """Cost breakdown model with detailed per-country and component costs."""
    route_id: str
    
    # Distance-based components
    fuel_costs: Dict[str, Decimal] = Field(..., description="Fuel costs per country")
    toll_costs: Dict[str, Decimal] = Field(..., description="Toll costs per country")
    maintenance_costs: Dict[str, Decimal] = Field(..., description="Maintenance costs per country")
    
    # Time-based components
    driver_costs: Dict[str, Decimal] = Field(..., description="Driver costs per country")
    rest_period_costs: Decimal = Field(..., description="Costs for mandatory rest periods")
    loading_unloading_costs: Decimal = Field(..., description="Costs for loading/unloading operations")
    
    # Empty driving components
    empty_driving_costs: Dict[str, Dict[str, Decimal]] = Field(
        ...,
        description="Empty driving costs per country and type (fuel, toll, driver)"
    )
    
    # Additional costs
    cargo_specific_costs: Dict[str, Decimal] = Field(..., description="Costs specific to cargo type")
    overheads: Dict[str, Decimal] = Field(..., description="Overhead costs by category")
    
    # Totals
    subtotal_distance_based: Decimal = Field(..., description="Total of all distance-based costs")
    subtotal_time_based: Decimal = Field(..., description="Total of all time-based costs")
    subtotal_empty_driving: Decimal = Field(..., description="Total of all empty driving costs")
    total_cost: Decimal = Field(..., description="Total cost including all components")
    currency: str = Field(default="EUR", description="Currency for all monetary values")

    @validator('fuel_costs', 'toll_costs', 'maintenance_costs', 'driver_costs')
    def validate_country_costs(cls, v):
        """Validate that all country-specific costs are positive."""
        for cost in v.values():
            if cost < 0:
                raise ValueError("Country-specific costs cannot be negative")
        return v

    @validator('empty_driving_costs')
    def validate_empty_driving_costs(cls, v):
        """Validate empty driving costs structure and values."""
        valid_types = {'fuel', 'toll', 'driver'}
        for country_costs in v.values():
            if not all(cost_type in valid_types for cost_type in country_costs):
                raise ValueError("Invalid empty driving cost type")
            if any(cost < 0 for cost in country_costs.values()):
                raise ValueError("Empty driving costs cannot be negative")
        return v


class CostSettings(BaseModel):
    """Enhanced cost settings model with detailed rates and factors."""
    # Per-country base rates
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
    
    # Time-based cost rates
    rest_period_rate: Decimal = Field(..., gt=0)
    loading_unloading_rate: Decimal = Field(..., gt=0)
    
    # Vehicle-related costs
    maintenance_rate_per_km: Decimal = Field(..., gt=0)
    
    # Empty driving factors
    empty_driving_factors: Dict[str, Decimal] = Field(
        ...,
        description="Factors for empty driving costs (fuel, toll, driver)"
    )
    
    # Cargo-specific factors
    cargo_factors: Dict[str, Dict[str, Decimal]] = Field(
        ...,
        description="Cost factors by cargo type and component"
    )
    
    # Overhead rates
    overhead_rates: Dict[str, Decimal] = Field(
        ...,
        description="Overhead rates by category"
    )
    
    # Metadata
    version: str = Field(..., description="Settings version")
    is_active: bool = Field(default=True)
    last_modified: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None

    @validator("fuel_prices", "toll_rates", "driver_rates", "overhead_rates")
    def validate_positive_rates(cls, v):
        """Validate that all rates are positive."""
        if any(rate <= 0 for rate in v.values()):
            raise ValueError("All rates must be positive")
        return v

    @validator("empty_driving_factors")
    def validate_factors(cls, v):
        """Validate empty driving factors."""
        valid_types = {"fuel", "toll", "driver"}
        if not all(factor_type in valid_types for factor_type in v):
            raise ValueError("Invalid empty driving factor type")
        if any(factor <= 0 for factor in v.values()):
            raise ValueError("Factors must be positive")
        return v

    @validator("cargo_factors")
    def validate_cargo_factors(cls, v):
        """Validate cargo-specific factors."""
        valid_components = {"fuel", "toll", "time"}
        for cargo_type, factors in v.items():
            if not all(component in valid_components for component in factors):
                raise ValueError(f"Invalid cost component for cargo type {cargo_type}")
            if any(factor <= 0 for factor in factors.values()):
                raise ValueError(f"All factors for cargo type {cargo_type} must be positive")
        return v

    @validator('last_modified')
    def ensure_timezone(cls, v):
        """Ensure datetime has timezone information."""
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        return v


class TransportSettings(BaseModel):
    """Transport settings model."""
    # Vehicle types and specifications
    vehicle_types: Dict[str, Dict[str, float]] = Field(
        ...,
        description="Vehicle specifications by type (e.g., dimensions, capacity)"
    )
    
    # Equipment settings
    equipment_types: Dict[str, Dict[str, float]] = Field(
        ...,
        description="Equipment specifications and costs"
    )
    
    # Cargo types and specifications
    cargo_types: Dict[str, Dict[str, float]] = Field(
        ...,
        description="Cargo type specifications and requirements"
    )
    
    # Loading/unloading settings
    loading_time_minutes: Dict[str, int] = Field(
        ...,
        description="Loading time by cargo type"
    )
    unloading_time_minutes: Dict[str, int] = Field(
        ...,
        description="Unloading time by cargo type"
    )
    
    # Driver settings
    max_driving_hours: float = Field(..., gt=0)
    required_rest_hours: float = Field(..., gt=0)
    max_working_days: int = Field(..., gt=0)


class SystemSettings(BaseModel):
    """System settings model."""
    # API configuration
    api_url: str = Field(..., description="Base URL for API")
    api_version: str = Field(..., description="API version")
    request_timeout_seconds: int = Field(..., gt=0)
    
    # Default values
    default_currency: str = Field(default="EUR")
    default_language: str = Field(default="en")
    
    # Feature flags
    enable_cost_history: bool = Field(default=True)
    enable_route_optimization: bool = Field(default=True)
    enable_real_time_tracking: bool = Field(default=False)
    
    # Integration settings
    maps_provider: str = Field(default="google")
    geocoding_provider: str = Field(default="google")
    
    # Business rules
    min_margin_percent: float = Field(..., ge=0, le=100)
    max_margin_percent: float = Field(..., ge=0, le=100)
    price_rounding_decimals: int = Field(default=2)


class OfferCreateRequest(BaseModel):
    """Request model for creating an offer."""
    route_id: str
    margin: float
    total_cost: Optional[float] = None
    metadata: Optional[Dict] = None
    created_by: Optional[str] = None
    status: Optional[str] = "draft"

    @validator('margin')
    def validate_margin(cls, v):
        """Validate margin is non-negative."""
        if v < 0:
            raise ValueError('margin must be non-negative')
        return v


class OfferUpdateRequest(BaseModel):
    """Request model for updating an offer."""
    margin: Optional[float] = None
    status: Optional[str] = None
    metadata: Optional[Dict] = None
    modified_by: Optional[str] = None
    change_reason: Optional[str] = None
    
    @validator('margin')
    def validate_margin(cls, v):
        """Validate margin is non-negative if provided."""
        if v is not None and v < 0:
            raise ValueError("Margin must be non-negative")
        return v
    
    @validator('status')
    def validate_status(cls, v):
        """Validate status if provided."""
        if v is not None and v not in {"draft", "active", "archived"}:
            raise ValueError("Status must be one of: draft, active, archived")
        return v


class OfferHistoryResponse(BaseModel):
    """Response model for offer history entries."""
    offer_id: str
    version: str
    status: str
    margin: float
    final_price: float
    fun_fact: Optional[str]
    extra_data: Optional[Dict]
    changed_at: datetime
    changed_by: Optional[str]
    change_reason: Optional[str]
    
    @validator('changed_at')
    def ensure_timezone(cls, v):
        """Ensure datetime has timezone information."""
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        return v

    @classmethod
    def from_domain(cls, history: OfferHistory) -> 'OfferHistoryResponse':
        """Convert domain model to response model."""
        return cls(
            offer_id=str(history.offer_id),
            version=history.version,
            status=history.status,
            margin=float(history.margin),
            final_price=float(history.final_price),
            fun_fact=history.fun_fact,
            extra_data=history.extra_data,
            changed_at=history.changed_at,
            changed_by=history.changed_by,
            change_reason=history.change_reason
        )


class OfferResponse(BaseModel):
    """Response model for offers."""
    id: str
    route_id: str
    version: str
    status: str
    total_cost: float
    margin: float
    final_price: float
    fun_fact: Optional[str]
    metadata: Optional[Dict]
    created_at: datetime
    created_by: Optional[str]
    modified_at: datetime
    modified_by: Optional[str]
    is_active: bool
    history: Optional[List[OfferHistoryResponse]] = None
    
    @validator('created_at', 'modified_at')
    def ensure_timezone(cls, v):
        """Ensure datetime has timezone information."""
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        return v

    @classmethod
    def from_domain(cls, offer: Offer) -> 'OfferResponse':
        """Convert domain model to response model."""
        return cls(
            id=str(offer.id),
            route_id=str(offer.route_id),
            version=offer.version,
            status=offer.status,
            total_cost=float(offer.total_cost),
            margin=float(offer.margin),
            final_price=float(offer.final_price),
            fun_fact=offer.fun_fact,
            metadata=offer.metadata,
            created_at=offer.created_at,
            created_by=offer.created_by,
            modified_at=offer.modified_at,
            modified_by=offer.modified_by,
            is_active=offer.is_active,
            history=None  # History is populated separately when requested
        )


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

    @validator('calculation_date')
    def ensure_timezone(cls, v):
        """Ensure datetime has timezone information."""
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        return v


class ValidationResult(BaseModel):
    """Validation result model."""
    is_valid: bool
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    validation_date: datetime = Field(default_factory=datetime.utcnow)

    @validator('validation_date')
    def ensure_timezone(cls, v):
        """Ensure datetime has timezone information."""
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        return v


class CostSettingsUpdateResponse(BaseModel):
    """Response model for cost settings update."""
    message: str
    updated_at: datetime

    @validator('updated_at')
    def ensure_timezone(cls, v):
        """Ensure datetime has timezone information."""
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        return v


class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str
    code: Optional[str] = None
    details: Optional[str] = None
