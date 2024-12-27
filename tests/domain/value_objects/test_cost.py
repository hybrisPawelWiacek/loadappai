"""Tests for cost-related value objects."""

from decimal import Decimal
from uuid import UUID

import pytest
from pydantic import ValidationError

from src.domain.value_objects.cost import Cost, CostBreakdown, Currency, CountrySettings


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
            _validation_mode="all",
        )


def test_cost_creation():
    """Test creating Cost."""
    cost = Cost(
        amount=Decimal("100.50"),
        currency="EUR",
        description="Test cost",
        category="fuel",
    )
    assert cost.amount == Decimal("100.50")
    assert cost.currency == "EUR"
    assert cost.description == "Test cost"
    assert cost.category == "fuel"


def test_cost_validation():
    """Test Cost validation."""
    with pytest.raises(ValidationError):
        Cost(
            amount=Decimal("-100.50"),  # Negative amount
            currency="EUR",
            _validation_mode="all",
        )

    with pytest.raises(ValidationError):
        Cost(
            amount=Decimal("100.50"),
            currency="EURO",  # Invalid currency code
            _validation_mode="all",
        )


def test_cost_breakdown_creation():
    """Test creating CostBreakdown."""
    breakdown = CostBreakdown(
        route_id=UUID("12345678-1234-5678-1234-567812345678"),
        fuel_costs={"country1": Decimal("100.50")},
        toll_costs={"highway1": Decimal("50.25")},
        driver_costs={"regular": Decimal("200.00")},
        rest_period_costs=Decimal("75.00"),
        total_cost=Decimal("425.75"),
    )
    assert breakdown.fuel_cost == Decimal("100.50")
    assert breakdown.toll_cost == Decimal("50.25")
    assert breakdown.driver_cost == Decimal("200.00")
    assert breakdown.total == Decimal("425.75")


def test_cost_breakdown_defaults():
    """Test CostBreakdown default values."""
    breakdown = CostBreakdown(
        route_id=UUID("12345678-1234-5678-1234-567812345678"),
    )
    assert breakdown.fuel_costs == {}
    assert breakdown.toll_costs == {}
    assert breakdown.driver_costs == {}
    assert breakdown.rest_period_costs == Decimal("0")
    assert breakdown.total_cost == Decimal("0")


def test_cost_breakdown_computed_fields():
    """Test CostBreakdown computed fields."""
    breakdown = CostBreakdown(
        route_id=UUID("12345678-1234-5678-1234-567812345678"),
        fuel_costs={
            "country1": Decimal("100.00"),
            "country2": Decimal("150.00"),
        },
        toll_costs={
            "highway1": Decimal("50.00"),
            "highway2": Decimal("75.00"),
        },
        driver_costs={
            "regular": Decimal("200.00"),
            "overtime": Decimal("100.00"),
        },
    )
    assert breakdown.fuel_cost == Decimal("250.00")
    assert breakdown.toll_cost == Decimal("125.00")
    assert breakdown.driver_cost == Decimal("300.00")


def test_country_settings_creation():
    """Test creating CountrySettings with default values."""
    settings = CountrySettings(
        country_code="DE",
    )
    assert settings.country_code == "DE"
    assert settings.currency == "EUR"
    assert settings.fuel_cost_per_km == Decimal("0")
    assert settings.toll_cost_per_km == Decimal("0")
    assert settings.driver_cost_per_hour == Decimal("0")
    assert settings.rest_period_cost == Decimal("0")
    assert settings.loading_unloading_cost == Decimal("0")
    assert settings.empty_driving_multiplier == Decimal("1")
    assert settings.maintenance_cost_per_km == Decimal("0")
    assert settings.overhead_percentage == Decimal("0")


def test_country_settings_custom_values():
    """Test creating CountrySettings with custom values."""
    settings = CountrySettings(
        country_code="PL",
        currency="PLN",
        fuel_cost_per_km=Decimal("2.5"),
        toll_cost_per_km=Decimal("0.8"),
        driver_cost_per_hour=Decimal("45.0"),
        rest_period_cost=Decimal("100.0"),
        loading_unloading_cost=Decimal("150.0"),
        empty_driving_multiplier=Decimal("1.2"),
        maintenance_cost_per_km=Decimal("0.3"),
        overhead_percentage=Decimal("15.0")
    )
    assert settings.country_code == "PL"
    assert settings.currency == "PLN"
    assert settings.fuel_cost_per_km == Decimal("2.5")
    assert settings.toll_cost_per_km == Decimal("0.8")
    assert settings.driver_cost_per_hour == Decimal("45.0")
    assert settings.rest_period_cost == Decimal("100.0")
    assert settings.loading_unloading_cost == Decimal("150.0")
    assert settings.empty_driving_multiplier == Decimal("1.2")
    assert settings.maintenance_cost_per_km == Decimal("0.3")
    assert settings.overhead_percentage == Decimal("15.0")


def test_country_settings_validation():
    """Test CountrySettings validation."""
    with pytest.raises(ValidationError):
        CountrySettings(
            country_code="DEU",  # Invalid country code length
            _validation_mode="all",
        )

    with pytest.raises(ValidationError):
        CountrySettings(
            country_code="DE",
            empty_driving_multiplier=Decimal("-0.5"),  # Negative multiplier
            _validation_mode="all",
        )


def test_cost_breakdown_additional_fields():
    """Test CostBreakdown additional fields."""
    breakdown = CostBreakdown(
        route_id=UUID("12345678-1234-5678-1234-567812345678"),
        maintenance_costs={"country1": Decimal("75.50")},
        loading_unloading_costs=Decimal("120.00"),
        empty_driving_costs={
            "country1": {
                "fuel": Decimal("30.00"),
                "toll": Decimal("15.00")
            }
        },
        cargo_specific_costs={"refrigeration": Decimal("85.00")},
        equipment_costs=Decimal("200.00"),
        overheads={"admin": Decimal("50.00"), "insurance": Decimal("100.00")},
        subtotal_distance_based=Decimal("300.00"),
        subtotal_time_based=Decimal("150.00"),
        subtotal_empty_driving=Decimal("45.00"),
    )
    
    assert sum(breakdown.maintenance_costs.values()) == Decimal("75.50")
    assert breakdown.loading_unloading_costs == Decimal("120.00")
    assert breakdown.empty_driving_costs["country1"]["fuel"] == Decimal("30.00")
    assert breakdown.cargo_specific_costs["refrigeration"] == Decimal("85.00")
    assert breakdown.equipment_costs == Decimal("200.00")
    assert sum(breakdown.overheads.values()) == Decimal("150.00")
    assert breakdown.subtotal_distance_based == Decimal("300.00")
    assert breakdown.subtotal_time_based == Decimal("150.00")
    assert breakdown.subtotal_empty_driving == Decimal("45.00")


def test_cost_breakdown_total_calculation():
    """Test CostBreakdown total cost calculation."""
    breakdown = CostBreakdown(
        route_id=UUID("12345678-1234-5678-1234-567812345678"),
        fuel_costs={"country1": Decimal("100.00")},
        toll_costs={"highway1": Decimal("50.00")},
        maintenance_costs={"country1": Decimal("30.00")},
        driver_costs={"regular": Decimal("200.00")},
        rest_period_costs=Decimal("75.00"),
        loading_unloading_costs=Decimal("120.00"),
        empty_driving_costs={
            "country1": {
                "fuel": Decimal("30.00"),
                "toll": Decimal("15.00")
            }
        },
        cargo_specific_costs={"refrigeration": Decimal("85.00")},
        equipment_costs=Decimal("200.00"),
        overheads={"admin": Decimal("50.00")},
        total_cost=Decimal("955.00")
    )
    
    assert breakdown.total == Decimal("955.00")
    assert breakdown.total_cost == breakdown.total  # Test alias property
