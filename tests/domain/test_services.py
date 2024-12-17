"""Unit tests for domain services."""
import pytest
from datetime import datetime, timedelta
from pytz import UTC
from decimal import Decimal
from typing import Dict, Optional, List
from uuid import uuid4

from src.domain.services import (
    RoutePlanningService,
    CostCalculationService,
    OfferGenerationService
)
from src.domain.entities import (
    Route,
    CostSettings,
    TransportType,
    Cargo,
    CountrySegment
)
from src.domain.value_objects import (
    Location,
    CostBreakdown,
    EmptyDriving,
    RouteMetadata
)

# Test Data
@pytest.fixture
def valid_location():
    return Location(
        latitude=52.2297,
        longitude=21.0122,
        address="Test Address",
        country_code="PL"
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
            country_code="PL"
        ),
        pickup_time=datetime.now(UTC) + timedelta(days=1),
        delivery_time=datetime.now(UTC) + timedelta(days=2),
        transport_type="standard",
        cargo_id=str(uuid4()),
        distance_km=500.0,
        duration_hours=8.0,
        empty_driving=EmptyDriving(distance_km=50.0, duration_hours=1.0),
        metadata=RouteMetadata(
            weather_data=None,
            traffic_data=None,
            compliance_data=None,
            optimization_data={"distance_km": 500.0, "duration_hours": 8.0}
        ),
        country_segments=[
            CountrySegment(
                country_code="PL",
                distance=500.0,
                toll_rates={"standard": Decimal("0.15")}
            )
        ]
    )

@pytest.fixture
def cost_settings():
    return CostSettings(
        fuel_price_per_liter=Decimal("6.50"),
        driver_daily_salary=Decimal("200.0"),
        toll_rates={"PL": Decimal("0.15")},
        overheads={
            "admin": Decimal("50.0"),
            "insurance": Decimal("100.0")
        },
        cargo_factors={
            "refrigerated": Decimal("1.2"),
            "hazmat": Decimal("1.5")
        }
    )

@pytest.fixture
def transport_type():
    return TransportType(
        id=str(uuid4()),
        name="standard",
        capacity=5000.0,
        fuel_consumption_empty=Decimal("25.0"),
        fuel_consumption_loaded=Decimal("30.0"),
        emissions_class="euro6",
        cargo_restrictions=["standard"]
    )

@pytest.fixture
def cargo():
    return Cargo(
        id=str(uuid4()),
        type="standard",
        weight=1000.0,
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
            return [CountrySegment(country_code="PL", distance=500.0, toll_rates={"standard": Decimal("0.15")})]

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
            country_code="PL"
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
