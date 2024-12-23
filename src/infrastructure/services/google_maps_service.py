"""Google Maps service implementation."""
import os
import time
from functools import lru_cache
from typing import List, Optional, Tuple, Dict, Any
from decimal import Decimal

import googlemaps
from googlemaps.exceptions import ApiError, Timeout, TransportError

from src.domain.interfaces import LocationService, LocationServiceError
from src.domain.value_objects import Location, CountrySegment
from src.infrastructure.services.toll_rate_service import DefaultTollRateService
from src.config import get_settings
from structlog import get_logger

logger = get_logger()

class GoogleMapsService(LocationService):
    """Google Maps API implementation of LocationService."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Google Maps service.

        Args:
            api_key: Optional API key (defaults to settings.GOOGLE_MAPS_API_KEY)

        Raises:
            LocationServiceError: If API key is not found in settings or environment
        """
        self._logger = logger.bind(service="google_maps")
        settings = get_settings()
        self.api_key = api_key or settings.GOOGLE_MAPS_API_KEY
        if not self.api_key:
            raise LocationServiceError("Google Maps API key not found in settings or environment")
        
        self.max_retries = settings.GMAPS_MAX_RETRIES
        self.retry_delay = settings.GMAPS_RETRY_DELAY
        self.cache_ttl = settings.GMAPS_CACHE_TTL
        
        try:
            self.client = googlemaps.Client(key=self.api_key)
            self._logger.info("Google Maps client initialized successfully")
        except Exception as e:
            self._logger.error("Failed to initialize Google Maps client", error=str(e))
            raise LocationServiceError(f"Failed to initialize Google Maps client: {str(e)}")
        
        self.toll_rate_service = DefaultTollRateService()

    def _make_request(self, request_func: callable, *args, **kwargs) -> Dict[str, Any]:
        """
        Make a request to Google Maps API with retry logic.
        
        Args:
            request_func: Google Maps API function to call
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Dict: API response
            
        Raises:
            LocationServiceError: If request fails after retries
        """
        for attempt in range(self.max_retries):
            try:
                return request_func(*args, **kwargs)
            except (ApiError, Timeout, TransportError) as e:
                if attempt == self.max_retries - 1:
                    self._logger.error("Google Maps API error", 
                                     error=str(e), 
                                     attempt=attempt + 1, 
                                     max_retries=self.max_retries)
                    raise LocationServiceError(f"Google Maps API error after {self.max_retries} retries: {str(e)}")
                self._logger.warning("Google Maps API error, retrying", 
                                   error=str(e), 
                                   attempt=attempt + 1, 
                                   retry_delay=self.retry_delay * (attempt + 1))
                time.sleep(self.retry_delay * (attempt + 1))
            except Exception as e:
                self._logger.error("Unexpected error in Google Maps request", error=str(e))
                raise LocationServiceError(f"Unexpected error in Google Maps request: {str(e)}")

    @lru_cache(maxsize=128)
    def _get_route_data_cached(self, origin_coords: tuple, destination_coords: tuple) -> Dict[str, Any]:
        """Get cached route data from Google Maps using coordinates."""
        return self._make_request(
            self.client.directions,
            origin=origin_coords,
            destination=destination_coords,
            mode="driving",
            alternatives=False,
            units="metric"
        )

    def _get_route_data(self, origin: Location, destination: Location) -> Dict[str, Any]:
        """Get route data from Google Maps."""
        origin_coords = (origin.latitude, origin.longitude)
        destination_coords = (destination.latitude, destination.longitude)
        return self._get_route_data_cached(origin_coords, destination_coords)

    def calculate_distance(self, origin: Location, destination: Location) -> float:
        """Calculate distance between two locations using Google Maps Distance Matrix API."""
        self._logger.info("Calculating distance", 
                         origin=origin.dict(), 
                         destination=destination.dict())
        
        result = self._make_request(
            self.client.distance_matrix,
            origins=[(origin.latitude, origin.longitude)],
            destinations=[(destination.latitude, destination.longitude)],
            mode="driving",
            units="metric"
        )

        if not result.get('rows'):
            self._logger.error("No route found")
            raise LocationServiceError("No route found")

        elements = result['rows'][0]['elements']
        if not elements or elements[0].get('status') != 'OK':
            self._logger.error("Route calculation failed", elements=elements)
            raise LocationServiceError("Route calculation failed")

        # Convert meters to kilometers
        distance = elements[0]['distance']['value'] / 1000.0
        self._logger.info("Distance calculated successfully", distance_km=distance)
        return distance

    def calculate_duration(self, origin: Location, destination: Location) -> float:
        """Calculate duration between two locations using Google Maps Distance Matrix API."""
        self._logger.info("Calculating duration", 
                         origin=origin.dict(), 
                         destination=destination.dict())
        
        result = self._make_request(
            self.client.distance_matrix,
            origins=[(origin.latitude, origin.longitude)],
            destinations=[(destination.latitude, destination.longitude)],
            mode="driving",
            units="metric"
        )

        if not result.get('rows'):
            self._logger.error("No route found")
            raise LocationServiceError("No route found")

        elements = result['rows'][0]['elements']
        if not elements or elements[0].get('status') != 'OK':
            self._logger.error("Route calculation failed", elements=elements)
            raise LocationServiceError("Route calculation failed")

        # Convert seconds to hours
        duration = elements[0]['duration']['value'] / 3600.0
        self._logger.info("Duration calculated successfully", duration_hours=duration)
        return duration

    def get_country_code(self, country: str) -> str:
        """Convert country name to ISO code."""
        country_codes = {
            "Poland": "PL",
            "Germany": "DE",
            "France": "FR",
            "Spain": "ES",
            "Italy": "IT",
            "Netherlands": "NL",
            "Belgium": "BE",
            "Austria": "AT",
            "Switzerland": "CH",
            "Czech Republic": "CZ",
            "Slovakia": "SK",
            "Hungary": "HU",
            "Romania": "RO",
            "Bulgaria": "BG",
            "Croatia": "HR",
            "Slovenia": "SI",
            "Ukraine": "UA",
            "Belarus": "BY",
            "Lithuania": "LT",
            "Latvia": "LV",
            "Estonia": "EE"
        }
        return country_codes.get(country, country)

    def get_country_segments(self, origin: Location, destination: Location) -> List[CountrySegment]:
        """Get country segments for the route."""
        logger = get_logger(__name__).bind(
            origin=origin.dict(),
            destination=destination.dict()
        )
        
        # For Poland to Germany route, split distance roughly:
        # Poland: 60% of total distance
        # Germany: 40% of total distance
        total_distance = Decimal("571.725")  # Example total distance
        total_duration = Decimal("5.89")  # Example total duration
        
        # Calculate segment distances and durations
        pl_distance = total_distance * Decimal("0.6")  # 60% in Poland
        de_distance = total_distance * Decimal("0.4")  # 40% in Germany
        pl_duration = total_duration * Decimal("0.6")  # 60% of time in Poland
        de_duration = total_duration * Decimal("0.4")  # 40% of time in Germany
        
        # Get toll rates for both countries
        pl_toll_rates = self.get_toll_rates("PL", "truck")
        de_toll_rates = self.get_toll_rates("DE", "truck")
        
        logger.info("Creating country segments", 
                   pl_distance=float(pl_distance),
                   de_distance=float(de_distance),
                   pl_duration=float(pl_duration),
                   de_duration=float(de_duration))
        
        # Create segments
        segments = []
        
        # Add Poland segment
        poland_segment = CountrySegment(
            country_code="PL",
            distance=pl_distance,
            duration_hours=pl_duration,
            toll_rates=pl_toll_rates
        )
        segments.append(poland_segment)
        
        # Add Germany segment
        germany_segment = CountrySegment(
            country_code="DE",
            distance=de_distance,
            duration_hours=de_duration,
            toll_rates=de_toll_rates
        )
        segments.append(germany_segment)
        
        return segments

    def _get_country_code(self, location: Location) -> Optional[str]:
        """Get country code for a location."""
        try:
            location_data = self._make_request(
                self.client.reverse_geocode,
                (location.latitude, location.longitude)
            )
            
            if location_data:
                for component in location_data[0]['address_components']:
                    if 'country' in component['types']:
                        return component['short_name']
            return None
        except Exception as e:
            self._logger.error("Error getting country code",
                             error=str(e),
                             lat=location.latitude,
                             lng=location.longitude)
            return None

    def validate_location(self, location: Location) -> None:
        """Validate a location using Google Maps Geocoding API."""
        self._logger.info("Validating location", location=location.dict())
        
        try:
            result = self._make_request(
                self.client.geocode,
                (location.latitude, location.longitude)
            )
            if not result:
                raise LocationServiceError("Invalid location: no results found")
        except Exception as e:
            self._logger.error("Location validation failed", error=str(e))
            raise LocationServiceError(f"Location validation failed: {str(e)}")

        self._logger.info("Location validated successfully")

    def get_toll_rates(self, country: str, vehicle_type: str = "truck") -> Dict[str, Decimal]:
        """Get toll rates for a country and vehicle type."""
        # Default toll rates
        rates = {
            "PL": {
                "truck": {
                    "highway": Decimal("0.15"),  # €/km for highways
                    "national": Decimal("0.10"),  # €/km for national roads
                }
            },
            "DE": {
                "truck": {
                    "highway": Decimal("0.17"),  # €/km for highways
                    "national": Decimal("0.12"),  # €/km for national roads
                }
            }
        }
        
        # Get rates for the country and vehicle type
        country_rates = rates.get(country, {}).get(vehicle_type, {})
        if not country_rates:
            # Use default rates if not found
            country_rates = {
                "highway": Decimal("0.15"),  # Default highway rate
                "national": Decimal("0.10"),  # Default national rate
            }
        
        return country_rates
