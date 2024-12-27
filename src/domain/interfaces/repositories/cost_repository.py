"""Cost repository interface."""
from abc import abstractmethod
from typing import List, Optional
from uuid import UUID

from src.domain.entities.cost import Cost
from src.domain.interfaces.repositories.base import Repository
from src.domain.interfaces.exceptions.repository_errors import EntityNotFoundError, ValidationError

class CostRepository(Repository[Cost]):
    """Interface for cost data access."""

    @abstractmethod
    def get_by_route_id(self, route_id: UUID) -> List[Cost]:
        """Get all costs for a route.
        
        Args:
            route_id: Route ID
            
        Returns:
            List of costs for the route
            
        Raises:
            EntityNotFoundError: If route not found
        """
        pass

    @abstractmethod
    def get_latest_for_route(self, route_id: UUID) -> Optional[Cost]:
        """Get latest cost calculation for a route.
        
        Args:
            route_id: Route ID
            
        Returns:
            Latest cost calculation if exists, None otherwise
            
        Raises:
            EntityNotFoundError: If route not found
        """
        pass

    @abstractmethod
    def save_with_breakdown(self, cost: Cost, breakdown: dict) -> Cost:
        """Save cost with detailed breakdown.
        
        Args:
            cost: Cost calculation
            breakdown: Detailed cost breakdown
            
        Returns:
            Saved cost
            
        Raises:
            ValidationError: If cost validation fails
        """
        pass

    @abstractmethod
    def get_cost_history(self, cost_id: UUID) -> List[Cost]:
        """Get history of changes for a cost calculation.
        
        Args:
            cost_id: Cost ID
            
        Returns:
            List of historical cost versions
            
        Raises:
            EntityNotFoundError: If cost not found
        """
        pass
