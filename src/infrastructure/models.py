"""SQLAlchemy models for the application."""
import uuid
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
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
    empty_driving = Column(JSON, nullable=False)
    is_feasible = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    extra_data = Column(JSON, nullable=True)

    # Relationships
    offers = relationship("Offer", back_populates="route")
    transport = relationship("TransportType", back_populates="routes")
    cargo = relationship("Cargo", back_populates="routes")


class Offer(Base):
    """Offer model representing a commercial offer for a route."""

    __tablename__ = "offers"

    id = Column(String, primary_key=True, default=generate_uuid)
    route_id = Column(String, ForeignKey("routes.id"), nullable=False)
    total_cost = Column(Float, nullable=False)
    margin = Column(Float, nullable=False)
    final_price = Column(Float, nullable=False)
    fun_fact = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    extra_data = Column(JSON, nullable=True)

    # Relationships
    route = relationship("Route", back_populates="offers")


class CostSettings(Base):
    """Cost settings model for storing pricing configurations."""

    __tablename__ = "cost_settings"

    id = Column(String, primary_key=True)  
    fuel_price_per_liter = Column(Float, nullable=False)
    driver_daily_salary = Column(Float, nullable=False)
    toll_rates = Column(JSON, nullable=False)
    overheads = Column(JSON, nullable=False)
    cargo_factors = Column(JSON, nullable=False)
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
