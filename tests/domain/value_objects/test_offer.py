"""Tests for offer-related value objects."""

from decimal import Decimal
from uuid import UUID, uuid4
from datetime import datetime, timezone, timedelta

import pytest
from pydantic import ValidationError

from src.domain.value_objects.offer import OfferGenerationResult, OfferMetadata
from src.domain.value_objects.cost import CostBreakdown
from src.domain.entities.offer import Offer, OfferStatus
from src.domain.entities.route import Route, TransportType

# Rebuild OfferGenerationResult model after importing actual types
OfferGenerationResult.model_rebuild()


def test_offer_metadata_default_creation():
    """Test creating OfferMetadata with default values."""
    metadata = OfferMetadata()
    assert metadata.version == "1.0"
    assert metadata.source is None
    assert metadata.tags == {}
    assert metadata.notes is None
    assert metadata.custom_fields == {}


def test_offer_metadata_custom_values():
    """Test creating OfferMetadata with custom values."""
    metadata = OfferMetadata(
        version="2.0",
        source="API",
        tags={"priority": "high", "type": "express"},
        notes="Special handling required",
        custom_fields={"customer_ref": "ABC123"}
    )
    
    assert metadata.version == "2.0"
    assert metadata.source == "API"
    assert metadata.tags == {"priority": "high", "type": "express"}
    assert metadata.notes == "Special handling required"
    assert metadata.custom_fields == {"customer_ref": "ABC123"}


def test_offer_metadata_immutability():
    """Test that OfferMetadata is immutable."""
    metadata = OfferMetadata(version="1.0")
    
    with pytest.raises(ValidationError) as exc_info:
        metadata.version = "2.0"  # type: ignore
    assert "frozen_instance" in str(exc_info.value)
    
    with pytest.raises(ValidationError) as exc_info:
        metadata.tags = {"new": "tag"}  # type: ignore
    assert "frozen_instance" in str(exc_info.value)


def test_offer_generation_result_creation():
    """Test creating OfferGenerationResult."""
    # Create actual Offer and Route objects
    route = Route(
        id=uuid4(),
        transport_type=TransportType.TRUCK,
        origin={"lat": 52.5200, "lon": 13.4050, "address": "Berlin, Germany"},
        destination={"lat": 48.8566, "lon": 2.3522, "address": "Paris, France"},
        pickup_time=datetime.now(timezone.utc),
        delivery_time=datetime.now(timezone.utc) + timedelta(hours=5),
        distance_km=1050.0,
        duration_hours=12.5,
    )
    
    cost_id = UUID("98765432-5432-9876-5432-987654321098")
    total_cost = Decimal("800.00")
    margin = Decimal("0.25")
    final_price = total_cost * (1 + margin)
    
    offer = Offer(
        id=UUID("12345678-1234-5678-1234-567812345678"),
        route_id=route.id,
        cost_id=cost_id,
        total_cost=total_cost,
        margin=margin,
        final_price=final_price,
        status=OfferStatus.DRAFT,
        version="1.0",
        fun_fact="This route crosses 3 time zones!",
    )
    
    cost_breakdown = CostBreakdown(
        route_id=route.id,
        fuel_costs={"country1": Decimal("200.00")},
        toll_costs={"highway1": Decimal("100.00")},
        driver_costs={"regular": Decimal("300.00")},
        total_cost=Decimal("600.00"),
    )
    
    result = OfferGenerationResult(
        offer=offer,
        route=route,
        cost_breakdown=cost_breakdown,
        fun_fact="This route crosses 3 time zones!",
    )
    
    assert result.offer == offer
    assert result.route == route
    assert result.cost_breakdown == cost_breakdown
    assert result.fun_fact == "This route crosses 3 time zones!"


def test_offer_generation_result_required_fields():
    """Test required fields in OfferGenerationResult."""
    # Create test data
    route = Route(
        id=uuid4(),
        transport_type=TransportType.TRUCK,
        origin={"lat": 52.5200, "lon": 13.4050, "address": "Berlin, Germany"},
        destination={"lat": 48.8566, "lon": 2.3522, "address": "Paris, France"},
        pickup_time=datetime.now(timezone.utc),
        delivery_time=datetime.now(timezone.utc) + timedelta(hours=5),
        distance_km=1050.0,
        duration_hours=12.5,
    )
    
    cost_id = UUID("98765432-5432-9876-5432-987654321098")
    total_cost = Decimal("800.00")
    margin = Decimal("0.25")
    final_price = total_cost * (1 + margin)
    
    offer = Offer(
        id=UUID("12345678-1234-5678-1234-567812345678"),
        route_id=route.id,
        cost_id=cost_id,
        total_cost=total_cost,
        margin=margin,
        final_price=final_price,
        status=OfferStatus.DRAFT,
        version="1.0",
    )
    
    with pytest.raises(ValidationError):
        OfferGenerationResult()  # type: ignore

    with pytest.raises(ValidationError):
        OfferGenerationResult(offer=offer)  # type: ignore

    with pytest.raises(ValidationError):
        OfferGenerationResult(offer=offer, route=route)  # type: ignore


def test_offer_generation_result_optional_fields():
    """Test optional fields in OfferGenerationResult."""
    route = Route(
        id=uuid4(),
        transport_type=TransportType.TRUCK,
        origin={"lat": 52.5200, "lon": 13.4050, "address": "Berlin, Germany"},
        destination={"lat": 48.8566, "lon": 2.3522, "address": "Paris, France"},
        pickup_time=datetime.now(timezone.utc),
        delivery_time=datetime.now(timezone.utc) + timedelta(hours=5),
        distance_km=1050.0,
        duration_hours=12.5,
    )
    
    cost_id = UUID("98765432-5432-9876-5432-987654321098")
    total_cost = Decimal("800.00")
    margin = Decimal("0.25")
    final_price = total_cost * (1 + margin)
    
    offer = Offer(
        id=UUID("12345678-1234-5678-1234-567812345678"),
        route_id=route.id,
        cost_id=cost_id,
        total_cost=total_cost,
        margin=margin,
        final_price=final_price,
        status=OfferStatus.DRAFT,
        version="1.0",
    )
    
    cost_breakdown = CostBreakdown(route_id=route.id)
    
    result = OfferGenerationResult(
        offer=offer,
        route=route,
        cost_breakdown=cost_breakdown,
        fun_fact=None,
    )
    
    assert result.fun_fact is None


def test_offer_generation_result_immutability():
    """Test that OfferGenerationResult is immutable."""
    route = Route(
        id=UUID("87654321-4321-8765-4321-876543210987"),
        transport_type=TransportType.TRUCK,
        origin={"lat": 52.5200, "lon": 13.4050, "address": "Berlin, Germany"},
        destination={"lat": 48.8566, "lon": 2.3522, "address": "Paris, France"},
        pickup_time=datetime.now(timezone.utc),
        delivery_time=datetime.now(timezone.utc) + timedelta(hours=5),
        distance_km=1050.0,
        duration_hours=12.5,
    )
    
    cost_id = UUID("98765432-5432-9876-5432-987654321098")
    total_cost = Decimal("800.00")
    margin = Decimal("0.25")
    final_price = total_cost * (1 + margin)
    
    offer = Offer(
        id=UUID("12345678-1234-5678-1234-567812345678"),
        route_id=route.id,
        cost_id=cost_id,
        total_cost=total_cost,
        margin=margin,
        final_price=final_price,
        status=OfferStatus.DRAFT,
        version="1.0",
    )
    
    cost_breakdown = CostBreakdown(route_id=route.id)
    
    result = OfferGenerationResult(
        offer=offer,
        route=route,
        cost_breakdown=cost_breakdown,
    )
    
    with pytest.raises(ValidationError) as exc_info:
        result.fun_fact = "New fact"  # type: ignore
    assert "frozen_instance" in str(exc_info.value)
    
    with pytest.raises(ValidationError) as exc_info:
        result.offer = offer  # type: ignore
    assert "frozen_instance" in str(exc_info.value)
