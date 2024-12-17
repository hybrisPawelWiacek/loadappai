"""Tests for the offer repository."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from src.domain.entities import Offer as OfferEntity
from src.infrastructure.models import Offer as OfferModel
from src.infrastructure.repositories.offer_repository import OfferRepository


@pytest.fixture
def offer_repository(db_session: Session):
    """Create an offer repository instance."""
    return OfferRepository(db_session)


@pytest.fixture
def valid_offer_entity():
    """Create a valid offer entity."""
    return OfferEntity(
        id=str(uuid4()),
        route_id=str(uuid4()),
        cost_id=str(uuid4()),
        margin=Decimal("0.15"),
        final_price=Decimal("1150.00"),
        fun_fact="This route is equivalent to 3 trips to the moon!",
        created_at=datetime.now(timezone.utc),
        metadata={"special_notes": "Priority delivery"}
    )


def test_create_offer(offer_repository: OfferRepository, valid_offer_entity: OfferEntity):
    """Test creating a new offer."""
    created_offer = offer_repository.create(valid_offer_entity)
    assert created_offer.id == valid_offer_entity.id
    assert created_offer.route_id == valid_offer_entity.route_id
    assert created_offer.margin == valid_offer_entity.margin
    assert created_offer.final_price == valid_offer_entity.final_price
    assert created_offer.fun_fact == valid_offer_entity.fun_fact


def test_get_offer(offer_repository: OfferRepository, valid_offer_entity: OfferEntity):
    """Test getting an offer by ID."""
    created_offer = offer_repository.create(valid_offer_entity)
    retrieved_offer = offer_repository.get(str(created_offer.id))
    assert retrieved_offer is not None
    assert str(retrieved_offer.id) == str(created_offer.id)
    assert retrieved_offer.metadata == valid_offer_entity.metadata


def test_get_nonexistent_offer(offer_repository: OfferRepository):
    """Test getting a nonexistent offer."""
    offer = offer_repository.get(str(uuid4()))
    assert offer is None


def test_update_offer(offer_repository: OfferRepository, valid_offer_entity: OfferEntity):
    """Test updating an offer."""
    created_offer = offer_repository.create(valid_offer_entity)
    created_offer.final_price = Decimal("1200.00")
    created_offer.fun_fact = "Updated fun fact!"
    updated_offer = offer_repository.update(str(created_offer.id), created_offer)
    assert updated_offer is not None
    assert updated_offer.final_price == Decimal("1200.00")
    assert updated_offer.fun_fact == "Updated fun fact!"


def test_delete_offer(offer_repository: OfferRepository, valid_offer_entity: OfferEntity):
    """Test deleting an offer."""
    created_offer = offer_repository.create(valid_offer_entity)
    assert offer_repository.delete(str(created_offer.id)) is True
    assert offer_repository.get(str(created_offer.id)) is None


def test_find_by_criteria(offer_repository: OfferRepository, valid_offer_entity: OfferEntity):
    """Test finding offers by criteria."""
    offer_repository.create(valid_offer_entity)
    
    # Test finding by route ID
    offers = offer_repository.find_by_criteria(
        route_id=str(valid_offer_entity.route_id),
        limit=10
    )
    assert len(offers) > 0
    assert str(offers[0].route_id) == str(valid_offer_entity.route_id)

    # Test finding by price range
    offers = offer_repository.find_by_criteria(
        min_price=float(valid_offer_entity.final_price) - 100,
        max_price=float(valid_offer_entity.final_price) + 100,
        limit=10
    )
    assert len(offers) > 0
    assert offers[0].final_price == valid_offer_entity.final_price

    # Test finding by date range
    start_date = valid_offer_entity.created_at - timedelta(hours=1)
    end_date = valid_offer_entity.created_at + timedelta(hours=1)
    offers = offer_repository.find_by_criteria(
        start_date=start_date,
        end_date=end_date,
        limit=10
    )
    assert len(offers) > 0
    assert offers[0].created_at >= start_date
    assert offers[0].created_at <= end_date


def test_get_all_offers(offer_repository: OfferRepository, valid_offer_entity: OfferEntity):
    """Test getting all offers with pagination."""
    # Create multiple offers
    offer_repository.create(valid_offer_entity)
    second_offer = valid_offer_entity.model_copy()
    second_offer.id = str(uuid4())
    offer_repository.create(second_offer)

    # Test pagination
    offers = offer_repository.get_all(skip=0, limit=1)
    assert len(offers) == 1
    
    offers = offer_repository.get_all(skip=0, limit=2)
    assert len(offers) == 2

    offers = offer_repository.get_all(skip=1, limit=1)
    assert len(offers) == 1
