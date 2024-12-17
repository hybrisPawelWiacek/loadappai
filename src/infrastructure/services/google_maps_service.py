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
        settings = get_settings()
        self.api_key = api_key or settings.GOOGLE_MAPS_API_KEY
        if not self.api_key:
            raise LocationServiceError("Google Maps API key not found in settings or environment")
        
        self.max_retries = settings.GMAPS_MAX_RETRIES
        self.retry_delay = settings.GMAPS_RETRY_DELAY
        self.cache_ttl = settings.GMAPS_CACHE_TTL
        
        try:
            self.client = googlemaps.Client(key=self.api_key)
        except Exception as e:
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
                    raise LocationServiceError(f"Google Maps API error after {self.max_retries} retries: {str(e)}")
                time.sleep(self.retry_delay * (attempt + 1))
            except Exception as e:
                raise LocationServiceError(f"Unexpected error in Google Maps request: {str(e)}")

    def _get_cache_key(self, origin: Location, destination: Location) -> str:
        """Generate a cache key for location pair."""
        return f"{origin.latitude},{origin.longitude}|{destination.latitude},{destination.longitude}"

    def calculate_distance(self, origin: Location, destination: Location) -> float:
        """Calculate distance between two locations using Google Maps Distance Matrix API."""
        cache_key = self._get_cache_key(origin, destination)
        if hasattr(self, '_distance_cache') and cache_key in self._distance_cache:
            return self._distance_cache[cache_key]

        result = self._make_request(
            self.client.distance_matrix,
            origins=[(origin.latitude, origin.longitude)],
            destinations=[(destination.latitude, destination.longitude)],
            mode="driving",
            units="metric"
        )

        if not result.get('rows'):
            raise LocationServiceError("No route found")

        elements = result['rows'][0]['elements']
        if not elements or elements[0].get('status') != 'OK':
            raise LocationServiceError("Route calculation failed")

        # Convert meters to kilometers
        distance = elements[0]['distance']['value'] / 1000.0
        
        # Cache the result
        if not hasattr(self, '_distance_cache'):
            self._distance_cache = {}
        self._distance_cache[cache_key] = distance
        
        return distance

    def calculate_duration(self, origin: Location, destination: Location) -> float:
        """Calculate travel duration between two locations using Google Maps Distance Matrix API."""
        cache_key = self._get_cache_key(origin, destination)
        if hasattr(self, '_duration_cache') and cache_key in self._duration_cache:
            return self._duration_cache[cache_key]

        result = self._make_request(
            self.client.distance_matrix,
            origins=[(origin.latitude, origin.longitude)],
            destinations=[(destination.latitude, destination.longitude)],
            mode="driving",
            units="metric"
        )

        if not result.get('rows'):
            raise LocationServiceError("No route found")

        elements = result['rows'][0]['elements']
        if not elements or elements[0].get('status') != 'OK':
            raise LocationServiceError("Route calculation failed")

        # Convert seconds to hours
        duration = elements[0]['duration']['value'] / 3600.0
        
        # Cache the result
        if not hasattr(self, '_duration_cache'):
            self._duration_cache = {}
        self._duration_cache[cache_key] = duration
        
        return duration

    def get_country_segments(self, origin: Location, destination: Location, transport_type: str) -> List[CountrySegment]:
        """Get country segments for a route using Google Maps Directions API."""
        result = self._make_request(
            self.client.directions,
            origin=(origin.latitude, origin.longitude),
            destination=(destination.latitude, destination.longitude),
            mode="driving"
        )

        if not result:
            raise LocationServiceError("No route found")

        # Process route and extract country segments
        segments = self._extract_country_segments(result[0])

        # Add toll rates to segments
        for segment in segments:
            toll_rates = self.toll_rate_service.calculate_segment_toll_rates(
                segment,
                transport_type
            )
            segment.toll_rates = toll_rates

        return segments

    def _extract_country_segments(self, route: Dict[str, Any]) -> List[CountrySegment]:
        """Extract country segments from a route."""
        segments = []
        current_country = None
        current_distance = Decimal("0")

        for leg in route.get('legs', [{}]):
            for step in leg.get('steps', []):
                country = self._get_country_from_location(step.get('end_location', {}))
                distance = Decimal(str(step.get('distance', {}).get('value', 0))) / Decimal("1000")  # meters to km

                if country != current_country:
                    if current_country:
                        segments.append(CountrySegment(
                            country_code=current_country,
                            distance=current_distance
                        ))
                    current_country = country
                    current_distance = distance
                else:
                    current_distance += distance

        # Add final segment
        if current_country:
            segments.append(CountrySegment(
                country_code=current_country,
                distance=current_distance
            ))

        return segments

    def _get_country_from_location(self, location: Dict[str, float]) -> str:
        """Get country code from location using reverse geocoding."""
        if not location:
            return "Unknown"

        result = self._make_request(
            self.client.reverse_geocode,
            (location.get('lat'), location.get('lng')),
            result_type=['country']
        )

        if result and result[0].get('address_components'):
            for component in result[0]['address_components']:
                if 'country' in component.get('types', []):
                    return component.get('short_name', 'Unknown')

        return "Unknown"
