"""Tests for offer repository."""
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Dict

import pytest
from sqlalchemy.orm import Session

from src.domain.entities.offer import Offer, OfferHistory, OfferStatus
from src.infrastructure.repositories.offer_repository import OfferRepository
from src.infrastructure.models import (
    Offer as OfferModel,
    Route as RouteModel,
    CostHistory as CostHistoryModel,
    OfferHistory as OfferHistoryModel
)
from src.domain.interfaces.exceptions.repository_errors import EntityNotFoundError


@pytest.fixture
def offer_repository(db_session: Session):
    """Create an offer repository instance."""
    repository = OfferRepository(db_session)
    return repository


@pytest.fixture
def sample_route(db_session: Session):
    """Create a sample route in the database."""
    route = RouteModel(
        id=str(uuid.uuid4()),
        origin={"name": "Berlin", "country": "DE"},
        destination={"name": "Hamburg", "country": "DE"},
        pickup_time=datetime.now(timezone.utc),
        delivery_time=datetime.now(timezone.utc) + timedelta(hours=5),
        transport_type="TRUCK",
        distance_km=300.0,
        duration_hours=4.0,
        is_feasible=True,
        status="ACTIVE"
    )
    db_session.add(route)
    db_session.commit()
    return route


@pytest.fixture
def sample_cost_history(db_session: Session):
    """Create a sample cost history in the database."""
    cost = CostHistoryModel(
        id=str(uuid.uuid4()),
        route_id='08e3ecf4-722c-4a27-8bb1-2db8c417ded9',
        calculation_date=datetime.now(timezone.utc),
        total_cost=Decimal('100.50'),
        currency='EUR',
        calculation_method='STANDARD',
        version='1.0',
        is_final=True,
        cost_components='{}',
        settings_snapshot='{}'
    )
    db_session.add(cost)
    db_session.commit()
    return cost


@pytest.fixture
def sample_offer(sample_cost_history):
    """Create a sample offer."""
    total_cost = Decimal('100.50')
    final_price = Decimal('116.60')
    margin = Decimal(str(round((final_price - total_cost) / total_cost, 4)))  # Round margin to 4 decimal places
    
    return Offer(
        id=uuid.UUID('ad888200-df91-4466-aed6-82dd69768ced'),
        route_id=uuid.UUID('08e3ecf4-722c-4a27-8bb1-2db8c417ded9'),
        cost_id=uuid.UUID(sample_cost_history.id),
        total_cost=total_cost,
        margin=margin,
        final_price=final_price,
        fun_fact='Test fun fact',
        status=OfferStatus.ACTIVE,
        is_active=True,
        valid_until=datetime.now(timezone.utc) + timedelta(days=7),
        version="1.0",
        metadata={"test_key": "test_value"},
        created_at=datetime.now(timezone.utc),
        modified_at=datetime.now(timezone.utc)
    )


def test_create_offer(offer_repository, sample_offer):
    """Test creating a new offer."""
    created_offer = offer_repository.create(sample_offer)
    
    assert isinstance(created_offer, Offer)
    assert str(created_offer.id) == str(sample_offer.id)
    assert str(created_offer.route_id) == str(sample_offer.route_id)
    assert str(created_offer.cost_id) == str(sample_offer.cost_id)
    assert created_offer.margin == sample_offer.margin
    assert created_offer.final_price == sample_offer.final_price
    assert created_offer.status == sample_offer.status
    assert created_offer.metadata == sample_offer.metadata
    
    # Check history was created
    history = offer_repository.get_offer_history(created_offer.id)
    assert len(history) == 1
    assert history[0].version == "1.0"
    assert history[0].status == sample_offer.status
    assert history[0].margin == sample_offer.margin
    assert history[0].final_price == sample_offer.final_price
    assert history[0].metadata == sample_offer.metadata


def test_get_by_id(offer_repository, sample_offer):
    """Test retrieving an offer by ID."""
    created = offer_repository.create(sample_offer)
    
    retrieved = offer_repository.get_by_id(str(created.id))
    assert retrieved is not None
    assert str(retrieved.id) == str(created.id)
    assert retrieved.status == created.status
    assert retrieved.metadata == created.metadata


def test_update_offer(offer_repository, sample_offer):
    """Test updating an existing offer."""
    created = offer_repository.create(sample_offer)
    
    # Calculate new margin and final price
    new_margin = Decimal("0.15")  # 15% as a ratio
    new_final_price = (created.total_cost * (1 + new_margin)).quantize(Decimal('0.01'))  # Round to 2 decimal places
    new_metadata = {"updated_key": "updated_value"}
    
    # Modify fields
    created.status = OfferStatus.EXPIRED
    created.margin = new_margin
    created.final_price = new_final_price
    created.metadata = new_metadata
    
    updated = offer_repository.update(created)
    assert updated.status == OfferStatus.EXPIRED
    assert updated.margin == new_margin
    assert updated.final_price == new_final_price
    assert updated.metadata == new_metadata
    assert updated.version == "1.1"
    
    # Check history was updated
    history = offer_repository.get_offer_history(updated.id)
    assert len(history) == 2  # Initial + update
    assert history[0].version == "1.1"  # Latest version
    assert history[0].status == OfferStatus.EXPIRED
    assert history[0].metadata == new_metadata


def test_delete_offer(offer_repository, sample_offer):
    """Test deleting an offer."""
    created = offer_repository.create(sample_offer)
    
    assert offer_repository.delete(str(created.id)) is True
    assert offer_repository.get_by_id(str(created.id)) is None


def test_get_active_offers(offer_repository, sample_offer):
    """Test getting active offers."""
    # Create an active offer
    active_offer = offer_repository.create(sample_offer)
    
    # Create an expired offer
    expired_offer = Offer(
        **{
            **sample_offer.model_dump(),
            "id": uuid.uuid4(),
            "status": OfferStatus.EXPIRED,
            "is_active": False
        }
    )
    offer_repository.create(expired_offer)

    # Get active offers
    active_offers = offer_repository.get_active_offers()
    assert len(active_offers) == 1
    assert str(active_offers[0].id) == str(active_offer.id)


def test_update_offer_status(offer_repository, sample_offer):
    """Test updating offer status."""
    created = offer_repository.create(sample_offer)
    
    # Update status
    updated = offer_repository.update_offer_status(
        created.id,
        OfferStatus.EXPIRED,
        "Test status update"
    )
    
    assert updated.status == OfferStatus.EXPIRED
    assert updated.version == "1.1"
    
    # Check history
    history = offer_repository.get_offer_history(updated.id)
    assert len(history) == 2
    assert history[0].status == OfferStatus.EXPIRED
    assert history[0].change_reason == "Test status update"


def test_extend_validity(offer_repository, sample_offer):
    """Test extending offer validity."""
    created = offer_repository.create(sample_offer)
    
    # Extend validity
    new_validity = datetime.now(timezone.utc) + timedelta(days=14)
    updated = offer_repository.extend_validity(
        created.id,
        new_validity,
        "Extended for testing"
    )
    
    assert updated.valid_until == new_validity
    assert updated.version == "1.1"
    
    # Check history
    history = offer_repository.get_offer_history(updated.id)
    assert len(history) == 2
    assert "Extended for testing" in history[0].change_reason
    assert str(new_validity.isoformat()) in history[0].change_reason


def test_get_offer_metadata(offer_repository, sample_offer):
    """Test retrieving offer metadata."""
    created = offer_repository.create(sample_offer)
    
    metadata = offer_repository.get_offer_metadata(created.id)
    assert metadata == sample_offer.metadata


def test_find_offers(offer_repository, sample_offer):
    """Test finding offers with criteria."""
    # Create test offers
    offer1 = offer_repository.create(sample_offer)
    
    # Calculate proper margin for offer2
    total_cost2 = Decimal("100.50")
    final_price2 = Decimal("200.00")
    margin2 = Decimal(str(round((final_price2 - total_cost2) / total_cost2, 4)))  # Calculate margin as ratio
    
    offer2 = Offer(
        **{
            **sample_offer.model_dump(),
            "id": uuid.uuid4(),
            "total_cost": total_cost2,
            "margin": margin2,
            "final_price": final_price2,
            "status": OfferStatus.CANCELLED
        }
    )
    offer_repository.create(offer2)
    
    # Test filtering
    offers, total = offer_repository.find_offers(
        route_id=offer1.route_id,
        status=OfferStatus.ACTIVE.value,
        min_price=Decimal("100.00"),
        max_price=Decimal("150.00")
    )
    
    assert total == 1
    assert len(offers) == 1
    assert str(offers[0].id) == str(offer1.id)


def test_get_version(offer_repository, sample_offer):
    """Test retrieving specific offer version."""
    created = offer_repository.create(sample_offer)
    
    # Make an update to create new version
    created.status = OfferStatus.EXPIRED
    updated = offer_repository.update(created)
    
    # Get original version
    v1 = offer_repository.get_version(created.id, "1.0")
    assert v1 is not None
    assert v1.version == "1.0"
    assert v1.status == OfferStatus.ACTIVE
    
    # Get updated version
    v2 = offer_repository.get_version(created.id, "1.1")
    assert v2 is not None
    assert v2.version == "1.1"
    assert v2.status == OfferStatus.EXPIRED


def test_compare_versions(offer_repository, sample_offer):
    """Test comparing offer versions."""
    created = offer_repository.create(sample_offer)
    
    # Make an update to create new version
    created.status = OfferStatus.EXPIRED
    updated = offer_repository.update(created)
    
    # Compare versions
    v1, v2 = offer_repository.compare_versions(created.id, "1.0", "1.1")
    
    assert v1 is not None
    assert v2 is not None
    assert v1.version == "1.0"
    assert v2.version == "1.1"
    assert v1.status == OfferStatus.ACTIVE
    assert v2.status == OfferStatus.EXPIRED


def test_get_offer_history(offer_repository, sample_offer):
    """Test retrieving offer history."""
    created = offer_repository.create(sample_offer)
    
    # Make multiple updates
    updates = [
        (OfferStatus.PENDING, "Changed to pending"),
        (OfferStatus.EXPIRED, "Offer expired"),
        (OfferStatus.CANCELLED, "Cancelled by user")
    ]
    
    current = created
    for status, reason in updates:
        current = offer_repository.update_offer_status(current.id, status, reason)
    
    # Get history
    history = offer_repository.get_offer_history(created.id)
    
    assert len(history) == 4  # Initial + 3 updates
    assert history[0].version == "1.3"  # Latest version
    assert history[0].status == OfferStatus.CANCELLED
    assert history[0].change_reason == "Cancelled by user"
    
    # Check order (newest first)
    for i, (status, _) in enumerate(reversed(updates)):
        assert history[i].status == status
