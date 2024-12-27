"""Tests for cost settings repository implementation."""
import pytest
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from src.domain.entities.cost import CostSettings, CostSettingsVersion
from src.domain.interfaces.exceptions.repository_errors import ValidationError
from src.infrastructure.database import Database
from src.infrastructure.repositories.cost_settings_repository import CostSettingsRepository
from src.infrastructure.models import CostSettings as CostSettingsModel


@pytest.fixture
def cost_settings():
    """Create test cost settings."""
    return CostSettings(
        id=uuid4(),
        route_id=uuid4(),
        fuel_rates={
            "DE": Decimal("1.50"),
            "FR": Decimal("1.60"),
            "IT": Decimal("1.70")
        },
        toll_rates={
            "DE": {"truck": Decimal("0.20")},
            "FR": {"truck": Decimal("0.25")},
            "IT": {"truck": Decimal("0.30")}
        },
        driver_rates={
            "DE": Decimal("35.00"),
            "FR": Decimal("40.00"),
            "IT": Decimal("38.00")
        },
        overhead_rates={
            "admin": Decimal("100.00"),
            "insurance": Decimal("50.00")
        },
        maintenance_rates={
            "truck": Decimal("0.15"),
            "van": Decimal("0.10")
        },
        enabled_components={"fuel", "toll", "driver"},
        version=CostSettingsVersion.V1_0,
        created_by="test_user",
        modified_by="test_user"
    )


@pytest.fixture
def repository(test_db):
    """Create test repository."""
    return CostSettingsRepository(test_db)


def test_get_by_route_id(repository, cost_settings):
    """Test getting cost settings by route ID."""
    # Save settings first
    saved = repository.save(cost_settings)
    
    # Test retrieving
    retrieved = repository.get_by_route_id(cost_settings.route_id)
    assert retrieved is not None
    assert retrieved.id == saved.id
    assert retrieved.route_id == saved.route_id
    assert retrieved.fuel_rates == saved.fuel_rates
    assert retrieved.toll_rates == saved.toll_rates
    assert retrieved.driver_rates == saved.driver_rates
    assert retrieved.overhead_rates == saved.overhead_rates
    assert retrieved.maintenance_rates == saved.maintenance_rates
    assert retrieved.enabled_components == saved.enabled_components
    assert retrieved.version == saved.version
    
    # Test getting non-existent settings
    assert repository.get_by_route_id(UUID('00000000-0000-0000-0000-000000000000')) is None


def test_save(repository, cost_settings):
    """Test saving cost settings."""
    # Test initial save
    saved = repository.save(cost_settings)
    assert saved.id == cost_settings.id
    assert saved.route_id == cost_settings.route_id
    assert saved.version == cost_settings.version
    
    # Test updating existing settings
    updated_settings = cost_settings.model_copy()
    updated_settings.id = uuid4()  # Generate new ID for update
    updated_settings.fuel_rates["DE"] = Decimal("1.55")
    updated_settings.version = CostSettingsVersion.V2_0
    
    updated = repository.save(updated_settings)
    assert updated.fuel_rates["DE"] == Decimal("1.55")
    assert updated.version == CostSettingsVersion.V2_0


def test_get_history(repository, cost_settings):
    """Test getting cost settings history."""
    # Create multiple versions
    v1 = repository.save(cost_settings)
    
    v2 = cost_settings.model_copy()
    v2.id = uuid4()  # Generate new ID for v2
    v2.version = CostSettingsVersion.V2_0
    v2.fuel_rates["DE"] = Decimal("1.55")
    v2 = repository.save(v2)
    
    v3 = cost_settings.model_copy()
    v3.id = uuid4()  # Generate new ID for v3
    v3.version = CostSettingsVersion.V3_0
    v3.fuel_rates["DE"] = Decimal("1.60")
    v3 = repository.save(v3)
    
    # Get history
    history = repository.get_history(cost_settings.route_id)
    assert len(history) == 3
    assert history[0].version == CostSettingsVersion.V3_0  # Most recent first
    assert history[1].version == CostSettingsVersion.V2_0
    assert history[2].version == CostSettingsVersion.V1_0


def test_get_defaults(repository):
    """Test getting default cost settings."""
    route_id = uuid4()
    defaults = repository.get_defaults(route_id)
    assert isinstance(defaults, CostSettings)
    assert defaults.route_id == route_id
    assert defaults.version == CostSettingsVersion.V1_0
    assert "fuel" in defaults.enabled_components
    assert "toll" in defaults.enabled_components
    assert "driver" in defaults.enabled_components


def test_get_by_version(repository, cost_settings):
    """Test getting cost settings by version."""
    # Create multiple versions
    v1 = repository.save(cost_settings)  # V1_0
    
    v2_settings = cost_settings.model_copy()
    v2_settings.id = uuid4()  # Generate new ID for v2
    v2_settings.version = CostSettingsVersion.V2_0
    v2_settings.fuel_rates["DE"] = Decimal("1.55")
    v2 = repository.save(v2_settings)
    
    # Test retrieving specific versions
    v1_retrieved = repository.get_by_version(cost_settings.route_id, CostSettingsVersion.V1_0)
    assert v1_retrieved is not None
    assert v1_retrieved.version == CostSettingsVersion.V1_0
    assert v1_retrieved.fuel_rates["DE"] == Decimal("1.50")
    
    v2_retrieved = repository.get_by_version(cost_settings.route_id, CostSettingsVersion.V2_0)
    assert v2_retrieved is not None
    assert v2_retrieved.version == CostSettingsVersion.V2_0
    assert v2_retrieved.fuel_rates["DE"] == Decimal("1.55")
    
    # Test getting non-existent version
    assert repository.get_by_version(cost_settings.route_id, CostSettingsVersion.V3_0) is None


def test_validate(repository, cost_settings):
    """Test settings validation."""
    # Test valid settings
    assert repository.validate(cost_settings) is True
    
    # Test invalid settings
    invalid_settings = cost_settings.model_copy()
    invalid_settings.enabled_components = set()  # Empty components
    with pytest.raises(ValidationError):
        repository.validate(invalid_settings)
    
    invalid_settings = cost_settings.model_copy()
    invalid_settings.fuel_rates = {}  # Empty fuel rates with fuel enabled
    with pytest.raises(ValidationError):
        repository.validate(invalid_settings)


def test_get_current(repository, cost_settings):
    """Test getting current active settings."""
    # Save new settings
    saved = repository.save(cost_settings)
    
    # Should return latest settings
    current = repository.get_current(cost_settings.route_id)
    assert current is not None
    assert current.id == saved.id
    assert current.version == saved.version


def test_count(repository, cost_settings):
    """Test counting settings records."""
    initial_count = repository.count(cost_settings.route_id)
    
    # Add some settings
    repository.save(cost_settings)
    
    v2 = cost_settings.model_copy()
    v2.id = uuid4()  # Generate new ID for v2
    v2.version = CostSettingsVersion.V2_0
    repository.save(v2)
    
    # Check count increased
    final_count = repository.count(cost_settings.route_id)
    assert final_count == initial_count + 2
