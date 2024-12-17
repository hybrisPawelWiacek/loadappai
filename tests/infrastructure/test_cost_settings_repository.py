"""Tests for the cost settings repository."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from src.domain.entities import CostSettings as CostSettingsEntity
from src.infrastructure.models import CostSettings as CostSettingsModel
from src.infrastructure.repositories.cost_settings_repository import CostSettingsRepository


@pytest.fixture
def cost_settings_repository(db_session: Session):
    """Create a cost settings repository instance."""
    return CostSettingsRepository(db_session)


@pytest.fixture
def valid_cost_settings_entity():
    """Create a valid cost settings entity."""
    return CostSettingsEntity(
        id=str(uuid4()),
        fuel_price_per_liter=Decimal("1.85"),
        driver_daily_salary=Decimal("200.00"),
        toll_rates={
            "DE": Decimal("0.20"),
            "FR": Decimal("0.15"),
            "PL": Decimal("0.10")
        },
        overheads={
            "maintenance": Decimal("0.05"),
            "insurance": Decimal("0.03")
        },
        cargo_factors={
            "standard": Decimal("1.0"),
            "hazmat": Decimal("1.5"),
            "refrigerated": Decimal("1.3")
        },
        last_modified=datetime.now(timezone.utc),
        metadata={"version": "1.0"}
    )


def test_create_cost_settings(
    cost_settings_repository: CostSettingsRepository,
    valid_cost_settings_entity: CostSettingsEntity
):
    """Test creating new cost settings."""
    created_settings = cost_settings_repository.create(valid_cost_settings_entity)
    assert created_settings.id == valid_cost_settings_entity.id
    assert created_settings.fuel_price_per_liter == valid_cost_settings_entity.fuel_price_per_liter
    assert created_settings.toll_rates == valid_cost_settings_entity.toll_rates
    assert created_settings.metadata == valid_cost_settings_entity.metadata


def test_get_cost_settings(
    cost_settings_repository: CostSettingsRepository,
    valid_cost_settings_entity: CostSettingsEntity
):
    """Test getting cost settings by ID."""
    created_settings = cost_settings_repository.create(valid_cost_settings_entity)
    retrieved_settings = cost_settings_repository.get(str(created_settings.id))
    assert retrieved_settings is not None
    assert str(retrieved_settings.id) == str(created_settings.id)
    assert retrieved_settings.cargo_factors == valid_cost_settings_entity.cargo_factors


def test_get_nonexistent_cost_settings(cost_settings_repository: CostSettingsRepository):
    """Test getting nonexistent cost settings."""
    settings = cost_settings_repository.get(str(uuid4()))
    assert settings is None


def test_update_cost_settings(
    cost_settings_repository: CostSettingsRepository,
    valid_cost_settings_entity: CostSettingsEntity
):
    """Test updating cost settings."""
    created_settings = cost_settings_repository.create(valid_cost_settings_entity)
    created_settings.fuel_price_per_liter = Decimal("2.00")
    created_settings.toll_rates["DE"] = Decimal("0.25")
    updated_settings = cost_settings_repository.update(str(created_settings.id), created_settings)
    assert updated_settings is not None
    assert updated_settings.fuel_price_per_liter == Decimal("2.00")
    assert updated_settings.toll_rates["DE"] == Decimal("0.25")


def test_delete_cost_settings(
    cost_settings_repository: CostSettingsRepository,
    valid_cost_settings_entity: CostSettingsEntity
):
    """Test deleting cost settings."""
    created_settings = cost_settings_repository.create(valid_cost_settings_entity)
    assert cost_settings_repository.delete(str(created_settings.id)) is True
    assert cost_settings_repository.get(str(created_settings.id)) is None


def test_get_latest_cost_settings(
    cost_settings_repository: CostSettingsRepository,
    valid_cost_settings_entity: CostSettingsEntity
):
    """Test getting the latest cost settings."""
    # Create first settings
    first_settings = valid_cost_settings_entity
    first_settings.last_modified = datetime.now(timezone.utc) - timedelta(days=1)
    cost_settings_repository.create(first_settings)

    # Create second settings with later timestamp
    second_settings = valid_cost_settings_entity.model_copy()
    second_settings.id = str(uuid4())
    second_settings.last_modified = datetime.now(timezone.utc)
    second_settings.fuel_price_per_liter = Decimal("2.10")
    cost_settings_repository.create(second_settings)

    latest_settings = cost_settings_repository.get_latest()
    assert latest_settings is not None
    assert latest_settings.fuel_price_per_liter == Decimal("2.10")


def test_get_by_date(
    cost_settings_repository: CostSettingsRepository,
    valid_cost_settings_entity: CostSettingsEntity
):
    """Test getting cost settings valid at a specific date."""
    # Create settings with different timestamps
    first_settings = valid_cost_settings_entity
    first_settings.last_modified = datetime.now(timezone.utc) - timedelta(days=2)
    first_settings.fuel_price_per_liter = Decimal("1.85")
    cost_settings_repository.create(first_settings)

    second_settings = valid_cost_settings_entity.model_copy()
    second_settings.id = str(uuid4())
    second_settings.last_modified = datetime.now(timezone.utc) - timedelta(days=1)
    second_settings.fuel_price_per_liter = Decimal("2.00")
    cost_settings_repository.create(second_settings)

    # Test getting settings at different points in time
    query_date = datetime.now(timezone.utc) - timedelta(days=1, hours=12)
    settings = cost_settings_repository.get_by_date(query_date)
    assert settings is not None
    assert settings.fuel_price_per_liter == Decimal("1.85")

    query_date = datetime.now(timezone.utc)
    settings = cost_settings_repository.get_by_date(query_date)
    assert settings is not None
    assert settings.fuel_price_per_liter == Decimal("2.00")
