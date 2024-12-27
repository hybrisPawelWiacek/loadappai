"""Domain interfaces for LoadApp.AI."""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime
from uuid import UUID

from src.domain.value_objects import Location


class LocationServiceError(Exception):
    """Exception raised for errors in the location service."""
    pass


class LocationService(ABC):
    """Interface for location and routing services."""

    @abstractmethod
    def calculate_distance(self, origin: Location, destination: Location) -> float:
        """Calculate distance between two locations in kilometers."""
        pass

    @abstractmethod
    def calculate_duration(self, origin: Location, destination: Location) -> float:
        """Calculate travel duration between two locations in hours."""
        pass

    @abstractmethod
    def get_country_segments(self, origin: Location, destination: Location) -> List[Dict]:
        """Get list of country segments for a route."""
        pass


class AIServiceError(Exception):
    """Exception raised for errors in the AI service."""
    pass


class AIService(ABC):
    """Interface for AI-powered services."""

    @abstractmethod
    def generate_route_fact(self, 
            origin: Location, 
            destination: Location, 
            context: Optional[Dict] = None
        ) -> str:
        """
        Generate an interesting fact about a route.
        
        Args:
            origin: Starting location
            destination: End location
            context: Optional additional context about the route
            
        Returns:
            str: An interesting fact about the route
            
        Raises:
            AIServiceError: If fact generation fails
        """
        pass

    @abstractmethod
    def enhance_route_description(self,
            origin: Location,
            destination: Location,
            distance_km: float,
            duration_hours: float,
            context: Optional[Dict] = None
        ) -> str:
        """
        Generate an enhanced description of a route.
        
        Args:
            origin: Starting location
            destination: End location
            distance_km: Route distance in kilometers
            duration_hours: Route duration in hours
            context: Optional additional context
            
        Returns:
            str: Enhanced route description
            
        Raises:
            AIServiceError: If description generation fails
        """
        pass
