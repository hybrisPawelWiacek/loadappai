"""Tests for pricing-related value objects."""

from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID
import pytest
from pydantic import ValidationError

from src.domain.value_objects.pricing import (
    PricingStrategy,
    CompetitorPrice,
    PricePrediction,
    MarketConditions,
    PriceHistoryEntry,
    PriceHistory,
    PricingRules,
)


def test_pricing_strategy_enum():
    """Test PricingStrategy enum."""
    assert PricingStrategy.COST_PLUS == "cost_plus"
    assert PricingStrategy.MARKET_BASED == "market_based"
    assert PricingStrategy.DYNAMIC == "dynamic"
    assert PricingStrategy.FIXED == "fixed"

    # Test invalid value
    with pytest.raises(ValueError):
        PricingStrategy("invalid_strategy")


def test_competitor_price_creation():
    """Test creating CompetitorPrice."""
    now = datetime.now()
    price = CompetitorPrice(
        competitor_id="COMP1",
        price=Decimal("150.00"),
        currency="EUR",
        timestamp=now,
        route_id=UUID("12345678-1234-5678-1234-567812345678"),
        reliability_score=0.85,
    )
    assert price.competitor_id == "COMP1"
    assert price.price == Decimal("150.00")
    assert price.currency == "EUR"
    assert price.timestamp == now
    assert price.reliability_score == 0.85


def test_competitor_price_validation():
    """Test CompetitorPrice validation."""
    now = datetime.now()
    
    with pytest.raises(ValidationError):
        CompetitorPrice(
            competitor_id="COMP1",
            price=Decimal("150.00"),
            currency="EUR",
            timestamp=now,
            reliability_score=1.5,  # Should be between 0 and 1
            _validation_mode="all",
        )


def test_price_prediction_creation():
    """Test creating PricePrediction."""
    now = datetime.now()
    prediction = PricePrediction(
        predicted_price=Decimal("200.00"),
        confidence_level=0.85,
        prediction_date=now,
        valid_until=now + timedelta(days=1),
        features_used=["distance", "cargo_type"],
        prediction_interval={
            "lower": Decimal("180.00"),
            "upper": Decimal("220.00"),
        },
    )
    assert prediction.predicted_price == Decimal("200.00")
    assert prediction.confidence_level == 0.85
    assert prediction.prediction_date == now
    assert prediction.features_used == ["distance", "cargo_type"]
    assert prediction.prediction_interval["lower"] == Decimal("180.00")


def test_price_prediction_validation():
    """Test PricePrediction validation."""
    now = datetime.now()
    
    with pytest.raises(ValidationError):
        PricePrediction(
            predicted_price=Decimal("200.00"),
            confidence_level=2.0,  # Should be between 0 and 1
            prediction_date=now,
            _validation_mode="all",
        )


def test_market_conditions_creation():
    """Test creating MarketConditions."""
    conditions = MarketConditions(
        demand_level=1.2,
        competition_level=0.8,
        seasonality_factor=1.1,
        market_trend="growing",
        region_specific_factors={"region1": 1.1, "region2": 0.9},
    )
    assert conditions.demand_level == 1.2
    assert conditions.competition_level == 0.8
    assert conditions.seasonality_factor == 1.1
    assert conditions.market_trend == "growing"
    assert conditions.region_specific_factors["region1"] == 1.1


def test_market_conditions_validation():
    """Test MarketConditions validation."""
    with pytest.raises(ValidationError):
        MarketConditions(
            demand_level=2.5,  # Should be between 0 and 2
            _validation_mode="all",
        )


def test_price_history_entry_creation():
    """Test creating PriceHistoryEntry."""
    now = datetime.now()
    entry = PriceHistoryEntry(
        timestamp=now,
        price=Decimal("175.00"),
        currency="EUR",
        route_id=UUID("12345678-1234-5678-1234-567812345678"),
    )
    assert entry.timestamp == now
    assert entry.price == Decimal("175.00")
    assert entry.currency == "EUR"


def test_price_history_creation():
    """Test creating PriceHistory."""
    now = datetime.now()
    entry1 = PriceHistoryEntry(
        timestamp=now - timedelta(days=1),
        price=Decimal("150.00"),
    )
    entry2 = PriceHistoryEntry(
        timestamp=now,
        price=Decimal("175.00"),
    )
    
    history = PriceHistory(
        entries=[entry1, entry2],
        route_id=UUID("12345678-1234-5678-1234-567812345678"),
        start_date=now - timedelta(days=1),
        end_date=now,
    )
    assert len(history.entries) == 2
    assert history.entries[0].price == Decimal("150.00")
    assert history.entries[1].price == Decimal("175.00")


def test_pricing_rules_creation():
    """Test creating PricingRules."""
    rules = PricingRules(
        strategy=PricingStrategy.COST_PLUS,
        markup_percentage=Decimal("25"),
        minimum_margin=Decimal("15"),
        maximum_margin=Decimal("45"),
        rounding_precision=2,
        custom_rules={"special_customer": "apply_10_percent_discount"},
    )
    assert rules.strategy == PricingStrategy.COST_PLUS
    assert rules.markup_percentage == Decimal("25")
    assert rules.minimum_margin == Decimal("15")
    assert rules.maximum_margin == Decimal("45")
    assert rules.rounding_precision == 2


def test_pricing_rules_validation():
    """Test PricingRules validation."""
    with pytest.raises(ValidationError):
        PricingRules(
            strategy=PricingStrategy.COST_PLUS,
            markup_percentage=Decimal("-10"),  # Should be non-negative
            _validation_mode="all",
        )

    with pytest.raises(ValidationError):
        PricingRules(
            strategy=PricingStrategy.COST_PLUS,
            minimum_margin=Decimal("60"),  # Should be less than maximum_margin
            maximum_margin=Decimal("50"),
            _validation_mode="all",
        )
