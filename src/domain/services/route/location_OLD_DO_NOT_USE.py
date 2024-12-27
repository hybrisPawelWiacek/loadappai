"""Location service implementation.

This module implements the location service interface.
It provides functionality for:
- Distance calculations
- Duration estimates
- Country segment identification
- Location validation
"""
from typing import Dict, List, Optional, Tuple

from src.domain.interfaces.services.location_service import LocationService
from src.domain.services.common.base import BaseService
from src.domain.value_objects import Location, CountrySegment

class LocationServiceImpl(BaseService, LocationService):
    """Implementation of location service.
    
    This service is responsible for:
    - Calculating distances between locations
    - Estimating travel durations
    - Identifying country segments
    - Validating locations
    """
    
    def __init__(self, maps_client: Optional['MapsClient'] = None):
        """Initialize location service.
        
        Args:
            maps_client: Optional external maps client
        """
        super().__init__()
        self._maps_client = maps_client
    
    def calculate_distance(
        self,
        origin: Location,
        destination: Location
    ) -> float:
        """Calculate distance between locations.
        
        Args:
            origin: Starting location
            destination: Ending location
            
        Returns:
            Distance in kilometers
            
        Raises:
            ValueError: If locations are invalid
        """
        self._log_entry(
            "calculate_distance",
            origin=origin,
            destination=destination
        )
        
        try:
            # Validate inputs
            self._validate_required(origin, "origin")
            self._validate_required(destination, "destination")
            self._validate_coordinates(origin)
            self._validate_coordinates(destination)
            
            # Use maps client if available
            if self._maps_client:
                distance = self._maps_client.get_distance(
                    origin.dict(),
                    destination.dict()
                )
            else:
                # Fallback to simple calculation
                distance = self._calculate_simple_distance(origin, destination)
            
            self._log_exit("calculate_distance", distance)
            return distance
            
        except Exception as e:
            self._log_error("calculate_distance", e)
            raise ValueError(f"Failed to calculate distance: {str(e)}")
    
    def calculate_duration(
        self,
        origin: Location,
        destination: Location
    ) -> float:
        """Calculate travel duration between locations.
        
        Args:
            origin: Starting location
            destination: Ending location
            
        Returns:
            Duration in hours
            
        Raises:
            ValueError: If locations are invalid
        """
        self._log_entry(
            "calculate_duration",
            origin=origin,
            destination=destination
        )
        
        try:
            # Validate inputs
            self._validate_required(origin, "origin")
            self._validate_required(destination, "destination")
            self._validate_coordinates(origin)
            self._validate_coordinates(destination)
            
            # Use maps client if available
            if self._maps_client:
                duration = self._maps_client.get_duration(
                    origin.dict(),
                    destination.dict()
                )
            else:
                # Fallback to simple calculation
                distance = self._calculate_simple_distance(origin, destination)
                duration = distance / 60.0  # Assume 60 km/h average speed
            
            self._log_exit("calculate_duration", duration)
            return duration
            
        except Exception as e:
            self._log_error("calculate_duration", e)
            raise ValueError(f"Failed to calculate duration: {str(e)}")
    
    def get_country_segments(
        self,
        origin: Location,
        destination: Location
    ) -> List[CountrySegment]:
        """Get country segments for a route.
        
        Args:
            origin: Starting location
            destination: Ending location
            
        Returns:
            List of country segments
            
        Raises:
            ValueError: If locations are invalid
        """
        self._log_entry(
            "get_country_segments",
            origin=origin,
            destination=destination
        )
        
        try:
            # Validate inputs
            self._validate_required(origin, "origin")
            self._validate_required(destination, "destination")
            self._validate_coordinates(origin)
            self._validate_coordinates(destination)
            
            # Use maps client if available
            if self._maps_client:
                segments = self._maps_client.get_segments(
                    origin.dict(),
                    destination.dict()
                )
            else:
                # Fallback to simple segment
                segments = [
                    CountrySegment(
                        country_code=origin.country_code,
                        entry_point=origin.dict(),
                        exit_point=destination.dict(),
                        distance_km=self._calculate_simple_distance(
                            origin,
                            destination
                        )
                    )
                ]
            
            self._log_exit("get_country_segments", segments)
            return segments
            
        except Exception as e:
            self._log_error("get_country_segments", e)
            raise ValueError(f"Failed to get country segments: {str(e)}")
    
    def validate_location(self, location: Location) -> bool:
        """Validate location data.
        
        Args:
            location: Location to validate
            
        Returns:
            True if location is valid
            
        Raises:
            ValueError: If location is invalid
        """
        self._log_entry("validate_location", location=location)
        
        try:
            # Check required fields
            self._validate_required(location, "location")
            self._validate_coordinates(location)
            
            # Validate country code
            if not location.country_code:
                raise ValueError("Country code is required")
            if len(location.country_code) != 2:
                raise ValueError("Country code must be 2 characters")
            
            # Validate postal code if present
            if location.postal_code and not self._is_valid_postal_code(
                location.postal_code,
                location.country_code
            ):
                raise ValueError("Invalid postal code")
            
            self._log_exit("validate_location", True)
            return True
            
        except Exception as e:
            self._log_error("validate_location", e)
            return False
    
    def _validate_coordinates(self, location: Location) -> None:
        """Validate location coordinates.
        
        Args:
            location: Location to validate
            
        Raises:
            ValueError: If coordinates are invalid
        """
        if not -90 <= location.latitude <= 90:
            raise ValueError("Invalid latitude")
        if not -180 <= location.longitude <= 180:
            raise ValueError("Invalid longitude")
    
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
        # Simple haversine formula
        from math import radians, sin, cos, sqrt, atan2
        
        lat1 = radians(origin.latitude)
        lon1 = radians(origin.longitude)
        lat2 = radians(destination.latitude)
        lon2 = radians(destination.longitude)
        
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
        # Add country-specific validation rules
        formats = {
            "DE": r"^\d{5}$",
            "PL": r"^\d{2}-\d{3}$",
            "FR": r"^\d{5}$",
            # Add more countries as needed
        }
        
        import re
        pattern = formats.get(country_code)
        if not pattern:
            return True  # Skip validation if format unknown
            
        return bool(re.match(pattern, postal_code))
