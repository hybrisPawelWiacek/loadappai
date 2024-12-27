"""Cost settings repository interface.

This module defines the interface for cost settings persistence.
The CostSettingsRepository interface provides methods for:
- Managing cost settings entities
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
    settings = repository.get_current()
    
    # Update settings
    new_settings = CostSettings(
        base_rate=Decimal("2.50"),
        per_km_rate=Decimal("1.75")
    )
    updated = repository.save(
        new_settings,
        "Updated rates for Q1 2024"
    )
    
    # View history
    history = repository.get_history()
    ```
"""
from abc import abstractmethod
from typing import Dict, List, Optional
from uuid import UUID

from src.domain.entities.cost import CostSettings
from src.domain.interfaces.repositories.base import Repository
from src.domain.interfaces.exceptions.repository_errors import (
    EntityNotFoundError,
    ValidationError
)

class CostSettingsRepository(Repository[CostSettings]):
    """Interface for cost settings persistence.
    
    This interface defines the contract for cost settings data access
    and management. It extends the base Repository interface with
    settings-specific operations.
    """

    @abstractmethod
    def get_current(self) -> CostSettings:
        """Get current active settings.
        
        Returns:
            Current settings configuration
            
        Raises:
            EntityNotFoundError: If no settings exist
            
        Implementation Notes:
            - Must return latest version
            - Should cache results
            - Must never return None
            - Should load all relations
        """
        pass

    @abstractmethod
    def save(
        self,
        settings: CostSettings,
        reason: str
    ) -> CostSettings:
        """Save new settings version.
        
        Args:
            settings: Settings to save
            reason: Reason for the change
            
        Returns:
            Saved settings
            
        Raises:
            ValidationError: If settings are invalid
            
        Implementation Notes:
            - Must validate all values
            - Should increment version
            - Must track changes
            - Should notify listeners
        """
        pass

    @abstractmethod
    def get_history(self) -> List[Dict]:
        """Get history of settings changes.
        
        Returns:
            List of historical changes
            
        Implementation Notes:
            - Must track all changes
            - Should include metadata
            - Must maintain audit trail
            - Should handle versions
        """
        pass

    @abstractmethod
    def get_version(
        self,
        version: str
    ) -> Optional[CostSettings]:
        """Get settings by version.
        
        Args:
            version: Settings version
            
        Returns:
            Settings if found, None otherwise
            
        Raises:
            ValidationError: If version format is invalid
            
        Implementation Notes:
            - Must validate version format
            - Should handle partial versions
            - Must track access
            - Should cache results
        """
        pass

    @abstractmethod
    def validate(
        self,
        settings: CostSettings
    ) -> bool:
        """Validate settings configuration.
        
        Args:
            settings: Settings to validate
            
        Returns:
            True if settings are valid
            
        Raises:
            ValidationError: If validation fails
            
        Implementation Notes:
            - Must check all fields
            - Should verify constraints
            - Must ensure consistency
            - Should explain failures
        """
        pass

    @abstractmethod
    def get_defaults(self) -> CostSettings:
        """Get default settings configuration.
        
        Returns:
            Default settings
            
        Implementation Notes:
            - Must provide sensible values
            - Should document choices
            - Must be consistent
            - Should cache results
        """
        pass
