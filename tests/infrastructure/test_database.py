"""Tests for database models and migrations."""
import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy.exc import IntegrityError

from src.infrastructure.models import (
    TransportType,
    CostSettings,
    Cargo,
    Route,
    Offer,
    Vehicle,
    Driver,
    SystemSettings,
    TransportSettings,
    Base
)
from tests.fixtures.seed_data import (
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
    now = datetime.now(timezone.utc)
    route = Route(
        id="test_route_cs",
        origin={"latitude": 52.520008, "longitude": 13.404954},
        destination={"latitude": 50.075538, "longitude": 14.437800},
        pickup_time=now,
        delivery_time=now + timedelta(hours=6),
        transport_type="test_transport_1",
        distance_km=350.0,
        duration_hours=6.0,
        is_feasible=True,
    )
    db_session.add(route)
    db_session.commit()

    # Test required fields
    settings = CostSettings(
        route_id=route.id,
        version="1.0",
        fuel_rates={"diesel": 1.8},
        toll_rates={"DE": {"standard": 0.187}},
        driver_rates={"daily": 200.0},
        overhead_rates={"maintenance_per_km": 0.15},
        maintenance_rates={"per_km": 0.12},
        enabled_components=["fuel", "toll", "driver"],
        created_at=now,
        modified_at=now,
    )
    db_session.add(settings)
    db_session.commit()

    # Verify the settings were saved
    saved_settings = db_session.query(CostSettings).filter_by(route_id=route.id).first()
    assert saved_settings is not None
    assert saved_settings.version == "1.0"
    assert saved_settings.fuel_rates["diesel"] == 1.8
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
        delivery_time=now + timedelta(hours=6),
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
        version="1.0",
        status="draft",
        margin=0.15,
        total_cost=450.00,
        final_price=517.50,
        currency="EUR",
        fun_fact="Test fun fact",
        created_at=now,
    )
    db_session.add(offer)
    db_session.commit()

    # Test relationships
    saved_offer = db_session.query(Offer).filter_by(id="test_offer_1").first()
    assert saved_offer is not None
    assert saved_offer.route.id == "test_route_2"
    assert saved_offer.route.transport.id == "test_transport_3"
    assert saved_offer.route.cargo.id == "test_cargo_3"


def test_vehicle_constraints(db_session):
    """Test Vehicle model constraints."""
    # Test required fields
    vehicle = Vehicle(
        fuel_consumption_rate=25.0,  # Missing vehicle_type
        empty_consumption_factor=0.8,
        maintenance_rate_per_km=0.15,
        toll_class="EURO6",
    )
    db_session.add(vehicle)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()

    # Test valid vehicle
    vehicle = Vehicle(
        vehicle_type="TRUCK_40T",
        fuel_consumption_rate=25.0,
        empty_consumption_factor=0.8,
        maintenance_rate_per_km=0.15,
        toll_class="EURO6",
        has_special_equipment=True,
        equipment_costs={"refrigeration": 50.0},
    )
    db_session.add(vehicle)
    db_session.commit()

    # Verify the vehicle was saved
    saved_vehicle = db_session.query(Vehicle).filter_by(vehicle_type="TRUCK_40T").first()
    assert saved_vehicle is not None
    assert saved_vehicle.fuel_consumption_rate == 25.0
    assert saved_vehicle.equipment_costs["refrigeration"] == 50.0


def test_driver_constraints(db_session):
    """Test Driver model constraints."""
    future_date = datetime.now(timezone.utc) + timedelta(days=365)
    
    # Test required fields
    driver = Driver(
        first_name="John",  # Missing last_name
        license_number="DL123456",
        license_type="CE",
        license_expiry=future_date,
        contact_number="+1234567890",
    )
    db_session.add(driver)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()

    # Test valid driver
    driver = Driver(
        first_name="John",
        last_name="Doe",
        license_number="DL123456",
        license_type="CE",
        license_expiry=future_date,
        contact_number="+1234567890",
        email="john.doe@example.com",
        years_experience=5,
    )
    db_session.add(driver)
    db_session.commit()

    # Verify the driver was saved
    saved_driver = db_session.query(Driver).filter_by(license_number="DL123456").first()
    assert saved_driver is not None
    assert saved_driver.first_name == "John"
    assert saved_driver.last_name == "Doe"
    assert saved_driver.years_experience == 5


def test_driver_vehicle_relationship(db_session):
    """Test relationship between Driver and Vehicle models."""
    future_date = datetime.now(timezone.utc) + timedelta(days=365)
    
    # Create a driver
    driver = Driver(
        first_name="Jane",
        last_name="Smith",
        license_number="DL789012",
        license_type="CE",
        license_expiry=future_date,
        contact_number="+1987654321",
    )
    db_session.add(driver)
    db_session.commit()

    # Create vehicles assigned to the driver
    vehicle1 = Vehicle(
        vehicle_type="TRUCK_40T",
        fuel_consumption_rate=25.0,
        empty_consumption_factor=0.8,
        maintenance_rate_per_km=0.15,
        toll_class="EURO6",
        driver_id=driver.id
    )
    vehicle2 = Vehicle(
        vehicle_type="TRUCK_20T",
        fuel_consumption_rate=20.0,
        empty_consumption_factor=0.75,
        maintenance_rate_per_km=0.12,
        toll_class="EURO5",
        driver_id=driver.id
    )
    db_session.add_all([vehicle1, vehicle2])
    db_session.commit()

    # Verify relationships
    saved_driver = db_session.query(Driver).filter_by(id=driver.id).first()
    assert len(saved_driver.vehicles) == 2
    assert any(v.vehicle_type == "TRUCK_40T" for v in saved_driver.vehicles)
    assert any(v.vehicle_type == "TRUCK_20T" for v in saved_driver.vehicles)

    # Test cascade delete
    db_session.delete(driver)
    db_session.commit()
    
    # Verify vehicles still exist but have no driver
    orphaned_vehicles = db_session.query(Vehicle).all()
    assert len(orphaned_vehicles) == 2  # All vehicles should still exist
    for vehicle in orphaned_vehicles:
        assert vehicle.driver_id is None  # Driver ID should be NULL
        assert vehicle.driver is None  # Driver relationship should be None


def test_system_settings(db_session):
    """Test SystemSettings model."""
    settings = SystemSettings(
        api_url="https://api.example.com",
        api_version="v1",
        request_timeout_seconds=30,
        min_margin_percent=5.0,
        max_margin_percent=20.0,
        maps_provider="google",
        geocoding_provider="google"
    )
    db_session.add(settings)
    db_session.commit()

    # Verify settings were saved
    saved_settings = db_session.query(SystemSettings).first()
    assert saved_settings is not None
    assert saved_settings.api_url == "https://api.example.com"
    assert saved_settings.default_currency == "EUR"  # Default value
    assert saved_settings.default_language == "en"   # Default value
    assert saved_settings.price_rounding_decimals == 2  # Default value


def test_transport_settings(db_session):
    """Test TransportSettings model."""
    settings = TransportSettings(
        vehicle_types={"TRUCK_40T": {"max_weight": 40000}},
        equipment_types={"REFRIGERATED": {"cost_per_hour": 10.0}},
        cargo_types={"PERISHABLE": {"requires_cooling": True}},
        loading_time_minutes=30,
        unloading_time_minutes=30,
        max_driving_hours=9.0,
        required_rest_hours=11.0,
        max_working_days=5,
        speed_limits={"highway": 80, "urban": 50}
    )
    db_session.add(settings)
    db_session.commit()

    # Verify settings were saved
    saved_settings = db_session.query(TransportSettings).first()
    assert saved_settings is not None
    assert saved_settings.vehicle_types["TRUCK_40T"]["max_weight"] == 40000
    assert saved_settings.max_driving_hours == 9.0
    assert saved_settings.speed_limits["highway"] == 80


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

    # Update some routes to active status
    routes = db_session.query(Route).all()  # Get all routes from the database
    for route in routes[:2]:
        route.status = "active"
        # Also update the corresponding offer
        offer = db_session.query(Offer).filter(Offer.route_id == route.id).first()
        if offer:
            offer.status = "active"
        else:
            print(f"No offer found for route {route.id}")
    db_session.commit()

    # Debug: Check what we have in the database
    print("\nDebug: Checking database state")
    print("Routes:")
    for route in db_session.query(Route).all():
        print(f"  Route {route.id}: status={route.status}")
        offer = db_session.query(Offer).filter(Offer.route_id == route.id).first()
        if offer:
            print(f"    Offer {offer.id}: status={offer.status}")
        else:
            print("    No offer found")

    # Test complex join query performance
    query = (
        db_session.query(Offer)
        .join(Route, Offer.route_id == Route.id)
        .join(TransportType, Route.transport_type == TransportType.id)
        .join(Cargo, Route.cargo_id == Cargo.id)
        .filter(TransportType.emissions_class == "EURO6")
        .filter(Cargo.hazmat.is_(False))
        .filter(Route.distance_km > 300)
    )

    # Execute query and verify results
    results = query.all()
    assert len(results) == 2  # Should find exactly two offers (standard and eco trucks)
    for result in results:
        assert result.route.transport.emissions_class == "EURO6"
        assert not result.route.cargo.hazmat
        assert result.route.distance_km > 300

    # Verify eager loading performance
    offer = (
        db_session.query(Offer)
        .filter_by(id="offer_standard")
        .first()
    )
    assert offer is not None
    assert offer.route is not None
    assert offer.route.transport is not None
    assert offer.route.cargo is not None
    assert float(offer.final_price) == 517.50
    assert float(offer.total_cost) == 450.0
    assert float(offer.margin) == 0.15


def test_error_cases(db_session):
    """Test various error cases and constraints."""
    future_date = datetime.now(timezone.utc) + timedelta(days=365)
    
    # Test duplicate license number
    driver1 = Driver(
        first_name="John",
        last_name="Doe",
        license_number="DL999999",
        license_type="CE",
        license_expiry=future_date,
        contact_number="+1234567890",
    )
    db_session.add(driver1)
    db_session.commit()

    driver2 = Driver(
        first_name="Jane",
        last_name="Smith",
        license_number="DL999999",  # Same license number
        license_type="CE",
        license_expiry=future_date,
        contact_number="+1987654321",
    )
    db_session.add(driver2)
    with pytest.raises(IntegrityError, match="UNIQUE constraint failed"):
        db_session.commit()
    db_session.rollback()

    # Test invalid email format
    driver3 = Driver(
        first_name="Alice",
        last_name="Johnson",
        license_number="DL888888",
        license_type="CE",
        license_expiry=future_date,
        contact_number="+1122334455",
        email="invalid.email",  # Invalid email format
    )
    db_session.add(driver3)
    db_session.commit()  # Email format is not validated at database level

    # Test expired license
    past_date = datetime.now(timezone.utc) - timedelta(days=1)
    driver4 = Driver(
        first_name="Bob",
        last_name="Wilson",
        license_number="DL777777",
        license_type="CE",
        license_expiry=past_date,  # Expired license
        contact_number="+1122334455",
    )
    db_session.add(driver4)
    db_session.commit()  # License expiry is not validated at database level


def test_query_performance_benchmarks(db_session):
    """Test performance of common database queries."""
    import time
    
    # Seed test data
    transport_types = seed_transport_types(db_session)
    seed_cost_settings(db_session)
    cargoes = seed_cargoes(db_session)
    routes = seed_routes(db_session, transport_types, cargoes)
    offers = seed_offers(db_session, routes)

    # Update some routes to active status
    routes = db_session.query(Route).all()  # Get all routes from the database
    for route in routes[:2]:
        route.status = "active"  # This wasn't taking effect
        # Also update the corresponding offer
        offer = db_session.query(Offer).filter(Offer.route_id == route.id).first()
        if offer:
            offer.status = "active"
        else:
            print(f"No offer found for route {route.id}")
    db_session.commit()

    # Debug: Check what we have in the database
    print("\nDebug: Checking database state")
    print("Routes:")
    for route in db_session.query(Route).all():
        print(f"  Route {route.id}: status={route.status}")
        offer = db_session.query(Offer).filter(Offer.route_id == route.id).first()
        if offer:
            print(f"    Offer {offer.id}: status={offer.status}")
        else:
            print("    No offer found")

    # Test 1: Simple query performance
    start_time = time.time()
    routes = db_session.query(Route).all()
    query_time = time.time() - start_time
    assert query_time < 1.0, f"Simple query took too long: {query_time:.3f} seconds"
    assert len(routes) > 0

    # Test 2: Complex join performance
    start_time = time.time()
    results = (
        db_session.query(Route)
        .join(TransportType, Route.transport_type == TransportType.id)
        .join(Cargo, Route.cargo_id == Cargo.id)
        .join(Offer, Route.id == Offer.route_id)
        .filter(Route.status == "active")
        .all()
    )
    query_time = time.time() - start_time
    assert query_time < 1.0, f"Complex join query took too long: {query_time:.3f} seconds"
    assert len(results) == 2  # Should find the two active routes

    # Test 3: Aggregation performance
    start_time = time.time()
    from sqlalchemy import func
    result = (
        db_session.query(
            Route.status,
            func.count(Route.id).label('count'),
            func.avg(Route.distance_km).label('avg_distance')
        )
        .group_by(Route.status)
        .all()
    )
    query_time = time.time() - start_time
    assert query_time < 1.0, f"Aggregation query took too long: {query_time:.3f} seconds"
    assert len(result) == 2  # Should have two status groups (active and draft)
    for status, count, avg_distance in result:
        assert status in ["active", "draft"]
        assert count > 0
        assert avg_distance > 0

    # Test 4: Bulk insert performance
    start_time = time.time()
    future_date = datetime.now(timezone.utc) + timedelta(days=365)
    drivers = [
        Driver(
            first_name=f"Driver{i}",
            last_name=f"Test{i}",
            license_number=f"DL{i:06d}",
            license_type="CE",
            license_expiry=future_date,
            contact_number=f"+1{i:010d}",
        )
        for i in range(1, 11)  # Create 10 test drivers
    ]
    db_session.bulk_save_objects(drivers)
    db_session.commit()
    query_time = time.time() - start_time
    assert query_time < 1.0, f"Bulk insert took too long: {query_time:.3f} seconds"
    
    # Verify bulk insert results
    driver_count = db_session.query(Driver).filter(
        Driver.license_number.like('DL%')
    ).count()
    assert driver_count == 10


def test_cascade_operations(db_session):
    """Test cascade operations and referential integrity."""
    # Create test data
    future_date = datetime.now(timezone.utc) + timedelta(days=365)
    
    # Create a driver with vehicles
    driver = Driver(
        first_name="Test",
        last_name="Driver",
        license_number="DL123TEST",
        license_type="CE",
        license_expiry=future_date,
        contact_number="+1234567890",
    )
    db_session.add(driver)
    db_session.commit()

    vehicles = [
        Vehicle(
            vehicle_type=f"TRUCK_{i}0T",
            fuel_consumption_rate=20.0 + i,
            empty_consumption_factor=0.7 + (i/10),
            maintenance_rate_per_km=0.1 + (i/10),
            toll_class=f"EURO{5+i}",
            driver_id=driver.id
        )
        for i in range(1, 4)
    ]
    db_session.bulk_save_objects(vehicles)
    db_session.commit()

    # Test cascade update
    driver.last_name = "UpdatedDriver"
    db_session.commit()
    
    # Verify vehicles still reference the driver
    vehicles = db_session.query(Vehicle).filter_by(driver_id=driver.id).all()
    assert len(vehicles) == 3
    
    # Test cascade delete
    db_session.delete(driver)
    db_session.commit()
    
    # Verify vehicles still exist but have no driver
    orphaned_vehicles = db_session.query(Vehicle).all()
    assert len(orphaned_vehicles) == 3  # All vehicles should still exist
    for vehicle in orphaned_vehicles:
        assert vehicle.driver_id is None  # Driver ID should be NULL
        assert vehicle.driver is None  # Driver relationship should be None
