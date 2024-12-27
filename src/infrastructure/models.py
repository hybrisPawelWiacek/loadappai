"""SQLAlchemy models for the application."""
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Index,
                       Integer, String, Text, event, Numeric, JSON)
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator

from src.domain.entities import transport as domain_transport
from src.domain.entities import vehicle as domain_vehicle
from src.infrastructure.database import Base


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


def utcnow_with_timezone():
    """Return current UTC time with timezone info."""
    return datetime.now(timezone.utc)


def ensure_timezone(dt: datetime) -> datetime:
    """Ensure datetime has timezone info, assuming UTC if naive."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class RouteStatus(str, Enum):
    """Route status enumeration."""
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class OfferStatus(str, Enum):
    """Offer status enumeration."""
    DRAFT = "draft"
    SENT = "sent"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class CalculationMethod(str, Enum):
    """Cost calculation method enumeration."""
    STANDARD = "standard"
    DETAILED = "detailed"
    ESTIMATED = "estimated"


class JSONEncodedDict(TypeDecorator):
    """Represents an immutable structure as a json-encoded string."""

    impl = JSON
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> Any:
        """Convert Python object to JSON string."""
        if value is None:
            return None
        if isinstance(value, dict):
            # If it's already a dict, just convert Decimal values
            result = value.copy()
        elif isinstance(value, (list, set)):
            return list(value)
        else:
            # Try to convert to dict if it's not already one
            try:
                result = dict(value)
            except (TypeError, ValueError):
                return value

        # Convert Decimal values to float for JSON serialization
        for k, v in result.items():
            if isinstance(v, Decimal):
                result[k] = float(v)
        return result

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        """Convert JSON string back to Python object."""
        if value is None:
            return None
        if isinstance(value, (dict, list)):
            return value
        try:
            return dict(value)
        except (TypeError, ValueError):
            return value


class TimezoneAwareDateTime(TypeDecorator):
    """SQLAlchemy type that ensures timezone info is preserved."""

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime, dialect: Any) -> datetime:
        """Convert datetime to UTC before storing."""
        if value is not None:
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            else:
                value = value.astimezone(timezone.utc)
        return value

    def process_result_value(self, value: datetime, dialect: Any) -> datetime:
        """Ensure timezone info is present when retrieving."""
        if value is not None and value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value


class Route(Base):
    """Route model representing a transport route."""

    __tablename__ = "routes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    origin = Column(JSONEncodedDict, nullable=False)
    destination = Column(JSONEncodedDict, nullable=False)
    pickup_time = Column(DateTime, nullable=False)
    delivery_time = Column(DateTime, nullable=False)
    transport_type = Column(String, ForeignKey("transport_types.id", ondelete="RESTRICT"), nullable=False)
    cargo_id = Column(String, ForeignKey("cargoes.id", ondelete="SET NULL"), nullable=True)
    distance_km = Column(Float, nullable=False)
    duration_hours = Column(Float, nullable=False)
    empty_driving = Column(JSONEncodedDict, nullable=True)
    is_feasible = Column(Boolean, nullable=False, default=True)
    status = Column(String, nullable=False, default=RouteStatus.DRAFT)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    route_metadata = Column(JSONEncodedDict, nullable=True)
    country_segments = Column(JSONEncodedDict, nullable=True)
    cargo_specs = Column(JSONEncodedDict, nullable=True)
    vehicle_specs = Column(JSONEncodedDict, nullable=True)
    time_windows = Column(JSONEncodedDict, nullable=True)
    extra_data = Column(JSONEncodedDict, nullable=True)

    # Relationships
    offers = relationship("Offer", back_populates="route", cascade="all, delete-orphan")
    transport = relationship("TransportType", back_populates="routes")
    cargo = relationship("Cargo", back_populates="routes")
    cost_history = relationship("CostHistory", back_populates="route", cascade="all, delete-orphan")
    cost_settings = relationship("CostSettings", back_populates="route", cascade="all, delete-orphan")
    costs = relationship("Cost", back_populates="route", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('ix_routes_status', 'status'),
        Index('ix_routes_pickup_time', 'pickup_time'),
        Index('ix_routes_delivery_time', 'delivery_time'),
        Index('ix_routes_created_at', 'created_at'),
        Index('ix_routes_is_active', 'is_active'),
    )


class Offer(Base):
    """Offer model representing a commercial offer for a route."""

    __tablename__ = "offers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    route_id = Column(String(36), ForeignKey("routes.id", ondelete="CASCADE"), nullable=False)
    cost_history_id = Column(String(36), ForeignKey("cost_history.id", ondelete="SET NULL"), nullable=True)
    total_cost = Column(Numeric(20, 10), nullable=False)
    version = Column(String, nullable=False, default="1.0")
    status = Column(String, nullable=False, default=OfferStatus.DRAFT)
    margin = Column(Numeric(20, 10), nullable=False)
    final_price = Column(Numeric(20, 10), nullable=False)
    currency = Column(String, nullable=False, default="EUR")
    fun_fact = Column(String, nullable=True)
    extra_data = Column(JSONEncodedDict, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    modified_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    valid_until = Column(DateTime, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    # Relationships
    route = relationship("Route", back_populates="offers")
    cost = relationship("CostHistory", back_populates="offers")
    history = relationship("OfferHistory", back_populates="offer", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('ix_offers_status', 'status'),
        Index('ix_offers_created_at', 'created_at'),
        Index('ix_offers_valid_until', 'valid_until'),
        Index('ix_offers_modified_at', 'modified_at'),
        Index('ix_offers_is_active', 'is_active'),
    )


class OfferHistory(Base):
    """Offer history model for tracking changes."""

    __tablename__ = "offer_history"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    offer_id = Column(String(36), ForeignKey("offers.id", ondelete="CASCADE"), nullable=False)
    version = Column(String, nullable=False, default="1.0")
    status = Column(String, nullable=False)
    margin = Column(Numeric(20, 10), nullable=False)
    final_price = Column(Numeric(20, 10), nullable=False)
    fun_fact = Column(String, nullable=True)
    extra_data = Column(JSONEncodedDict, nullable=True)
    changed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    changed_by = Column(String, nullable=True)
    change_reason = Column(String, nullable=True)

    # Relationships
    offer = relationship("Offer", back_populates="history")

    # Indexes
    __table_args__ = (
        Index('ix_offer_history_changed_at', 'changed_at'),
    )


class CostSettings(Base):
    """Cost settings model for storing pricing configurations."""

    __tablename__ = "cost_settings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    route_id = Column(String(36), ForeignKey("routes.id", ondelete="CASCADE"), nullable=False)
    version = Column(String, nullable=False)
    fuel_rates = Column(JSONEncodedDict, nullable=False, default=dict)
    toll_rates = Column(JSONEncodedDict, nullable=False, default=dict)
    driver_rates = Column(JSONEncodedDict, nullable=False, default=dict)
    overhead_rates = Column(JSONEncodedDict, nullable=False, default=dict)
    maintenance_rates = Column(JSONEncodedDict, nullable=False, default=dict)
    enabled_components = Column(JSONEncodedDict, nullable=False, default=lambda: {
        'fuel': True,
        'toll': True,
        'driver': True,
        'overhead': True,
        'maintenance': True
    })
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    modified_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String, nullable=True)
    modified_by = Column(String, nullable=True)

    # Relationships
    route = relationship("Route", back_populates="cost_settings")

    # Indexes
    __table_args__ = (
        Index('ix_cost_settings_created_at', 'created_at'),
        Index('ix_cost_settings_modified_at', 'modified_at'),
    )

    def update_json_field(self, field_name: str, value: Dict[str, Any]) -> None:
        """Update a JSON field and mark the record as modified."""
        current = getattr(self, field_name)
        if isinstance(current, dict):
            if field_name == "enabled_components":
                # For enabled_components, we want to replace existing values
                # with the new ones
                setattr(self, field_name, value)
            else:
                # For other fields, we want to do a complete replacement
                setattr(self, field_name, value)
            self.modified_at = datetime.utcnow()


@event.listens_for(CostSettings, 'before_update')
def cost_settings_before_update(mapper, connection, target):
    """Update modified_at timestamp before update."""
    target.modified_at = datetime.utcnow()


class TransportType(Base):
    """Transport type model representing different types of trucks."""

    __tablename__ = "transport_types"

    id = Column(String(36), primary_key=True)
    name = Column(String, nullable=False)
    capacity = Column(Float, nullable=False)
    emissions_class = Column(String, nullable=False)
    fuel_consumption_empty = Column(Float, nullable=False)
    fuel_consumption_loaded = Column(Float, nullable=False)
    extra_data = Column(JSONEncodedDict, nullable=True)

    # Relationships
    routes = relationship("Route", back_populates="transport")

    # Indexes
    __table_args__ = (
        Index('ix_transport_types_name', 'name'),
    )


class Cargo(Base):
    """Cargo model representing goods being transported."""

    __tablename__ = "cargoes"

    id = Column(String(36), primary_key=True)
    weight = Column(Float, nullable=False)
    value = Column(Float, nullable=False)
    special_requirements = Column(JSONEncodedDict, nullable=True)
    hazmat = Column(Boolean, nullable=False, default=False)
    extra_data = Column(JSONEncodedDict, nullable=True)

    # Relationships
    routes = relationship("Route", back_populates="cargo")

    # Indexes
    __table_args__ = (
        Index('ix_cargoes_hazmat', 'hazmat'),
    )


class TransportSettings(Base):
    """Transport settings model for vehicle and cargo configuration."""

    __tablename__ = "transport_settings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    vehicle_types = Column(JSONEncodedDict, nullable=False, default=dict)
    equipment_types = Column(JSONEncodedDict, nullable=False, default=dict)
    cargo_types = Column(JSONEncodedDict, nullable=False, default=dict)
    loading_time_minutes = Column(Integer, nullable=False)
    unloading_time_minutes = Column(Integer, nullable=False)
    max_driving_hours = Column(Float, nullable=False)
    required_rest_hours = Column(Float, nullable=False)
    max_working_days = Column(Integer, nullable=False)
    speed_limits = Column(JSONEncodedDict, nullable=False, default=dict)
    is_active = Column(Boolean, nullable=False, default=True)
    last_modified = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index('ix_transport_settings_is_active', 'is_active'),
        Index('ix_transport_settings_last_modified', 'last_modified'),
    )

    def to_domain(self) -> domain_transport.TransportSettings:
        """Convert to domain entity."""
        return domain_transport.TransportSettings(
            id=UUID(self.id),
            vehicle_types={k: domain_transport.VehicleType(**v) for k, v in self.vehicle_types.items()},
            equipment_types={k: domain_transport.EquipmentType(**v) for k, v in self.equipment_types.items()},
            cargo_types={k: domain_transport.CargoTypeConfig(**v) for k, v in self.cargo_types.items()},
            loading_time_minutes=self.loading_time_minutes,
            unloading_time_minutes=self.unloading_time_minutes,
            max_driving_hours=self.max_driving_hours,
            required_rest_hours=self.required_rest_hours,
            max_working_days=self.max_working_days,
            speed_limits={k: domain_transport.SpeedLimit(**v) for k, v in self.speed_limits.items()},
            is_active=self.is_active,
            last_modified=self.last_modified
        )

    @classmethod
    def from_domain(cls, entity: domain_transport.TransportSettings) -> 'TransportSettings':
        """Create from domain entity."""
        return cls(
            id=str(entity.id),
            vehicle_types={k: {f: v for f, v in v.model_dump().items() if v is not None} 
                         for k, v in entity.vehicle_types.items()},
            equipment_types={k: {f: v for f, v in v.model_dump().items() if v is not None}
                           for k, v in entity.equipment_types.items()},
            cargo_types={k: {f: v for f, v in v.model_dump().items() if v is not None}
                        for k, v in entity.cargo_types.items()},
            loading_time_minutes=entity.loading_time_minutes,
            unloading_time_minutes=entity.unloading_time_minutes,
            max_driving_hours=entity.max_driving_hours,
            required_rest_hours=entity.required_rest_hours,
            max_working_days=entity.max_working_days,
            speed_limits={k: {f: v for f, v in v.model_dump().items() if v is not None}
                         for k, v in entity.speed_limits.items()},
            is_active=entity.is_active,
            last_modified=entity.last_modified
        )


class Vehicle(Base):
    """SQLAlchemy model for vehicles."""

    __tablename__ = "vehicles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    vehicle_type = Column(String(50), nullable=False)
    fuel_consumption_rate = Column(Float, nullable=False)
    empty_consumption_factor = Column(Float, nullable=False)
    maintenance_rate_per_km = Column(Float, nullable=False)
    toll_class = Column(String(20), nullable=False)
    has_special_equipment = Column(Boolean, default=False)
    equipment_costs = Column(JSONEncodedDict, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    driver_id = Column(String(36), ForeignKey("drivers.id"), nullable=True)

    # Relationships
    driver = relationship("Driver", back_populates="vehicles")

    # Indexes
    __table_args__ = (
        Index('ix_vehicles_vehicle_type', 'vehicle_type'),
        Index('ix_vehicles_is_active', 'is_active'),
    )

    def to_domain(self) -> domain_vehicle.VehicleSpecification:
        """Convert to domain entity."""
        return domain_vehicle.VehicleSpecification(
            vehicle_type=self.vehicle_type,
            fuel_consumption_rate=self.fuel_consumption_rate,
            empty_consumption_factor=self.empty_consumption_factor,
            maintenance_rate_per_km=Decimal(str(self.maintenance_rate_per_km)),
            toll_class=self.toll_class,
            has_special_equipment=self.has_special_equipment,
            equipment_costs={k: Decimal(str(v)) for k, v in self.equipment_costs.items()}
        )

    @classmethod
    def from_domain(cls, entity: domain_vehicle.VehicleSpecification) -> 'Vehicle':
        """Create from domain entity."""
        return cls(
            vehicle_type=entity.vehicle_type,
            fuel_consumption_rate=entity.fuel_consumption_rate,
            empty_consumption_factor=entity.empty_consumption_factor,
            maintenance_rate_per_km=float(entity.maintenance_rate_per_km),
            toll_class=entity.toll_class,
            has_special_equipment=entity.has_special_equipment,
            equipment_costs={k: float(v) for k, v in entity.equipment_costs.items()}
        )


class SystemSettings(Base):
    """System settings model for global configuration."""

    __tablename__ = "system_settings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    api_url = Column(String, nullable=False)
    api_version = Column(String, nullable=False)
    request_timeout_seconds = Column(Integer, nullable=False)
    default_currency = Column(String, nullable=False, default="EUR")
    default_language = Column(String, nullable=False, default="en")
    enable_cost_history = Column(Boolean, nullable=False, default=True)
    enable_route_optimization = Column(Boolean, nullable=False, default=True)
    enable_real_time_tracking = Column(Boolean, nullable=False, default=False)
    maps_provider = Column(String, nullable=False, default="google")
    geocoding_provider = Column(String, nullable=False, default="google")
    min_margin_percent = Column(Float, nullable=False)
    max_margin_percent = Column(Float, nullable=False)
    price_rounding_decimals = Column(Integer, nullable=False, default=2)
    max_route_duration = Column(Text, nullable=False, default="5 days")
    is_active = Column(Boolean, nullable=False, default=True)
    last_modified = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index('ix_system_settings_is_active', 'is_active'),
    )

    def to_domain(self) -> domain_vehicle.SystemSettings:
        """Convert to domain entity."""
        return domain_vehicle.SystemSettings(
            id=UUID(self.id),
            api_url=self.api_url,
            api_version=self.api_version,
            request_timeout_seconds=self.request_timeout_seconds,
            default_currency=self.default_currency,
            default_language=self.default_language,
            enable_cost_history=self.enable_cost_history,
            enable_route_optimization=self.enable_route_optimization,
            enable_real_time_tracking=self.enable_real_time_tracking,
            maps_provider=self.maps_provider,
            geocoding_provider=self.geocoding_provider,
            min_margin_percent=Decimal(str(self.min_margin_percent)),
            max_margin_percent=Decimal(str(self.max_margin_percent)),
            price_rounding_decimals=self.price_rounding_decimals,
            max_route_duration=timedelta(days=int(self.max_route_duration.split()[0])),
            is_active=self.is_active,
            last_modified=self.last_modified
        )

    @classmethod
    def from_domain(cls, entity: domain_vehicle.SystemSettings) -> 'SystemSettings':
        """Create from domain entity."""
        return cls(
            id=str(entity.id),
            api_url=entity.api_url,
            api_version=entity.api_version,
            request_timeout_seconds=entity.request_timeout_seconds,
            default_currency=entity.default_currency,
            default_language=entity.default_language,
            enable_cost_history=entity.enable_cost_history,
            enable_route_optimization=entity.enable_route_optimization,
            enable_real_time_tracking=entity.enable_real_time_tracking,
            maps_provider=entity.maps_provider,
            geocoding_provider=entity.geocoding_provider,
            min_margin_percent=float(entity.min_margin_percent),
            max_margin_percent=float(entity.max_margin_percent),
            price_rounding_decimals=entity.price_rounding_decimals,
            max_route_duration=f"{entity.max_route_duration.days} days",
            is_active=entity.is_active,
            last_modified=entity.last_modified
        )


class CostHistory(Base):
    """Cost history model for tracking cost calculations."""

    __tablename__ = "cost_history"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    route_id = Column(String(36), ForeignKey("routes.id", ondelete="CASCADE"), nullable=False)
    calculation_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    total_cost = Column(Float, nullable=False)
    currency = Column(String, nullable=False, default="EUR")
    calculation_method = Column(String, nullable=False, default=CalculationMethod.STANDARD)
    version = Column(String, nullable=False)
    is_final = Column(Boolean, nullable=False, default=False)
    cost_components = Column(JSONEncodedDict, nullable=False)
    settings_snapshot = Column(JSONEncodedDict, nullable=False)

    # Relationships
    route = relationship("Route", back_populates="cost_history")
    offers = relationship("Offer", back_populates="cost")

    # Indexes
    __table_args__ = (
        Index('ix_cost_history_calculation_date', 'calculation_date'),
        Index('ix_cost_history_is_final', 'is_final'),
    )


class Driver(Base):
    """SQLAlchemy model for drivers."""

    __tablename__ = "drivers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    license_number = Column(String(50), unique=True, nullable=False)
    license_type = Column(String(20), nullable=False)
    license_expiry = Column(TimezoneAwareDateTime, nullable=False)
    contact_number = Column(String(20), nullable=False)
    email = Column(String(100), nullable=True)
    years_experience = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(TimezoneAwareDateTime, default=utcnow_with_timezone)
    updated_at = Column(TimezoneAwareDateTime, default=utcnow_with_timezone, onupdate=utcnow_with_timezone)
    vehicles = relationship("Vehicle", back_populates="driver")

    __table_args__ = (
        Index('ix_drivers_license_number', 'license_number'),
        Index('ix_drivers_is_active', 'is_active'),
    )


@event.listens_for(Driver, 'init')
def receive_init(target, args, kwargs):
    """Ensure timezone info is present when initializing."""
    if 'license_expiry' in kwargs:
        kwargs['license_expiry'] = ensure_timezone(kwargs['license_expiry'])


@event.listens_for(Driver, 'load')
def receive_load(target, context):
    """Ensure timezone info is present when loading from database."""
    target.license_expiry = ensure_timezone(target.license_expiry)
    target.created_at = ensure_timezone(target.created_at)
    target.updated_at = ensure_timezone(target.updated_at)


class Cost(Base):
    """Cost model for storing cost calculations."""

    __tablename__ = "costs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    route_id = Column(String(36), ForeignKey("routes.id", ondelete="CASCADE"), nullable=False)
    calculation_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    total_cost = Column(Float, nullable=False)
    currency = Column(String, nullable=False, default="EUR")
    calculation_method = Column(String, nullable=False, default=CalculationMethod.STANDARD)
    version = Column(String, nullable=False)
    is_final = Column(Boolean, nullable=False, default=False)
    cost_components = Column(JSONEncodedDict, nullable=False)
    settings_snapshot = Column(JSONEncodedDict, nullable=False)
    route = relationship("Route", back_populates="costs")

    __table_args__ = (
        Index('ix_costs_calculation_date', 'calculation_date'),
        Index('ix_costs_is_final', 'is_final'),
    )


def validate_version(version: str) -> bool:
    """Validate version format (X.Y)."""
    if not version or not isinstance(version, str):
        return False
    parts = version.split('.')
    if len(parts) != 2:
        return False
    return all(part.isdigit() for part in parts)


@event.listens_for(Offer, 'before_insert')
@event.listens_for(Offer, 'before_update')
def offer_version_validator(mapper, connection, target):
    """Validate version before insert/update."""
    if not validate_version(target.version):
        raise ValueError("Version must be in format X.Y")


@event.listens_for(OfferHistory, 'before_insert')
@event.listens_for(OfferHistory, 'before_update')
def offer_history_version_validator(mapper, connection, target):
    """Validate version before insert/update."""
    if not validate_version(target.version):
        raise ValueError("Version must be in format X.Y")
