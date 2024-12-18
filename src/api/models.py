"""API request and response models."""
from datetime import datetime
from typing import Optional, Dict
from pydantic import BaseModel, Field, validator
from decimal import Decimal


class Location(BaseModel):
    """Location model with address and coordinates."""
    address: str
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class EmptyDriving(BaseModel):
    """Empty driving details."""
    distance_km: float
    duration_hours: float


class RouteCreateRequest(BaseModel):
    """Request model for route creation."""
    origin: Location
    destination: Location
    pickup_time: datetime
    delivery_time: datetime
    transport_type: str
    cargo_id: Optional[str] = None

    @validator('delivery_time')
    def delivery_after_pickup(cls, v, values):
        """Validate that delivery time is after pickup time."""
        if 'pickup_time' in values and v <= values['pickup_time']:
            raise ValueError('delivery_time must be after pickup_time')
        return v


class RouteResponse(BaseModel):
    """Response model for route operations."""
    id: str
    origin: Location
    destination: Location
    pickup_time: datetime
    delivery_time: datetime
    transport_type: str
    cargo_id: Optional[str]
    distance_km: float
    duration_hours: float
    empty_driving: EmptyDriving
    is_feasible: bool
    created_at: datetime


class CostBreakdown(BaseModel):
    """Cost breakdown model."""
    route_id: str
    fuel_cost: Decimal
    toll_cost: Decimal
    driver_cost: Decimal
    overheads: Decimal
    cargo_specific_costs: Dict[str, Decimal]
    total_cost: Decimal
    currency: str = "EUR"


class OfferCreateRequest(BaseModel):
    """Request model for offer creation."""
    route_id: str
    margin: Decimal = Field(..., ge=0, le=1)  # Margin between 0 and 1 (0% to 100%)


class OfferResponse(BaseModel):
    """Response model for offer operations."""
    id: str
    route_id: str
    total_cost: Decimal
    margin: Decimal
    final_price: Decimal
    fun_fact: str
    created_at: datetime


class CostSettings(BaseModel):
    """Cost settings model."""
    fuel_price_per_liter: Decimal = Field(..., gt=0)
    driver_daily_salary: Decimal = Field(..., gt=0)
    toll_rates: Dict[str, Decimal] = Field(..., description="Per-country toll rates")
    overheads: Dict[str, Decimal]
    cargo_factors: Dict[str, Decimal]

    @validator('toll_rates')
    def validate_toll_rates(cls, v):
        """Validate that toll rates are positive."""
        for rate in v.values():
            if rate <= 0:
                raise ValueError("Toll rates must be positive")
        return v

    @validator('overheads', 'cargo_factors')
    def validate_cost_factors(cls, v):
        """Validate that all cost factors are non-negative."""
        for cost in v.values():
            if cost < 0:
                raise ValueError("Cost factors cannot be negative")
        return v


class CostSettingsUpdateResponse(BaseModel):
    """Response model for cost settings update."""
    message: str
    updated_at: datetime


class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str
    code: Optional[str] = None
    details: Optional[str] = None
