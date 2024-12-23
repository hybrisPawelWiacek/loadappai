"""Deprecated mock location service."""
import warnings
from typing import List
from src.domain.interfaces import LocationService, LocationServiceError
from src.domain.value_objects import Location, CountrySegment
from src.infrastructure.services.google_maps_service import GoogleMapsService
from structlog import get_logger

logger = get_logger()

class MockLocationService(LocationService):
    """
    Deprecated mock implementation of LocationService.
    This class is maintained only for backwards compatibility and testing.
    Please use GoogleMapsService for production.
    """

    def __init__(self):
        """Initialize with deprecation warning."""
        warnings.warn(
            "MockLocationService is deprecated. Use GoogleMapsService for production.",
            DeprecationWarning,
            stacklevel=2
        )
        self._google_maps = None
        self._logger = logger.bind(service="mock_location")

    @property
    def google_maps(self) -> GoogleMapsService:
        """Lazy initialization of Google Maps service."""
        if self._google_maps is None:
            try:
                self._google_maps = GoogleMapsService()
                self._logger.info("Successfully initialized Google Maps service")
            except LocationServiceError as e:
                self._logger.warning("Failed to initialize Google Maps service, using mock values", error=str(e))
        return self._google_maps

    def calculate_distance(self, origin: Location, destination: Location) -> float:
        """Calculate distance between two locations."""
        try:
            if self._google_maps:
                return self.google_maps.calculate_distance(origin, destination)
        except LocationServiceError as e:
            self._logger.warning("Google Maps distance calculation failed, using mock value", error=str(e))
        return 500.0  # Fallback mock value

    def calculate_duration(self, origin: Location, destination: Location) -> float:
        """Calculate duration between two locations."""
        try:
            if self._google_maps:
                return self.google_maps.calculate_duration(origin, destination)
        except LocationServiceError as e:
            self._logger.warning("Google Maps duration calculation failed, using mock value", error=str(e))
        return 8.0  # Fallback mock value

    def get_country_segments(self, origin: Location, destination: Location) -> List[CountrySegment]:
        """Get country segments for a route."""
        try:
            if self._google_maps:
                return self.google_maps.get_country_segments(origin, destination)
        except LocationServiceError as e:
            self._logger.warning("Google Maps segment calculation failed, using mock value", error=str(e))
        return [
            CountrySegment(
                country="PL",
                distance_km=300.0,
                duration_hours=4.0,
                toll_rates={"standard": 0.15}
            ),
            CountrySegment(
                country="DE",
                distance_km=200.0,
                duration_hours=4.0,
                toll_rates={"standard": 0.20}
            )
        ]

    def validate_location(self, location: Location) -> None:
        """Validate a location."""
        try:
            if self._google_maps:
                return self.google_maps.validate_location(location)
        except LocationServiceError as e:
            self._logger.warning("Google Maps location validation failed", error=str(e))
        pass  # All locations are valid in mock service

    def get_toll_rates(self, country_code: str) -> dict:
        """Get toll rates for a country."""
        try:
            if self._google_maps:
                return self.google_maps.get_toll_rates(country_code)
        except LocationServiceError as e:
            self._logger.warning("Google Maps toll rate lookup failed, using mock value", error=str(e))
        return {"standard": 0.15}
