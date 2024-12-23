"""Tests for domain entities."""
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4
from pytz import UTC
import pytest
from pydantic import ValidationError

from src.domain.entities import (
    Route, Location, CountrySegment, EmptyDriving, TransportType,
    CargoSpecification, VehicleSpecification, Cost, CostSettings, Offer,
    TimeWindow, Cargo
)
from src.domain.value_objects import (
    CostBreakdown,
    RouteMetadata
)


@pytest.fixture
def valid_cargo_spec():
    """Fixture for valid cargo specification."""
    return CargoSpecification(
        cargo_type="refrigerated",
        weight_kg=5000.0,
        volume_m3=20.0,
        temperature_controlled=True,
        required_temp_celsius=-18.0,
        special_handling=["quick_loading"],
        hazmat_class=None
    )


@pytest.fixture
def valid_vehicle_spec():
    """Fixture for valid vehicle specification."""
    return VehicleSpecification(
        vehicle_type="reefer_truck",
        fuel_consumption_rate=32.5,
        empty_consumption_factor=0.85,
        maintenance_rate_per_km=Decimal("0.15"),
        toll_class="heavy",
        has_special_equipment=True,
        equipment_costs={"refrigeration_unit": Decimal("50.00")}
    )


@pytest.fixture
def valid_time_windows():
    """Fixture for valid time windows."""
    now = datetime.now(UTC)
    return [
        TimeWindow(
            location=Location(address="Warsaw", latitude=52.23, longitude=21.01),
            earliest=now + timedelta(hours=1),
            latest=now + timedelta(hours=2),
            operation_type="pickup",
            duration_hours=1.0
        ),
        TimeWindow(
            location=Location(address="Berlin", latitude=52.52, longitude=13.40),
            earliest=now + timedelta(hours=8),
            latest=now + timedelta(hours=10),
            operation_type="delivery",
            duration_hours=1.0
        )
    ]


def test_route_creation_with_specs(valid_cargo_spec, valid_vehicle_spec, valid_time_windows):
    """Test creating a Route with specifications."""
    route = Route(
        origin=Location(address="Warsaw", latitude=52.23, longitude=21.01),
        destination=Location(address="Berlin", latitude=52.52, longitude=13.40),
        pickup_time=datetime.now(UTC),
        delivery_time=datetime.now(UTC) + timedelta(days=1),
        transport_type=TransportType.TRUCK,
        distance_km=1050.0,
        duration_hours=12.5,
        empty_driving=EmptyDriving(distance_km=200.0, duration_hours=4.0),
        cargo_specs=valid_cargo_spec,
        vehicle_specs=valid_vehicle_spec,
        time_windows=valid_time_windows,
        country_segments=[
            CountrySegment(
                country="Poland",
                country_code="PL",
                distance_km=400.0,
                duration_hours=5.0,
                road_types={"highway": 300.0, "rural": 100.0},
                toll_roads=True
            ),
            CountrySegment(
                country="Germany",
                country_code="DE",
                distance_km=650.0,
                duration_hours=7.5,
                road_types={"highway": 500.0, "rural": 150.0},
                toll_roads=True
            )
        ]
    )
    assert route.total_distance == 1250.0
    assert route.total_duration == 16.5
    assert route.get_country_distance("PL") == 400.0
    assert route.get_country_duration("DE") == 7.5


def test_cost_creation_with_validity():
    """Test creating a Cost with validity period."""
    cost = Cost(
        route_id=uuid4(),
        breakdown={
            "fuel_costs": {
                "PL": Decimal("150.75"),
                "DE": Decimal("180.25")
            },
            "toll_costs": {
                "PL": Decimal("85.50"),
                "DE": Decimal("120.75")
            },
            "driver_costs": {
                "PL": Decimal("100.00"),
                "DE": Decimal("150.00")
            },
            "rest_period_costs": Decimal("75.00")
        },
        validity_period=timedelta(hours=24),
        calculation_method="detailed",
        version="2.0"
    )
    assert cost.is_valid()
    assert cost.total == Decimal("862.25")
    assert not cost.recalculate_needed()


def test_cost_settings_with_factors():
    """Test CostSettings with enhanced factors."""
    settings = CostSettings(
        fuel_prices={"PL": Decimal("6.50"), "DE": Decimal("7.20")},
        driver_rates={"PL": Decimal("25.00"), "DE": Decimal("35.00")},
        toll_rates={"PL": Decimal("0.15"), "DE": Decimal("0.20")},
        maintenance_rate_per_km=Decimal("0.15"),
        rest_period_rate=Decimal("30.00"),
        loading_unloading_rate=Decimal("40.00"),
        empty_driving_factors={
            "fuel": Decimal("0.85"),
            "toll": Decimal("1.00"),
            "driver": Decimal("1.00")
        },
        cargo_factors={
            "refrigerated": {
                "weight": Decimal("0.001"),
                "volume": Decimal("0.05"),
                "temperature": Decimal("2.50")
            }
        },
        overhead_rates={
            "distance": Decimal("0.10"),
            "time": Decimal("15.00"),
            "fixed": Decimal("100.00")
        }
    )
    
    assert settings.get_fuel_price("PL") == Decimal("6.50")
    assert settings.get_driver_rate("DE") == Decimal("35.00")
    assert settings.get_toll_rate("PL") == Decimal("0.15")
    assert settings.get_cargo_factors("refrigerated") == {
        "weight": Decimal("0.001"),
        "volume": Decimal("0.05"),
        "temperature": Decimal("2.50")
    }


def test_time_window_validation():
    """Test TimeWindow validation."""
    now = datetime.now(UTC)
    with pytest.raises(ValidationError):
        TimeWindow(
            location=Location(address="Warsaw", latitude=52.23, longitude=21.01),
            earliest=now + timedelta(hours=2),
            latest=now + timedelta(hours=1),  # Invalid: latest before earliest
            operation_type="pickup",
            duration_hours=1.0
        )


def test_vehicle_spec_validation():
    """Test VehicleSpecification validation."""
    with pytest.raises(ValidationError):
        VehicleSpecification(
            vehicle_type="reefer_truck",
            fuel_consumption_rate=-1.0,  # Invalid: negative consumption
            empty_consumption_factor=0.85,
            maintenance_rate_per_km=Decimal("0.15"),
            toll_class="heavy"
        )


def test_cargo_spec_validation():
    """Test CargoSpecification validation."""
    with pytest.raises(ValidationError):
        CargoSpecification(
            cargo_type="refrigerated",
            weight_kg=-100.0,  # Invalid: negative weight
            volume_m3=20.0,
            temperature_controlled=True,
            required_temp_celsius=-18.0
        )


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
        cost_id=uuid4(),  # Add required cost_id
        base_cost=Decimal("536.25"),
        margin=Decimal("0.1"),  # Use Decimal for margin
        final_price=Decimal("589.88"),
        fun_fact="Trucks transport over 70% of all freight in the EU!",
    )
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
        type="standard",  # Add required type
        special_requirements={"temperature": "ambient"},  # Use string values
        hazmat=False,
    )
    assert cargo.id == "cargo_001"
    assert cargo.weight == 15000.0
    assert cargo.value == Decimal("50000.00")


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
