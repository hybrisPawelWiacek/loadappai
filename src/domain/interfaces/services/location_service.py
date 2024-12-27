"""Location service interface.

This module defines the interface for location and routing services.
The LocationService interface provides methods for:
- Distance calculations
- Duration estimates
- Route segmentation
- Location validation

Implementation Requirements:
1. Distance Calculation:
   - Must use real-world routes
   - Should handle multiple transportation modes
   - Must consider traffic conditions
   - Should cache common routes

2. Duration Estimation:
   - Must include traffic conditions
   - Should consider time of day
   - Must handle different vehicle types
   - Should update estimates in real-time

3. Route Segmentation:
   - Must identify country segments
   - Should handle border crossings
   - Must calculate segment distances
   - Should identify toll roads

4. Location Validation:
   - Must verify addresses exist
   - Should standardize formats
   - Must handle multiple countries
   - Should suggest corrections

Example Usage:
    ```python
    # Calculate route distance
    distance = location_service.calculate_distance(
        origin="Berlin, Germany",
        destination="Paris, France"
    )
    
    # Get route segments
    segments = location_service.get_route_segments(
        origin="Berlin, Germany",
        destination="Paris, France",
        include_tolls=True
    )
    ```
"""
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from src.domain.value_objects import Location, CountrySegment
from src.domain.interfaces.exceptions.service_errors import LocationServiceError

class LocationService(ABC):
    """Interface for location and routing services.
    
    This interface defines the contract for location-based operations
    including distance calculations, duration estimates, and route
    segmentation.
    """

    @abstractmethod
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
            LocationServiceError: If distance calculation fails
            
        Implementation Notes:
            - Must use real driving routes
            - Should consider road restrictions
            - Must handle multiple countries
            - Should cache common routes
        """
        pass

    @abstractmethod
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
            LocationServiceError: If duration calculation fails
            
        Implementation Notes:
            - Must include traffic conditions
            - Should consider time of day
            - Must handle rest periods
            - Should update in real-time
        """
        pass

    @abstractmethod
    def get_route_segments(
        self,
        origin: Location,
        destination: Location,
        include_tolls: bool = False
    ) -> List[CountrySegment]:
        """Get country segments for a route.
        
        Args:
            origin: Starting location
            destination: End location
            include_tolls: Whether to include toll information
            
        Returns:
            List of country segments with distances
            
        Raises:
            LocationServiceError: If segment calculation fails
            
        Implementation Notes:
            - Must identify all countries
            - Should handle border crossings
            - Must calculate segment distances
            - Should identify toll roads
        """
        pass

    @abstractmethod
    def validate_location(
        self,
        location: Location
    ) -> bool:
        """Validate a location.
        
        Args:
            location: Location to validate
            
        Returns:
            True if location is valid, False otherwise
            
        Raises:
            LocationServiceError: If validation fails
            
        Implementation Notes:
            - Must verify address exists
            - Should standardize format
            - Must handle multiple countries
            - Should suggest corrections
        """
        pass
