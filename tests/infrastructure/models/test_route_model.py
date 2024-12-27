"""Tests for the Route SQLAlchemy model."""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from src.infrastructure.models import Route, TransportType, Cargo, RouteStatus
from src.domain.value_objects.location import Location
from src.domain.value_objects.route import CountrySegment, EmptyDriving


def decimal_to_float(obj):
    """Convert Decimal objects to float for JSON serialization."""
    if isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decimal_to_float(x) for x in obj]
    elif isinstance(obj, Decimal):
        return float(obj)
    return obj


@pytest.fixture
def transport_type(db_session):
    """Create a test transport type."""
    transport = TransportType(
        id="test-transport",
        name="Test Transport",
        capacity=1000.0,
        emissions_class="Euro 6",
        fuel_consumption_empty=20.0,
        fuel_consumption_loaded=25.0
    )
    db_session.add(transport)
    db_session.commit()
    return transport

@pytest.fixture
def cargo(db_session):
    """Create a test cargo."""
    cargo = Cargo(
        id="test-cargo",
        weight=500.0,
        value=1000.0,
        special_requirements={"temperature": "controlled"},
        hazmat=False
    )
    db_session.add(cargo)
    db_session.commit()
    return cargo

@pytest.fixture
def route_data(transport_type, cargo):
    """Create test route data."""
    now = datetime.utcnow()
    origin = Location(
        latitude=52.5200,
        longitude=13.4050,
        address="Berlin, Germany",
        country="DE"
    )
    destination = Location(
        latitude=48.8566,
        longitude=2.3522,
        address="Paris, France",
        country="FR"
    )
    empty_driving = EmptyDriving(
        distance_km=100.0,
        duration_hours=2.0,
        origin=origin,
        destination=destination,
        segments=[
            CountrySegment(
                country_code="DE",
                distance=Decimal("50.0"),
                duration_hours=Decimal("1.0")
            ),
            CountrySegment(
                country_code="FR",
                distance=Decimal("50.0"),
                duration_hours=Decimal("1.0")
            )
        ]
    )
    return {
        "origin": origin.model_dump(),
        "destination": destination.model_dump(),
        "pickup_time": now,
        "delivery_time": now + timedelta(days=1),
        "transport_type": transport_type.id,
        "cargo_id": cargo.id,
        "distance_km": 1000.0,
        "duration_hours": 12.0,
        "empty_driving": decimal_to_float(empty_driving.model_dump()),
        "is_feasible": True,
        "status": RouteStatus.DRAFT,
        "route_metadata": {"priority": "high"},
        "country_segments": [
            {
                "country_code": "DE",
                "distance": 500.0,
                "duration_hours": 6.0
            },
            {
                "country_code": "FR",
                "distance": 500.0,
                "duration_hours": 6.0
            }
        ]
    }

def test_create_route(db_session, route_data):
    """Test creating a new route."""
    route = Route(**route_data)
    db_session.add(route)
    db_session.commit()

    assert route.id is not None
    assert route.origin == route_data["origin"]
    assert route.destination == route_data["destination"]
    assert route.pickup_time == route_data["pickup_time"]
    assert route.delivery_time == route_data["delivery_time"]
    assert route.transport_type == route_data["transport_type"]
    assert route.cargo_id == route_data["cargo_id"]
    assert route.distance_km == route_data["distance_km"]
    assert route.duration_hours == route_data["duration_hours"]
    assert route.empty_driving == route_data["empty_driving"]
    assert route.is_feasible == route_data["is_feasible"]
    assert route.status == route_data["status"]
    assert route.route_metadata == route_data["route_metadata"]
    assert route.country_segments == route_data["country_segments"]
    assert route.created_at is not None

def test_route_relationships(db_session, route_data):
    """Test route relationships."""
    route = Route(**route_data)
    db_session.add(route)
    db_session.commit()

    # Test transport relationship
    assert route.transport.name == "Test Transport"
    assert route in route.transport.routes

    # Test cargo relationship
    assert route.cargo.weight == 500.0
    assert route in route.cargo.routes

def test_route_status_transitions(db_session, route_data):
    """Test route status transitions."""
    route = Route(**route_data)
    db_session.add(route)
    db_session.commit()

    assert route.status == RouteStatus.DRAFT

    # Test status transitions
    route.status = RouteStatus.ACTIVE
    db_session.commit()
    assert route.status == RouteStatus.ACTIVE

    route.status = RouteStatus.COMPLETED
    db_session.commit()
    assert route.status == RouteStatus.COMPLETED

def test_route_json_fields(db_session, route_data):
    """Test JSON encoded fields."""
    route = Route(**route_data)
    db_session.add(route)
    db_session.commit()

    # Test origin/destination JSON encoding
    assert isinstance(route.origin, dict)
    assert route.origin["latitude"] == 52.5200
    assert route.origin["longitude"] == 13.4050

    # Test empty_driving JSON encoding
    assert isinstance(route.empty_driving, dict)
    assert route.empty_driving["distance_km"] == 100.0
    assert len(route.empty_driving["segments"]) == 2

    # Test route_metadata JSON encoding
    assert isinstance(route.route_metadata, dict)
    assert route.route_metadata["priority"] == "high"

def test_route_indexes(db_session, route_data):
    """Test route indexes."""
    route = Route(**route_data)
    db_session.add(route)
    db_session.commit()

    # Test status index
    found_route = db_session.query(Route).filter(
        Route.status == RouteStatus.DRAFT
    ).first()
    assert found_route.id == route.id

    # Test pickup_time index
    found_route = db_session.query(Route).filter(
        Route.pickup_time == route_data["pickup_time"]
    ).first()
    assert found_route.id == route.id

    # Test delivery_time index
    found_route = db_session.query(Route).filter(
        Route.delivery_time == route_data["delivery_time"]
    ).first()
    assert found_route.id == route.id
