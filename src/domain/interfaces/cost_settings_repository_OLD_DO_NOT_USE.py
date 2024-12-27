"""Interface for cost settings repository."""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from src.domain.entities.cost import CostSettings


class CostSettingsRepository(ABC):
    """Repository interface for cost settings.
    
    Responsibilities:
    - Store and retrieve cost settings for routes
    - Track settings versions and changes
    - Maintain settings history for auditing
    """
    
    @abstractmethod
    def get_by_route_id(self, route_id: UUID) -> Optional[CostSettings]:
        """Get cost settings for a route.
        
        Args:
            route_id: UUID of the route
            
        Returns:
            CostSettings if found, None otherwise
        """
        pass
        
    @abstractmethod
    def save(self, settings: CostSettings) -> CostSettings:
        """Save cost settings.
        
        Args:
            settings: CostSettings to save
            
        Returns:
            Saved CostSettings with updated metadata
            
        Raises:
            ValueError: If settings are invalid
        """
        pass
        
    @abstractmethod
    def get_history(self, route_id: UUID) -> List[CostSettings]:
        """Get history of cost settings for a route.
        
        Args:
            route_id: UUID of the route
            
        Returns:
            List of historical CostSettings, ordered by version
        """
        pass

    @abstractmethod
    def get_defaults(self) -> CostSettings:
        """Get default cost settings."""
        pass

    @abstractmethod
    def get_by_version(self, route_id: UUID, version: str) -> Optional[CostSettings]:
        """Get specific version of cost settings."""
        pass
