"""Settings service interface."""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from uuid import UUID

from src.domain.entities.cost import CostSettings
from src.domain.interfaces.exceptions.service_errors import ServiceError

class SettingsServiceError(ServiceError):
    """Exception raised for errors in the settings service."""
    pass

class SettingsService(ABC):
    """Interface for settings management."""

    @abstractmethod
    def get_cost_settings(self, version: Optional[str] = None) -> CostSettings:
        """Get cost calculation settings.
        
        Args:
            version: Optional specific version to retrieve
            
        Returns:
            Cost settings
            
        Raises:
            SettingsServiceError: If settings retrieval fails
        """
        pass

    @abstractmethod
    def update_cost_settings(self, settings: CostSettings) -> CostSettings:
        """Update cost calculation settings.
        
        Args:
            settings: New settings
            
        Returns:
            Updated settings
            
        Raises:
            SettingsServiceError: If update fails
        """
        pass

    @abstractmethod
    def get_settings_history(self, settings_type: str) -> List[Dict]:
        """Get history of settings changes.
        
        Args:
            settings_type: Type of settings to get history for
            
        Returns:
            List of historical settings
            
        Raises:
            SettingsServiceError: If history retrieval fails
        """
        pass

    @abstractmethod
    def validate_settings(self, settings: Dict) -> bool:
        """Validate settings configuration.
        
        Args:
            settings: Settings to validate
            
        Returns:
            True if settings are valid, False otherwise
            
        Raises:
            SettingsServiceError: If validation fails
        """
        pass

    @abstractmethod
    def get_defaults(self, settings_type: str) -> Dict:
        """Get default settings.
        
        Args:
            settings_type: Type of settings to get defaults for
            
        Returns:
            Default settings
            
        Raises:
            SettingsServiceError: If defaults retrieval fails
        """
        pass
