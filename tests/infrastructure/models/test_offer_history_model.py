"""Tests for the OfferHistory SQLAlchemy model."""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import desc
from uuid import uuid4

from src.domain.entities.offer import OfferStatus
from src.infrastructure.models import Offer, OfferHistory, Route, CostHistory


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
def cost_history(db_session, route):
    """Create a test cost history."""
    cost = CostHistory(
        route_id=route.id,
        total_cost=1000.0,
        version="1.0",
        cost_components={"fuel": 500, "driver": 500},
        settings_snapshot={"fuel_price": 1.5}
    )
    db_session.add(cost)
    db_session.commit()
    return cost


@pytest.fixture
def offer_data(route, cost_history):
    """Create test offer data."""
    total_cost = cost_history.total_cost  # 1000.0
    final_price = 1100.0
    margin = (final_price - total_cost) / total_cost  # 0.1
    return {
        "route_id": route.id,
        "cost_history_id": cost_history.id,
        "total_cost": total_cost,
        "version": "1.0",
        "status": OfferStatus.DRAFT,
        "margin": margin,
        "final_price": final_price,
        "currency": "EUR",
        "fun_fact": "Test offer"
    }


@pytest.fixture
def offer(db_session, offer_data):
    """Create a test offer."""
    offer = Offer(**offer_data)
    db_session.add(offer)
    db_session.commit()
    return offer


def test_create_offer_history(db_session, offer):
    """Test creating an offer history entry."""
    history = OfferHistory(
        offer_id=offer.id,
        version="1.0",
        status=OfferStatus.DRAFT,
        margin=0.1,
        final_price=1100.0,
        fun_fact="Initial version",
        changed_by="system",
        change_reason="Initial creation"
    )
    db_session.add(history)
    db_session.commit()

    assert history.id is not None
    assert history.offer_id == offer.id
    assert history.version == "1.0"
    assert history.status == OfferStatus.DRAFT
    assert float(history.margin) == pytest.approx(0.1)
    assert float(history.final_price) == pytest.approx(1100.0)
    assert history.fun_fact == "Initial version"
    assert history.changed_by == "system"
    assert history.change_reason == "Initial creation"
    assert history.changed_at is not None
    assert history.offer == offer


def test_offer_history_relationship(db_session, offer):
    """Test relationship between offer and its history."""
    # Create multiple history entries
    history1 = OfferHistory(
        offer_id=offer.id,
        version="1.0",
        status=OfferStatus.DRAFT,
        margin=0.1,
        final_price=1100.0,
        changed_by="system",
        change_reason="Initial version"
    )
    db_session.add(history1)

    history2 = OfferHistory(
        offer_id=offer.id,
        version="1.1",
        status=OfferStatus.ACTIVE,
        margin=0.15,
        final_price=1150.0,
        changed_by="user",
        change_reason="Price adjustment"
    )
    db_session.add(history2)
    db_session.commit()

    # Test relationship from offer to history
    assert len(offer.history) == 2
    assert history1 in offer.history
    assert history2 in offer.history

    # Test ordering by changed_at
    history_ordered = (
        db_session.query(OfferHistory)
        .filter(OfferHistory.offer_id == offer.id)
        .order_by(desc(OfferHistory.changed_at))
        .all()
    )
    assert history_ordered[0] == history2  # Most recent first
    assert history_ordered[1] == history1


def test_cascade_delete(db_session, offer):
    """Test that history entries are deleted when offer is deleted."""
    # Create history entries
    history1 = OfferHistory(
        offer_id=offer.id,
        version="1.0",
        status=OfferStatus.DRAFT,
        margin=0.1,
        final_price=1100.0
    )
    history2 = OfferHistory(
        offer_id=offer.id,
        version="1.1",
        status=OfferStatus.ACTIVE,
        margin=0.15,
        final_price=1150.0
    )
    db_session.add_all([history1, history2])
    db_session.commit()

    # Delete offer
    db_session.delete(offer)
    db_session.commit()

    # Verify history entries are deleted
    history_count = db_session.query(OfferHistory).filter(
        OfferHistory.offer_id == offer.id
    ).count()
    assert history_count == 0


def test_offer_history_metadata(db_session, offer):
    """Test storing and retrieving metadata in offer history."""
    metadata = {
        "user_agent": "test-browser",
        "ip_address": "127.0.0.1",
        "changes": ["margin", "status"]
    }
    
    history = OfferHistory(
        offer_id=offer.id,
        version="1.0",
        status=OfferStatus.DRAFT,
        margin=0.1,
        final_price=1100.0,
        extra_data=metadata,
        changed_by="user",
        change_reason="Test metadata"
    )
    db_session.add(history)
    db_session.commit()

    # Refresh from database
    db_session.refresh(history)
    assert history.extra_data == metadata
    assert history.extra_data["user_agent"] == "test-browser"
    assert "changes" in history.extra_data


def test_offer_history_null_constraints(db_session, offer):
    """Test null constraints on offer history."""
    # Test required fields
    history = OfferHistory(offer_id=offer.id)
    db_session.add(history)
    
    with pytest.raises(Exception):
        db_session.commit()
    db_session.rollback()

    # Test with minimal required fields
    history = OfferHistory(
        offer_id=offer.id,
        version="1.0",
        status=OfferStatus.DRAFT,
        margin=0.1,
        final_price=1100.0
    )
    db_session.add(history)
    db_session.commit()

    assert history.id is not None
    assert history.changed_at is not None
    assert history.changed_by is None  # Optional
    assert history.change_reason is None  # Optional
    assert history.extra_data is None  # Optional


def test_offer_history_querying(db_session, offer):
    """Test querying offer history with various filters."""
    # Create multiple history entries
    histories = []
    for i in range(5):
        history = OfferHistory(
            offer_id=offer.id,
            version=f"1.{i}",
            status=OfferStatus.DRAFT if i < 3 else OfferStatus.ACTIVE,
            margin=0.1 + (i * 0.05),
            final_price=1000.0 + (i * 50),
            changed_by="user" if i % 2 == 0 else "system",
            changed_at=datetime.utcnow() + timedelta(hours=i)
        )
        histories.append(history)
    db_session.add_all(histories)
    db_session.commit()

    # Test filtering by status
    draft_histories = db_session.query(OfferHistory).filter(
        OfferHistory.status == OfferStatus.DRAFT
    ).all()
    assert len(draft_histories) == 3

    # Test filtering by changed_by
    user_histories = db_session.query(OfferHistory).filter(
        OfferHistory.changed_by == "user"
    ).all()
    assert len(user_histories) == 3

    # Test ordering by changed_at
    ordered_histories = db_session.query(OfferHistory).order_by(
        desc(OfferHistory.changed_at)
    ).all()
    assert ordered_histories[0].version == "1.4"  # Most recent first
    assert ordered_histories[-1].version == "1.0"  # Oldest last
