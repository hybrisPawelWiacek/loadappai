"""Vehicle and settings-related domain entities."""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator
from pytz import UTC

from .transport import TransportSettings  # Import from transport.py


def utc_now() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(UTC)


class VehicleSpecification(BaseModel):
    """Vehicle specifications affecting cost calculations."""

    vehicle_type: str
    fuel_consumption_rate: float = Field(gt=0)
    empty_consumption_factor: float = Field(gt=0, le=1.0)
    maintenance_rate_per_km: Decimal = Field(gt=0)
    toll_class: str
    has_special_equipment: bool = False
    equipment_costs: Dict[str, Decimal] = Field(default_factory=dict)


class Vehicle(BaseModel):
    """Vehicle entity."""

    id: UUID = Field(default_factory=uuid4)
    specifications: VehicleSpecification


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

    @model_validator(mode='after')
    def validate_margins(cls, data) -> 'SystemSettings':
        """Validate that min_margin_percent is less than or equal to max_margin_percent."""
        if data.min_margin_percent > data.max_margin_percent:
            raise ValueError("min_margin_percent must be less than or equal to max_margin_percent")
        return data

    @classmethod
    def get_default(cls) -> "SystemSettings":
        """Get default system settings."""
        return cls(
            api_url="http://localhost:5001",
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
            max_margin_percent=Decimal("50"),
            price_rounding_decimals=2,
            max_route_duration=timedelta(days=5)
        )
