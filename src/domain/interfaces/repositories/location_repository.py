"""Location repository interface."""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from uuid import UUID

from src.domain.interfaces.repositories.base import Repository
from src.domain.value_objects.location import Location


class LocationRepository(Repository, ABC):
    """Interface for location data persistence."""

    @abstractmethod
    def find_by_name(self, name: str) -> Optional[Location]:
        """Find a location by its name."""
        pass

    @abstractmethod
    def find_by_coordinates(self, lat: float, lon: float) -> Optional[Location]:
        """Find a location by its coordinates."""
        pass

    @abstractmethod
    def search(
        self,
        query: str,
        country: Optional[str] = None,
        limit: int = 10
    ) -> List[Location]:
        """Search for locations matching query."""
        pass

    @abstractmethod
    def get_metadata(self, location_id: UUID) -> Dict[str, Any]:
        """Get metadata for a location."""
        pass
