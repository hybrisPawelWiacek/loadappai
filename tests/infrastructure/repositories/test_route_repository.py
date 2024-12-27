"""Tests for route repository."""
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict

import pytest
from sqlalchemy.orm import Session

from src.domain.entities.route import Route, RouteMetadata, TransportType, RouteStatus
from src.domain.value_objects import Location, EmptyDriving
from src.infrastructure.repositories.route_repository import RouteRepository
from src.infrastructure.models import Route as RouteModel
from src.domain.interfaces.exceptions.repository_errors import EntityNotFoundError


@pytest.fixture
def route_repository(db_session: Session):
    """Create a route repository instance."""
    repository = RouteRepository()
    repository.db = db_session
    return repository


@pytest.fixture
def sample_route():
    """Create a sample route."""
    pickup_time = datetime.now(timezone.utc)
    delivery_time = pickup_time + timedelta(hours=5)
    return Route(
        id=uuid.uuid4(),
        origin={
            "name": "Berlin",
            "address": "Sample St 1",
            "latitude": 52.5200,
            "longitude": 13.4050,
            "country": "DE"
        },
        destination={
            "name": "Hamburg",
            "address": "Sample St 2",
            "latitude": 53.5511,
            "longitude": 9.9937,
            "country": "DE"
        },
        pickup_time=pickup_time,
        delivery_time=delivery_time,
        transport_type=TransportType.TRUCK.value,
        cargo_id=uuid.uuid4(),
        distance_km=300,
        duration_hours=4,
        empty_driving=EmptyDriving(
            distance_km=50,
            duration_hours=1,
            origin=Location(
                name="Previous Location",
                address="Previous St 1",
                latitude=52.0,
                longitude=13.0,
                country="DE"
            )
        ),
        is_feasible=True,
        status=RouteStatus.IN_PROGRESS.value,
        metadata=RouteMetadata(
            version="1.0",
            tags=["express", "priority"],
            notes="Test route"
        )
    )


def test_create(route_repository, sample_route):
    """Test creating a route."""
    created_route = route_repository.create(sample_route)
    assert created_route is not None
    assert created_route.id == sample_route.id
    assert created_route.origin["name"] == sample_route.origin["name"]
    assert created_route.destination["name"] == sample_route.destination["name"]
    assert created_route.status == RouteStatus.IN_PROGRESS.value


def test_get_by_id(route_repository, sample_route):
    """Test getting a route by ID."""
    created_route = route_repository.create(sample_route)
    retrieved_route = route_repository.get_by_id(created_route.id)
    assert retrieved_route is not None
    assert retrieved_route.id == created_route.id
    assert retrieved_route.origin["name"] == created_route.origin["name"]
    assert retrieved_route.destination["name"] == created_route.destination["name"]


def test_get_all(route_repository, sample_route):
    """Test getting all routes."""
    route_repository.create(sample_route)
    routes = route_repository.get_all()
    assert len(routes) > 0
    assert isinstance(routes[0], Route)


def test_update(route_repository, sample_route):
    """Test updating a route."""
    created_route = route_repository.create(sample_route)
    created_route.status = RouteStatus.COMPLETED.value
    updated_route = route_repository.update(created_route.id, created_route)
    assert updated_route is not None
    assert updated_route.status == RouteStatus.COMPLETED.value


def test_delete(route_repository, sample_route):
    """Test deleting a route."""
    created_route = route_repository.create(sample_route)
    assert route_repository.delete(created_route.id) is True
    assert route_repository.get_by_id(created_route.id) is None


def test_find_by_criteria(route_repository, sample_route):
    """Test finding routes by criteria."""
    route_repository.create(sample_route)
    
    # Test finding by origin
    origin = Location(
        name="Berlin",
        address="Sample St 1",
        latitude=52.5200,
        longitude=13.4050,
        country="DE"
    )
    routes = route_repository.find_routes(origin=origin)
    assert len(routes) > 0
    assert routes[0].origin["name"] == "Berlin"

    # Test finding by status
    routes = route_repository.find_routes(status=RouteStatus.IN_PROGRESS.value)
    assert len(routes) > 0
    assert routes[0].status == RouteStatus.IN_PROGRESS.value

    # Test finding by vehicle type
    routes = route_repository.find_routes(vehicle_type=TransportType.TRUCK.value)
    assert len(routes) > 0
    assert routes[0].transport_type == TransportType.TRUCK.value


def test_nonexistent_route(route_repository):
    """Test handling of nonexistent routes."""
    nonexistent_id = uuid.uuid4()
    assert route_repository.get_by_id(nonexistent_id) is None
    with pytest.raises(EntityNotFoundError):
        route_repository.update_route_status(nonexistent_id, RouteStatus.COMPLETED.value)


def test_empty_driving_handling(route_repository, sample_route):
    """Test handling of empty driving data."""
    created_route = route_repository.create(sample_route)
    assert created_route.empty_driving is not None
    assert created_route.empty_driving.distance_km == 50
    assert created_route.empty_driving.duration_hours == 1
    assert created_route.empty_driving.origin.address == "Previous St 1"


def test_metadata_handling(route_repository, sample_route):
    """Test handling of route metadata."""
    created_route = route_repository.create(sample_route)
    metadata = route_repository.get_route_metadata(created_route.id)
    assert metadata is not None
    assert metadata["version"] == "1.0"
    assert "express" in metadata["tags"]
    assert metadata["notes"] == "Test route"


def test_get_active_routes(route_repository, sample_route):
    """Test getting active routes."""
    # Create an active route
    active_route = route_repository.create(sample_route)
    assert active_route.is_active is True

    # Create an inactive route
    inactive_route = sample_route.model_copy()
    inactive_route.id = uuid.uuid4()
    inactive_route.is_active = False
    route_repository.create(inactive_route)

    # Get active routes
    active_routes = route_repository.get_active_routes()
    assert len(active_routes) > 0
    assert all(route.is_active for route in active_routes)
    assert all(route.id != inactive_route.id for route in active_routes)


def test_update_route_status(route_repository, sample_route):
    """Test updating route status."""
    created_route = route_repository.create(sample_route)
    updated_route = route_repository.update_route_status(
        created_route.id,
        RouteStatus.COMPLETED.value,
        reason="Delivery confirmed"
    )
    assert updated_route is not None
    assert updated_route.status == RouteStatus.COMPLETED.value


def test_route_history(route_repository, sample_route):
    """Test route history tracking."""
    created_route = route_repository.create(sample_route)
    history = route_repository.get_route_history(created_route.id)
    # Currently returns empty list as history is not implemented
    assert isinstance(history, list)


def test_count(route_repository, sample_route):
    """Test route counting."""
    initial_count = route_repository.count()
    route_repository.create(sample_route)
    assert route_repository.count() == initial_count + 1
