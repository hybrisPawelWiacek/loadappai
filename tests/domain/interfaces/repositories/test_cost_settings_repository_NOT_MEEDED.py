"""Tests for CostSettingsRepository interface contract."""
import pytest
from datetime import datetime
from decimal import Decimal
from typing import Dict
from uuid import uuid4

from src.domain.entities.cost import CostSettings
from src.domain.interfaces.repositories.cost_settings_repository import CostSettingsRepository
from src.domain.interfaces.exceptions.repository_errors import EntityNotFoundError, ValidationError

class MockCostSettingsRepository(CostSettingsRepository):
    """Mock implementation of CostSettingsRepository for testing."""
    
    def __init__(self):
        self.settings = {}
        self.history = []
        self._setup_defaults()
    
    def _setup_defaults(self):
        """Setup default settings."""
        self.defaults = CostSettings(
            id=str(uuid4()),
            version="1.0.0",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            base_rate=Decimal("2.50"),
            per_km_rate=Decimal("1.75"),
            per_hour_rate=Decimal("45.00"),
            minimum_charge=Decimal("50.00"),
            currency="EUR",
            country_multipliers={"DE": 1.0, "FR": 1.1, "IT": 1.2},
            toll_multiplier=Decimal("1.1"),
            weekend_multiplier=Decimal("1.2"),
            night_multiplier=Decimal("1.15"),
            waiting_time_rate=Decimal("35.00"),
            cancellation_fee=Decimal("25.00")
        )
    
    def get_current_settings(self) -> CostSettings:
        if not self.settings:
            return self.defaults
        return max(self.settings.values(), key=lambda x: x.version)
    
    def get_by_version(self, version: str) -> CostSettings:
        for settings in self.settings.values():
            if settings.version == version:
                return settings
        return None
    
    def save_with_history(self, settings: CostSettings, change_reason: str) -> CostSettings:
        if not settings.id:
            settings.id = str(uuid4())
        self.settings[settings.id] = settings
        self.history.append({
            "id": str(uuid4()),
            "settings_id": settings.id,
            "version": settings.version,
            "change_reason": change_reason,
            "changed_at": datetime.now()
        })
        return settings
    
    def get_settings_history(self) -> List[Dict]:
        return self.history
    
    def get_defaults(self) -> CostSettings:
        return self.defaults

def test_get_current_settings_returns_latest_version():
    """Should return settings with highest version number."""
    repo = MockCostSettingsRepository()
    
    # Create settings with different versions
    settings_v1 = repo.defaults.copy()
    settings_v1.version = "1.0.0"
    settings_v2 = repo.defaults.copy() 
    settings_v2.version = "2.0.0"
    
    repo.save_with_history(settings_v1, "Initial version")
    repo.save_with_history(settings_v2, "Updated version")
    
    current = repo.get_current_settings()
    assert current.version == "2.0.0"

def test_get_by_version_returns_correct_settings():
    """Should return settings matching specified version."""
    repo = MockCostSettingsRepository()
    
    settings = repo.defaults.copy()
    settings.version = "1.0.0"
    repo.save_with_history(settings, "Test version")
    
    result = repo.get_by_version("1.0.0")
    assert result is not None
    assert result.version == "1.0.0"

def test_save_with_history_creates_history_entry():
    """Should create history entry when saving settings."""
    repo = MockCostSettingsRepository()
    settings = repo.defaults.copy()
    
    repo.save_with_history(settings, "Test change")
    history = repo.get_settings_history()
    
    assert len(history) == 1
    assert history[0]["change_reason"] == "Test change"
    assert history[0]["version"] == settings.version

def test_get_defaults_returns_valid_settings():
    """Should return valid default settings."""
    repo = MockCostSettingsRepository()
    defaults = repo.get_defaults()
    
    assert isinstance(defaults, CostSettings)
    assert defaults.base_rate > 0
    assert defaults.per_km_rate > 0
    assert defaults.per_hour_rate > 0
