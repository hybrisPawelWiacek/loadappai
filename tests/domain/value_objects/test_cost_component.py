"""Tests for cost component value object."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from src.domain.value_objects.cost_component import CostComponent


def test_cost_component_creation():
    """Test creating a valid CostComponent."""
    cost = CostComponent(
        amount=Decimal("100.50"),
        currency="EUR",
        description="Test cost",
        category="fuel",
    )
    assert cost.amount == Decimal("100.50")
    assert cost.currency == "EUR"
    assert cost.description == "Test cost"
    assert cost.category == "fuel"


def test_cost_component_validation():
    """Test CostComponent validation."""
    with pytest.raises(ValidationError):
        CostComponent(
            amount=Decimal("-100.50"),  # Negative amount
            currency="EUR",
            _validation_mode="all",
        )

    with pytest.raises(ValidationError):
        CostComponent(
            amount=Decimal("100.50"),
            currency="EURO",  # Invalid currency code
            _validation_mode="all",
        )


def test_cost_component_immutability():
    """Test that CostComponent is immutable."""
    cost = CostComponent(
        amount=Decimal("100.50"),
        currency="EUR",
    )
    
    with pytest.raises(ValidationError, match=r".*frozen_instance.*"):
        cost.amount = Decimal("200.00")  # type: ignore

    with pytest.raises(ValidationError, match=r".*frozen_instance.*"):
        cost.currency = "USD"  # type: ignore


def test_cost_component_metadata():
    """Test CostComponent metadata handling."""
    metadata = {
        "source": "fuel_calculator",
        "calculation_method": "distance_based",
        "rates": {"base_rate": "2.50", "surcharge": "0.50"},
    }
    
    cost = CostComponent(
        amount=Decimal("100.50"),
        currency="EUR",
        metadata=metadata,
    )
    assert cost.metadata == metadata
    assert cost.metadata["source"] == "fuel_calculator"
    assert cost.metadata["rates"]["base_rate"] == "2.50"
