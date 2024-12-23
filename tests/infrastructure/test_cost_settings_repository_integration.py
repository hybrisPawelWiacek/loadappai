"""Integration tests for the enhanced cost settings repository."""
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from src.domain.entities import (
    CostSettings as CostSettingsEntity,
    TransportSettings as TransportSettingsEntity,
    SystemSettings as SystemSettingsEntity,
    CostHistoryEntry as CostHistoryEntryEntity
)
from src.infrastructure.repositories.cost_settings_repository import CostSettingsRepository
from src.infrastructure.database import Database


@pytest.fixture
def cost_settings_repository(test_db: Database):
    """Create a cost settings repository instance."""
    return CostSettingsRepository(test_db)


@pytest.fixture
def valid_cost_settings():
    """Create valid cost settings."""
    return CostSettingsEntity(
        id=str(uuid4()),
        # Per-country base rates
        fuel_prices={
            "DE": Decimal("1.85"),
            "FR": Decimal("1.90"),
            "PL": Decimal("1.70")
        },
        toll_rates={
            "DE": Decimal("0.20"),
            "FR": Decimal("0.15"),
            "PL": Decimal("0.10")
        },
        driver_rates={
            "DE": Decimal("250.00"),
            "FR": Decimal("230.00"),
            "PL": Decimal("180.00")
        },
        
        # Time-based cost rates
        rest_period_rate=Decimal("30.00"),
        loading_unloading_rate=Decimal("45.00"),
        
        # Vehicle-related costs
        maintenance_rate_per_km=Decimal("0.15"),
        
        # Factors for empty driving
        empty_driving_factors={
            "distance": Decimal("0.8"),
            "time": Decimal("0.7"),
            "fuel": Decimal("0.9")
        },
        
        # Cargo-specific factors
        cargo_factors={
            "standard": {
                "weight": Decimal("1.0"),
                "volume": Decimal("1.0"),
                "handling": Decimal("1.0")
            },
            "refrigerated": {
                "weight": Decimal("1.2"),
                "volume": Decimal("1.2"),
                "handling": Decimal("1.3")
            },
            "hazmat": {
                "weight": Decimal("1.5"),
                "volume": Decimal("1.5"),
                "handling": Decimal("2.0")
            }
        },
        
        # Overhead rates
        overhead_rates={
            "admin": Decimal("50.00"),
            "insurance": Decimal("100.00"),
            "misc": Decimal("30.00")
        },
        
        # Version control
        version="1.0",
        is_active=True,
        last_modified=datetime.now(timezone.utc),
        
        # Additional metadata
        metadata={"source": "test"}
    )


@pytest.fixture
def valid_transport_settings():
    """Create valid transport settings."""
    return TransportSettingsEntity(
        id=str(uuid4()),
        vehicle_types=["standard", "refrigerated", "hazmat"],
        equipment_types=["gps", "temperature_control", "hazmat_equipment"],
        cargo_types=["standard", "refrigerated", "hazmat"],
        loading_time_minutes=45,
        unloading_time_minutes=30,
        max_driving_hours=9.0,
        required_rest_hours=11.0,
        max_working_days=5,
        speed_limits={
            "urban": 50,
            "rural": 90,
            "highway": 130
        },
        is_active=True,
        last_modified=datetime.now(timezone.utc)
    )


@pytest.fixture
def valid_system_settings():
    """Create valid system settings."""
    return SystemSettingsEntity(
        id=str(uuid4()),
        api_url="https://api.loadapp.ai",
        api_version="v1",
        request_timeout_seconds=30,
        default_currency="EUR",
        default_language="en",
        enable_cost_history=True,
        enable_route_optimization=True,
        enable_real_time_tracking=False,
        maps_provider="google",
        geocoding_provider="google",
        min_margin_percent=Decimal("5.0"),
        max_margin_percent=Decimal("20.0"),
        price_rounding_decimals=2,
        max_route_duration=timedelta(days=5),
        is_active=True,
        last_modified=datetime.now(timezone.utc)
    )


@pytest.fixture
def valid_cost_history_entry(valid_cost_settings):
    """Create a valid cost history entry."""
    return CostHistoryEntryEntity(
        id=str(uuid4()),
        route_id=str(uuid4()),
        calculation_date=datetime.now(timezone.utc),
        total_cost=Decimal("1500.00"),
        currency="EUR",
        calculation_method="standard",
        version="1.0",
        is_final=True,
        cost_components={
            "fuel": Decimal("500.00"),
            "toll": Decimal("200.00"),
            "driver": Decimal("600.00"),
            "maintenance": Decimal("200.00")
        },
        settings_snapshot=valid_cost_settings.model_dump()
    )


def test_get_current_settings_creates_default_if_none_exist(cost_settings_repository):
    """Test that get_current creates default settings if none exist."""
    settings = cost_settings_repository.get_current_cost_settings()
    assert settings is not None
    assert isinstance(settings, CostSettingsEntity)


def test_update_settings_creates_new_version(cost_settings_repository, valid_cost_settings):
    """Test that updating settings creates a new version."""
    # Create initial settings
    initial = cost_settings_repository.create_cost_settings(valid_cost_settings)
    assert initial is not None
    assert isinstance(initial, CostSettingsEntity)
    
    # Update settings
    valid_cost_settings.fuel_prices["DE"] = Decimal("2.00")
    updated = cost_settings_repository.update_cost_settings(valid_cost_settings)
    assert updated is not None
    assert isinstance(updated, CostSettingsEntity)
    assert updated.fuel_prices["DE"] == Decimal("2.00")


def test_cost_history_tracking(cost_settings_repository, valid_cost_history_entry):
    """Test cost history tracking functionality."""
    # Create history entry
    entry = cost_settings_repository.add_cost_history_entry(valid_cost_history_entry)
    assert entry is not None
    assert isinstance(entry, CostHistoryEntryEntity)
    
    # Get history for route
    history = cost_settings_repository.get_cost_history(valid_cost_history_entry.route_id)
    assert len(history) > 0
    assert isinstance(history[0], CostHistoryEntryEntity)


def test_transport_settings_management(cost_settings_repository, valid_transport_settings):
    """Test transport settings management."""
    # Create transport settings
    initial = cost_settings_repository.create_transport_settings(valid_transport_settings)
    assert initial is not None
    assert isinstance(initial, TransportSettingsEntity)
    
    # Update settings
    valid_transport_settings.max_driving_hours = 10.0
    updated = cost_settings_repository.update_transport_settings(valid_transport_settings)
    assert updated is not None
    assert isinstance(updated, TransportSettingsEntity)
    assert updated.max_driving_hours == 10.0


def test_system_settings_management(cost_settings_repository, valid_system_settings):
    """Test system settings management."""
    # Create system settings
    initial = cost_settings_repository.create_system_settings(valid_system_settings)
    assert initial is not None
    assert isinstance(initial, SystemSettingsEntity)
    
    # Update settings
    valid_system_settings.request_timeout_seconds = 45
    updated = cost_settings_repository.update_system_settings(valid_system_settings)
    assert updated is not None
    assert isinstance(updated, SystemSettingsEntity)
    assert updated.request_timeout_seconds == 45


def test_settings_version_control(cost_settings_repository, valid_cost_settings):
    """Test settings version control functionality."""
    # Create initial version
    v1 = cost_settings_repository.create_cost_settings(valid_cost_settings)
    assert v1 is not None
    assert v1.version == "1.0"
    
    # Create new version
    valid_cost_settings.version = "2.0"
    v2 = cost_settings_repository.create_cost_settings(valid_cost_settings)
    assert v2 is not None
    assert v2.version == "2.0"
    
    # Get specific version
    v1_retrieved = cost_settings_repository.get_cost_settings_by_version("1.0")
    assert v1_retrieved is not None
    assert v1_retrieved.version == "1.0"
    
    v2_retrieved = cost_settings_repository.get_cost_settings_by_version("2.0")
    assert v2_retrieved is not None
    assert v2_retrieved.version == "2.0"


def test_error_scenarios(cost_settings_repository):
    """Test error handling scenarios."""
    # Test getting non-existent version
    non_existent = cost_settings_repository.get_cost_settings_by_version("999.0")
    assert non_existent is None
    
    # Test getting history for non-existent route
    history = cost_settings_repository.get_cost_history(str(uuid4()))
    assert len(history) == 0
