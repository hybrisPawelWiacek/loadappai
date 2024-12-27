"""Tests for offer-related domain entities."""

from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from pytz import UTC

from src.domain.entities.offer import (
    OfferStatus,
    Offer,
    OfferHistory
)


def test_offer_status_enum():
    """Test OfferStatus enum values."""
    assert OfferStatus.DRAFT.value == "draft"
    assert OfferStatus.PENDING.value == "pending"
    assert OfferStatus.ACTIVE.value == "active"
    assert OfferStatus.EXPIRED.value == "expired"
    assert OfferStatus.CANCELLED.value == "cancelled"
    assert OfferStatus.ACCEPTED.value == "accepted"
    assert OfferStatus.REJECTED.value == "rejected"


def test_offer_creation():
    """Test Offer entity creation with valid data."""
    offer_id = uuid4()
    route_id = uuid4()
    cost_id = uuid4()
    
    offer = Offer(
        id=offer_id,
        route_id=route_id,
        cost_id=cost_id,
        total_cost=Decimal("1000.00"),
        margin=Decimal("0.20"),
        final_price=Decimal("1200.00"),
        fun_fact="This route crosses 3 countries!",
        status=OfferStatus.DRAFT
    )
    
    assert offer.id == offer_id
    assert offer.route_id == route_id
    assert offer.cost_id == cost_id
    assert offer.total_cost == Decimal("1000.00")
    assert offer.margin == Decimal("0.20")
    assert offer.final_price == Decimal("1200.00")
    assert offer.fun_fact == "This route crosses 3 countries!"
    assert offer.status == OfferStatus.DRAFT
    assert offer.is_active is True
    assert isinstance(offer.created_at, datetime)
    assert isinstance(offer.modified_at, datetime)
    assert offer.created_at.tzinfo == UTC
    assert offer.modified_at.tzinfo == UTC


def test_offer_decimal_validation():
    """Test validation of decimal fields."""
    with pytest.raises(ValueError, match="Input should be greater than 0"):
        Offer(
            route_id=uuid4(),
            cost_id=uuid4(),
            total_cost=Decimal("0"),
            margin=Decimal("20"),
            final_price=Decimal("1200")
        )

    with pytest.raises(ValueError, match="Input should be greater than or equal to 0"):
        Offer(
            route_id=uuid4(),
            cost_id=uuid4(),
            total_cost=Decimal("1000"),
            margin=Decimal("-1"),
            final_price=Decimal("1200")
        )

    with pytest.raises(ValueError, match="Input should be greater than 0"):
        Offer(
            route_id=uuid4(),
            cost_id=uuid4(),
            total_cost=Decimal("1000"),
            margin=Decimal("20"),
            final_price=Decimal("0")
        )


def test_offer_price_validation():
    """Test validation of price in relation to total cost."""
    with pytest.raises(ValueError, match="Final price must be greater than total cost"):
        Offer(
            route_id=uuid4(),
            cost_id=uuid4(),
            total_cost=Decimal("1000"),
            margin=Decimal("20"),
            final_price=Decimal("900")
        )


def test_offer_margin_calculation():
    """Test margin calculation validation."""
    # Valid margin calculation
    offer = Offer(
        route_id=uuid4(),
        cost_id=uuid4(),
        total_cost=Decimal("1000"),
        final_price=Decimal("1200"),  # First set final_price
        margin=Decimal("0.20")  # Then set margin
    )
    assert offer.margin == Decimal("0.20")

    # Invalid margin
    with pytest.raises(ValueError, match=r".*Margin does not match the calculation from total cost and final price \(expected 0\.2000, got 0\.25\).*"):
        Offer(
            route_id=uuid4(),
            cost_id=uuid4(),
            total_cost=Decimal("1000"),
            final_price=Decimal("1200"),  # First set final_price
            margin=Decimal("0.25")  # Then set margin with wrong value
        )


def test_offer_status_transitions():
    """Test offer status transitions."""
    offer = Offer(
        route_id=uuid4(),
        cost_id=uuid4(),
        total_cost=Decimal("1000"),
        margin=Decimal("0.20"),
        final_price=Decimal("1200")
    )
    
    assert offer.status == OfferStatus.DRAFT
    assert offer.is_active is True

    # Test activation
    original_modified = offer.modified_at
    offer.activate()
    assert offer.status == OfferStatus.ACTIVE
    assert offer.is_active is True
    assert offer.modified_at > original_modified

    # Test cancellation
    original_modified = offer.modified_at
    offer.cancel()
    assert offer.status == OfferStatus.CANCELLED
    assert offer.is_active is False
    assert offer.modified_at > original_modified

    # Test cannot activate cancelled offer
    with pytest.raises(ValueError, match="Cannot activate cancelled offer"):
        offer.activate()


def test_offer_history():
    """Test OfferHistory entity."""
    history_id = uuid4()
    offer_id = uuid4()
    
    # Valid history entry
    history = OfferHistory(
        id=history_id,
        offer_id=offer_id,
        version="1.0",
        status=OfferStatus.DRAFT,
        margin=Decimal("0.20"),
        final_price=Decimal("1200.00"),
        fun_fact="This route crosses 3 countries!",
        metadata={"reason": "Initial offer"},
        change_reason="Created offer"
    )
    assert history.id == history_id
    assert history.offer_id == offer_id
    assert history.version == "1.0"
    assert history.status == OfferStatus.DRAFT
    assert history.margin == Decimal("0.20")
    assert history.final_price == Decimal("1200.00")
    assert history.fun_fact == "This route crosses 3 countries!"
    assert history.metadata == {"reason": "Initial offer"}
    assert history.changed_at is not None
    assert history.changed_by is None
    assert history.change_reason == "Created offer"


def test_offer_history_validation():
    """Test OfferHistory validation."""
    # Test invalid version format
    with pytest.raises(ValueError, match="Version must be in format X.Y"):
        OfferHistory(
            offer_id=uuid4(),
            version="invalid",
            status=OfferStatus.DRAFT,
            margin=Decimal("0.20"),
            final_price=Decimal("1200")
        )

    # Test negative margin
    with pytest.raises(ValueError, match="Input should be greater than or equal to 0"):
        OfferHistory(
            offer_id=uuid4(),
            version="1.0",
            status=OfferStatus.DRAFT,
            margin=Decimal("-1"),
            final_price=Decimal("1200")
        )

    # Test zero final price
    with pytest.raises(ValueError, match="Input should be greater than 0"):
        OfferHistory(
            offer_id=uuid4(),
            version="1.0",
            status=OfferStatus.DRAFT,
            margin=Decimal("0.20"),
            final_price=Decimal("0")
        )
