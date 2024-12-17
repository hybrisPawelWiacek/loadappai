"""Tests for the route repository."""
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from src.domain.entities import Route as RouteEntity
from src.domain.value_objects import EmptyDriving, Location, RouteMetadata
from src.infrastructure.models import Route as RouteModel
from src.infrastructure.repositories.route_repository import RouteRepository


@pytest.fixture
def route_repository(db_session: Session):
    """Create a route repository instance."""
    return RouteRepository(db_session)


@pytest.fixture
def valid_route_entity():
    """Create a valid route entity."""
    return RouteEntity(
        id=str(uuid4()),
        origin=Location(
            address="Test Origin",
            latitude=52.2297,
            longitude=21.0122
        ),
        destination=Location(
            address="Test Destination",
            latitude=53.2297,
            longitude=22.0122
        ),
        pickup_time=datetime.fromtimestamp(datetime.now().timestamp(), tz=timezone.utc),
        delivery_time=datetime.fromtimestamp((datetime.now() + timedelta(days=1)).timestamp(), tz=timezone.utc),
        transport_type="standard",
        cargo_id=None,
        distance_km=500.0,
        duration_hours=8.0,
        empty_driving=EmptyDriving(
            distance_km=50.0,
            duration_hours=1.0
        ),
        is_feasible=True,
        metadata=RouteMetadata(
            weather_data={"test": "data"}
        )
    )


def test_create_route(route_repository: RouteRepository, valid_route_entity: RouteEntity):
    """Test creating a new route."""
    created_route = route_repository.create(valid_route_entity)
    assert created_route.id == valid_route_entity.id
    assert created_route.origin.latitude == valid_route_entity.origin.latitude
    assert created_route.destination.longitude == valid_route_entity.destination.longitude
    assert created_route.distance_km == valid_route_entity.distance_km


def test_get_route(route_repository: RouteRepository, valid_route_entity: RouteEntity):
    """Test getting a route by ID."""
    created_route = route_repository.create(valid_route_entity)
    retrieved_route = route_repository.get(str(created_route.id))
    assert retrieved_route is not None
    assert str(retrieved_route.id) == str(created_route.id)


def test_get_nonexistent_route(route_repository: RouteRepository):
    """Test getting a nonexistent route."""
    route = route_repository.get(str(uuid4()))
    assert route is None


def test_update_route(route_repository: RouteRepository, valid_route_entity: RouteEntity):
    """Test updating a route."""
    created_route = route_repository.create(valid_route_entity)
    created_route.distance_km = 600.0
    updated_route = route_repository.update(str(created_route.id), created_route)
    assert updated_route is not None
    assert updated_route.distance_km == 600.0


def test_delete_route(route_repository: RouteRepository, valid_route_entity: RouteEntity):
    """Test deleting a route."""
    created_route = route_repository.create(valid_route_entity)
    assert route_repository.delete(str(created_route.id)) is True
    assert route_repository.get(str(created_route.id)) is None


def test_find_by_criteria(route_repository: RouteRepository, valid_route_entity: RouteEntity):
    """Test finding routes by criteria."""
    route_repository.create(valid_route_entity)
    
    # Test finding by origin location
    routes = route_repository.find_by_criteria(
        origin_location=valid_route_entity.origin,
        limit=10
    )
    assert len(routes) > 0
    assert routes[0].origin.latitude == valid_route_entity.origin.latitude

    # Test finding by transport type
    routes = route_repository.find_by_criteria(
        transport_type=valid_route_entity.transport_type,
        limit=10
    )
    assert len(routes) > 0
    assert routes[0].transport_type == valid_route_entity.transport_type

    # Test finding by date range
    start_date = datetime.fromtimestamp((valid_route_entity.pickup_time - timedelta(hours=1)).timestamp(), tz=timezone.utc)
    end_date = datetime.fromtimestamp((valid_route_entity.delivery_time + timedelta(hours=1)).timestamp(), tz=timezone.utc)
    routes = route_repository.find_by_criteria(
        start_date=start_date,
        end_date=end_date,
        limit=10
    )
    assert len(routes) > 0
    assert routes[0].pickup_time >= start_date
    assert routes[0].delivery_time <= end_date
