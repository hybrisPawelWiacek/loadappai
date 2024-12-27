"""Settings models for the application."""
from datetime import datetime
from decimal import Decimal
from typing import Dict, Optional
from pydantic import BaseModel, Field


class CostSettings(BaseModel):
    """Cost settings model."""
    
    base_rate: Decimal = Field(
        ...,
        description="Base rate per kilometer"
    )
    minimum_rate: Decimal = Field(
        ...,
        description="Minimum rate for any trip"
    )
    toll_multiplier: Decimal = Field(
        ...,
        description="Multiplier for toll costs"
    )
    fuel_cost_per_km: Decimal = Field(
        ...,
        description="Fuel cost per kilometer"
    )
    last_updated: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last update timestamp"
    )


class CostSettingsUpdateRequest(BaseModel):
    """Request model for updating cost settings."""
    
    base_rate: Optional[Decimal] = Field(
        None,
        description="Base rate per kilometer"
    )
    minimum_rate: Optional[Decimal] = Field(
        None,
        description="Minimum rate for any trip"
    )
    toll_multiplier: Optional[Decimal] = Field(
        None,
        description="Multiplier for toll costs"
    )
    fuel_cost_per_km: Optional[Decimal] = Field(
        None,
        description="Fuel cost per kilometer"
    )


class TransportSettings(BaseModel):
    """Transport settings model."""
    
    vehicle_types: Dict[str, Dict] = Field(
        ...,
        description="Vehicle types and their specifications"
    )
    default_vehicle_type: str = Field(
        ...,
        description="Default vehicle type"
    )
    max_distance_per_day: Decimal = Field(
        ...,
        description="Maximum distance per day in kilometers"
    )
    rest_duration_hours: Decimal = Field(
        ...,
        description="Required rest duration in hours"
    )
    last_updated: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last update timestamp"
    )


class SystemSettings(BaseModel):
    """System settings model."""
    
    cache_ttl: int = Field(
        ...,
        description="Cache time-to-live in seconds"
    )
    max_retries: int = Field(
        ...,
        description="Maximum number of retries for external services"
    )
    retry_delay: int = Field(
        ...,
        description="Delay between retries in seconds"
    )
    log_level: str = Field(
        ...,
        description="Logging level"
    )
    last_updated: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last update timestamp"
    )
