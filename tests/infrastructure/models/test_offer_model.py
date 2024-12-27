"""Tests for the Offer SQLAlchemy model."""

import pytest
from datetime import datetime, timedelta

from src.infrastructure.models import (
    Offer, OfferHistory, Route, CostHistory, OfferStatus,
    TransportType, Cargo
)
from src.domain.value_objects.location import Location


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
def route(db_session, transport_type, cargo):
    """Create a test route."""
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
    route = Route(
        origin=origin.model_dump(),
        destination=destination.model_dump(),
        pickup_time=now,
        delivery_time=now + timedelta(days=1),
        transport_type=transport_type.id,
        cargo_id=cargo.id,
        distance_km=1000.0,
        duration_hours=12.0,
        is_feasible=True,
        country_segments=[
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
    )
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
        is_final=True,
        cost_components={
            "fuel": 300.0,
            "toll": 200.0,
            "driver": 400.0,
            "overhead": 100.0
        },
        settings_snapshot={
            "fuel_rate": 1.5,
            "toll_rates": {"DE": 0.2, "FR": 0.3},
            "driver_rate": 35.0
        }
    )
    db_session.add(cost)
    db_session.commit()
    return cost


@pytest.fixture
def offer_data(route, cost_history):
    """Create test offer data."""
    total_cost = cost_history.total_cost
    margin = 0.15
    final_price = total_cost * (1 + margin)
    
    return {
        "route_id": route.id,
        "cost_history_id": cost_history.id,
        "total_cost": total_cost,
        "version": "1.0",
        "status": OfferStatus.DRAFT,
        "margin": margin,
        "final_price": final_price,
        "currency": "EUR",
        "fun_fact": "This route crosses the historic Berlin-Paris corridor",
        "extra_data": {
            "negotiation_rounds": 0,
            "priority": "standard"
        },
        "valid_until": datetime.utcnow() + timedelta(days=7)
    }


def test_create_offer(db_session, offer_data):
    """Test creating a new offer."""
    offer = Offer(**offer_data)
    db_session.add(offer)
    db_session.commit()

    assert offer.id is not None
    assert offer.route_id == offer_data["route_id"]
    assert offer.cost_history_id == offer_data["cost_history_id"]
    assert offer.version == offer_data["version"]
    assert offer.status == offer_data["status"]
    assert float(offer.margin) == pytest.approx(float(offer_data["margin"]))
    assert float(offer.final_price) == pytest.approx(float(offer_data["final_price"]))
    assert offer.currency == offer_data["currency"]
    assert offer.fun_fact == offer_data["fun_fact"]
    assert offer.extra_data == offer_data["extra_data"]
    assert offer.valid_until == offer_data["valid_until"]
    assert offer.created_at is not None


def test_offer_relationships(db_session, offer_data):
    """Test offer relationships."""
    offer = Offer(**offer_data)
    db_session.add(offer)
    db_session.commit()

    # Test route relationship
    assert offer.route.id == offer_data["route_id"]
    assert offer in offer.route.offers

    # Test cost relationship
    assert offer.cost.id == offer_data["cost_history_id"]
    assert offer in offer.cost.offers


def test_offer_status_transitions(db_session, offer_data):
    """Test offer status transitions."""
    offer = Offer(**offer_data)
    db_session.add(offer)
    db_session.commit()

    assert offer.status == OfferStatus.DRAFT

    # Create history entry for DRAFT -> SENT transition
    offer.status = OfferStatus.SENT
    history_entry1 = OfferHistory(
        offer_id=offer.id,
        version=offer.version,
        status=OfferStatus.SENT,
        margin=offer.margin,
        final_price=offer.final_price,
        fun_fact=offer.fun_fact,
        extra_data=offer.extra_data,
        changed_by="test_user",
        change_reason="Status update to SENT"
    )
    db_session.add(history_entry1)
    db_session.commit()
    assert offer.status == OfferStatus.SENT

    # Create history entry for SENT -> ACCEPTED transition
    offer.status = OfferStatus.ACCEPTED
    history_entry2 = OfferHistory(
        offer_id=offer.id,
        version=offer.version,
        status=OfferStatus.ACCEPTED,
        margin=offer.margin,
        final_price=offer.final_price,
        fun_fact=offer.fun_fact,
        extra_data=offer.extra_data,
        changed_by="test_user",
        change_reason="Status update to ACCEPTED"
    )
    db_session.add(history_entry2)
    db_session.commit()
    assert offer.status == OfferStatus.ACCEPTED

    # Create history entry for ACCEPTED -> REJECTED transition
    offer.status = OfferStatus.REJECTED
    history_entry3 = OfferHistory(
        offer_id=offer.id,
        version=offer.version,
        status=OfferStatus.REJECTED,
        margin=offer.margin,
        final_price=offer.final_price,
        fun_fact=offer.fun_fact,
        extra_data=offer.extra_data,
        changed_by="test_user",
        change_reason="Status update to REJECTED"
    )
    db_session.add(history_entry3)
    db_session.commit()
    assert offer.status == OfferStatus.REJECTED

    # Create history entry for REJECTED -> EXPIRED transition
    offer.status = OfferStatus.EXPIRED
    history_entry4 = OfferHistory(
        offer_id=offer.id,
        version=offer.version,
        status=OfferStatus.EXPIRED,
        margin=offer.margin,
        final_price=offer.final_price,
        fun_fact=offer.fun_fact,
        extra_data=offer.extra_data,
        changed_by="test_user",
        change_reason="Status update to EXPIRED"
    )
    db_session.add(history_entry4)
    db_session.commit()
    assert offer.status == OfferStatus.EXPIRED

    # Test history entries
    history = db_session.query(OfferHistory).filter_by(offer_id=offer.id).order_by(OfferHistory.changed_at).all()
    assert len(history) == 4
    assert history[0].status == OfferStatus.SENT
    assert history[1].status == OfferStatus.ACCEPTED
    assert history[2].status == OfferStatus.REJECTED
    assert history[3].status == OfferStatus.EXPIRED


def test_offer_price_and_margin(db_session, offer_data):
    """Test offer price and margin calculations."""
    offer = Offer(**offer_data)
    db_session.add(offer)
    db_session.commit()

    # Convert to float for calculations to avoid Decimal/float mismatch
    total_cost = float(offer.cost.total_cost)
    margin = float(offer.margin)
    expected_price = total_cost * (1 + margin)
    
    assert float(offer.final_price) == pytest.approx(expected_price)
    assert float(offer.margin) == pytest.approx(margin)

    # Test margin update
    new_margin = 0.20
    offer.margin = new_margin
    offer.final_price = offer.cost.total_cost * (1 + new_margin)
    db_session.commit()

    assert float(offer.margin) == pytest.approx(new_margin)
    expected_price = float(offer.cost.total_cost) * (1 + new_margin)
    assert float(offer.final_price) == pytest.approx(expected_price)


def test_offer_history_tracking(db_session, offer_data):
    """Test offer history tracking."""
    offer = Offer(**offer_data)
    db_session.add(offer)
    db_session.commit()

    # Create history entry
    history_entry = OfferHistory(
        offer_id=offer.id,
        version=offer.version,
        status=OfferStatus.SENT,
        margin=offer.margin,
        final_price=offer.final_price,
        fun_fact=offer.fun_fact,
        extra_data=offer.extra_data,
        changed_by="test_user",
        change_reason="Status update to SENT"
    )
    db_session.add(history_entry)
    db_session.commit()

    # Verify history relationship
    assert len(offer.history) == 1
    assert offer.history[0].status == OfferStatus.SENT
    assert offer.history[0].changed_by == "test_user"
    assert offer.history[0].change_reason == "Status update to SENT"


def test_offer_indexes(db_session, offer_data):
    """Test offer indexes."""
    offer = Offer(**offer_data)
    db_session.add(offer)
    db_session.commit()

    # Test status index
    found_offer = db_session.query(Offer).filter(
        Offer.status == OfferStatus.DRAFT
    ).first()
    assert found_offer.id == offer.id

    # Test created_at index
    found_offer = db_session.query(Offer).filter(
        Offer.created_at <= datetime.utcnow()
    ).first()
    assert found_offer.id == offer.id

    # Test valid_until index
    found_offer = db_session.query(Offer).filter(
        Offer.valid_until == offer_data["valid_until"]
    ).first()
    assert found_offer.id == offer.id
