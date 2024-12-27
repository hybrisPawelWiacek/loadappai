"""Settings repository interface."""
from abc import abstractmethod
from typing import Dict, List, Optional
from uuid import UUID

from src.domain.entities.cost import CostSettings
from src.domain.interfaces.repositories.base import Repository
from src.domain.interfaces.exceptions.repository_errors import EntityNotFoundError, ValidationError

class SettingsRepository(Repository[CostSettings]):
    """Interface for settings data access."""

    @abstractmethod
    def get_current_settings(self) -> CostSettings:
        """Get current active settings.
        
        Returns:
            Current settings
            
        Raises:
            EntityNotFoundError: If no active settings found
        """
        pass

    @abstractmethod
    def get_by_version(self, version: str) -> Optional[CostSettings]:
        """Get settings by version.
        
        Args:
            version: Settings version
            
        Returns:
            Settings if found, None otherwise
        """
        pass

    @abstractmethod
    def save_with_history(self, 
        settings: CostSettings, 
        change_reason: str
    ) -> CostSettings:
        """Save settings with change history.
        
        Args:
            settings: Settings to save
            change_reason: Reason for the change
            
        Returns:
            Saved settings
            
        Raises:
            ValidationError: If settings validation fails
        """
        pass

    @abstractmethod
    def get_settings_history(self) -> List[Dict]:
        """Get history of settings changes.
        
        Returns:
            List of historical changes
        """
        pass

    @abstractmethod
    def get_defaults(self) -> CostSettings:
        """Get default settings.
        
        Returns:
            Default settings configuration
        """
        pass
