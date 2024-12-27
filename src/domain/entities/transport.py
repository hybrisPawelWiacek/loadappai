"""Transport-related domain entities."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, ValidationInfo
from pytz import UTC


def utc_now() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(UTC)


class VehicleType(BaseModel):
    """Vehicle type configuration."""
    name: str
    capacity_kg: float = Field(gt=0)
    volume_m3: float = Field(gt=0)
    length_m: float = Field(gt=0)
    width_m: float = Field(gt=0)
    height_m: float = Field(gt=0)
    emissions_class: str
    fuel_consumption_empty: float = Field(gt=0)
    fuel_consumption_loaded: float = Field(gt=0)
    equipment_requirements: List[str] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None


class EquipmentType(BaseModel):
    """Equipment type configuration."""
    name: str
    description: str
    weight_kg: float = Field(ge=0)
    compatible_vehicles: List[str] = Field(default_factory=list)
    compatible_cargo_types: List[str] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None


class CargoTypeConfig(BaseModel):
    """Cargo type configuration."""
    name: str
    description: str
    requires_temperature_control: bool = False
    default_temp_range: Optional[Dict[str, float]] = None  # {"min": -20, "max": -18}
    special_handling_requirements: List[str] = Field(default_factory=list)
    compatible_vehicles: List[str] = Field(default_factory=list)
    required_equipment: List[str] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None

    @field_validator('default_temp_range')
    def validate_temp_range(cls, v: Optional[Dict[str, float]], info: ValidationInfo) -> Optional[Dict[str, float]]:
        """Validate temperature range if temperature control is required."""
        if info.data.get('requires_temperature_control', False):
            if not v or 'min' not in v or 'max' not in v:
                raise ValueError("Temperature range must be specified when temperature control is required")
            if v['min'] > v['max']:
                raise ValueError("Minimum temperature must be less than maximum temperature")
        return v


class SpeedLimit(BaseModel):
    """Speed limit configuration."""
    country: str
    highway_kmh: float = Field(gt=0)
    rural_kmh: float = Field(gt=0)
    urban_kmh: float = Field(gt=0)
    vehicle_specific: Optional[Dict[str, Dict[str, float]]] = None  # {"truck_40t": {"highway": 80}}


class TransportSettings(BaseModel):
    """Transport settings for vehicle and cargo configuration."""
    id: UUID = Field(default_factory=uuid4)
    vehicle_types: Dict[str, VehicleType]
    equipment_types: Dict[str, EquipmentType]
    cargo_types: Dict[str, CargoTypeConfig]
    loading_time_minutes: int = Field(gt=0)
    unloading_time_minutes: int = Field(gt=0)
    max_driving_hours: float = Field(gt=0)
    required_rest_hours: float = Field(gt=0)
    max_working_days: int = Field(gt=0, le=7)
    speed_limits: Dict[str, SpeedLimit]
    is_active: bool = True
    last_modified: datetime = Field(default_factory=utc_now)
    metadata: Optional[Dict[str, Any]] = None

    @field_validator('max_driving_hours')
    def validate_driving_hours(cls, v: float) -> float:
        """Validate max driving hours."""
        if v > 24:
            raise ValueError("Maximum driving hours cannot exceed 24")
        return v

    @field_validator('required_rest_hours')
    def validate_rest_hours(cls, v: float, info: ValidationInfo) -> float:
        """Validate required rest hours."""
        max_driving = info.data.get('max_driving_hours', 24)
        if v + max_driving > 24:
            raise ValueError("Sum of driving and rest hours cannot exceed 24")
        return v

    @field_validator('vehicle_types')
    def validate_vehicle_types(cls, v: Dict[str, VehicleType]) -> Dict[str, VehicleType]:
        """Validate that there is at least one vehicle type."""
        if not v:
            raise ValueError("At least one vehicle type must be defined")
        return v

    @field_validator('cargo_types')
    def validate_cargo_types(cls, v: Dict[str, CargoTypeConfig]) -> Dict[str, CargoTypeConfig]:
        """Validate cargo type configurations."""
        if not v:
            raise ValueError("At least one cargo type must be defined")
        return v

    @field_validator('speed_limits')
    def validate_speed_limits(cls, v: Dict[str, SpeedLimit]) -> Dict[str, SpeedLimit]:
        """Validate speed limit configurations."""
        if not v:
            raise ValueError("At least one country speed limit must be defined")
        return v

    @classmethod
    def get_default(cls) -> 'TransportSettings':
        """Get default transport settings."""
        return cls(
            vehicle_types={
                "truck_40t": VehicleType(
                    name="40t Truck",
                    capacity_kg=40000,
                    volume_m3=90,
                    length_m=13.6,
                    width_m=2.4,
                    height_m=2.6,
                    emissions_class="EURO6",
                    fuel_consumption_empty=25.0,
                    fuel_consumption_loaded=32.0
                )
            },
            equipment_types={
                "tail_lift": EquipmentType(
                    name="Tail Lift",
                    description="Hydraulic lift for loading/unloading",
                    weight_kg=500,
                    compatible_vehicles=["truck_40t"],
                    compatible_cargo_types=["pallets", "machinery"]
                )
            },
            cargo_types={
                "general": CargoTypeConfig(
                    name="General Cargo",
                    description="Standard non-temperature controlled cargo",
                    requires_temperature_control=False,
                    compatible_vehicles=["truck_40t"],
                    required_equipment=[]
                )
            },
            loading_time_minutes=45,
            unloading_time_minutes=45,
            max_driving_hours=9.0,
            required_rest_hours=11.0,
            max_working_days=5,
            speed_limits={
                "EU": SpeedLimit(
                    country="EU",
                    highway_kmh=90,
                    rural_kmh=80,
                    urban_kmh=50
                )
            }
        )
