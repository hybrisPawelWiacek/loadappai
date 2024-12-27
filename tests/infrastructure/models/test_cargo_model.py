"""Tests for the Cargo model and its alignment with domain entities."""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from sqlalchemy.exc import IntegrityError
from src.infrastructure.models import Cargo, Route, TransportType, JSONEncodedDict
from src.domain.entities.cargo import Cargo as DomainCargo, CargoSpecification


@pytest.fixture
def default_cargo_data():
    """Default test data for cargo."""
    return {
        "id": str(uuid4()),
        "weight": 1500.0,  # kg
        "value": 25000.0,  # currency units
        "special_requirements": {
            "temperature": "2-8C",
            "handling": "fragile",
            "stacking": "max 2 layers"
        },
        "hazmat": False,
        "extra_data": {
            "volume": 3.5,  # m3
            "fragile": True,
            "stackable": False,
            "cargo_type": "pharmaceuticals"
        }
    }


@pytest.fixture
def domain_cargo():
    """Create a domain cargo entity."""
    return DomainCargo(
        weight=1500.0,
        volume=3.5,
        value=Decimal("25000.0"),
        type="pharmaceuticals",
        hazmat=False,
        refrigerated=True,
        fragile=True,
        stackable=False,
        special_requirements={
            "temperature": "2-8C",
            "handling": "fragile",
            "stacking": "max 2 layers"
        }
    )


@pytest.fixture
def cargo_specification():
    """Create a cargo specification."""
    return CargoSpecification(
        cargo_type="pharmaceuticals",
        weight_kg=1500.0,
        volume_m3=3.5,
        temperature_controlled=True,
        required_temp_celsius=5.0,
        special_handling=["fragile", "temperature_sensitive"],
        hazmat_class=None
    )


@pytest.fixture
def transport_type(db_session):
    """Create a transport type for testing."""
    transport = TransportType(
        id=str(uuid4()),
        name="Standard Truck",
        capacity=24000.0,  # kg
        emissions_class="EURO6",
        fuel_consumption_empty=25.0,  # L/100km
        fuel_consumption_loaded=32.0,  # L/100km
        extra_data={
            "length": 13.6,
            "width": 2.4,
            "height": 2.6,
            "max_weight": 24000,
            "description": "Standard 40ft truck",
            "cost_modifiers": {
                "base_rate": 1.0,
                "distance_rate": 0.8,
                "time_rate": 1.2
            }
        }
    )
    db_session.add(transport)
    db_session.commit()
    return transport


def test_create_cargo(db_session, default_cargo_data):
    """Test creating a new cargo entry."""
    cargo = Cargo(**default_cargo_data)
    db_session.add(cargo)
    db_session.commit()

    saved_cargo = db_session.query(Cargo).filter_by(id=cargo.id).first()
    assert saved_cargo is not None
    assert saved_cargo.weight == 1500.0
    assert saved_cargo.value == 25000.0
    assert saved_cargo.hazmat is False
    assert saved_cargo.special_requirements["temperature"] == "2-8C"
    assert saved_cargo.extra_data["volume"] == 3.5


def test_update_cargo(db_session, default_cargo_data):
    """Test updating cargo attributes."""
    cargo = Cargo(**default_cargo_data)
    db_session.add(cargo)
    db_session.commit()

    # Update various fields
    cargo.weight = 1600.0
    cargo.value = 27000.0
    cargo.hazmat = True
    
    # Update JSON fields
    new_special_requirements = cargo.special_requirements.copy()
    new_special_requirements["temperature"] = "15-25C"
    cargo.special_requirements = new_special_requirements

    new_extra_data = cargo.extra_data.copy()
    new_extra_data["volume"] = 4.0
    cargo.extra_data = new_extra_data
    
    db_session.commit()

    updated_cargo = db_session.query(Cargo).filter_by(id=cargo.id).first()
    assert updated_cargo.weight == 1600.0
    assert updated_cargo.value == 27000.0
    assert updated_cargo.hazmat is True
    assert updated_cargo.special_requirements["temperature"] == "15-25C"
    assert updated_cargo.extra_data["volume"] == 4.0


def test_delete_cargo(db_session, default_cargo_data):
    """Test deleting a cargo."""
    cargo = Cargo(**default_cargo_data)
    db_session.add(cargo)
    db_session.commit()

    db_session.delete(cargo)
    db_session.commit()

    deleted_cargo = db_session.query(Cargo).filter_by(id=cargo.id).first()
    assert deleted_cargo is None


def test_null_constraints(db_session):
    """Test null constraints on required fields."""
    # Test missing weight
    cargo = Cargo(
        id=str(uuid4()),
        value=25000.0,
        hazmat=False
    )
    with pytest.raises(IntegrityError):
        db_session.add(cargo)
        db_session.commit()
    db_session.rollback()

    # Test missing value
    cargo = Cargo(
        id=str(uuid4()),
        weight=1500.0,
        hazmat=False
    )
    with pytest.raises(IntegrityError):
        db_session.add(cargo)
        db_session.commit()
    db_session.rollback()


def test_json_field_handling(db_session, default_cargo_data):
    """Test JSON field handling."""
    cargo = Cargo(**default_cargo_data)
    db_session.add(cargo)
    db_session.commit()

    # Test updating special_requirements
    new_special_requirements = {
        "temperature": "15-25C",
        "handling": "standard",
        "stacking": "no limit",
        "additional": "requires GPS tracking"
    }
    cargo.special_requirements = new_special_requirements
    db_session.commit()

    updated_cargo = db_session.query(Cargo).filter_by(id=cargo.id).first()
    assert updated_cargo.special_requirements == new_special_requirements
    assert "requires GPS tracking" in updated_cargo.special_requirements["additional"]


def test_route_relationship(db_session, default_cargo_data, transport_type):
    """Test relationship with Route model."""
    cargo = Cargo(**default_cargo_data)
    db_session.add(cargo)
    db_session.commit()

    # Create a route using this cargo
    route = Route(
        id=str(uuid4()),
        origin={"city": "Warsaw", "country": "PL", "lat": 52.2297, "lon": 21.0122},
        destination={"city": "Berlin", "country": "DE", "lat": 52.5200, "lon": 13.4050},
        pickup_time=datetime.utcnow(),
        delivery_time=datetime.utcnow() + timedelta(days=1),
        transport_type=transport_type.id,  # Add transport type
        cargo_id=cargo.id,
        distance_km=575.0,
        duration_hours=8.0,
        is_feasible=True
    )
    db_session.add(route)
    db_session.commit()

    # Test accessing route through relationship
    assert len(cargo.routes) == 1
    assert cargo.routes[0].id == route.id
    assert cargo.routes[0].origin["city"] == "Warsaw"
    assert cargo.routes[0].transport_type == transport_type.id


def test_domain_alignment(db_session, domain_cargo):
    """Test alignment between domain entity and infrastructure model."""
    # Create infrastructure model from domain entity
    cargo = Cargo(
        id=str(domain_cargo.id),
        weight=domain_cargo.weight,
        value=float(domain_cargo.value),  # Convert Decimal to float
        hazmat=domain_cargo.hazmat,
        special_requirements=domain_cargo.special_requirements,
        extra_data={
            "volume": domain_cargo.volume,
            "fragile": domain_cargo.fragile,
            "stackable": domain_cargo.stackable,
            "cargo_type": domain_cargo.type,
            "refrigerated": domain_cargo.refrigerated
        }
    )
    db_session.add(cargo)
    db_session.commit()

    # Retrieve and verify
    saved_cargo = db_session.query(Cargo).filter_by(id=str(domain_cargo.id)).first()
    assert saved_cargo is not None
    assert saved_cargo.weight == domain_cargo.weight
    assert saved_cargo.value == float(domain_cargo.value)
    assert saved_cargo.hazmat == domain_cargo.hazmat
    assert saved_cargo.special_requirements == domain_cargo.special_requirements
    assert saved_cargo.extra_data["volume"] == domain_cargo.volume
    assert saved_cargo.extra_data["fragile"] == domain_cargo.fragile
    assert saved_cargo.extra_data["stackable"] == domain_cargo.stackable
    assert saved_cargo.extra_data["cargo_type"] == domain_cargo.type


def test_specification_support(db_session, cargo_specification):
    """Test support for cargo specifications."""
    # Create infrastructure model from specification
    cargo = Cargo(
        id=str(uuid4()),
        weight=cargo_specification.weight_kg,
        value=10000.0,  # Example value
        hazmat=cargo_specification.hazmat_class is not None,
        special_requirements={
            "temperature_control": cargo_specification.temperature_controlled,
            "required_temp": cargo_specification.required_temp_celsius,
            "special_handling": cargo_specification.special_handling
        },
        extra_data={
            "volume": cargo_specification.volume_m3,
            "cargo_type": cargo_specification.cargo_type
        }
    )
    db_session.add(cargo)
    db_session.commit()

    # Retrieve and verify
    saved_cargo = db_session.query(Cargo).filter_by(id=cargo.id).first()
    assert saved_cargo is not None
    assert saved_cargo.weight == cargo_specification.weight_kg
    assert saved_cargo.extra_data["volume"] == cargo_specification.volume_m3
    assert saved_cargo.special_requirements["temperature_control"] == cargo_specification.temperature_controlled
    assert saved_cargo.special_requirements["required_temp"] == cargo_specification.required_temp_celsius


def test_query_performance(db_session):
    """Test index performance for common queries."""
    # Create multiple cargo entries
    for i in range(10):
        cargo = Cargo(
            id=str(uuid4()),
            weight=1000.0 + i * 100,
            value=20000.0 + i * 1000,
            hazmat=i % 2 == 0  # Alternate between True and False
        )
        db_session.add(cargo)
    db_session.commit()

    # Test querying by hazmat flag (should use index)
    hazmat_cargo = db_session.query(Cargo).filter_by(hazmat=True).all()
    assert len(hazmat_cargo) == 5  # Half of the entries should be hazmat

    # Test querying with weight range
    heavy_cargo = db_session.query(Cargo).filter(
        Cargo.weight >= 1500.0
    ).all()
    assert len(heavy_cargo) == 5  # Should find cargo with weight >= 1500.0


def test_valid_ranges(db_session):
    """Test valid ranges for numeric fields."""
    # Test negative weight
    cargo = Cargo(
        id=str(uuid4()),
        weight=-100.0,  # Invalid negative weight
        value=1000.0,
        hazmat=False
    )
    db_session.add(cargo)
    db_session.commit()  # This should work as we don't have range validation

    # Test negative value
    cargo = Cargo(
        id=str(uuid4()),
        weight=100.0,
        value=-1000.0,  # Invalid negative value
        hazmat=False
    )
    db_session.add(cargo)
    db_session.commit()  # This should work as we don't have range validation

    # Note: If we want to add range validation, we should:
    # 1. Add CHECK constraints in the database
    # 2. Add validation in the model or service layer
