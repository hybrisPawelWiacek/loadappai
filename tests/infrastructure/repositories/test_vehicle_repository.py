"""Tests for vehicle repository implementation."""
import pytest
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy.orm import Session, sessionmaker

from src.domain.entities.vehicle import Vehicle, VehicleSpecification
from src.infrastructure.database import Base, Database
from src.infrastructure.repositories.vehicle_repository import VehicleRepository
from src.infrastructure.models import Vehicle as VehicleModel


@pytest.fixture
def vehicle_spec():
    """Create test vehicle specification."""
    return VehicleSpecification(
        vehicle_type="truck",
        fuel_consumption_rate=30.5,
        empty_consumption_factor=0.8,
        maintenance_rate_per_km=Decimal("0.15"),
        toll_class="class_2",
        has_special_equipment=True,
        equipment_costs={"refrigeration": Decimal("100.00")}
    )


@pytest.fixture
def vehicle(vehicle_spec):
    """Create test vehicle."""
    return Vehicle(id=uuid4(), specifications=vehicle_spec)


@pytest.fixture
def repository(db_session):
    """Create test repository."""
    class TestDatabase(Database):
        def __init__(self, session):
            self.session = session

    return VehicleRepository(TestDatabase(db_session))


def test_create(repository, vehicle):
    """Test creating a vehicle."""
    created = repository.create(vehicle)
    assert created.id == vehicle.id
    assert created.specifications == vehicle.specifications


def test_get(repository, vehicle):
    """Test getting a vehicle."""
    created = repository.create(vehicle)
    
    retrieved = repository.get(vehicle.id)
    assert retrieved is not None
    assert retrieved.id == vehicle.id
    assert retrieved.specifications == vehicle.specifications
    
    # Test getting non-existent vehicle
    assert repository.get(UUID('00000000-0000-0000-0000-000000000000')) is None


def test_get_all(repository, vehicle, vehicle_spec):
    """Test getting all vehicles."""
    # Create multiple vehicles
    vehicles = [
        vehicle,
        Vehicle(id=uuid4(), specifications=vehicle_spec),
        Vehicle(id=uuid4(), specifications=vehicle_spec)
    ]
    
    for v in vehicles:
        repository.create(v)
    
    # Test without pagination
    all_vehicles = repository.get_all()
    assert len(all_vehicles) == 3
    
    # Test with pagination
    paginated = repository.get_all(skip=1, limit=1)
    assert len(paginated) == 1


def test_update(repository, vehicle):
    """Test updating a vehicle."""
    created = repository.create(vehicle)
    
    # Update vehicle specifications
    updated_spec = VehicleSpecification(
        vehicle_type="van",
        fuel_consumption_rate=25.0,
        empty_consumption_factor=0.7,
        maintenance_rate_per_km=Decimal("0.12"),
        toll_class="class_1",
        has_special_equipment=False,
        equipment_costs={}
    )
    updated_vehicle = Vehicle(id=vehicle.id, specifications=updated_spec)
    
    updated = repository.update(vehicle.id, updated_vehicle)
    assert updated is not None
    assert updated.id == vehicle.id
    assert updated.specifications == updated_spec
    
    # Test updating non-existent vehicle
    non_existent = Vehicle(id=UUID('00000000-0000-0000-0000-000000000000'), specifications=updated_spec)
    assert repository.update(non_existent.id, non_existent) is None


def test_delete(repository, vehicle):
    """Test deleting a vehicle."""
    created = repository.create(vehicle)
    
    # Delete vehicle
    assert repository.delete(vehicle.id) is True
    assert repository.get(vehicle.id) is None
    
    # Test deleting non-existent vehicle
    assert repository.delete(UUID('00000000-0000-0000-0000-000000000000')) is False


def test_count(repository, vehicle, vehicle_spec):
    """Test counting vehicles."""
    assert repository.count() == 0
    
    # Create multiple vehicles
    vehicles = [
        vehicle,
        Vehicle(id=uuid4(), specifications=vehicle_spec),
        Vehicle(id=uuid4(), specifications=vehicle_spec)
    ]
    
    for v in vehicles:
        repository.create(v)
        
    assert repository.count() == 3
    
    repository.delete(vehicles[0].id)
    assert repository.count() == 2


def test_get_by_type(repository, vehicle, vehicle_spec):
    """Test getting vehicles by type."""
    # Create vehicles of different types
    truck = vehicle  # type is "truck"
    van = Vehicle(
        id=uuid4(),
        specifications=VehicleSpecification(
            vehicle_type="van",
            fuel_consumption_rate=25.0,
            empty_consumption_factor=0.7,
            maintenance_rate_per_km=Decimal("0.12"),
            toll_class="class_1",
            has_special_equipment=False,
            equipment_costs={}
        )
    )
    
    repository.create(truck)
    repository.create(van)
    
    # Test filtering by type
    trucks = repository.get_by_type("truck")
    assert len(trucks) == 1
    assert trucks[0].specifications.vehicle_type == "truck"
    
    vans = repository.get_by_type("van")
    assert len(vans) == 1
    assert vans[0].specifications.vehicle_type == "van"
    
    # Test non-existent type
    assert len(repository.get_by_type("non-existent")) == 0


def test_get_active(repository, vehicle, vehicle_spec):
    """Test getting active vehicles."""
    # Create active and inactive vehicles
    active_vehicle = vehicle
    inactive_vehicle = Vehicle(id=uuid4(), specifications=vehicle_spec)
    
    repository.create(active_vehicle)
    repository.create(inactive_vehicle)
    
    # Deactivate one vehicle by setting is_active=False
    repository._session.query(VehicleModel).filter(
        VehicleModel.id == str(inactive_vehicle.id)
    ).update({"is_active": False})
    repository._session.commit()
    
    # Test getting only active vehicles
    active_vehicles = repository.get_active()
    assert len(active_vehicles) == 1
    assert active_vehicles[0].id == active_vehicle.id
