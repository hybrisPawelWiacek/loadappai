"""Tests for the CostSettings model."""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy.exc import IntegrityError

from src.infrastructure.models import CostSettings, Route, JSONEncodedDict, TransportType

@pytest.fixture
def transport_type(db_session):
    """Create a test transport type."""
    transport = TransportType(
        id="standard_truck",
        name="Standard Truck",
        capacity=24000.0,  # 24 tons
        emissions_class="EURO6",
        fuel_consumption_empty=25.0,  # L/100km
        fuel_consumption_loaded=32.0,  # L/100km
    )
    db_session.add(transport)
    db_session.commit()
    return transport

@pytest.fixture
def route(db_session, transport_type):
    """Create a test route."""
    route = Route(
        id=str(uuid4()),
        origin={"city": "Warsaw", "country": "PL", "lat": 52.2297, "lon": 21.0122},
        destination={"city": "Berlin", "country": "DE", "lat": 52.5200, "lon": 13.4050},
        pickup_time=datetime.utcnow(),
        delivery_time=datetime.utcnow() + timedelta(days=1),
        transport_type=transport_type.id,
        distance_km=575.0,
        duration_hours=8.0,
        is_feasible=True
    )
    db_session.add(route)
    db_session.commit()
    return route

@pytest.fixture
def default_settings_data():
    """Default test data for cost settings."""
    return {
        "fuel_rates": {
            "PL": 1.50,
            "DE": 1.80
        },
        "toll_rates": {
            "PL": {"highway": 0.15, "national": 0.10},
            "DE": {"highway": 0.25, "national": 0.20}
        },
        "driver_rates": {
            "PL": 25.00,
            "DE": 35.00
        },
        "overhead_rates": {
            "fixed": 100.00,
            "per_km": 0.05
        },
        "maintenance_rates": {
            "per_km": 0.10,
            "fixed": 50.00
        },
        "enabled_components": {
            "fuel": True,
            "toll": True,
            "driver": True,
            "overhead": True,
            "maintenance": True
        }
    }

def test_create_cost_settings(db_session, route, default_settings_data):
    """Test creating a new cost settings entry."""
    settings = CostSettings(
        id=str(uuid4()),
        route_id=route.id,
        version="1.0",
        **default_settings_data
    )
    db_session.add(settings)
    db_session.commit()

    saved_settings = db_session.query(CostSettings).filter_by(id=settings.id).first()
    assert saved_settings is not None
    assert saved_settings.route_id == route.id
    assert saved_settings.version == "1.0"
    assert saved_settings.fuel_rates == default_settings_data["fuel_rates"]
    assert saved_settings.created_at is not None
    assert saved_settings.modified_at is not None

def test_json_field_validation(db_session, route, default_settings_data):
    """Test JSON field validation and manipulation."""
    settings = CostSettings(
        id=str(uuid4()),
        route_id=route.id,
        version="1.0",
        **default_settings_data
    )
    db_session.add(settings)
    db_session.commit()

    # Test updating JSON fields using update_json_field method
    settings.update_json_field("fuel_rates", {"PL": 1.60})
    db_session.commit()

    # Refresh the session to get the latest data
    db_session.refresh(settings)
    assert settings.fuel_rates["PL"] == 1.60

def test_versioning(db_session, route, default_settings_data):
    """Test version management for cost settings."""
    # Create initial version
    v1_settings = CostSettings(
        id=str(uuid4()),
        route_id=route.id,
        version="1.0",
        **default_settings_data
    )
    db_session.add(v1_settings)
    db_session.commit()

    # Create new version with modified rates
    v2_data = default_settings_data.copy()
    v2_data["fuel_rates"]["PL"] = 1.70
    v2_settings = CostSettings(
        id=str(uuid4()),
        route_id=route.id,
        version="2.0",
        **v2_data
    )
    db_session.add(v2_settings)
    db_session.commit()

    # Verify both versions exist
    versions = db_session.query(CostSettings).filter_by(route_id=route.id).all()
    assert len(versions) == 2
    assert any(s.version == "1.0" for s in versions)
    assert any(s.version == "2.0" for s in versions)

def test_route_relationship(db_session, route, default_settings_data):
    """Test relationship with Route model."""
    settings = CostSettings(
        id=str(uuid4()),
        route_id=route.id,
        version="1.0",
        **default_settings_data
    )
    db_session.add(settings)
    db_session.commit()

    # Test accessing route through relationship
    assert settings.route.id == route.id
    assert settings.route.origin["city"] == "Warsaw"

    # Test accessing settings through route
    assert route.cost_settings[0].id == settings.id

def test_cascade_delete(db_session, route, default_settings_data):
    """Test cascade deletion with Route."""
    settings = CostSettings(
        id=str(uuid4()),
        route_id=route.id,
        version="1.0",
        **default_settings_data
    )
    db_session.add(settings)
    db_session.commit()

    # Delete route and verify settings are deleted
    db_session.delete(route)
    db_session.commit()

    deleted_settings = db_session.query(CostSettings).filter_by(id=settings.id).first()
    assert deleted_settings is None

def test_null_constraints(db_session, route):
    """Test null constraints on required fields."""
    settings = CostSettings(
        id=str(uuid4()),
        route_id=route.id,
        version="1.0"
    )
    
    # The model should use default values for JSON fields
    db_session.add(settings)
    db_session.commit()

    # Verify default values are used
    saved_settings = db_session.query(CostSettings).filter_by(id=settings.id).first()
    assert saved_settings.fuel_rates == {}
    assert saved_settings.toll_rates == {}
    assert saved_settings.driver_rates == {}
    assert saved_settings.overhead_rates == {}
    assert saved_settings.maintenance_rates == {}
    assert saved_settings.enabled_components == {
        'fuel': True,
        'toll': True,
        'driver': True,
        'overhead': True,
        'maintenance': True
    }

def test_timestamp_fields(db_session, route, default_settings_data):
    """Test creation and modification timestamps."""
    settings = CostSettings(
        id=str(uuid4()),
        route_id=route.id,
        version="1.0",
        **default_settings_data
    )
    db_session.add(settings)
    db_session.commit()
    
    initial_modified = settings.modified_at
    
    # Sleep briefly to ensure timestamp difference
    import time
    time.sleep(0.1)
    
    # Update using update_json_field method
    settings.update_json_field("fuel_rates", {"PL": 1.75})
    db_session.commit()
    
    # Refresh the session to get the latest data
    db_session.refresh(settings)
    assert settings.modified_at > initial_modified
    assert settings.created_at < settings.modified_at

def test_enabled_components(db_session, route, default_settings_data):
    """Test enabling/disabling cost components."""
    settings = CostSettings(
        id=str(uuid4()),
        route_id=route.id,
        version="1.0",
        **default_settings_data
    )
    db_session.add(settings)
    db_session.commit()

    # Update enabled components
    settings.update_json_field("enabled_components", {
        'fuel': True,
        'toll': False,
        'driver': True,
        'overhead': True,
        'maintenance': False
    })
    db_session.commit()

    # Refresh the session to get the latest data
    db_session.refresh(settings)
    assert settings.enabled_components["toll"] is False
    assert settings.enabled_components["maintenance"] is False
    assert settings.enabled_components["fuel"] is True
    assert settings.enabled_components["driver"] is True
    assert settings.enabled_components["overhead"] is True

def test_query_performance(db_session, route, default_settings_data):
    """Test index performance for common queries."""
    # Create multiple versions
    versions = []
    for i in range(10):
        settings = CostSettings(
            id=str(uuid4()),
            route_id=route.id,
            version=f"{i+1}.0",
            **default_settings_data
        )
        versions.append(settings)
        db_session.add(settings)
    db_session.commit()

    # Test querying by route_id (should use index)
    result = db_session.query(CostSettings).filter_by(route_id=route.id).all()
    assert len(result) == 10

    # Test querying by created_at (should use index)
    recent = datetime.utcnow() - timedelta(minutes=1)
    result = db_session.query(CostSettings).filter(CostSettings.created_at >= recent).all()
    assert len(result) == 10
