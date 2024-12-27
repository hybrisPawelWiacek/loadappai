"""Settings-related models for API request/response handling."""
from typing import Dict, Optional
from pydantic import BaseModel, Field


class TransportSettings(BaseModel):
    """Transport settings model."""
    vehicle_types: Dict[str, Dict[str, float]] = Field(
        ...,
        description="Vehicle specifications by type (e.g., dimensions, capacity)"
    )
    equipment_types: Dict[str, Dict[str, float]] = Field(
        ...,
        description="Equipment specifications and costs"
    )
    cargo_types: Dict[str, Dict[str, float]] = Field(
        ...,
        description="Cargo type specifications and requirements"
    )
    loading_time_minutes: Dict[str, int] = Field(
        ...,
        description="Loading time by cargo type"
    )
    unloading_time_minutes: Dict[str, int] = Field(
        ...,
        description="Unloading time by cargo type"
    )
    max_driving_hours: float = Field(..., gt=0)
    required_rest_hours: float = Field(..., gt=0)
    max_working_days: int = Field(..., gt=0)


class SystemSettings(BaseModel):
    """System settings model."""
    api_url: str = Field(..., description="Base URL for API")
    api_version: str = Field(..., description="API version")
    request_timeout_seconds: int = Field(..., gt=0)
    default_currency: str = Field(default="EUR")
    default_language: str = Field(default="en")
    enable_cost_history: bool = Field(default=True)
    enable_route_optimization: bool = Field(default=True)
    enable_real_time_tracking: bool = Field(default=False)
    maps_provider: str = Field(default="google")
    geocoding_provider: str = Field(default="google")
    min_margin_percent: float = Field(..., ge=0, le=100)
    max_margin_percent: float = Field(..., ge=0, le=100)
    price_rounding_decimals: int = Field(default=2)
