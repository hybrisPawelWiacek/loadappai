"""Tests for cargo-related domain entities."""

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from pytz import UTC

from src.domain.entities.cargo import (
    CargoSpecification,
    Cargo
)


@pytest.fixture
def valid_cargo_spec_data():
    """Fixture providing valid cargo specification data."""
    return {
        "cargo_type": "general",
        "weight_kg": 1000.0,
        "volume_m3": 2.5,
        "temperature_controlled": True,
        "required_temp_celsius": 4.0,
        "special_handling": ["fragile"],
        "hazmat_class": "3"
    }


@pytest.fixture
def valid_cargo_data():
    """Fixture providing valid cargo data."""
    return {
        "id": uuid4(),
        "weight": 1000.0,
        "volume": 2.5,
        "value": Decimal("5000.00"),
        "type": "general",
        "hazmat": True,
        "refrigerated": True,
        "fragile": True,
        "stackable": False,
        "special_requirements": {"handling": "with care"}
    }


def test_cargo_specification_creation(valid_cargo_spec_data):
    """Test CargoSpecification creation and validation."""
    # Valid specification
    spec = CargoSpecification(**valid_cargo_spec_data)
    assert spec.cargo_type == valid_cargo_spec_data["cargo_type"]
    assert spec.weight_kg == valid_cargo_spec_data["weight_kg"]
    assert spec.volume_m3 == valid_cargo_spec_data["volume_m3"]
    assert spec.temperature_controlled is True
    assert spec.required_temp_celsius == 4.0
    assert spec.special_handling == ["fragile"]
    assert spec.hazmat_class == "3"


def test_cargo_specification_validation():
    """Test CargoSpecification validation rules."""
    # Invalid weight
    with pytest.raises(ValueError):
        CargoSpecification(
            cargo_type="general",
            weight_kg=0,
            volume_m3=2.5
        )
    
    # Invalid volume
    with pytest.raises(ValueError):
        CargoSpecification(
            cargo_type="general",
            weight_kg=1000.0,
            volume_m3=0
        )
    
    # Temperature validation
    with pytest.raises(ValueError, match="required_temp_celsius must be set"):
        CargoSpecification(
            cargo_type="general",
            weight_kg=1000.0,
            volume_m3=2.5,
            temperature_controlled=True,
            required_temp_celsius=None
        )


def test_cargo_creation(valid_cargo_data):
    """Test Cargo entity creation and validation."""
    # Valid cargo
    cargo = Cargo(**valid_cargo_data)
    assert cargo.id == valid_cargo_data["id"]
    assert cargo.weight == valid_cargo_data["weight"]
    assert cargo.volume == valid_cargo_data["volume"]
    assert cargo.value == valid_cargo_data["value"]
    assert cargo.type == valid_cargo_data["type"]
    assert cargo.hazmat is True
    assert cargo.refrigerated is True
    assert cargo.fragile is True
    assert cargo.stackable is False
    assert cargo.special_requirements == {"handling": "with care"}
    
    # Check ExtensibleEntity inheritance
    assert cargo.version == "1.0"
    assert cargo.created_at is not None
    assert cargo.modified_at is not None
    assert isinstance(cargo.created_at, datetime)
    assert isinstance(cargo.modified_at, datetime)


def test_cargo_validation():
    """Test Cargo validation rules."""
    # Invalid weight
    with pytest.raises(ValueError):
        Cargo(
            weight=0,
            volume=2.5,
            value=Decimal("5000.00"),
            type="general"
        )
    
    # Invalid volume
    with pytest.raises(ValueError):
        Cargo(
            weight=1000.0,
            volume=0,
            value=Decimal("5000.00"),
            type="general"
        )
    
    # Invalid value
    with pytest.raises(ValueError):
        Cargo(
            weight=1000.0,
            volume=2.5,
            value=Decimal("-5000.00"),
            type="general"
        )


def test_cargo_defaults():
    """Test Cargo default values."""
    cargo = Cargo(
        weight=1000.0,
        volume=2.5,
        value=Decimal("5000.00"),
        type="general"
    )
    assert cargo.hazmat is False
    assert cargo.refrigerated is False
    assert cargo.fragile is False
    assert cargo.stackable is True
    assert cargo.special_requirements is None
    assert cargo.metadata is None


def test_cargo_update(valid_cargo_data):
    """Test cargo update functionality."""
    cargo = Cargo(**valid_cargo_data)
    initial_modified = cargo.modified_at
    
    # Update cargo using model_copy
    cargo = cargo.model_copy(
        update={
            "weight": 2000.0,
            "modified_at": datetime.now(UTC)
        }
    )
    
    # Verify update
    assert cargo.weight == 2000.0
    assert cargo.modified_at > initial_modified


def test_cargo_metadata():
    """Test cargo metadata handling."""
    metadata = {
        "customer_notes": "Handle with extra care",
        "priority": "high",
        "customs_info": {
            "tariff_code": "12345",
            "origin_country": "DE"
        }
    }
    
    cargo = Cargo(
        weight=1000.0,
        volume=2.5,
        value=Decimal("5000.00"),
        type="general",
        metadata=metadata
    )
    
    assert cargo.metadata == metadata
    assert cargo.metadata["customer_notes"] == "Handle with extra care"
    assert cargo.metadata["customs_info"]["tariff_code"] == "12345"


def test_cargo_specification():
    """Test CargoSpecification entity."""
    # Valid specification
    spec = CargoSpecification(
        cargo_type="general",
        weight_kg=1000.0,
        volume_m3=2.5,
        temperature_controlled=True,
        required_temp_celsius=4.0,
        special_handling=["fragile"],
        hazmat_class="3"
    )
    assert spec.cargo_type == "general"
    assert spec.weight_kg == 1000.0
    assert spec.volume_m3 == 2.5
    assert spec.temperature_controlled is True
    assert spec.required_temp_celsius == 4.0
    assert spec.special_handling == ["fragile"]
    assert spec.hazmat_class == "3"
    
    # Invalid weight
    with pytest.raises(ValueError):
        CargoSpecification(
            cargo_type="general",
            weight_kg=0,
            volume_m3=2.5
        )
    
    # Invalid volume
    with pytest.raises(ValueError):
        CargoSpecification(
            cargo_type="general",
            weight_kg=1000.0,
            volume_m3=0
        )


def test_cargo():
    """Test Cargo entity."""
    cargo_id = uuid4()
    
    # Valid cargo
    cargo = Cargo(
        id=cargo_id,
        weight=1000.0,
        volume=2.5,
        value=Decimal("5000.00"),
        type="general",
        hazmat=True,
        refrigerated=True,
        fragile=True,
        stackable=False,
        special_requirements={"handling": "with care"}
    )
    assert cargo.id == cargo_id
    assert cargo.weight == 1000.0
    assert cargo.volume == 2.5
    assert cargo.value == Decimal("5000.00")
    assert cargo.type == "general"
    assert cargo.hazmat is True
    assert cargo.refrigerated is True
    assert cargo.fragile is True
    assert cargo.stackable is False
    assert cargo.special_requirements == {"handling": "with care"}
    
    # Invalid weight
    with pytest.raises(ValueError):
        Cargo(
            id=cargo_id,
            weight=0,
            volume=2.5,
            value=Decimal("5000.00"),
            type="general"
        )
    
    # Invalid volume
    with pytest.raises(ValueError):
        Cargo(
            id=cargo_id,
            weight=1000.0,
            volume=0,
            value=Decimal("5000.00"),
            type="general"
        )
    
    # Invalid value
    with pytest.raises(ValueError):
        Cargo(
            id=cargo_id,
            weight=1000.0,
            volume=2.5,
            value=Decimal("-5000.00"),
            type="general"
        )
