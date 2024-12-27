"""Interface for location-based services."""
from abc import ABC, abstractmethod
from typing import List

from src.domain.value_objects import Location, CountrySegment


class LocationService(ABC):
    """Interface for services that provide location-based calculations and information."""

    @abstractmethod
    def calculate_distance(self, origin: Location, destination: Location) -> float:
        """
        Calculate the distance between two locations in kilometers.

        Args:
            origin: Starting location
            destination: End location

        Returns:
            float: Distance in kilometers

        Raises:
            LocationServiceError: If distance calculation fails
        """
        pass

    @abstractmethod
    def calculate_duration(self, origin: Location, destination: Location) -> float:
        """
        Calculate the estimated travel duration between two locations in hours.

        Args:
            origin: Starting location
            destination: End location

        Returns:
            float: Duration in hours

        Raises:
            LocationServiceError: If duration calculation fails
        """
        pass

    @abstractmethod
    def get_country_segments(self, origin: Location, destination: Location) -> List[CountrySegment]:
        """
        Get a list of country segments that a route passes through.

        Args:
            origin: Starting location
            destination: End location

        Returns:
            List[CountrySegment]: List of country segments with distances

        Raises:
            LocationServiceError: If country segment determination fails
        """
        pass


class LocationServiceError(Exception):
    """Base exception for location service errors."""
    pass
