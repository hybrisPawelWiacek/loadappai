"""Cargo-related domain entities."""

from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, ValidationInfo

from .route import ExtensibleEntity


class CargoSpecification(BaseModel):
    """Cargo specifications affecting cost calculations."""
    cargo_type: str
    weight_kg: float = Field(gt=0)
    volume_m3: float = Field(gt=0)
    temperature_controlled: bool = False
    required_temp_celsius: Optional[float] = None
    special_handling: List[str] = Field(default_factory=list)
    hazmat_class: Optional[str] = None

    @field_validator('required_temp_celsius')
    def validate_temperature(cls, v: Optional[float], info: ValidationInfo) -> Optional[float]:
        """Validate temperature requirements."""
        if info.data.get('temperature_controlled', False) and v is None:
            raise ValueError("required_temp_celsius must be set when temperature_controlled is True")
        return v


class Cargo(ExtensibleEntity):
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
