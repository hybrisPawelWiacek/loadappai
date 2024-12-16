"""Tests for domain value objects."""
from decimal import Decimal

import pytest
from pydantic import ValidationError

from src.domain.value_objects import (
    CostBreakdown,
    Currency,
    EmptyDriving,
    Location,
    RouteMetadata,
)


def test_location_creation():
    """Test creating a valid Location."""
    location = Location(
        address="123 Main St, City",
        latitude=40.7128,
        longitude=-74.0060,
    )
    assert location.address == "123 Main St, City"
    assert location.latitude == 40.7128
    assert location.longitude == -74.0060


def test_location_validation():
    """Test Location validation."""
    with pytest.raises(ValidationError):
        Location(
            address="123 Main St",
            latitude=100,  # Invalid latitude
            longitude=-74.0060,
        )

    with pytest.raises(ValidationError):
        Location(
            address="123 Main St",
            latitude=40.7128,
            longitude=200,  # Invalid longitude
        )


def test_route_metadata_creation():
    """Test creating RouteMetadata."""
    metadata = RouteMetadata(
        weather_data={"temperature": 20, "conditions": "clear"},
        traffic_data={"congestion_level": "low"},
    )
    assert metadata.weather_data["temperature"] == 20
    assert metadata.traffic_data["congestion_level"] == "low"
    assert metadata.compliance_data is None


def test_cost_breakdown_creation():
    """Test creating CostBreakdown."""
    breakdown = CostBreakdown(
        fuel_cost=Decimal("100.50"),
        toll_cost=Decimal("50.25"),
        driver_cost=Decimal("200.00"),
        overheads=Decimal("75.00"),
        cargo_specific_costs={"cleaning": Decimal("25.00"), "insurance": Decimal("30.00")},
        total=Decimal("480.75"),
    )
    assert breakdown.fuel_cost == Decimal("100.50")
    assert breakdown.total == Decimal("480.75")


def test_cost_breakdown_addition():
    """Test adding two CostBreakdowns."""
    breakdown1 = CostBreakdown(
        fuel_cost=Decimal("100.00"),
        toll_cost=Decimal("50.00"),
        driver_cost=Decimal("200.00"),
        overheads=Decimal("75.00"),
        cargo_specific_costs={"cleaning": Decimal("25.00")},
        total=Decimal("450.00"),
    )

    breakdown2 = CostBreakdown(
        fuel_cost=Decimal("150.00"),
        toll_cost=Decimal("60.00"),
        driver_cost=Decimal("220.00"),
        overheads=Decimal("80.00"),
        cargo_specific_costs={"insurance": Decimal("30.00")},
        total=Decimal("540.00"),
    )

    combined = breakdown1 + breakdown2
    assert combined.fuel_cost == Decimal("250.00")
    assert combined.cargo_specific_costs["cleaning"] == Decimal("25.00")
    assert combined.cargo_specific_costs["insurance"] == Decimal("30.00")
    assert combined.total == Decimal("990.00")


def test_empty_driving_creation():
    """Test creating EmptyDriving."""
    empty_driving = EmptyDriving(
        distance_km=200.0,
        duration_hours=4.0,
    )
    assert empty_driving.distance_km == 200.0
    assert empty_driving.duration_hours == 4.0


def test_empty_driving_validation():
    """Test EmptyDriving validation."""
    with pytest.raises(ValidationError):
        EmptyDriving(
            distance_km=-100.0,  # Invalid negative distance
            duration_hours=4.0,
        )

    with pytest.raises(ValidationError):
        EmptyDriving(
            distance_km=200.0,
            duration_hours=0.0,  # Invalid zero duration
        )


def test_currency_creation():
    """Test creating Currency."""
    currency = Currency(
        code="EUR",
        symbol="€",
        exchange_rate=Decimal("1.0"),
    )
    assert currency.code == "EUR"
    assert currency.symbol == "€"
    assert currency.exchange_rate == Decimal("1.0")


def test_currency_validation():
    """Test Currency validation."""
    with pytest.raises(ValidationError):
        Currency(
            code="EURO",  # Invalid code length
            symbol="€",
            exchange_rate=Decimal("1.0"),
        )
