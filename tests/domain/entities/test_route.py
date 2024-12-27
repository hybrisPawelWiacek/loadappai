"""Tests for route-related domain entities."""

from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4
import time
import pytest
from pytz import UTC

from src.domain.entities.route import (
    Route,
    TimeWindow,
    TransportType,
    TimelineEventType,
    RouteStatus,
    ExtensibleEntity,
)
from src.domain.value_objects.route import RouteSegment, EmptyDriving
from src.domain.value_objects.location import Location
from src.domain.value_objects.country_segment import CountrySegment
from src.domain.value_objects.route import RouteMetadata


@pytest.fixture
def location_factory():
    """Factory fixture for creating Location objects."""
    def _create_location(latitude: float, longitude: float, address: str) -> Location:
        return Location(latitude=latitude, longitude=longitude, address=address)
    return _create_location


@pytest.fixture
def route_segment_factory(location_factory):
    """Factory fixture for creating RouteSegment objects."""
    def _create_segment(
        start_latitude: float,
        start_longitude: float,
        end_latitude: float,
        end_longitude: float,
        distance: float,
        duration: float,
        country: str,
        is_empty_driving: bool = False,
        timeline_event: str = None
    ) -> RouteSegment:
        return RouteSegment(
            start_location=location_factory(start_latitude, start_longitude, f"Start {start_latitude}, {start_longitude}"),
            end_location=location_factory(end_latitude, end_longitude, f"End {end_latitude}, {end_longitude}"),
            distance_km=distance,
            duration_hours=duration,
            country=country,
            is_empty_driving=is_empty_driving,
            timeline_event=timeline_event
        )
    return _create_segment


@pytest.fixture
def country_segment_factory():
    """Factory fixture for creating CountrySegment objects."""
    def _create_country_segment(
        code: str,
        distance: float,
        duration: float,
        toll_rates: dict = None
    ) -> CountrySegment:
        return CountrySegment(
            country_code=code,
            distance=Decimal(str(distance)),
            duration_hours=Decimal(str(duration)),
            toll_rates=toll_rates or {"highway": Decimal("0.15"), "national": Decimal("0.10")}
        )
    return _create_country_segment


@pytest.fixture
def valid_route_data(location_factory):
    """Fixture providing valid route data."""
    now = datetime.now(UTC)
    return {
        "id": uuid4(),
        "origin": {"latitude": 0, "longitude": 0, "address": "Origin"},
        "destination": {"latitude": 1, "longitude": 1, "address": "Destination"},
        "pickup_time": now,
        "delivery_time": now + timedelta(hours=2),
        "distance_km": 100.0,
        "duration_hours": 2.0,
        "transport_type": TransportType.TRUCK.value,
        "is_optimized": False,
        "is_active": True,
        "is_feasible": True
    }


def test_transport_type_enum():
    """Test TransportType enum values."""
    assert TransportType.TRUCK.value == "truck"
    assert TransportType.VAN.value == "van"
    assert TransportType.TRAILER.value == "trailer"
    assert TransportType.FLATBED_TRUCK.value == "flatbed_truck"


def test_timeline_event_type_enum():
    """Test TimelineEventType enum values."""
    assert TimelineEventType.PICKUP.value == "pickup"
    assert TimelineEventType.DELIVERY.value == "delivery"
    assert TimelineEventType.REST.value == "rest"
    assert TimelineEventType.EMPTY_DRIVING.value == "empty_driving"
    assert TimelineEventType.LOADED_DRIVING.value == "loaded_driving"


def test_route_status_enum():
    """Test RouteStatus enum values."""
    assert RouteStatus.DRAFT.value == "draft"
    assert RouteStatus.PLANNED.value == "planned"
    assert RouteStatus.IN_PROGRESS.value == "in_progress"
    assert RouteStatus.COMPLETED.value == "completed"
    assert RouteStatus.CANCELLED.value == "cancelled"


def test_time_window_validation():
    """Test TimeWindow validation rules."""
    now = datetime.now(UTC)
    location = Location(latitude=0, longitude=0, address="Test")
    
    # Valid time window
    window = TimeWindow(
        location=location,
        earliest=now,
        latest=now + timedelta(hours=2),
        operation_type="pickup",
        duration_hours=1.0
    )
    assert window.duration_hours == 1.0
    
    # Invalid time window (latest before earliest)
    with pytest.raises(ValueError, match="Latest time must be after earliest time"):
        TimeWindow(
            location=location,
            earliest=now,
            latest=now - timedelta(hours=1),
            operation_type="pickup",
            duration_hours=1.0
        )
    
    # Invalid duration
    with pytest.raises(ValueError):
        TimeWindow(
            location=location,
            earliest=now,
            latest=now + timedelta(hours=1),
            operation_type="pickup",
            duration_hours=0
        )


def test_extensible_entity():
    """Test ExtensibleEntity base class."""
    entity = ExtensibleEntity()
    assert entity.version == "1.0"
    assert entity.metadata is None
    assert entity.created_at is not None
    assert entity.modified_at is not None
    assert entity.created_by is None
    assert entity.modified_by is None


def test_route_creation(valid_route_data):
    """Test Route entity creation and validation."""
    route = Route(**valid_route_data)
    assert route.id == valid_route_data["id"]
    assert route.transport_type == TransportType.TRUCK
    assert route.is_optimized is False
    assert route.is_active is True
    
    # Invalid route (delivery before pickup)
    invalid_data = valid_route_data.copy()
    invalid_data["delivery_time"] = valid_route_data["pickup_time"] - timedelta(hours=1)
    with pytest.raises(ValueError, match="Delivery time must be after pickup time"):
        Route(**invalid_data)
    
    # Invalid route (negative distance)
    invalid_data = valid_route_data.copy()
    invalid_data["distance_km"] = -100.0
    with pytest.raises(ValueError):
        Route(**invalid_data)
    
    # Invalid route (zero duration)
    invalid_data = valid_route_data.copy()
    invalid_data["duration_hours"] = 0
    with pytest.raises(ValueError):
        Route(**invalid_data)


def test_route_segments():
    """Test route segments functionality."""
    # Create route segments
    segment1 = RouteSegment(
        start_location=Location(latitude=0, longitude=0, address="Start 0, 0"),
        end_location=Location(latitude=0.5, longitude=0.5, address="End 0.5, 0.5"),
        distance_km=50.0,
        duration_hours=1.0,
        country="DE",
        is_empty_driving=False,
        timeline_event=TimelineEventType.PICKUP.value
    )
    
    segment2 = RouteSegment(
        start_location=Location(latitude=0.5, longitude=0.5, address="Start 0.5, 0.5"),
        end_location=Location(latitude=1, longitude=1, address="End 1, 1"),
        distance_km=50.0,
        duration_hours=1.0,
        country="DE",
        is_empty_driving=False,
        timeline_event=TimelineEventType.DELIVERY.value
    )
    
    # Create route with segments
    route = Route(
        origin={"latitude": 0, "longitude": 0, "address": "Origin"},
        destination={"latitude": 1, "longitude": 1, "address": "Destination"},
        pickup_time=datetime.now(UTC),
        delivery_time=datetime.now(UTC) + timedelta(hours=2),
        transport_type=TransportType.VAN.value,
        distance_km=100.0,
        duration_hours=2.0,
        segments=[segment1, segment2]
    )
    
    # Verify segments
    assert len(route.segments) == 2
    assert route.segments[0].distance_km == 50.0
    assert route.segments[1].distance_km == 50.0
    assert route.segments[0].timeline_event == TimelineEventType.PICKUP.value
    assert route.segments[1].timeline_event == TimelineEventType.DELIVERY.value


def test_country_segments(valid_route_data, country_segment_factory):
    """Test country segments handling."""
    route = Route(**valid_route_data)
    
    # Add valid country segments
    segment1 = country_segment_factory("DE", 50.0, 1.0)
    segment2 = country_segment_factory("FR", 50.0, 1.0)
    
    route.country_segments = [segment1, segment2]
    assert len(route.country_segments) == 2
    assert route.country_segments[0].country_code == "DE"
    assert route.country_segments[1].country_code == "FR"
    assert sum(float(seg.distance) for seg in route.country_segments) == route.distance_km


def test_empty_driving(valid_route_data):
    """Test empty driving functionality."""
    route = Route(**valid_route_data)
    
    # Add empty driving
    empty_driving = EmptyDriving(
        distance_km=30.0,
        duration_hours=0.5,
        start_location=Location(latitude=0, longitude=0, address="Start"),
        end_location=Location(latitude=0.5, longitude=0.5, address="End")
    )
    
    route.empty_driving = empty_driving
    assert route.empty_driving.distance_km == 30.0
    assert route.empty_driving.duration_hours == 0.5


def test_route_metadata(valid_route_data):
    """Test route metadata handling."""
    route = Route(**valid_route_data)
    
    # Add metadata
    metadata = RouteMetadata(
        weather_data={"temperature": 20, "conditions": "clear"},
        traffic_data={"congestion_level": "low"},
        compliance_data={"restrictions": None},
        optimization_data={"score": 0.95}
    )
    
    route.metadata = metadata
    assert route.metadata.weather_data["temperature"] == 20
    assert route.metadata.traffic_data["congestion_level"] == "low"


def test_time_windows(valid_route_data):
    """Test time windows handling."""
    route = Route(**valid_route_data)
    now = datetime.now(UTC)
    
    # Add time windows
    window1 = TimeWindow(
        location=Location(latitude=0, longitude=0, address="Pickup"),
        earliest=now,
        latest=now + timedelta(hours=2),
        operation_type=TimelineEventType.PICKUP.value,
        duration_hours=1.0
    )
    
    window2 = TimeWindow(
        location=Location(latitude=1, longitude=1, address="Delivery"),
        earliest=now + timedelta(hours=3),
        latest=now + timedelta(hours=5),
        operation_type=TimelineEventType.DELIVERY.value,
        duration_hours=1.0
    )
    
    route.time_windows = [window1, window2]
    assert len(route.time_windows) == 2
    assert route.time_windows[0].operation_type == TimelineEventType.PICKUP.value
    assert route.time_windows[1].operation_type == TimelineEventType.DELIVERY.value


def test_route_update(valid_route_data):
    """Test route update functionality."""
    # Create initial route
    route = Route(
        origin={"latitude": 0, "longitude": 0, "address": "Origin"},
        destination={"latitude": 1, "longitude": 1, "address": "Destination"},
        pickup_time=datetime.now(UTC),
        delivery_time=datetime.now(UTC) + timedelta(hours=2),
        transport_type=TransportType.VAN.value,
        distance_km=150.0,
        duration_hours=3.0
    )
    
    initial_modified = route.modified_at
    
    # Sleep briefly to ensure timestamp difference
    time.sleep(0.1)
    
    # Update route using model_copy
    route = route.model_copy(update={"distance_km": 200.0, "modified_at": datetime.now(UTC)})
    
    # Verify update
    assert route.distance_km == 200.0
    assert route.modified_at > initial_modified


def test_route_feasibility(valid_route_data):
    """Test route feasibility handling."""
    route = Route(**valid_route_data)
    assert route.is_feasible is True
    assert route.feasibility_notes is None
    
    # Mark as infeasible
    route.is_feasible = False
    route.feasibility_notes = "Time window constraints violated"
    
    assert route.is_feasible is False
    assert route.feasibility_notes == "Time window constraints violated"
