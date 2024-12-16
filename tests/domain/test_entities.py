"""Tests for domain entities."""
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.domain.entities import Cargo, Cost, CostSettings, Offer, Route, TransportType
from src.domain.value_objects import CostBreakdown, EmptyDriving, Location, RouteMetadata


def test_route_creation():
    """Test creating a valid Route."""
    route = Route(
        origin=Location(address="Paris, France", latitude=48.8566, longitude=2.3522),
        destination=Location(address="Berlin, Germany", latitude=52.5200, longitude=13.4050),
        pickup_time=datetime.utcnow(),
        delivery_time=datetime.utcnow() + timedelta(days=1),
        transport_type="flatbed_truck",
        distance_km=1050.0,
        duration_hours=12.5,
        empty_driving=EmptyDriving(distance_km=200.0, duration_hours=4.0),
    )
    assert route.total_distance == 1250.0  # 1050 + 200
    assert route.total_duration == 16.5  # 12.5 + 4.0


def test_route_validation():
    """Test Route validation."""
    with pytest.raises(ValidationError):
        Route(
            origin=Location(address="Paris, France", latitude=48.8566, longitude=2.3522),
            destination=Location(address="Berlin, Germany", latitude=52.5200, longitude=13.4050),
            pickup_time=datetime.utcnow(),
            delivery_time=datetime.utcnow() - timedelta(days=1),  # Invalid: delivery before pickup
            transport_type="flatbed_truck",
            distance_km=1050.0,
            duration_hours=12.5,
            empty_driving=EmptyDriving(distance_km=200.0, duration_hours=4.0),
        )


def test_cost_creation():
    """Test creating a valid Cost."""
    cost = Cost(
        route_id=uuid4(),
        breakdown=CostBreakdown(
            fuel_cost=Decimal("150.75"),
            toll_cost=Decimal("85.50"),
            driver_cost=Decimal("200.00"),
            overheads=Decimal("75.00"),
            cargo_specific_costs={"cleaning": Decimal("25.00")},
            total=Decimal("536.25"),
        ),
    )
    assert cost.total == Decimal("536.25")


def test_offer_creation():
    """Test creating a valid Offer."""
    offer = Offer(
        route_id=uuid4(),
        total_cost=Decimal("536.25"),
        margin=0.1,  # 10% margin
        final_price=Decimal("589.88"),  # 536.25 * 1.1
        fun_fact="Trucks transport over 70% of all freight in the EU!",
    )
    assert offer.margin == 0.1
    assert offer.final_price == Decimal("589.88")


def test_offer_price_validation():
    """Test Offer price validation."""
    with pytest.raises(ValidationError):
        Offer(
            route_id=uuid4(),
            total_cost=Decimal("536.25"),
            margin=0.1,
            final_price=Decimal("600.00"),  # Incorrect price
            fun_fact="Trucks transport over 70% of all freight in the EU!",
        )


def test_transport_type_creation():
    """Test creating a valid TransportType."""
    transport = TransportType(
        id="flatbed_truck",
        name="Flatbed Truck",
        capacity=24000.0,
        emissions_class="EURO6",
        fuel_consumption_empty=25.0,
        fuel_consumption_loaded=32.0,
    )
    
    # Test fuel consumption calculation
    empty_consumption = transport.calculate_fuel_consumption(100, is_loaded=False)
    loaded_consumption = transport.calculate_fuel_consumption(100, is_loaded=True)
    
    assert empty_consumption == 25.0  # 25L/100km * 100km
    assert loaded_consumption == 32.0  # 32L/100km * 100km


def test_cargo_creation():
    """Test creating a valid Cargo."""
    cargo = Cargo(
        id="cargo_001",
        weight=15000.0,
        value=Decimal("50000.00"),
        special_requirements={"temperature_controlled": False},
        hazmat=False,
    )
    
    # Test transport type validation
    valid_transport = TransportType(
        id="flatbed_truck",
        name="Flatbed Truck",
        capacity=24000.0,
        emissions_class="EURO6",
        fuel_consumption_empty=25.0,
        fuel_consumption_loaded=32.0,
    )
    
    invalid_transport = TransportType(
        id="small_truck",
        name="Small Truck",
        capacity=10000.0,  # Too small
        emissions_class="EURO6",
        fuel_consumption_empty=20.0,
        fuel_consumption_loaded=25.0,
    )
    
    assert cargo.validate_transport_type(valid_transport) is True
    assert cargo.validate_transport_type(invalid_transport) is False


def test_cost_settings_creation():
    """Test creating valid CostSettings."""
    settings = CostSettings(
        fuel_price_per_liter=Decimal("1.50"),
        driver_daily_salary=Decimal("138.00"),
        toll_rates={"DE": Decimal("0.10"), "FR": Decimal("0.12")},
        overheads={
            "leasing": Decimal("20.00"),
            "depreciation": Decimal("10.00"),
        },
        cargo_factors={
            "cleaning": Decimal("10.00"),
            "insurance_rate": Decimal("0.001"),
        },
    )
    
    # Test toll cost calculation
    toll_cost = settings.calculate_toll_cost({"DE": 500.0, "FR": 300.0})
    expected_cost = Decimal("0.10") * Decimal("500") + Decimal("0.12") * Decimal("300")
    assert toll_cost == expected_cost
