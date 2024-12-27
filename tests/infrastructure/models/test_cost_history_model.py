"""Tests for the CostHistory SQLAlchemy model."""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import desc
from uuid import uuid4

from src.infrastructure.models import Route, CostHistory, Offer, CalculationMethod


@pytest.fixture
def route_data():
    """Create test route data."""
    return {
        "origin": {"lat": 52.52, "lon": 13.405},
        "destination": {"lat": 51.12, "lon": 17.038},
        "pickup_time": datetime.utcnow(),
        "delivery_time": datetime.utcnow() + timedelta(days=1),
        "transport_type": "standard",
        "distance_km": 350.0,
        "duration_hours": 5.0,
        "is_feasible": True,
        "status": "DRAFT"
    }


@pytest.fixture
def route(db_session, route_data):
    """Create a test route."""
    route = Route(**route_data)
    db_session.add(route)
    db_session.commit()
    return route


@pytest.fixture
def cost_history_data(route):
    """Create test cost history data."""
    return {
        "route_id": route.id,
        "total_cost": 1000.0,
        "currency": "EUR",
        "calculation_method": CalculationMethod.STANDARD,
        "version": "1.0",
        "is_final": False,
        "cost_components": {
            "fuel": 500.0,
            "driver": 300.0,
            "maintenance": 200.0
        },
        "settings_snapshot": {
            "fuel_price": 1.5,
            "driver_cost_per_hour": 30.0,
            "maintenance_rate": 0.2
        }
    }


def test_create_cost_history(db_session, route, cost_history_data):
    """Test creating a cost history entry."""
    history = CostHistory(**cost_history_data)
    db_session.add(history)
    db_session.commit()

    assert history.id is not None
    assert history.route_id == route.id
    assert history.total_cost == 1000.0
    assert history.currency == "EUR"
    assert history.calculation_method == CalculationMethod.STANDARD
    assert history.version == "1.0"
    assert history.is_final is False
    assert history.cost_components == cost_history_data["cost_components"]
    assert history.settings_snapshot == cost_history_data["settings_snapshot"]
    assert history.calculation_date is not None
    assert history.route == route


def test_route_relationship(db_session, route, cost_history_data):
    """Test relationship between route and its cost history."""
    # Create multiple history entries
    history1 = CostHistory(**cost_history_data)
    db_session.add(history1)

    history2 = CostHistory(
        **{
            **cost_history_data,
            "version": "1.1",
            "total_cost": 1100.0,
            "is_final": True,
            "cost_components": {**cost_history_data["cost_components"], "fuel": 600.0}
        }
    )
    db_session.add(history2)
    db_session.commit()

    # Test relationship from route to cost history
    assert len(route.cost_history) == 2
    assert history1 in route.cost_history
    assert history2 in route.cost_history

    # Test ordering by calculation_date
    history_ordered = (
        db_session.query(CostHistory)
        .filter(CostHistory.route_id == route.id)
        .order_by(desc(CostHistory.calculation_date))
        .all()
    )
    assert history_ordered[0] == history2  # Most recent first
    assert history_ordered[1] == history1


def test_cascade_delete(db_session, route, cost_history_data):
    """Test that history entries are deleted when route is deleted."""
    # Create history entries
    history1 = CostHistory(**cost_history_data)
    history2 = CostHistory(**{**cost_history_data, "version": "1.1", "total_cost": 1100.0})
    db_session.add_all([history1, history2])
    db_session.commit()

    # Create an offer linked to history1
    offer = Offer(
        route_id=route.id,
        cost_history_id=history1.id,
        version="1.0",
        status="DRAFT",
        margin=0.1,
        final_price=1100.0,
        total_cost=1000.0
    )
    db_session.add(offer)
    db_session.commit()

    # Delete route
    db_session.delete(route)
    db_session.commit()

    # Verify history entries and related offer are deleted
    history_count = db_session.query(CostHistory).filter(
        CostHistory.route_id == route.id
    ).count()
    assert history_count == 0

    offer_count = db_session.query(Offer).filter(
        Offer.cost_history_id.in_([history1.id, history2.id])
    ).count()
    assert offer_count == 0


def test_cost_components_json(db_session, route, cost_history_data):
    """Test storing and retrieving JSON data in cost components."""
    history = CostHistory(**cost_history_data)
    db_session.add(history)
    db_session.commit()

    # Refresh from database
    db_session.refresh(history)
    assert history.cost_components == cost_history_data["cost_components"]
    assert history.cost_components["fuel"] == 500.0
    assert history.cost_components["driver"] == 300.0
    assert history.cost_components["maintenance"] == 200.0

    # Test updating JSON fields
    history.cost_components = {**history.cost_components, "toll": 150.0}
    db_session.commit()
    db_session.refresh(history)
    assert history.cost_components["toll"] == 150.0


def test_null_constraints(db_session, route):
    """Test null constraints on cost history."""
    # Test missing required fields
    with pytest.raises(Exception) as exc_info:
        history = CostHistory(
            route_id=route.id,
            version="1.0"
        )
        db_session.add(history)
        db_session.commit()
    assert "NOT NULL constraint failed" in str(exc_info.value)
    db_session.rollback()

    # Test with minimal required fields
    history = CostHistory(
        route_id=route.id,
        total_cost=1000.0,
        version="1.0",
        cost_components={},
        settings_snapshot={}
    )
    db_session.add(history)
    db_session.commit()
    assert history.id is not None


def test_cost_history_querying(db_session, route, cost_history_data):
    """Test querying cost history with various filters."""
    # Create multiple history entries
    histories = []
    for i in range(3):
        history = CostHistory(
            **{
                **cost_history_data,
                "version": f"1.{i}",
                "total_cost": 1000.0 + i * 100,
                "is_final": i == 2  # Last one is final
            }
        )
        histories.append(history)
    db_session.add_all(histories)
    db_session.commit()

    # Test filtering by is_final
    final_histories = (
        db_session.query(CostHistory)
        .filter(CostHistory.is_final.is_(True))
        .all()
    )
    assert len(final_histories) == 1
    assert final_histories[0] == histories[2]

    # Test filtering by version
    v1_histories = (
        db_session.query(CostHistory)
        .filter(CostHistory.version == "1.1")
        .all()
    )
    assert len(v1_histories) == 1
    assert v1_histories[0] == histories[1]

    # Test ordering by calculation_date
    ordered_histories = (
        db_session.query(CostHistory)
        .order_by(desc(CostHistory.calculation_date))
        .all()
    )
    assert ordered_histories == list(reversed(histories))
