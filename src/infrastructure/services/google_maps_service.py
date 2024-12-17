"""Google Maps service implementation."""
import os
from functools import lru_cache
from typing import List, Optional, Tuple
from decimal import Decimal

import googlemaps
from googlemaps.exceptions import ApiError, Timeout, TransportError

from src.domain.interfaces import LocationService, LocationServiceError
from src.domain.value_objects import Location, CountrySegment
from src.infrastructure.services.toll_rate_service import DefaultTollRateService


class GoogleMapsService(LocationService):
    """Google Maps API implementation of LocationService."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Google Maps service.

        Args:
            api_key: Optional API key. If not provided, will look for GOOGLE_MAPS_API_KEY env var.

        Raises:
            LocationServiceError: If API key is not provided and not found in environment
        """
        self.api_key = api_key or os.environ.get('GOOGLE_MAPS_API_KEY')
        if not self.api_key:
            raise LocationServiceError("Google Maps API key not found")
        
        try:
            self.client = googlemaps.Client(key=self.api_key)
        except Exception as e:
            raise LocationServiceError(f"Failed to initialize Google Maps client: {str(e)}")
        
        self.toll_rate_service = DefaultTollRateService()

    @lru_cache(maxsize=1000)
    def calculate_distance(self, origin: Location, destination: Location) -> float:
        """Calculate distance between two locations using Google Maps Distance Matrix API."""
        try:
            result = self.client.distance_matrix(
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
            return elements[0]['distance']['value'] / 1000.0

        except (ApiError, Timeout, TransportError) as e:
            raise LocationServiceError(f"Google Maps API error: {str(e)}")
        except Exception as e:
            raise LocationServiceError(f"Unexpected error calculating distance: {str(e)}")

    @lru_cache(maxsize=1000)
    def calculate_duration(self, origin: Location, destination: Location) -> float:
        """Calculate travel duration between two locations using Google Maps Distance Matrix API."""
        try:
            result = self.client.distance_matrix(
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
            return elements[0]['duration']['value'] / 3600.0

        except (ApiError, Timeout, TransportError) as e:
            raise LocationServiceError(f"Google Maps API error: {str(e)}")
        except Exception as e:
            raise LocationServiceError(f"Unexpected error calculating duration: {str(e)}")

    def get_country_segments(
        self, origin: Location, destination: Location, transport_type: str
    ) -> List[CountrySegment]:
        """Get country segments for a route using Google Maps Directions API."""
        try:
            directions = self.client.directions(
                origin=(origin.latitude, origin.longitude),
                destination=(destination.latitude, destination.longitude),
                mode="driving"
            )

            if not directions:
                raise LocationServiceError("No route found")

            segments = []

            for leg in directions[0]["legs"]:
                current_country = None
                current_distance = 0

                for step in leg["steps"]:
                    country = self._extract_country(step)
                    distance = step["distance"]["value"] / 1000  # Convert to km

                    if current_country != country:
                        if current_country:
                            temp_segment = CountrySegment(
                                country_code=current_country,
                                distance=Decimal(str(current_distance)),
                                toll_rates={}
                            )
                            toll_rates = self.toll_rate_service.calculate_segment_toll_rates(
                                temp_segment,
                                transport_type
                            )
                            segments.append(
                                CountrySegment(
                                    country_code=current_country,
                                    distance=Decimal(str(current_distance)),
                                    toll_rates=toll_rates
                                )
                            )
                        current_country = country
                        current_distance = distance
                    else:
                        current_distance += distance

                # Add the last segment
                if current_country:
                    temp_segment = CountrySegment(
                        country_code=current_country,
                        distance=Decimal(str(current_distance)),
                        toll_rates={}
                    )
                    toll_rates = self.toll_rate_service.calculate_segment_toll_rates(
                        temp_segment,
                        transport_type
                    )
                    segments.append(
                        CountrySegment(
                            country_code=current_country,
                            distance=Decimal(str(current_distance)),
                            toll_rates=toll_rates
                        )
                    )

            return segments

        except ApiError as e:
            raise LocationServiceError(f"Google Maps API error: {str(e)}")
        except Exception as e:
            raise LocationServiceError(f"Failed to get country segments: {str(e)}")

    def _extract_country(self, step: dict) -> str:
        """
        Extract country from a Google Maps step.
        
        This is a simplified implementation that estimates country based on
        the step's end location. For more accurate results, you might want to:
        1. Use the Routes API instead of Directions API
        2. Implement more sophisticated country border detection
        3. Consider using additional geospatial data sources
        """
        lat = step['end_location']['lat']
        lng = step['end_location']['lng']
        
        try:
            geocode_result = self.client.reverse_geocode((lat, lng))
            if geocode_result:
                for component in geocode_result[0]['address_components']:
                    if 'country' in component['types']:
                        return component['short_name']
        except Exception:
            # If geocoding fails, we'll skip this step
            pass
        
        # If country cannot be determined, return None
        return None
