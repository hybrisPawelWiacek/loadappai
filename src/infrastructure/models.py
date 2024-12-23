"""SQLAlchemy models for the application."""
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, String, Integer, Interval
from sqlalchemy.orm import relationship

from src.infrastructure.database import Base


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


class Route(Base):
    """Route model representing a transport route."""

    __tablename__ = "routes"

    id = Column(String, primary_key=True, default=generate_uuid)
    origin = Column(JSON, nullable=False)
    destination = Column(JSON, nullable=False)
    pickup_time = Column(DateTime, nullable=False)
    delivery_time = Column(DateTime, nullable=False)
    transport_type = Column(String, ForeignKey("transport_types.id"), nullable=False)
    cargo_id = Column(String, ForeignKey("cargoes.id"), nullable=True)
    distance_km = Column(Float, nullable=False)
    duration_hours = Column(Float, nullable=False)
    empty_driving = Column(JSON, nullable=True)
    is_feasible = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    route_metadata = Column(JSON, nullable=True)
    country_segments = Column(JSON, nullable=True)
    cargo_specs = Column(JSON, nullable=True)
    vehicle_specs = Column(JSON, nullable=True)
    time_windows = Column(JSON, nullable=True)
    extra_data = Column(JSON, nullable=True)

    # Relationships
    offers = relationship("Offer", back_populates="route")
    transport = relationship("TransportType", back_populates="routes")
    cargo = relationship("Cargo", back_populates="routes")
    cost_history = relationship("CostHistory", back_populates="route")


class Offer(Base):
    """Offer model representing a commercial offer for a route."""

    __tablename__ = "offers"

    id = Column(String, primary_key=True, default=generate_uuid)
    route_id = Column(String, ForeignKey("routes.id"), nullable=False)
    cost_id = Column(String, ForeignKey("cost_history.id"), nullable=False)
    total_cost = Column(Float, nullable=False)
    margin = Column(Float, nullable=False)
    final_price = Column(Float, nullable=False)
    fun_fact = Column(String, nullable=True)
    status = Column(String, nullable=False, default="draft")
    version = Column(String, nullable=False, default="1.0")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    modified_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_by = Column(String, nullable=True)
    modified_by = Column(String, nullable=True)
    extra_data = Column(JSON, nullable=True)

    # Relationships
    route = relationship("Route", back_populates="offers")
    cost = relationship("CostHistory", back_populates="offers")
    history = relationship("OfferHistory", back_populates="offer")


class OfferHistory(Base):
    """Offer history model for tracking changes."""

    __tablename__ = "offer_history"

    id = Column(String, primary_key=True, default=generate_uuid)
    offer_id = Column(String, ForeignKey("offers.id"), nullable=False)
    version = Column(String, nullable=False)
    status = Column(String, nullable=False)
    margin = Column(Float, nullable=False)
    final_price = Column(Float, nullable=False)
    fun_fact = Column(String, nullable=True)
    extra_data = Column(JSON, nullable=True)
    changed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    changed_by = Column(String, nullable=True)
    change_reason = Column(String, nullable=True)

    # Relationships
    offer = relationship("Offer", back_populates="history")


class CostSettings(Base):
    """Cost settings model for storing pricing configurations."""

    __tablename__ = "cost_settings"

    id = Column(String, primary_key=True, default=generate_uuid)
    fuel_prices = Column(JSON, nullable=False)
    toll_rates = Column(JSON, nullable=False)
    driver_rates = Column(JSON, nullable=False)
    rest_period_rate = Column(Float, nullable=False)
    loading_unloading_rate = Column(Float, nullable=False)
    maintenance_rate_per_km = Column(Float, nullable=False)
    empty_driving_factors = Column(JSON, nullable=False)
    cargo_factors = Column(JSON, nullable=False)
    overhead_rates = Column(JSON, nullable=False)
    version = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    last_modified = Column(DateTime, nullable=False, default=datetime.utcnow)
    extra_data = Column(JSON, nullable=True)


class TransportType(Base):
    """Transport type model representing different types of trucks."""

    __tablename__ = "transport_types"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    capacity = Column(Float, nullable=False)
    emissions_class = Column(String, nullable=False)
    fuel_consumption_empty = Column(Float, nullable=False)
    fuel_consumption_loaded = Column(Float, nullable=False)
    extra_data = Column(JSON, nullable=True)

    # Relationships
    routes = relationship("Route", back_populates="transport")


class Cargo(Base):
    """Cargo model representing goods being transported."""

    __tablename__ = "cargoes"

    id = Column(String, primary_key=True)
    weight = Column(Float, nullable=False)
    value = Column(Float, nullable=False)
    special_requirements = Column(JSON, nullable=True)
    hazmat = Column(Boolean, nullable=False, default=False)
    extra_data = Column(JSON, nullable=True)

    # Relationships
    routes = relationship("Route", back_populates="cargo")


class TransportSettings(Base):
    """Transport settings model for vehicle and cargo configuration."""

    __tablename__ = "transport_settings"

    id = Column(String, primary_key=True, default=generate_uuid)
    vehicle_types = Column(JSON, nullable=False)
    equipment_types = Column(JSON, nullable=False)
    cargo_types = Column(JSON, nullable=False)
    loading_time_minutes = Column(Integer, nullable=False)
    unloading_time_minutes = Column(Integer, nullable=False)
    max_driving_hours = Column(Float, nullable=False)
    required_rest_hours = Column(Float, nullable=False)
    max_working_days = Column(Integer, nullable=False)
    speed_limits = Column(JSON, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    last_modified = Column(DateTime, nullable=False, default=datetime.utcnow)


class SystemSettings(Base):
    """System settings model for global configuration."""

    __tablename__ = "system_settings"

    id = Column(String, primary_key=True, default=generate_uuid)
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
    max_route_duration = Column(Interval, nullable=False, default=timedelta(days=5))
    is_active = Column(Boolean, nullable=False, default=True)
    last_modified = Column(DateTime, nullable=False, default=datetime.utcnow)


class CostHistory(Base):
    """Cost history model for tracking cost calculations."""

    __tablename__ = "cost_history"

    id = Column(String, primary_key=True, default=generate_uuid)
    route_id = Column(String, ForeignKey("routes.id"), nullable=False)
    calculation_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    total_cost = Column(Float, nullable=False)
    currency = Column(String, nullable=False, default="EUR")
    calculation_method = Column(String, nullable=False)
    version = Column(String, nullable=False)
    is_final = Column(Boolean, nullable=False, default=False)
    cost_components = Column(JSON, nullable=False)
    settings_snapshot = Column(JSON, nullable=False)

    # Relationships
    route = relationship("Route", back_populates="cost_history")
    offers = relationship("Offer", back_populates="cost")
