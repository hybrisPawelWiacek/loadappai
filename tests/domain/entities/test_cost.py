"""Tests for cost-related domain entities."""

from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from pytz import UTC

from src.domain.entities.cost import (
    CostComponent,
    CostBreakdown,
    Cost,
    CostSettings,
    CostHistoryEntry,
    CostSettingsVersion
)


@pytest.fixture
def valid_cost_component():
    """Return a valid cost component."""
    return CostComponent(
        type="fuel",
        amount=Decimal("100.50"),
        currency="EUR",
        country="DE"
    )


@pytest.fixture
def valid_cost_breakdown():
    """Return a valid cost breakdown."""
    route_id = uuid4()
    return CostBreakdown(
        route_id=route_id,
        fuel_costs={"DE": Decimal("100.50")},
        toll_costs={"DE": Decimal("50.25")},
        maintenance_costs={"truck": Decimal("25.00")},
        driver_costs={"DE": Decimal("75.00")},
        rest_period_costs=Decimal("20.00"),
        loading_unloading_costs=Decimal("30.00"),
        empty_driving_costs={"DE": {"fuel": Decimal("40.00")}},
        cargo_specific_costs={"refrigeration": Decimal("15.00")},
        overheads={"admin": Decimal("10.00")},
        total_cost=Decimal("365.75")
    )


def test_cost_component_validation(valid_cost_component):
    """Test CostComponent validation rules."""
    # Valid component
    component = valid_cost_component
    assert component.type == "fuel"
    assert component.amount == Decimal("100.50")
    assert component.currency == "EUR"
    
    # Invalid type
    with pytest.raises(ValueError, match="Invalid cost component type: invalid"):
        CostComponent(
            type="invalid",
            amount=Decimal("100.50"),
            currency="EUR"
        )
    
    # Invalid amount
    with pytest.raises(ValueError, match="Input should be greater than 0"):
        CostComponent(
            type="fuel",
            amount=Decimal("-100.50"),
            currency="EUR"
        )
    
    # Test details field
    component = CostComponent(
        type="fuel",
        amount=Decimal("100.50"),
        currency="EUR",
        details={"rate": Decimal("2.50"), "distance": 40}
    )
    assert component.details["rate"] == Decimal("2.50")
    assert component.details["distance"] == 40


def test_cost_breakdown(valid_cost_breakdown):
    """Test CostBreakdown entity."""
    breakdown = valid_cost_breakdown
    
    # Test all cost components
    assert breakdown.fuel_costs["DE"] == Decimal("100.50")
    assert breakdown.toll_costs["DE"] == Decimal("50.25")
    assert breakdown.maintenance_costs["truck"] == Decimal("25.00")
    assert breakdown.driver_costs["DE"] == Decimal("75.00")
    assert breakdown.rest_period_costs == Decimal("20.00")
    assert breakdown.loading_unloading_costs == Decimal("30.00")
    assert breakdown.empty_driving_costs["DE"]["fuel"] == Decimal("40.00")
    assert breakdown.cargo_specific_costs["refrigeration"] == Decimal("15.00")
    assert breakdown.overheads["admin"] == Decimal("10.00")
    assert breakdown.total_cost == Decimal("365.75")

    # Test default values
    empty_breakdown = CostBreakdown(route_id=uuid4())
    assert empty_breakdown.fuel_costs == {}
    assert empty_breakdown.toll_costs == {}
    assert empty_breakdown.total_cost == Decimal("0")

    # Test subtotal calculations
    breakdown = CostBreakdown(
        route_id=uuid4(),
        fuel_costs={"DE": Decimal("100.00")},
        toll_costs={"DE": Decimal("50.00")},
        maintenance_costs={"truck": Decimal("30.00")},
        driver_costs={"DE": Decimal("80.00")},
        rest_period_costs=Decimal("20.00"),
        loading_unloading_costs=Decimal("25.00"),
        empty_driving_costs={"DE": {"fuel": Decimal("40.00"), "toll": Decimal("20.00")}},
        subtotal_distance_based=Decimal("180.00"),  # fuel + toll + maintenance
        subtotal_time_based=Decimal("125.00"),      # driver + rest + loading/unloading
        subtotal_empty_driving=Decimal("60.00"),    # empty driving total
        total_cost=Decimal("365.00")                # all subtotals combined
    )
    assert breakdown.subtotal_distance_based == Decimal("180.00")
    assert breakdown.subtotal_time_based == Decimal("125.00")
    assert breakdown.subtotal_empty_driving == Decimal("60.00")
    assert breakdown.total_cost == Decimal("365.00")


def test_cost(valid_cost_breakdown):
    """Test Cost entity."""
    route_id = uuid4()
    breakdown = valid_cost_breakdown
    
    cost = Cost(
        route_id=route_id,
        breakdown=breakdown,
        calculation_method="standard",
        validity_period=timedelta(hours=24)
    )
    
    # Test total cost methods
    assert cost.total() == Decimal("365.75")
    assert cost.total_cost == Decimal("365.75")
    assert cost.is_valid() is True
    
    # Test validity period
    cost.calculated_at = datetime.now(UTC) - timedelta(hours=25)
    assert cost.is_valid() is False
    assert cost.recalculate_needed() is True
    
    # Test metadata
    cost_with_meta = Cost(
        route_id=route_id,
        breakdown=breakdown,
        calculation_method="standard",
        metadata={"source": "test", "version": "1.0"}
    )
    assert cost_with_meta.metadata["source"] == "test"
    
    # Test invalid calculation method
    with pytest.raises(ValueError, match="Invalid calculation method: invalid"):
        Cost(
            route_id=route_id,
            breakdown=breakdown,
            calculation_method="invalid",
            validity_period=timedelta(hours=24)
        )

    # Test version checks
    cost_old_version = Cost(
        route_id=route_id,
        breakdown=breakdown,
        calculation_method="standard",
        version="1.0"
    )
    assert cost_old_version.recalculate_needed() is True

    cost_current_version = Cost(
        route_id=route_id,
        breakdown=breakdown,
        calculation_method="standard",
        version="2.0"
    )
    assert cost_current_version.recalculate_needed() is False

    # Test metadata handling
    cost_with_meta = Cost(
        route_id=route_id,
        breakdown=breakdown,
        calculation_method="standard",
        metadata={
            "source": "manual",
            "user": "test_user",
            "reason": "price_update",
            "previous_total": "350.00"
        }
    )
    assert cost_with_meta.metadata["source"] == "manual"
    assert cost_with_meta.metadata["user"] == "test_user"
    assert cost_with_meta.metadata["reason"] == "price_update"
    assert cost_with_meta.metadata["previous_total"] == "350.00"


def test_cost_settings():
    """Test CostSettings entity."""
    route_id = uuid4()
    
    # Test valid settings
    settings = CostSettings(
        route_id=route_id,
        fuel_rates={"DE": Decimal("1.50")},
        toll_rates={"DE": {"truck": Decimal("0.20")}},
        driver_rates={"DE": Decimal("30.00")},
        overhead_rates={"admin": Decimal("100.00")},
        maintenance_rates={"truck": Decimal("0.15")},
        enabled_components={"fuel", "toll", "driver"},
        version=CostSettingsVersion.V2_0
    )
    assert settings.route_id == route_id
    assert settings.fuel_rates["DE"] == Decimal("1.50")
    
    # Test invalid components
    with pytest.raises(ValueError, match="Invalid cost components"):
        CostSettings(
            route_id=route_id,
            enabled_components={"invalid"}
        )
    
    # Test default settings
    default = CostSettings.get_default(route_id)
    assert default.route_id == route_id
    assert default.version == CostSettingsVersion.V1_0
    assert "fuel" in default.enabled_components
    
    # Test timestamps
    assert default.created_at is not None
    assert default.modified_at is not None
    assert default.created_at <= default.modified_at

    # Test rate validations
    with pytest.raises(ValueError, match="Input should be greater than 0"):
        CostSettings(
            route_id=route_id,
            fuel_rates={"DE": Decimal("-1.50")}
        )

    with pytest.raises(ValueError, match="Input should be greater than 0"):
        CostSettings(
            route_id=route_id,
            driver_rates={"DE": Decimal("-30.00")}
        )

    with pytest.raises(ValueError, match="Input should be greater than 0"):
        CostSettings(
            route_id=route_id,
            maintenance_rates={"truck": Decimal("-0.15")}
        )

    # Test default values
    settings = CostSettings(route_id=route_id)
    assert settings.fuel_rates == {}
    assert settings.toll_rates == {}
    assert settings.driver_rates == {}
    assert settings.maintenance_rates == {}
    assert settings.overhead_rates == {}
    assert settings.enabled_components == {"fuel", "toll", "driver"}
    assert settings.version == CostSettingsVersion.V1_0


def test_cost_history_entry():
    """Test CostHistoryEntry entity."""
    route_id = uuid4()
    
    # Test valid entry
    entry = CostHistoryEntry(
        route_id=route_id,
        total_cost=Decimal("365.75"),
        calculation_method="standard",
        version="2.0",
        cost_components={"fuel": Decimal("100.50"), "toll": Decimal("50.25")},
        settings_snapshot={"fuel_rates": {"DE": Decimal("1.50")}}
    )
    assert entry.route_id == route_id
    assert entry.total_cost == Decimal("365.75")
    assert entry.cost_components["fuel"] == Decimal("100.50")
    
    # Test invalid cost components
    with pytest.raises(ValueError, match="Input should be greater than 0"):
        CostHistoryEntry(
            route_id=route_id,
            total_cost=Decimal("100.50"),
            calculation_method="standard",
            version="2.0",
            cost_components={"fuel": Decimal("-100.50")},
            settings_snapshot={}
        )
    
    # Test invalid calculation method
    with pytest.raises(ValueError, match="Invalid calculation method: invalid"):
        CostHistoryEntry(
            route_id=route_id,
            total_cost=Decimal("100.50"),
            calculation_method="invalid",
            version="2.0",
            cost_components={"fuel": Decimal("100.50")},
            settings_snapshot={}
        )

    # Test settings snapshot validation
    valid_snapshot = {
        "fuel_rates": {"DE": Decimal("1.50")},
        "toll_rates": {"DE": {"truck": Decimal("0.20")}},
        "driver_rates": {"DE": Decimal("30.00")},
        "maintenance_rates": {"truck": Decimal("0.15")},
        "enabled_components": ["fuel", "toll", "driver"],
        "version": "2.0"
    }
    entry = CostHistoryEntry(
        route_id=route_id,
        total_cost=Decimal("100.50"),
        calculation_method="standard",
        version="2.0",
        cost_components={"fuel": Decimal("100.50")},
        settings_snapshot=valid_snapshot
    )
    assert entry.settings_snapshot == valid_snapshot

    # Test invalid settings snapshot
    invalid_snapshot = {
        "fuel_rates": {"DE": Decimal("-1.50")},  # Invalid negative rate
        "version": "2.0"
    }
    with pytest.raises(ValueError, match="Input should be greater than 0"):
        CostHistoryEntry(
            route_id=route_id,
            total_cost=Decimal("100.50"),
            calculation_method="standard",
            version="2.0",
            cost_components={"fuel": Decimal("100.50")},
            settings_snapshot=invalid_snapshot
        )
