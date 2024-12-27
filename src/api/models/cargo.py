"""Cargo-related models for API request/response handling."""
from typing import Optional
from pydantic import BaseModel, Field


class CargoSpecification(BaseModel):
    """Cargo specifications."""
    weight_kg: float = Field(..., gt=0)
    volume_m3: float = Field(..., gt=0)
    cargo_type: str
    hazmat_class: Optional[str] = None
    temperature_controlled: bool = False
    required_temp_celsius: Optional[float] = None
