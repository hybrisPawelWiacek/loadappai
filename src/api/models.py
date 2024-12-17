"""API request and response models."""
from datetime import datetime
from typing import Optional
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


class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str
    code: Optional[str] = None
