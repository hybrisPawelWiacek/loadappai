"""Pricing-related value objects."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from decimal import Decimal
from uuid import UUID
from pydantic import Field, field_validator

from .common import BaseValueObject


class PricingStrategy(str, Enum):
    """Pricing strategy enum."""

    COST_PLUS = "cost_plus"
    MARKET_BASED = "market_based"
    DYNAMIC = "dynamic"
    FIXED = "fixed"


class CompetitorPrice(BaseValueObject):
    """Competitor price information."""

    competitor_id: str
    price: Decimal
    currency: str = Field(default="EUR")
    timestamp: datetime
    route_id: Optional[UUID] = None
    offer_id: Optional[UUID] = None
    source: Optional[str] = None
    reliability_score: float = Field(default=1.0, ge=0.0, le=1.0)
    notes: Optional[str] = None


class PricePrediction(BaseValueObject):
    """Price prediction for a route or offer."""

    predicted_price: Decimal
    confidence_level: float = Field(default=0.0, ge=0.0, le=1.0)
    prediction_date: datetime
    valid_until: Optional[datetime] = None
    currency: str = Field(default="EUR")
    route_id: Optional[UUID] = None
    offer_id: Optional[UUID] = None
    model_version: str = Field(default="1.0")
    features_used: List[str] = Field(default_factory=list)
    prediction_interval: Optional[Dict[str, Decimal]] = None
    notes: Optional[str] = None


class MarketConditions(BaseValueObject):
    """Market conditions affecting pricing."""

    demand_level: float = Field(default=1.0, ge=0.0, le=2.0)
    competition_level: float = Field(default=1.0, ge=0.0, le=2.0)
    seasonality_factor: float = Field(default=1.0, ge=0.0, le=2.0)
    market_trend: str = Field(default="stable")
    region_specific_factors: Dict[str, float] = Field(default_factory=dict)
    competitor_prices: List[CompetitorPrice] = Field(default_factory=list)
    price_prediction: Optional[PricePrediction] = None
    notes: Optional[str] = None


class PriceHistoryEntry(BaseValueObject):
    """Individual price history entry."""

    timestamp: datetime
    price: Decimal
    currency: str = Field(default="EUR")
    route_id: Optional[UUID] = None
    offer_id: Optional[UUID] = None
    market_conditions: Optional[MarketConditions] = None
    notes: Optional[str] = None


class PriceHistory(BaseValueObject):
    """Price history for a route or offer."""

    entries: List[PriceHistoryEntry] = Field(default_factory=list)
    route_id: Optional[UUID] = None
    offer_id: Optional[UUID] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    currency: str = Field(default="EUR")
    notes: Optional[str] = None


class PricingRules(BaseValueObject):
    """Pricing rules for an offer."""

    strategy: PricingStrategy = Field(default=PricingStrategy.COST_PLUS)
    markup_percentage: Decimal = Field(default=Decimal("20"), ge=0)
    minimum_margin: Decimal = Field(default=Decimal("10"), ge=0)
    maximum_margin: Decimal = Field(default=Decimal("50"), ge=0)
    rounding_precision: int = Field(default=2, ge=0)
    currency: str = Field(default="EUR")
    custom_rules: Dict[str, str] = Field(default_factory=dict)
    notes: Optional[str] = None

    @field_validator("currency")
    def validate_currency(cls, v: str) -> str:
        """Validate currency code."""
        if len(v) != 3:
            raise ValueError("Currency code must be 3 characters")
        return v.upper()
    
    @field_validator("maximum_margin")
    def validate_margins(cls, v: Decimal, values: Dict) -> Decimal:
        """Validate maximum margin is greater than minimum margin."""
        if "minimum_margin" in values.data and v < values.data["minimum_margin"]:
            raise ValueError("Maximum margin must be greater than minimum margin")
        return v
