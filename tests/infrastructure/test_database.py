"""Tests for database models and migrations."""
import pytest
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError

from src.infrastructure.models import (
    TransportType,
    CostSettings,
    Cargo,
    Route,
    Offer,
    Base
)
from src.infrastructure.seed_data import (
    seed_transport_types,
    seed_cost_settings,
    seed_cargoes,
    seed_routes,
    seed_offers,
)


def test_transport_type_constraints(db_session):
    """Test TransportType model constraints."""
    # Test required fields
    transport = TransportType(
        name="Test Truck",  # Missing id
        capacity=24000.0,
        emissions_class="EURO6",
        fuel_consumption_empty=25.0,
        fuel_consumption_loaded=32.0,
    )
    db_session.add(transport)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()

    # Test valid transport type
    transport = TransportType(
        id="test_transport_1",
        name="Test Truck",
        capacity=24000.0,
        emissions_class="EURO6",
        fuel_consumption_empty=25.0,
        fuel_consumption_loaded=32.0,
    )
    db_session.add(transport)
    db_session.commit()

    # Verify the transport was saved
    saved_transport = db_session.query(TransportType).filter_by(id="test_transport_1").first()
    assert saved_transport is not None
    assert saved_transport.name == "Test Truck"
    assert saved_transport.capacity == 24000.0


def test_cost_settings_constraints(db_session):
    """Test CostSettings model constraints."""
    # Test required fields
    settings = CostSettings(
        fuel_price_per_liter=1.8,  # Missing id
        driver_daily_salary=200.0,
        toll_rates={"DE": {"standard": 0.187}},
        overheads={"maintenance_per_km": 0.15},
        cargo_factors={"value_factor": 0.001},
        last_modified=datetime.now(timezone.utc),
    )
    db_session.add(settings)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()

    # Test valid settings
    settings = CostSettings(
        id="test_settings_1",
        fuel_price_per_liter=1.8,
        driver_daily_salary=200.0,
        toll_rates={"DE": {"standard": 0.187}},
        overheads={"maintenance_per_km": 0.15},
        cargo_factors={"value_factor": 0.001},
        last_modified=datetime.now(timezone.utc),
    )
    db_session.add(settings)
    db_session.commit()

    # Verify the settings were saved
    saved_settings = db_session.query(CostSettings).filter_by(id="test_settings_1").first()
    assert saved_settings is not None
    assert saved_settings.fuel_price_per_liter == 1.8
    assert saved_settings.toll_rates["DE"]["standard"] == 0.187


def test_cargo_constraints(db_session):
    """Test Cargo model constraints."""
    # Test required fields
    cargo = Cargo(
        weight=18000.0,  # Missing id
        value=50000.0,
        special_requirements={"temperature_control": False},
        hazmat=False,
    )
    db_session.add(cargo)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()

    # Test valid cargo
    cargo = Cargo(
        id="test_cargo_1",
        weight=18000.0,
        value=50000.0,
        special_requirements={"temperature_control": False},
        hazmat=False,
    )
    db_session.add(cargo)
    db_session.commit()

    # Verify the cargo was saved
    saved_cargo = db_session.query(Cargo).filter_by(id="test_cargo_1").first()
    assert saved_cargo is not None
    assert saved_cargo.weight == 18000.0
    assert saved_cargo.value == 50000.0
    assert saved_cargo.hazmat is False


def test_route_relationships(db_session):
    """Test Route model relationships."""
    # Create required related objects
    transport = TransportType(
        id="test_transport_2",
        name="Test Truck",
        capacity=24000.0,
        emissions_class="EURO6",
        fuel_consumption_empty=25.0,
        fuel_consumption_loaded=32.0,
    )
    cargo = Cargo(
        id="test_cargo_2",
        weight=18000.0,
        value=50000.0,
        special_requirements={"temperature_control": False},
        hazmat=False,
    )
    db_session.add(transport)
    db_session.add(cargo)
    db_session.commit()

    # Create route with relationships
    now = datetime.now(timezone.utc)
    route = Route(
        id="test_route_1",
        origin={"latitude": 52.520008, "longitude": 13.404954},
        destination={"latitude": 50.075538, "longitude": 14.437800},
        pickup_time=now,
        delivery_time=now,
        transport_type=transport.id,
        cargo_id=cargo.id,
        distance_km=350.0,
        duration_hours=6.0,
        empty_driving={"before_km": 20.0, "after_km": 15.0},
        is_feasible=True,
        created_at=now,
    )
    db_session.add(route)
    db_session.commit()

    # Test relationships
    saved_route = db_session.query(Route).filter_by(id="test_route_1").first()
    assert saved_route is not None
    assert saved_route.transport.id == "test_transport_2"
    assert saved_route.cargo.id == "test_cargo_2"


def test_offer_relationships(db_session):
    """Test Offer model relationships."""
    # Create required related objects
    transport = TransportType(
        id="test_transport_3",
        name="Test Truck",
        capacity=24000.0,
        emissions_class="EURO6",
        fuel_consumption_empty=25.0,
        fuel_consumption_loaded=32.0,
    )
    cargo = Cargo(
        id="test_cargo_3",
        weight=18000.0,
        value=50000.0,
        special_requirements={"temperature_control": False},
        hazmat=False,
    )
    now = datetime.now(timezone.utc)
    route = Route(
        id="test_route_2",
        origin={"latitude": 52.520008, "longitude": 13.404954},
        destination={"latitude": 50.075538, "longitude": 14.437800},
        pickup_time=now,
        delivery_time=now,
        transport_type=transport.id,
        cargo_id=cargo.id,
        distance_km=350.0,
        duration_hours=6.0,
        empty_driving={"before_km": 20.0, "after_km": 15.0},
        is_feasible=True,
        created_at=now,
    )
    db_session.add_all([transport, cargo, route])
    db_session.commit()

    # Create offer with relationships
    offer = Offer(
        id="test_offer_1",
        route_id=route.id,
        total_cost=450.0,
        margin=0.15,
        final_price=517.50,
        fun_fact="Test fun fact",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(offer)
    db_session.commit()

    # Test relationships
    saved_offer = db_session.query(Offer).filter_by(id="test_offer_1").first()
    assert saved_offer is not None
    assert saved_offer.route.id == "test_route_2"
    assert saved_offer.route.transport.id == "test_transport_3"
    assert saved_offer.route.cargo.id == "test_cargo_3"


def test_seed_data(db_session):
    """Test seeding data."""
    # Clean up any existing data
    for table in reversed(Base.metadata.sorted_tables):
        db_session.execute(table.delete())
    db_session.commit()

    # Seed all data
    transport_types = seed_transport_types(db_session)
    cost_settings = seed_cost_settings(db_session)
    cargoes = seed_cargoes(db_session)
    routes = seed_routes(db_session, transport_types, cargoes)
    offers = seed_offers(db_session, routes)

    # Verify counts
    assert len(transport_types) == 3
    assert db_session.query(TransportType).count() == 3

    assert db_session.query(CostSettings).count() == 1
    assert cost_settings.id == "default"

    assert len(cargoes) == 3
    assert db_session.query(Cargo).count() == 3

    assert len(routes) == 3
    assert db_session.query(Route).count() == 3

    assert len(offers) == 3
    assert db_session.query(Offer).count() == 3


def test_query_performance(db_session):
    """Test query performance with seeded data."""
    # Seed test data
    transport_types = seed_transport_types(db_session)
    cost_settings = seed_cost_settings(db_session)
    cargoes = seed_cargoes(db_session)
    routes = seed_routes(db_session, transport_types, cargoes)
    offers = seed_offers(db_session, routes)

    # Test complex join query performance
    query = (
        db_session.query(Offer)
        .join(Route)
        .join(TransportType)
        .join(Cargo)
        .filter(TransportType.emissions_class == "EURO6")
        .filter(Cargo.hazmat.is_(False))
        .filter(Route.distance_km > 300)
    )

    # Execute query and verify results
    results = query.all()
    assert len(results) > 0  # Should find at least one matching offer

    # Verify eager loading performance
    offer = (
        db_session.query(Offer)
        .filter_by(id="offer_standard")
        .first()
    )
    assert offer is not None
    
    # Access relationships (should not trigger additional queries due to eager loading)
    assert offer.route is not None
    assert offer.route.transport is not None
    assert offer.route.cargo is not None
