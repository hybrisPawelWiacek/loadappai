"""Cost settings service implementation.

This module implements the cost settings service interface.
It provides functionality for:
- Managing cost settings
- Version control
- Settings validation
- Default values
"""
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Union
from uuid import UUID

from src.domain.entities.cost import CostSettings, CostSettingsVersion
from src.domain.interfaces.repositories.cost_settings_repository import (
    CostSettingsRepository
)
from src.domain.interfaces.services.cost_settings_service import (
    CostSettingsService
)
from src.domain.services.common.base import BaseService
from src.domain.value_objects import CountrySettings

class CostSettingsServiceImpl(BaseService, CostSettingsService):
    """Service for managing cost settings.
    
    This service is responsible for:
    - Creating and updating cost settings
    - Managing settings versions
    - Validating settings
    - Providing default values
    """
    
    def __init__(self, repository: CostSettingsRepository):
        """Initialize cost settings service.
        
        Args:
            repository: Repository for cost settings persistence
        """
        super().__init__()
        self.repository = repository
    
    def create_settings(
        self,
        name: str,
        description: Optional[str] = None,
        country_settings: Optional[Dict[str, CountrySettings]] = None,
        default_fuel_consumption: Optional[float] = None,
        default_maintenance_rate: Optional[float] = None,
        overhead_rate: Optional[float] = None,
        metadata: Optional[Dict] = None
    ) -> CostSettings:
        """Create new cost settings.
        
        Args:
            name: Settings name
            description: Optional description
            country_settings: Optional country-specific settings
            default_fuel_consumption: Optional default fuel consumption
            default_maintenance_rate: Optional default maintenance rate
            overhead_rate: Optional overhead rate
            metadata: Optional metadata
            
        Returns:
            Created settings
            
        Raises:
            ValueError: If settings are invalid
        """
        self._log_entry(
            "create_settings",
            name=name,
            description=description
        )
        
        try:
            # Create settings object
            settings = CostSettings(
                name=name,
                description=description or "",
                country_settings=country_settings or {},
                default_fuel_consumption=(
                    default_fuel_consumption or
                    self._get_default_fuel_consumption()
                ),
                default_maintenance_rate=(
                    default_maintenance_rate or
                    self._get_default_maintenance_rate()
                ),
                overhead_rate=overhead_rate or self._get_default_overhead_rate(),
                metadata=metadata or {},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Validate settings
            self._validate_settings(settings)
            
            # Save settings
            settings = self.repository.create(settings)
            
            # Create initial version
            version = CostSettingsVersion(
                settings_id=settings.id,
                version=1,
                data=settings.dict(),
                created_at=datetime.utcnow(),
                metadata={
                    "action": "create",
                    "user": "system"
                }
            )
            self.repository.create_version(version)
            
            self._log_exit("create_settings", settings)
            return settings
            
        except Exception as e:
            self._log_error("create_settings", e)
            raise ValueError(f"Failed to create settings: {str(e)}")
    
    def update_settings(
        self,
        settings_id: UUID,
        updates: Dict[str, any]
    ) -> CostSettings:
        """Update existing cost settings.
        
        Args:
            settings_id: ID of settings to update
            updates: Dictionary of updates
            
        Returns:
            Updated settings
            
        Raises:
            ValueError: If settings are invalid
        """
        self._log_entry(
            "update_settings",
            settings_id=settings_id,
            updates=updates
        )
        
        try:
            # Get current settings
            settings = self.repository.get_by_id(settings_id)
            if not settings:
                raise ValueError(f"Settings not found: {settings_id}")
            
            # Create new version
            current_version = self.repository.get_latest_version(settings_id)
            new_version = current_version.version + 1 if current_version else 1
            
            # Update settings
            for key, value in updates.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)
            
            settings.updated_at = datetime.utcnow()
            
            # Validate updated settings
            self._validate_settings(settings)
            
            # Save settings
            settings = self.repository.update(settings)
            
            # Create version
            version = CostSettingsVersion(
                settings_id=settings.id,
                version=new_version,
                data=settings.dict(),
                created_at=datetime.utcnow(),
                metadata={
                    "action": "update",
                    "user": "system",
                    "changes": updates
                }
            )
            self.repository.create_version(version)
            
            self._log_exit("update_settings", settings)
            return settings
            
        except Exception as e:
            self._log_error("update_settings", e)
            raise ValueError(f"Failed to update settings: {str(e)}")
    
    def get_settings(
        self,
        settings_id: UUID,
        version: Optional[int] = None
    ) -> CostSettings:
        """Get cost settings by ID and optional version.
        
        Args:
            settings_id: Settings ID
            version: Optional version number
            
        Returns:
            Cost settings
            
        Raises:
            ValueError: If settings not found
        """
        self._log_entry(
            "get_settings",
            settings_id=settings_id,
            version=version
        )
        
        try:
            if version:
                # Get specific version
                version_obj = self.repository.get_version(settings_id, version)
                if not version_obj:
                    raise ValueError(
                        f"Version {version} not found for settings {settings_id}"
                    )
                settings = CostSettings(**version_obj.data)
            else:
                # Get current settings
                settings = self.repository.get_by_id(settings_id)
                if not settings:
                    raise ValueError(f"Settings not found: {settings_id}")
            
            self._log_exit("get_settings", settings)
            return settings
            
        except Exception as e:
            self._log_error("get_settings", e)
            raise ValueError(f"Failed to get settings: {str(e)}")
    
    def get_current_settings(self) -> CostSettings:
        """Get current active cost settings.
        
        Returns:
            Current cost settings
            
        Raises:
            ValueError: If no settings found
        """
        self._log_entry("get_current_settings")
        
        try:
            # Get current settings
            settings = self.repository.get_current()
            if not settings:
                # Create default settings
                settings = self.create_settings(
                    name="Default Settings",
                    description="Auto-generated default settings"
                )
            
            self._log_exit("get_current_settings", settings)
            return settings
            
        except Exception as e:
            self._log_error("get_current_settings", e)
            raise ValueError(f"Failed to get current settings: {str(e)}")
    
    def _validate_settings(self, settings: CostSettings) -> None:
        """Validate cost settings.
        
        Args:
            settings: Settings to validate
            
        Raises:
            ValueError: If settings are invalid
        """
        # Validate name
        if not settings.name:
            raise ValueError("Settings name is required")
        
        # Validate rates
        if settings.default_fuel_consumption <= 0:
            raise ValueError("Default fuel consumption must be positive")
        if settings.default_maintenance_rate <= 0:
            raise ValueError("Default maintenance rate must be positive")
        if settings.overhead_rate < 0:
            raise ValueError("Overhead rate cannot be negative")
        
        # Validate country settings
        for code, country in settings.country_settings.items():
            if len(code) != 2:
                raise ValueError(f"Invalid country code: {code}")
            
            if country.fuel_price <= 0:
                raise ValueError(
                    f"Fuel price must be positive for country: {code}"
                )
            if country.toll_rate < 0:
                raise ValueError(
                    f"Toll rate cannot be negative for country: {code}"
                )
            if country.driver_rate <= 0:
                raise ValueError(
                    f"Driver rate must be positive for country: {code}"
                )
    
    def _get_default_fuel_consumption(self) -> float:
        """Get default fuel consumption rate.
        
        Returns:
            Default fuel consumption in L/km
        """
        return 0.35  # Typical truck consumption
    
    def _get_default_maintenance_rate(self) -> float:
        """Get default maintenance rate.
        
        Returns:
            Default maintenance rate per km
        """
        return 0.15  # Typical maintenance cost per km
    
    def _get_default_overhead_rate(self) -> float:
        """Get default overhead rate.
        
        Returns:
            Default overhead rate per hour
        """
        return 25.0  # Typical overhead cost per hour
