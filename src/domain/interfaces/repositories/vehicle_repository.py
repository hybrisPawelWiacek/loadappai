"""Vehicle repository interface."""
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from src.domain.entities.vehicle import Vehicle
from src.domain.interfaces.repositories.base import Repository


class VehicleRepository(Repository[Vehicle]):
    """Repository interface for managing vehicle entities."""

    @abstractmethod
    def get_by_type(self, vehicle_type: str) -> List[Vehicle]:
        """Get all vehicles of a specific type.
        
        Args:
            vehicle_type: Type of vehicle to filter by
            
        Returns:
            List of vehicles matching the type
        """
        pass

    @abstractmethod
    def get_active(self) -> List[Vehicle]:
        """Get all active vehicles.
        
        Returns:
            List of active vehicles
        """
        pass
