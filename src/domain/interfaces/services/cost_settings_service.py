"""Cost settings service interface.

This module defines the interface for managing cost settings.
The CostSettingsService interface provides methods for:
- Managing cost calculation settings
- Version control of settings
- Settings validation
- History tracking

Implementation Requirements:
1. Settings Management:
   - Must handle settings lifecycle
   - Should track versions
   - Must validate changes
   - Should maintain defaults

2. Version Control:
   - Must use semantic versioning
   - Should track all changes
   - Must prevent conflicts
   - Should handle rollbacks

3. Validation:
   - Must verify all values
   - Should check constraints
   - Must ensure consistency
   - Should prevent invalid states

4. History:
   - Must track all changes
   - Should store reasons
   - Must maintain audit trail
   - Should handle versions

Example Usage:
    ```python
    # Get current settings
    settings = service.get_current_settings()
    
    # Update settings
    new_settings = CostSettings(
        base_rate=Decimal("2.50"),
        per_km_rate=Decimal("1.75")
    )
    updated = service.update_settings(
        new_settings,
        "Updated rates for Q1 2024"
    )
    
    # View history
    history = service.get_settings_history()
    ```
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from uuid import UUID

from src.domain.entities.cost import CostSettings
from src.domain.interfaces.exceptions.service_errors import ServiceError

class CostSettingsServiceError(ServiceError):
    """Exception raised for errors in the cost settings service.
    
    This includes:
    - Invalid settings values
    - Version conflicts
    - Validation failures
    - History tracking errors
    """
    pass

class CostSettingsService(ABC):
    """Interface for cost settings management.
    
    This interface defines the contract for managing cost calculation
    settings, including versioning, validation, and history tracking.
    """

    @abstractmethod
    def get_current_settings(self) -> CostSettings:
        """Get current active settings.
        
        Returns:
            Current settings configuration
            
        Raises:
            CostSettingsServiceError: If settings retrieval fails
            
        Implementation Notes:
            - Must return latest version
            - Should cache results
            - Must never return None
            - Should load all relations
        """
        pass

    @abstractmethod
    def update_settings(
        self,
        settings: CostSettings,
        reason: str
    ) -> CostSettings:
        """Update cost settings.
        
        Args:
            settings: New settings configuration
            reason: Reason for the update
            
        Returns:
            Updated settings
            
        Raises:
            CostSettingsServiceError: If update fails
            
        Implementation Notes:
            - Must validate all values
            - Should increment version
            - Must track changes
            - Should notify listeners
        """
        pass

    @abstractmethod
    def validate_settings(
        self,
        settings: CostSettings
    ) -> bool:
        """Validate settings configuration.
        
        Args:
            settings: Settings to validate
            
        Returns:
            True if settings are valid
            
        Raises:
            CostSettingsServiceError: If validation fails
            
        Implementation Notes:
            - Must check all fields
            - Should verify constraints
            - Must ensure consistency
            - Should explain failures
        """
        pass

    @abstractmethod
    def get_settings_history(self) -> List[Dict]:
        """Get history of settings changes.
        
        Returns:
            List of historical changes
            
        Raises:
            CostSettingsServiceError: If history retrieval fails
            
        Implementation Notes:
            - Must track all changes
            - Should include metadata
            - Must maintain audit trail
            - Should handle versions
        """
        pass

    @abstractmethod
    def get_settings_version(
        self,
        version: str
    ) -> Optional[CostSettings]:
        """Get settings by version.
        
        Args:
            version: Settings version
            
        Returns:
            Settings if found, None otherwise
            
        Raises:
            CostSettingsServiceError: If version retrieval fails
            
        Implementation Notes:
            - Must validate version format
            - Should handle partial versions
            - Must track access
            - Should cache results
        """
        pass

    @abstractmethod
    def get_defaults(self) -> CostSettings:
        """Get default settings configuration.
        
        Returns:
            Default settings
            
        Raises:
            CostSettingsServiceError: If defaults retrieval fails
            
        Implementation Notes:
            - Must provide sensible values
            - Should document choices
            - Must be consistent
            - Should cache results
        """
        pass
