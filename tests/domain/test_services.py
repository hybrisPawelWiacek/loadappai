"""Unit tests for domain services."""
import pytest
from datetime import datetime, timedelta
from pytz import UTC
from decimal import Decimal
from uuid import uuid4
from typing import Dict, Optional, List

from src.domain.entities import (
    Route, Location, CountrySegment, EmptyDriving, TransportType,
    CargoSpecification, VehicleSpecification, Cost, CostSettings, Offer, Cargo
)
from src.domain.services import (
    RoutePlanningService, CostCalculationService, OfferGenerationService
)
from src.domain.value_objects import (
    CostBreakdown, RouteMetadata
)

# Test Data
@pytest.fixture
def valid_location():
    return Location(
        latitude=52.2297,
        longitude=21.0122,
        address="Test Address",
        country="PL"
    )

@pytest.fixture
def valid_route(valid_location):
    return Route(
        id=str(uuid4()),
        origin=valid_location,
        destination=Location(
            latitude=53.2297,
            longitude=22.0122,
            address="Destination Address",
            country="PL"
        ),
        pickup_time=datetime.now(UTC) + timedelta(days=1),
        delivery_time=datetime.now(UTC) + timedelta(days=2),
        transport_type=TransportType.TRUCK,
        cargo_id=str(uuid4()),
        distance_km=500.0,
        duration_hours=8.0,
        empty_driving=EmptyDriving(distance_km=50.0, duration_hours=1.0),
        metadata={"optimization_data": {"distance_km": 500.0, "duration_hours": 8.0}},
        country_segments=[
            CountrySegment(
                country="Poland",
                distance_km=500.0,
                duration_hours=8.0,
                road_types=[{"highway": 400.0}, {"rural": 100.0}],
                toll_class="standard"
            )
        ]
    )

@pytest.fixture
def cost_settings():
    """Fixture for basic cost settings."""
    return CostSettings(
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
            "standard": {
                "weight": Decimal("0.001"),
                "volume": Decimal("0.05")
            },
            "refrigerated": {
                "weight": Decimal("0.001"),
                "volume": Decimal("0.05"),
                "temperature": Decimal("2.50")
            },
            "hazmat": {
                "weight": Decimal("0.002"),
                "volume": Decimal("0.07"),
                "risk": Decimal("5.00")
            }
        },
        overhead_rates={
            "distance": Decimal("0.10"),
            "time": Decimal("15.00"),
            "fixed": Decimal("100.00")
        }
    )

@pytest.fixture
def transport_type():
    return TransportType.TRUCK

@pytest.fixture
def cargo():
    return Cargo(
        id=str(uuid4()),
        type="standard",
        weight=1000.0,
        volume=10.0,
        value=Decimal("5000.0"),
        special_requirements={"temperature": "ambient"},
        hazmat=False,
        metadata=None
    )

@pytest.fixture
def mock_location_service():
    class MockLocationService:
        def calculate_distance(self, origin: Location, destination: Location) -> float:
            return 500.0

        def calculate_duration(self, origin: Location, destination: Location) -> float:
            return 8.0

        def get_country_segments(self, origin: Location, destination: Location, transport_type: str = "standard") -> List[CountrySegment]:
            return [CountrySegment(
                country_code="PL",
                distance=500.0,
                duration_hours=8.0,
                toll_rates={"standard": Decimal("0.15")}
            )]

    return MockLocationService()

@pytest.fixture
def mock_ai_service():
    class MockAIService:
        def generate_response(self, prompt: str, **kwargs) -> str:
            return "Test response"

        def generate_route_fact(self, origin: Location, destination: Location, context: Optional[Dict] = None) -> str:
            return "Test fact"

        def enhance_route_description(self, origin: Location, destination: Location, context: Optional[Dict] = None) -> str:
            return "Test description"

    return MockAIService()

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
def enhanced_cost_settings():
    """Fixture for enhanced cost settings."""
    return CostSettings(
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


# RoutePlanningService Tests
class TestRoutePlanningService:
    """Test cases for RoutePlanningService."""

    def test_create_route_success(self, valid_location, mock_location_service):
        """Test successful route creation."""
        service = RoutePlanningService(location_service=mock_location_service)
        pickup_time = datetime.now(UTC) + timedelta(days=1)
        delivery_time = datetime.now(UTC) + timedelta(days=2)

        destination = Location(
            latitude=53.2297,
            longitude=22.0122,
            address="Destination Address",
            country="PL"
        )

        route = service.create_route(
            origin=valid_location,
            destination=destination,
            pickup_time=pickup_time,
            delivery_time=delivery_time,
            transport_type="standard"
        )

        assert route.origin == valid_location
        assert route.destination == destination
        assert route.pickup_time == pickup_time
        assert route.delivery_time == delivery_time
        assert route.transport_type == "standard"
        assert route.distance_km == 500.0
        assert route.duration_hours == 8.0

    def test_create_route_invalid_times(self, valid_location, mock_location_service):
        """Test route creation with invalid times."""
        service = RoutePlanningService(location_service=mock_location_service)
        pickup_time = datetime.now(UTC) + timedelta(days=2)
        delivery_time = datetime.now(UTC) + timedelta(days=1)

        with pytest.raises(ValueError):
            service.create_route(
                origin=valid_location,
                destination=valid_location,
                pickup_time=pickup_time,
                delivery_time=delivery_time,
                transport_type="standard"
            )

    def test_create_route_same_locations(self, valid_location, mock_location_service):
        """Test route creation with same origin and destination."""
        service = RoutePlanningService(location_service=mock_location_service)
        pickup_time = datetime.now(UTC)
        delivery_time = datetime.now(UTC) + timedelta(hours=1)

        with pytest.raises(ValueError):
            service.create_route(
                origin=valid_location,
                destination=valid_location,
                pickup_time=pickup_time,
                delivery_time=delivery_time,
                transport_type="standard"
            )


# CostCalculationService Tests
class TestCostCalculationService:
    """Test cases for enhanced CostCalculationService."""

    def test_calculate_detailed_cost(self, valid_route, enhanced_cost_settings, valid_cargo_spec, valid_vehicle_spec):
        """Test detailed cost calculation with all components."""
        # Update route with specs
        valid_route.cargo_specs = valid_cargo_spec
        valid_route.vehicle_specs = valid_vehicle_spec
        
        service = CostCalculationService()
        cost = service.calculate_detailed_cost(
            route=valid_route,
            settings=enhanced_cost_settings,
            cargo_spec=valid_cargo_spec,
            vehicle_spec=valid_vehicle_spec,
            include_empty_driving=True,
            include_country_breakdown=True
        )
        
        # Verify cost components
        assert isinstance(cost.breakdown.fuel_costs, dict)
        assert isinstance(cost.breakdown.toll_costs, dict)
        assert isinstance(cost.breakdown.driver_costs, dict)
        assert isinstance(cost.breakdown.empty_driving_costs, dict)
        assert isinstance(cost.breakdown.cargo_specific_costs, dict)
        assert isinstance(cost.breakdown.overheads, dict)
        
        # Verify country-specific costs
        assert "PL" in cost.breakdown.fuel_costs
        assert "DE" in cost.breakdown.toll_costs
        
        # Verify cargo-specific costs
        assert "temperature" in cost.breakdown.cargo_specific_costs
        assert "weight" in cost.breakdown.cargo_specific_costs
        
        # Verify empty driving costs
        assert "fuel" in cost.breakdown.empty_driving_costs["PL"]
        assert "toll" in cost.breakdown.empty_driving_costs["PL"]
        
        # Verify total cost is positive
        assert cost.total > 0

    def test_calculate_cost_with_time_windows(self, valid_route, enhanced_cost_settings):
        """Test cost calculation with time window constraints."""
        valid_route.time_windows = {"pickup": (datetime.now(UTC), datetime.now(UTC) + timedelta(hours=2))}
        
        service = CostCalculationService()
        cost = service.calculate_detailed_cost(
            route=valid_route,
            settings=enhanced_cost_settings
        )
        
        # Verify loading/unloading costs
        assert cost.breakdown.loading_unloading_costs > 0
        
        # Verify rest period costs
        assert cost.breakdown.rest_period_costs > 0

    def test_calculate_cost_with_special_equipment(self, valid_route, enhanced_cost_settings, valid_vehicle_spec):
        """Test cost calculation with special equipment."""
        valid_route.vehicle_specs = valid_vehicle_spec
        
        service = CostCalculationService()
        cost = service.calculate_detailed_cost(
            route=valid_route,
            settings=enhanced_cost_settings
        )
        
        # Verify equipment costs are included in overheads
        assert cost.breakdown.overheads["fixed"] >= valid_vehicle_spec.equipment_costs["refrigeration_unit"]

    def test_calculate_cost_with_empty_driving(self, valid_route, enhanced_cost_settings):
        """Test cost calculation with empty driving segments."""
        service = CostCalculationService()
        
        # Calculate with empty driving
        cost_with_empty = service.calculate_detailed_cost(
            route=valid_route,
            settings=enhanced_cost_settings,
            include_empty_driving=True
        )
        
        # Calculate without empty driving
        cost_without_empty = service.calculate_detailed_cost(
            route=valid_route,
            settings=enhanced_cost_settings,
            include_empty_driving=False
        )
        
        # Verify empty driving costs
        assert cost_with_empty.total > cost_without_empty.total
        assert len(cost_with_empty.breakdown.empty_driving_costs) > 0

    def test_cost_validity_period(self, valid_route, enhanced_cost_settings):
        """Test cost calculation with validity period."""
        service = CostCalculationService()
        
        cost = service.calculate_detailed_cost(
            route=valid_route,
            settings=enhanced_cost_settings,
            validity_period=timedelta(hours=24)
        )
        
        assert cost.is_valid
        assert cost.validity_period == timedelta(hours=24)
        assert not cost.recalculate_needed()

    def test_calculate_route_cost(self, valid_route, cost_settings, transport_type, cargo):
        service = CostCalculationService()
        
        cost_breakdown = service.calculate_route_cost(
            route=valid_route,
            settings=cost_settings,
            cargo=cargo,
            transport_type=transport_type
        )
        
        assert isinstance(cost_breakdown, CostBreakdown)
        assert cost_breakdown.total > 0

    def test_calculate_route_cost_no_cargo(self, valid_route, cost_settings, transport_type):
        service = CostCalculationService()
        
        cost_breakdown = service.calculate_route_cost(
            route=valid_route,
            settings=cost_settings,
            transport_type=transport_type
        )
        
        assert isinstance(cost_breakdown, CostBreakdown)
        assert cost_breakdown.total > 0

    def test_calculate_route_cost_default_settings(self, valid_route):
        service = CostCalculationService()
        
        cost_breakdown = service.calculate_route_cost(route=valid_route)
        
        assert isinstance(cost_breakdown, CostBreakdown)
        assert cost_breakdown.total > 0


# OfferGenerationService Tests
class TestOfferGenerationService:
    """Test cases for OfferGenerationService."""

    def test_generate_offer_success(self, valid_route, cost_settings, transport_type, cargo, mock_ai_service):
        """Test successful offer generation."""
        cost_service = CostCalculationService()
        service = OfferGenerationService(cost_service=cost_service, ai_service=mock_ai_service)

        offer = service.generate_offer(
            route=valid_route,
            margin=0.1,
            settings=cost_settings,
            cargo=cargo,
            transport_type=transport_type
        )

        assert offer.route_id == valid_route.id
        assert offer.margin == Decimal("0.1")
        assert offer.final_price > 0
        assert offer.fun_fact == "Test fact"

    def test_generate_offer_invalid_margin(self, valid_route, mock_ai_service):
        """Test offer generation with invalid margin."""
        cost_service = CostCalculationService()
        service = OfferGenerationService(cost_service=cost_service, ai_service=mock_ai_service)

        with pytest.raises(ValueError):
            service.generate_offer(
                route=valid_route,
                margin=-0.1
            )

    def test_generate_offer_zero_margin(self, valid_route, cost_settings, mock_ai_service):
        """Test offer generation with zero margin."""
        cost_service = CostCalculationService()
        service = OfferGenerationService(cost_service=cost_service, ai_service=mock_ai_service)

        offer = service.generate_offer(
            route=valid_route,
            margin=0.0,
            settings=cost_settings
        )

        assert offer.margin == Decimal("0")
        assert offer.final_price > 0
