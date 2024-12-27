"""Tests for the cost repository implementation."""

import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict

import pytest
from sqlalchemy.orm import Session

from src.domain.entities.cost import Cost, CostBreakdown
from src.domain.interfaces.exceptions.repository_errors import EntityNotFoundError, ValidationError
from src.infrastructure.database import Database
from src.infrastructure.repositories.cost_repository import CostRepository


@pytest.fixture
def repository(test_db: Database) -> CostRepository:
    """Create a cost repository instance."""
    return CostRepository(test_db)


@pytest.fixture
def sample_cost() -> Cost:
    """Create a sample cost entity."""
    route_id = uuid.uuid4()
    breakdown = CostBreakdown(
        route_id=route_id,
        fuel_costs={'DE': Decimal('100.00')},
        toll_costs={'DE': Decimal('50.00')},
        driver_costs={'DE': Decimal('75.00')},
        maintenance_costs={'truck': Decimal('25.00')}
    )
    return Cost(
        route_id=route_id,
        breakdown=breakdown,
        calculated_at=datetime.utcnow(),
        metadata={"currency": "EUR"},
        version="2.0",
        is_final=False,
        calculation_method="standard"
    )


@pytest.fixture
def cleanup_database(repository: CostRepository):
    """Clean up the database after each test."""
    yield
    with repository.db.session() as session:
        session.query(repository.model).delete()
        session.commit()


def test_create(repository: CostRepository, sample_cost: Cost, cleanup_database):
    """Test creating a new cost entity."""
    created = repository.create(sample_cost)
    assert created.id is not None
    assert created.route_id == sample_cost.route_id
    assert created.total() == sample_cost.total()


def test_get(repository: CostRepository, sample_cost: Cost, cleanup_database):
    """Test getting a cost entity by ID."""
    created = repository.create(sample_cost)
    retrieved = repository.get(created.id)
    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.route_id == created.route_id
    assert retrieved.total() == created.total()


def test_get_nonexistent_cost(repository: CostRepository, cleanup_database):
    """Test getting a nonexistent cost entity."""
    nonexistent_id = uuid.uuid4()
    result = repository.get(nonexistent_id)
    assert result is None


def test_update(repository: CostRepository, sample_cost: Cost, cleanup_database):
    """Test updating a cost entity."""
    created = repository.create(sample_cost)
    created.metadata = {"currency": "USD"}
    updated = repository.update(created.id, created)
    assert updated is not None
    assert updated.metadata.get("currency") == "USD"


def test_update_nonexistent_cost(repository: CostRepository, sample_cost: Cost, cleanup_database):
    """Test updating a nonexistent cost entity."""
    nonexistent_id = uuid.uuid4()
    result = repository.update(nonexistent_id, sample_cost)
    assert result is None


def test_delete(repository: CostRepository, sample_cost: Cost, cleanup_database):
    """Test deleting a cost entity."""
    created = repository.create(sample_cost)
    assert repository.delete(created.id) is True
    assert repository.get(created.id) is None


def test_delete_nonexistent_cost(repository: CostRepository, cleanup_database):
    """Test deleting a nonexistent cost entity."""
    nonexistent_id = uuid.uuid4()
    assert repository.delete(nonexistent_id) is False


def test_get_all(repository: CostRepository, sample_cost: Cost, cleanup_database):
    """Test getting all cost entities."""
    repository.create(sample_cost)
    costs = repository.get_all()
    assert len(costs) == 1
    assert costs[0].route_id == sample_cost.route_id


def test_get_latest_for_route(repository: CostRepository, sample_cost: Cost, cleanup_database):
    """Test getting the latest cost for a route."""
    created = repository.create(sample_cost)
    latest = repository.get_latest_for_route(created.route_id)
    assert latest is not None
    assert latest.id == created.id


def test_get_by_route_id(repository: CostRepository, sample_cost: Cost, cleanup_database):
    """Test getting costs by route ID."""
    created = repository.create(sample_cost)
    costs = repository.get_by_route_id(created.route_id)
    assert len(costs) == 1
    assert costs[0].id == created.id


def test_get_by_route_id_not_found(repository: CostRepository, cleanup_database):
    """Test getting costs for a nonexistent route ID."""
    nonexistent_id = uuid.uuid4()
    with pytest.raises(Exception):
        repository.get_by_route_id(nonexistent_id)


def test_save_with_breakdown(repository: CostRepository, sample_cost: Cost, cleanup_database):
    """Test saving a cost with detailed breakdown."""
    breakdown = {
        'fuel_costs': {'DE': Decimal('100.00')},
        'toll_costs': {'DE': Decimal('50.00')},
        'driver_costs': {'DE': Decimal('75.00')},
        'maintenance_costs': {'truck': Decimal('25.00')}
    }
    created = repository.save_with_breakdown(sample_cost, breakdown)
    assert created.id is not None
    assert created.total() > 0
    assert created.breakdown.fuel_costs.get('DE') == Decimal('100.00')
    assert created.breakdown.toll_costs.get('DE') == Decimal('50.00')


def test_get_cost_breakdown(repository: CostRepository, cleanup_database):
    """Test getting cost breakdown."""
    route_id = uuid.uuid4()
    breakdown = CostBreakdown(
        route_id=route_id,
        fuel_costs={'DE': Decimal('100.00')},
        toll_costs={'DE': Decimal('50.00')},
        driver_costs={'DE': Decimal('75.00')},
        maintenance_costs={'truck': Decimal('25.00')}
    )
    cost = Cost(
        route_id=route_id,
        breakdown=breakdown,
        calculated_at=datetime.utcnow(),
        metadata={"currency": "EUR"},
        version="2.0",
        is_final=False,
        calculation_method="standard"
    )
    created = repository.create(cost)
    retrieved = repository.get(created.id)
    assert retrieved is not None
    assert retrieved.breakdown.fuel_costs.get('DE') == Decimal('100.00')
    assert retrieved.breakdown.toll_costs.get('DE') == Decimal('50.00')


def test_get_cost_breakdown_with_serialized_uuids_and_decimals(repository: CostRepository, cleanup_database):
    """Test getting cost breakdown with serialized UUIDs and Decimals."""
    route_id = uuid.uuid4()
    breakdown = CostBreakdown(
        route_id=route_id,
        fuel_costs={'DE': Decimal('100.00')},
        toll_costs={'DE': Decimal('50.00')},
        driver_costs={'DE': Decimal('75.00')},
        maintenance_costs={'truck': Decimal('25.00')}
    )
    cost = Cost(
        route_id=route_id,
        breakdown=breakdown,
        calculated_at=datetime.utcnow(),
        metadata={"currency": "EUR"},
        version="2.0",
        is_final=False,
        calculation_method="standard"
    )
    created = repository.create(cost)
    retrieved = repository.get(created.id)
    assert retrieved is not None
    assert isinstance(retrieved.breakdown.fuel_costs.get('DE'), Decimal)
    assert isinstance(retrieved.breakdown.toll_costs.get('DE'), Decimal)
    assert isinstance(retrieved.breakdown.driver_costs.get('DE'), Decimal)


def test_validate_breakdown_with_missing_fields(repository: CostRepository, cleanup_database):
    """Test validation of breakdown with missing fields."""
    route_id = uuid.uuid4()
    incomplete_breakdown = {
        'fuel_costs': {'DE': Decimal('100.00')}
        # Missing other cost components
    }
    
    # Create a cost with incomplete breakdown
    breakdown = CostBreakdown(route_id=route_id, **incomplete_breakdown)
    cost = Cost(
        route_id=route_id,
        breakdown=breakdown,
        calculated_at=datetime.utcnow(),
        metadata={"currency": "EUR"},
        version="2.0",
        is_final=False,
        calculation_method="standard"
    )
    created = repository.create(cost)
    
    # Verify that missing fields are initialized with default values
    assert created.breakdown.toll_costs == {}
    assert created.breakdown.driver_costs == {}
    assert created.breakdown.maintenance_costs == {}


def test_validate_breakdown_with_invalid_data(repository: CostRepository, cleanup_database):
    """Test validation of breakdown with invalid data types."""
    route_id = uuid.uuid4()
    invalid_breakdown = {
        'route_id': route_id,
        'fuel_costs': {'DE': 'not a decimal'}  # Invalid type for fuel cost
    }
    
    with pytest.raises(ValidationError) as exc_info:
        repository._validate_breakdown(invalid_breakdown)
    assert "value 'not a decimal' in fuel_costs is not a valid decimal number" in str(exc_info.value)

def test_save_with_breakdown_invalid_data(repository: CostRepository, sample_cost: Cost, cleanup_database):
    """Test saving cost with invalid breakdown data."""
    invalid_breakdown = {
        'fuel_costs': {'DE': 'not a decimal'}  # Invalid type for fuel cost
    }
    
    with pytest.raises(ValidationError) as exc_info:
        repository.save_with_breakdown(sample_cost, invalid_breakdown)
    assert "value 'not a decimal' in fuel_costs is not a valid decimal number" in str(exc_info.value)


def test_get_cost_history_not_found_error(repository: CostRepository, cleanup_database):
    """Test getting history for nonexistent cost raises error."""
    nonexistent_id = uuid.uuid4()
    
    with pytest.raises(EntityNotFoundError) as exc_info:
        repository.get_cost_history(nonexistent_id)
    assert f"No history found for cost {nonexistent_id}" in str(exc_info.value)


def test_create_with_empty_metadata(repository: CostRepository, sample_cost: Cost, cleanup_database):
    """Test creating cost with empty metadata."""
    sample_cost.metadata = None
    created = repository.create(sample_cost)
    assert created.metadata == {}
    assert created.id is not None


def test_get_all_pagination(repository: CostRepository, sample_cost: Cost, cleanup_database):
    """Test pagination in get_all method."""
    # Create multiple cost entities
    costs = []
    for _ in range(5):
        cost = Cost(
            route_id=uuid.uuid4(),
            breakdown=sample_cost.breakdown,
            calculated_at=datetime.utcnow(),
            metadata={"currency": "EUR"},
            version="2.0",
            is_final=False,
            calculation_method="standard"
        )
        costs.append(repository.create(cost))

    # Test different pagination scenarios
    all_costs = repository.get_all(skip=0, limit=10)
    assert len(all_costs) == 5

    first_page = repository.get_all(skip=0, limit=2)
    assert len(first_page) == 2

    second_page = repository.get_all(skip=2, limit=2)
    assert len(second_page) == 2

    last_page = repository.get_all(skip=4, limit=2)
    assert len(last_page) == 1


def test_save_with_invalid_breakdown(repository: CostRepository, sample_cost: Cost, cleanup_database):
    """Test saving a cost with invalid breakdown."""
    invalid_breakdown = "not a dictionary"
    with pytest.raises(ValidationError) as exc_info:
        repository.save_with_breakdown(sample_cost, invalid_breakdown)
    assert "Invalid breakdown format" in str(exc_info.value)


def test_get_cost_history(repository: CostRepository, sample_cost: Cost, cleanup_database):
    """Test getting cost history."""
    created = repository.create(sample_cost)
    history = repository.get_cost_history(created.id)
    assert len(history) == 1
    assert history[0].id == created.id


def test_get_cost_history_not_found(repository: CostRepository, cleanup_database):
    """Test getting history for a nonexistent cost."""
    nonexistent_id = uuid.uuid4()
    with pytest.raises(EntityNotFoundError) as exc_info:
        repository.get_cost_history(nonexistent_id)
    assert f"No history found for cost {nonexistent_id}" in str(exc_info.value)


def test_cost_entity_conversion(repository: CostRepository, sample_cost: Cost, cleanup_database):
    """Test converting between domain entity and database model."""
    created = repository.create(sample_cost)
    assert created is not None
    assert isinstance(created, Cost)
    assert created.route_id == sample_cost.route_id
    assert created.breakdown is not None
    assert created.total() == sample_cost.total()


def test_create_cost_with_serialized_uuids_and_decimals(repository: CostRepository, cleanup_database):
    """Test creating a cost with serialized UUIDs and Decimals."""
    route_id = uuid.uuid4()
    breakdown = CostBreakdown(
        route_id=route_id,
        fuel_costs={'DE': Decimal('100.00')},
        toll_costs={'DE': Decimal('50.00')},
        driver_costs={'DE': Decimal('75.00')},
        maintenance_costs={'truck': Decimal('25.00')}
    )
    cost = Cost(
        route_id=route_id,
        breakdown=breakdown,
        calculated_at=datetime.utcnow(),
        metadata={"route_id": str(route_id), "amount": float(Decimal('250.00'))},
        version="2.0",
        is_final=False,
        calculation_method="standard"
    )
    created = repository.create(cost)
    assert created is not None
    assert isinstance(created.metadata.get("route_id"), str)
    assert isinstance(created.metadata.get("amount"), float)


def test_update_cost_with_serialized_uuids_and_decimals(repository: CostRepository, cleanup_database):
    """Test updating a cost with serialized UUIDs and Decimals."""
    route_id = uuid.uuid4()
    breakdown = CostBreakdown(
        route_id=route_id,
        fuel_costs={'DE': Decimal('100.00')},
        toll_costs={'DE': Decimal('50.00')},
        driver_costs={'DE': Decimal('75.00')},
        maintenance_costs={'truck': Decimal('25.00')}
    )
    cost = Cost(
        route_id=route_id,
        breakdown=breakdown,
        calculated_at=datetime.utcnow(),
        metadata={"route_id": str(route_id), "amount": float(Decimal('250.00'))},
        version="2.0",
        is_final=False,
        calculation_method="standard"
    )
    created = repository.create(cost)
    created.metadata = {"route_id": str(route_id), "amount": float(Decimal('300.00'))}
    updated = repository.update(created.id, created)
    assert updated is not None
    assert isinstance(updated.metadata.get("route_id"), str)
    assert isinstance(updated.metadata.get("amount"), float)
    assert updated.metadata.get("amount") == 300.0
