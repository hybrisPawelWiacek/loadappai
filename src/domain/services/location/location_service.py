"""Location service implementation.

This module implements the location service interface.
It provides functionality for:
- Distance calculations
- Duration estimates
- Country segment identification
- Location validation
"""
from decimal import Decimal
from typing import Dict, List, Optional
from math import radians, sin, cos, sqrt, atan2

from src.domain.interfaces.services.location_service import LocationService as LocationServiceInterface
from src.domain.services.common.base import BaseService
from src.domain.value_objects import Location, CountrySegment
from src.infrastructure.logging import get_logger
from src.infrastructure.services.google_maps_service import GoogleMapsService
from src.infrastructure.services.toll_rate_service import DefaultTollRateService

logger = get_logger(__name__)


class LocationIntegrationService(BaseService, LocationServiceInterface):
    """Service for location-based operations."""
    
    def __init__(
        self,
        maps_client: Optional[GoogleMapsService] = None,
        toll_rate_service: Optional[DefaultTollRateService] = None,
        cache_service: Optional['CacheService'] = None
    ):
        """Initialize location service.
        
        Args:
            maps_client: Optional Google Maps client
            toll_rate_service: Optional toll rate service
            cache_service: Optional caching service
        """
        super().__init__()
        self._maps_client = maps_client
        self._toll_rate_service = toll_rate_service or DefaultTollRateService()
        self._cache_service = cache_service
        self._logger = logger.bind(service="location")
        
    def validate_location(self, location: Location) -> bool:
        """Validate location data.
        
        Args:
            location: Location to validate
            
        Returns:
            True if location is valid
            
        Raises:
            ValueError: If location is invalid
        """
        self._logger.info("Validating location", location=location.model_dump())
        
        try:
            # Check required fields
            if not location:
                raise ValueError("Location is required")
                
            # Validate coordinates
            if not -90 <= location.latitude <= 90:
                raise ValueError("Invalid latitude")
            if not -180 <= location.longitude <= 180:
                raise ValueError("Invalid longitude")
                
            # Validate country if present
            if location.country:
                if len(location.country) != 2:
                    raise ValueError("Country code must be 2 characters")
                    
            # Validate address if present
            if not location.address or len(location.address.strip()) == 0:
                raise ValueError("Address cannot be empty")
                    
            # Use external validation if available
            if self._maps_client:
                self._maps_client.validate_location(location)
                
            self._logger.info("Location validated successfully")
            return True
            
        except Exception as e:
            self._logger.error("Location validation failed", error=str(e))
            return False
            
    def calculate_distance(
        self,
        origin: Location,
        destination: Location,
        avoid_tolls: bool = False
    ) -> Decimal:
        """Calculate driving distance between locations.
        
        Args:
            origin: Starting location
            destination: End location
            avoid_tolls: Whether to avoid toll roads
            
        Returns:
            Distance in kilometers
            
        Raises:
            ValueError: If distance calculation fails
        """
        self._logger.info(
            "Calculating distance",
            origin=origin.model_dump(),
            destination=destination.model_dump(),
            avoid_tolls=avoid_tolls
        )
        
        try:
            # Validate inputs
            self.validate_location(origin)
            self.validate_location(destination)
            
            # Check cache first
            cache_key = f"distance:{origin.latitude},{origin.longitude}:" \
                       f"{destination.latitude},{destination.longitude}:" \
                       f"{avoid_tolls}"
                       
            if self._cache_service:
                cached = self._cache_service.get(cache_key)
                if cached:
                    self._logger.info("Returning cached distance", distance=cached)
                    return Decimal(str(cached))
            
            # Use external service if available
            if self._maps_client:
                distance = self._maps_client.calculate_distance(
                    origin,
                    destination,
                    avoid_tolls=avoid_tolls
                )
            else:
                # Fallback to simple calculation
                distance = self._calculate_simple_distance(origin, destination)
                
            # Cache result
            if self._cache_service:
                self._cache_service.set(cache_key, str(distance))
                
            self._logger.info("Distance calculated", distance=float(distance))
            return Decimal(str(distance))
            
        except Exception as e:
            self._logger.error("Distance calculation failed", error=str(e))
            raise ValueError(f"Failed to calculate distance: {str(e)}")
            
    def calculate_duration(
        self,
        origin: Location,
        destination: Location,
        departure_time: Optional[str] = None
    ) -> Decimal:
        """Calculate driving duration between locations.
        
        Args:
            origin: Starting location
            destination: End location
            departure_time: Optional departure time
            
        Returns:
            Duration in hours
            
        Raises:
            ValueError: If duration calculation fails
        """
        self._logger.info(
            "Calculating duration",
            origin=origin.model_dump(),
            destination=destination.model_dump(),
            departure_time=departure_time
        )
        
        try:
            # Validate inputs
            self.validate_location(origin)
            self.validate_location(destination)
            
            # Check cache first
            cache_key = f"duration:{origin.latitude},{origin.longitude}:" \
                       f"{destination.latitude},{destination.longitude}:" \
                       f"{departure_time}"
                       
            if self._cache_service:
                cached = self._cache_service.get(cache_key)
                if cached:
                    self._logger.info("Returning cached duration", duration=cached)
                    return Decimal(str(cached))
            
            # Use external service if available
            if self._maps_client:
                duration = self._maps_client.calculate_duration(
                    origin,
                    destination,
                    departure_time=departure_time
                )
            else:
                # Fallback to simple calculation
                distance = self._calculate_simple_distance(origin, destination)
                duration = Decimal(str(float(distance) / 60.0))  # Assume 60 km/h average speed
                
            # Cache result
            if self._cache_service:
                self._cache_service.set(cache_key, str(duration))
                
            self._logger.info("Duration calculated", duration=float(duration))
            return Decimal(str(duration))
            
        except Exception as e:
            self._logger.error("Duration calculation failed", error=str(e))
            raise ValueError(f"Failed to calculate duration: {str(e)}")
            
    def get_route_segments(
        self,
        origin: Location,
        destination: Location,
        include_tolls: bool = False,
        vehicle_type: str = "truck"
    ) -> List[CountrySegment]:
        """Get country segments for a route.
        
        Args:
            origin: Starting location
            destination: End location
            include_tolls: Whether to include toll information
            vehicle_type: Type of vehicle for toll calculations
            
        Returns:
            List of country segments with distances
            
        Raises:
            ValueError: If segment calculation fails
        """
        self._logger.info(
            "Getting route segments",
            origin=origin.model_dump(),
            destination=destination.model_dump(),
            include_tolls=include_tolls,
            vehicle_type=vehicle_type
        )
        
        try:
            # Validate locations
            if not self.validate_location(origin):
                raise ValueError("Invalid origin location")
            if not self.validate_location(destination):
                raise ValueError("Invalid destination location")
                
            # Try to get segments from maps client
            if self._maps_client:
                # Get toll rates first if needed
                toll_rates_by_country = {}
                if include_tolls and self._toll_rate_service:
                    # Pre-fetch toll rates for both countries
                    toll_rates_by_country = {
                        origin.country: self._toll_rate_service.get_toll_rates(
                            country=origin.country,
                            vehicle_type=vehicle_type
                        ),
                        destination.country: self._toll_rate_service.get_toll_rates(
                            country=destination.country,
                            vehicle_type=vehicle_type
                        )
                    }
                
                # Get segments with toll rates
                segments = []
                for segment in self._maps_client.get_route_segments(origin=origin, destination=destination):
                    segments.append(CountrySegment(
                        country_code=segment.country_code,
                        distance=segment.distance,
                        duration_hours=segment.duration_hours,
                        toll_rates=toll_rates_by_country.get(segment.country_code) if include_tolls else None
                    ))
            else:
                # Fallback to simple segments based on countries
                distance = self._calculate_simple_distance(origin, destination)
                distance_decimal = Decimal(str(distance))
                
                # Calculate duration assuming average speed of 60 km/h
                duration_hours = Decimal(str(float(distance_decimal) / 60.0))
                
                # Split distance between countries
                if origin.country == destination.country:
                    # Get toll rates if needed
                    toll_rates = None
                    if include_tolls and self._toll_rate_service:
                        toll_rates = self._toll_rate_service.get_toll_rates(
                            country=origin.country,
                            vehicle_type=vehicle_type
                        )
                    
                    segments = [
                        CountrySegment(
                            country_code=origin.country,
                            distance=distance_decimal,
                            duration_hours=duration_hours,
                            toll_rates=toll_rates
                        )
                    ]
                else:
                    # Get toll rates if needed
                    toll_rates = {}
                    if include_tolls and self._toll_rate_service:
                        toll_rates = {
                            origin.country: self._toll_rate_service.get_toll_rates(
                                country=origin.country,
                                vehicle_type=vehicle_type
                            ),
                            destination.country: self._toll_rate_service.get_toll_rates(
                                country=destination.country,
                                vehicle_type=vehicle_type
                            )
                        }
                    
                    # Split distance roughly between countries
                    segments = [
                        CountrySegment(
                            country_code=origin.country,
                            distance=distance_decimal * Decimal("0.5"),
                            duration_hours=duration_hours * Decimal("0.5"),
                            toll_rates=toll_rates.get(origin.country) if include_tolls else None
                        ),
                        CountrySegment(
                            country_code=destination.country,
                            distance=distance_decimal * Decimal("0.5"),
                            duration_hours=duration_hours * Decimal("0.5"),
                            toll_rates=toll_rates.get(destination.country) if include_tolls else None
                        )
                    ]
                    
            return segments
                
        except Exception as e:
            self._logger.error("Segment calculation failed", error=str(e))
            raise ValueError(f"Failed to calculate segments: {str(e)}")
            
    def _calculate_simple_distance(
        self,
        origin: Location,
        destination: Location
    ) -> float:
        """Calculate simple straight-line distance.
        
        Args:
            origin: Starting location
            destination: Ending location
            
        Returns:
            Distance in kilometers
        """
        # Convert to radians
        lat1 = radians(origin.latitude)
        lon1 = radians(origin.longitude)
        lat2 = radians(destination.latitude)
        lon2 = radians(destination.longitude)
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        # Earth radius in kilometers
        r = 6371
        
        return r * c
        
    def _is_valid_postal_code(
        self,
        postal_code: str,
        country_code: str
    ) -> bool:
        """Validate postal code format.
        
        Args:
            postal_code: Postal code to validate
            country_code: Country code for format rules
            
        Returns:
            True if postal code is valid
        """
        import re
        
        # Postal code formats by country
        formats = {
            "DE": r"^\d{5}$",               # German format
            "PL": r"^\d{2}-\d{3}$",         # Polish format
            "FR": r"^\d{5}$",               # French format
            "IT": r"^\d{5}$",               # Italian format
            "ES": r"^\d{5}$",               # Spanish format
            "GB": r"^[A-Z]{1,2}\d[A-Z\d]?", # UK format (partial)
            "NL": r"^\d{4}\s?[A-Z]{2}$",    # Dutch format
            "BE": r"^\d{4}$",               # Belgian format
            "AT": r"^\d{4}$",               # Austrian format
            "CH": r"^\d{4}$",               # Swiss format
            "CZ": r"^\d{3}\s?\d{2}$",       # Czech format
            "SK": r"^\d{3}\s?\d{2}$",       # Slovak format
            "HU": r"^\d{4}$",               # Hungarian format
            "DK": r"^\d{4}$",               # Danish format
            "SE": r"^\d{3}\s?\d{2}$",       # Swedish format
            "NO": r"^\d{4}$",               # Norwegian format
            "FI": r"^\d{5}$",               # Finnish format
        }
        
        # Get format pattern for country
        pattern = formats.get(country_code)
        if not pattern:
            self._logger.warning(
                "No postal code format for country",
                country_code=country_code
            )
            return True  # Accept if no format defined
            
        # Validate against pattern
        is_valid = bool(re.match(pattern, postal_code))
        if not is_valid:
            self._logger.warning(
                "Invalid postal code format",
                postal_code=postal_code,
                country_code=country_code,
                pattern=pattern
            )
            
        return is_valid
