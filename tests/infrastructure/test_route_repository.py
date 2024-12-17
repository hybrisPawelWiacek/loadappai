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


@pytest.fixture
def another_route_entity(valid_route_entity: RouteEntity):
    """Create another valid route entity with different values."""
    return RouteEntity(
        id=str(uuid4()),
        origin=Location(
            address="Another Origin",
            latitude=51.5074,
            longitude=-0.1278
        ),
        destination=Location(
            address="Another Destination",
            latitude=48.8566,
            longitude=2.3522
        ),
        pickup_time=datetime.fromtimestamp((datetime.now() + timedelta(days=2)).timestamp(), tz=timezone.utc),
        delivery_time=datetime.fromtimestamp((datetime.now() + timedelta(days=3)).timestamp(), tz=timezone.utc),
        transport_type="refrigerated",
        cargo_id="CARGO123",
        distance_km=750.0,
        duration_hours=12.0,
        empty_driving=EmptyDriving(
            distance_km=75.0,
            duration_hours=1.5
        ),
        is_feasible=False,
        metadata=RouteMetadata(
            weather_data={"another": "data"}
        )
    )


def test_create_route(route_repository: RouteRepository, valid_route_entity: RouteEntity):
    """Test creating a new route."""
    created_route = route_repository.create(valid_route_entity)
    assert created_route.id == valid_route_entity.id
    assert created_route.origin.latitude == valid_route_entity.origin.latitude
    assert created_route.destination.longitude == valid_route_entity.destination.longitude
    assert created_route.distance_km == valid_route_entity.distance_km
    assert created_route.empty_driving.distance_km == valid_route_entity.empty_driving.distance_km
    assert created_route.metadata.weather_data == valid_route_entity.metadata.weather_data


def test_get_route(route_repository: RouteRepository, valid_route_entity: RouteEntity):
    """Test getting a route by ID."""
    created_route = route_repository.create(valid_route_entity)
    retrieved_route = route_repository.get(str(created_route.id))
    assert retrieved_route is not None
    assert str(retrieved_route.id) == str(created_route.id)
    assert retrieved_route.cargo_id == created_route.cargo_id
    assert retrieved_route.is_feasible == created_route.is_feasible


def test_get_nonexistent_route(route_repository: RouteRepository):
    """Test getting a nonexistent route."""
    route = route_repository.get(str(uuid4()))
    assert route is None


def test_get_all_routes(route_repository: RouteRepository, valid_route_entity: RouteEntity, another_route_entity: RouteEntity):
    """Test getting all routes with pagination."""
    # Create two routes
    route_repository.create(valid_route_entity)
    route_repository.create(another_route_entity)

    # Test pagination
    routes = route_repository.get_all(skip=0, limit=1)
    assert len(routes) == 1

    routes = route_repository.get_all(skip=0, limit=2)
    assert len(routes) == 2

    routes = route_repository.get_all(skip=1, limit=1)
    assert len(routes) == 1

    # Test without pagination
    routes = route_repository.get_all()
    assert len(routes) == 2


def test_update_route(route_repository: RouteRepository, valid_route_entity: RouteEntity):
    """Test updating a route."""
    created_route = route_repository.create(valid_route_entity)
    
    # Update multiple fields
    created_route.distance_km = 600.0
    created_route.duration_hours = 10.0
    created_route.is_feasible = False
    created_route.cargo_id = "NEW_CARGO"
    # Create a new EmptyDriving instance instead of modifying the existing one
    created_route.empty_driving = EmptyDriving(distance_km=60.0, duration_hours=created_route.empty_driving.duration_hours)
    # Create a new RouteMetadata instance instead of modifying the existing one
    created_route.metadata = RouteMetadata(
        weather_data={"updated": "data"},
        traffic_data=created_route.metadata.traffic_data,
        compliance_data=created_route.metadata.compliance_data,
        optimization_data=created_route.metadata.optimization_data
    )

    updated_route = route_repository.update(str(created_route.id), created_route)
    assert updated_route is not None
    assert updated_route.distance_km == 600.0
    assert updated_route.duration_hours == 10.0
    assert updated_route.is_feasible is False
    assert updated_route.cargo_id == "NEW_CARGO"
    assert updated_route.empty_driving.distance_km == 60.0
    assert updated_route.metadata.weather_data == {"updated": "data"}


def test_update_nonexistent_route(route_repository: RouteRepository, valid_route_entity: RouteEntity):
    """Test updating a nonexistent route."""
    updated_route = route_repository.update(str(uuid4()), valid_route_entity)
    assert updated_route is None


def test_delete_route(route_repository: RouteRepository, valid_route_entity: RouteEntity):
    """Test deleting a route."""
    created_route = route_repository.create(valid_route_entity)
    assert route_repository.delete(str(created_route.id)) is True
    assert route_repository.get(str(created_route.id)) is None


def test_delete_nonexistent_route(route_repository: RouteRepository):
    """Test deleting a nonexistent route."""
    assert route_repository.delete(str(uuid4())) is False


def test_find_by_criteria_all_params(
    route_repository: RouteRepository,
    valid_route_entity: RouteEntity,
    another_route_entity: RouteEntity
):
    """Test finding routes using all criteria parameters."""
    # Create two routes with different parameters
    route_repository.create(valid_route_entity)
    route_repository.create(another_route_entity)

    # Test finding by origin location
    routes = route_repository.find_by_criteria(
        origin_location=valid_route_entity.origin,
        limit=10
    )
    assert len(routes) == 1
    assert routes[0].origin.latitude == valid_route_entity.origin.latitude

    # Test finding by destination location
    routes = route_repository.find_by_criteria(
        destination_location=another_route_entity.destination,
        limit=10
    )
    assert len(routes) == 1
    assert routes[0].destination.latitude == another_route_entity.destination.latitude

    # Test finding by transport type
    routes = route_repository.find_by_criteria(
        transport_type=valid_route_entity.transport_type,
        limit=10
    )
    assert len(routes) == 1
    assert routes[0].transport_type == valid_route_entity.transport_type

    # Test finding by feasibility
    routes = route_repository.find_by_criteria(
        is_feasible=False,
        limit=10
    )
    assert len(routes) == 1
    assert routes[0].is_feasible is False

    # Test finding by date range
    start_date = valid_route_entity.pickup_time - timedelta(hours=1)
    end_date = valid_route_entity.delivery_time + timedelta(hours=1)
    routes = route_repository.find_by_criteria(
        start_date=start_date,
        end_date=end_date,
        limit=10
    )
    assert len(routes) == 1
    assert routes[0].pickup_time >= start_date
    assert routes[0].delivery_time <= end_date


def test_find_by_criteria_combined(
    route_repository: RouteRepository,
    valid_route_entity: RouteEntity,
    another_route_entity: RouteEntity
):
    """Test finding routes using combined criteria."""
    # Create two routes
    route_repository.create(valid_route_entity)
    route_repository.create(another_route_entity)

    # Test finding with multiple criteria
    routes = route_repository.find_by_criteria(
        transport_type=valid_route_entity.transport_type,
        is_feasible=True,
        origin_location=valid_route_entity.origin,
        limit=10
    )
    assert len(routes) == 1
    assert routes[0].id == valid_route_entity.id

    # Test finding with no matches
    routes = route_repository.find_by_criteria(
        transport_type=valid_route_entity.transport_type,
        is_feasible=False,
        limit=10
    )
    assert len(routes) == 0


def test_find_by_criteria_pagination(
    route_repository: RouteRepository,
    valid_route_entity: RouteEntity,
    another_route_entity: RouteEntity
):
    """Test pagination in find_by_criteria."""
    # Create two routes
    route_repository.create(valid_route_entity)
    route_repository.create(another_route_entity)

    # Test with different skip and limit values
    routes = route_repository.find_by_criteria(skip=0, limit=1)
    assert len(routes) == 1

    routes = route_repository.find_by_criteria(skip=1, limit=1)
    assert len(routes) == 1

    routes = route_repository.find_by_criteria(skip=2, limit=1)
    assert len(routes) == 0

    routes = route_repository.find_by_criteria(skip=0, limit=2)
    assert len(routes) == 2
