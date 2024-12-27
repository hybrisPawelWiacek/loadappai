"""Tests for the TransportType model."""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy.exc import IntegrityError

from src.infrastructure.models import TransportType, Route, JSONEncodedDict


@pytest.fixture
def default_transport_data():
    """Default test data for transport type."""
    return {
        "id": "standard_truck",
        "name": "Standard Truck",
        "capacity": 24000.0,  # 24 tons
        "emissions_class": "EURO6",
        "fuel_consumption_empty": 25.0,  # L/100km
        "fuel_consumption_loaded": 32.0,  # L/100km
        "extra_data": {
            "max_speed": 90,  # km/h
            "trailer_type": "curtainsider",
            "adr_classes": ["2", "3", "4.1"],
            "features": ["tail_lift", "gps_tracking"]
        }
    }


def test_create_transport_type(db_session, default_transport_data):
    """Test creating a new transport type entry."""
    transport = TransportType(**default_transport_data)
    db_session.add(transport)
    db_session.commit()

    saved_transport = db_session.query(TransportType).filter_by(id=transport.id).first()
    assert saved_transport is not None
    assert saved_transport.name == "Standard Truck"
    assert saved_transport.capacity == 24000.0
    assert saved_transport.emissions_class == "EURO6"
    assert saved_transport.fuel_consumption_empty == 25.0
    assert saved_transport.fuel_consumption_loaded == 32.0
    assert saved_transport.extra_data["max_speed"] == 90


def test_update_transport_type(db_session, default_transport_data):
    """Test updating transport type attributes."""
    transport = TransportType(**default_transport_data)
    db_session.add(transport)
    db_session.commit()

    # Update various fields
    transport.name = "Premium Truck"
    transport.capacity = 26000.0
    transport.emissions_class = "EURO7"
    
    # Update the entire extra_data dictionary
    new_extra_data = transport.extra_data.copy()
    new_extra_data["max_speed"] = 95
    transport.extra_data = new_extra_data
    
    db_session.commit()

    updated_transport = db_session.query(TransportType).filter_by(id=transport.id).first()
    assert updated_transport.name == "Premium Truck"
    assert updated_transport.capacity == 26000.0
    assert updated_transport.emissions_class == "EURO7"
    assert updated_transport.extra_data["max_speed"] == 95


def test_delete_transport_type(db_session, default_transport_data):
    """Test deleting a transport type."""
    transport = TransportType(**default_transport_data)
    db_session.add(transport)
    db_session.commit()

    db_session.delete(transport)
    db_session.commit()

    deleted_transport = db_session.query(TransportType).filter_by(id=transport.id).first()
    assert deleted_transport is None


def test_null_constraints(db_session):
    """Test null constraints on required fields."""
    # Test missing name
    transport = TransportType(
        id="test_truck",
        capacity=24000.0,
        emissions_class="EURO6",
        fuel_consumption_empty=25.0,
        fuel_consumption_loaded=32.0
    )
    with pytest.raises(IntegrityError):
        db_session.add(transport)
        db_session.commit()
    db_session.rollback()

    # Test missing capacity
    transport = TransportType(
        id="test_truck",
        name="Test Truck",
        emissions_class="EURO6",
        fuel_consumption_empty=25.0,
        fuel_consumption_loaded=32.0
    )
    with pytest.raises(IntegrityError):
        db_session.add(transport)
        db_session.commit()
    db_session.rollback()

    # Test missing emissions_class
    transport = TransportType(
        id="test_truck",
        name="Test Truck",
        capacity=24000.0,
        fuel_consumption_empty=25.0,
        fuel_consumption_loaded=32.0
    )
    with pytest.raises(IntegrityError):
        db_session.add(transport)
        db_session.commit()
    db_session.rollback()


def test_json_field_handling(db_session, default_transport_data):
    """Test JSON field handling for extra_data."""
    transport = TransportType(**default_transport_data)
    db_session.add(transport)
    db_session.commit()

    # Test updating JSON field
    new_extra_data = {
        "max_speed": 95,
        "trailer_type": "box",
        "adr_classes": ["1", "2", "3"],
        "features": ["tail_lift", "gps_tracking", "refrigeration"]
    }
    transport.extra_data = new_extra_data
    db_session.commit()

    updated_transport = db_session.query(TransportType).filter_by(id=transport.id).first()
    assert updated_transport.extra_data == new_extra_data
    assert "refrigeration" in updated_transport.extra_data["features"]


def test_route_relationship(db_session, default_transport_data):
    """Test relationship with Route model."""
    transport = TransportType(**default_transport_data)
    db_session.add(transport)
    db_session.commit()

    # Create a route using this transport type
    route = Route(
        id=str(uuid4()),
        origin={"city": "Warsaw", "country": "PL", "lat": 52.2297, "lon": 21.0122},
        destination={"city": "Berlin", "country": "DE", "lat": 52.5200, "lon": 13.4050},
        pickup_time=datetime.utcnow(),
        delivery_time=datetime.utcnow() + timedelta(days=1),
        transport_type=transport.id,
        distance_km=575.0,
        duration_hours=8.0,
        is_feasible=True
    )
    db_session.add(route)
    db_session.commit()

    # Test accessing route through relationship
    assert len(transport.routes) == 1
    assert transport.routes[0].id == route.id
    assert transport.routes[0].origin["city"] == "Warsaw"

    # Test cascade delete protection
    with pytest.raises(IntegrityError):
        db_session.delete(transport)
        db_session.commit()
    db_session.rollback()


def test_unique_constraints(db_session, default_transport_data):
    """Test unique constraints if any."""
    transport1 = TransportType(**default_transport_data)
    db_session.add(transport1)
    db_session.commit()

    # Try to create another transport with the same ID
    transport2 = TransportType(
        id=default_transport_data["id"],  # Same ID
        name="Different Truck",
        capacity=20000.0,
        emissions_class="EURO6",
        fuel_consumption_empty=23.0,
        fuel_consumption_loaded=30.0
    )
    with pytest.raises(IntegrityError):
        db_session.add(transport2)
        db_session.commit()
    db_session.rollback()


def test_query_performance(db_session):
    """Test index performance for common queries."""
    # Create multiple transport types
    for i in range(10):
        transport = TransportType(
            id=f"truck_{i}",
            name=f"Truck {i}",
            capacity=24000.0,
            emissions_class="EURO6",
            fuel_consumption_empty=25.0,
            fuel_consumption_loaded=32.0
        )
        db_session.add(transport)
    db_session.commit()

    # Test querying by name (should use index)
    result = db_session.query(TransportType).filter_by(name="Truck 5").first()
    assert result is not None
    assert result.id == "truck_5"

    # Test querying multiple records
    result = db_session.query(TransportType).filter(
        TransportType.capacity >= 24000.0
    ).all()
    assert len(result) == 10


def test_valid_ranges(db_session):
    """Test valid ranges for numeric fields."""
    # Test negative capacity
    transport = TransportType(
        id="test_truck",
        name="Test Truck",
        capacity=-1000.0,  # Invalid negative capacity
        emissions_class="EURO6",
        fuel_consumption_empty=25.0,
        fuel_consumption_loaded=32.0
    )
    db_session.add(transport)
    db_session.commit()  # This should work as we don't have range validation

    # Test negative fuel consumption
    transport = TransportType(
        id="test_truck_2",
        name="Test Truck 2",
        capacity=24000.0,
        emissions_class="EURO6",
        fuel_consumption_empty=-25.0,  # Invalid negative consumption
        fuel_consumption_loaded=-32.0   # Invalid negative consumption
    )
    db_session.add(transport)
    db_session.commit()  # This should work as we don't have range validation

    # Note: If we want to add range validation, we should:
    # 1. Add CHECK constraints in the database
    # 2. Add validation in the model or service layer
