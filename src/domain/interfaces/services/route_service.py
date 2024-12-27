"""Route service interface.

This module defines the interface for route planning services.
The RouteService interface provides methods for:
- Route planning and optimization
- Empty driving calculations
- Route validation and analysis
- History tracking

Implementation Requirements:
1. Route Planning:
   - Must consider vehicle constraints
   - Should optimize for efficiency
   - Must handle multiple stops
   - Should avoid restricted areas

2. Empty Driving:
   - Must calculate empty segments
   - Should optimize positioning
   - Must track empty distances
   - Should suggest alternatives

3. Validation:
   - Must verify all locations
   - Should check time windows
   - Must validate distances
   - Should verify restrictions

4. History:
   - Must track all changes
   - Should store optimizations
   - Must maintain versions
   - Should explain changes

Example Usage:
    ```python
    # Plan a new route
    route = route_service.plan_route(
        pickup="Berlin, Germany",
        delivery="Paris, France",
        vehicle_type="truck_40t"
    )
    
    # Calculate empty driving
    empty_route = route_service.calculate_empty_driving(
        end_location="Munich",
        next_pickup="Frankfurt"
    )
    ```
"""
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from src.domain.entities.route import Route
from src.domain.value_objects import Location
from src.domain.interfaces.exceptions.service_errors import ServiceError

class RouteServiceError(ServiceError):
    """Exception raised for errors in the route service.
    
    This includes:
    - Invalid locations
    - Planning failures
    - Optimization errors
    - Validation failures
    """
    pass

class RouteService(ABC):
    """Interface for route planning services.
    
    This interface defines the contract for route-related operations
    including planning, optimization, and empty driving calculations.
    """

    @abstractmethod
    def plan_route(
        self,
        pickup: Location,
        delivery: Location,
        vehicle_type: str,
        constraints: Optional[Dict] = None
    ) -> Route:
        """Plan an optimal route.
        
        Args:
            pickup: Pickup location
            delivery: Delivery location
            vehicle_type: Type of vehicle
            constraints: Optional routing constraints
            
        Returns:
            Planned route
            
        Raises:
            RouteServiceError: If planning fails
            
        Implementation Notes:
            - Must validate locations
            - Should optimize path
            - Must consider restrictions
            - Should handle constraints
        """
        pass

    @abstractmethod
    def calculate_empty_driving(
        self,
        end_location: Location,
        next_pickup: Location,
        constraints: Optional[Dict] = None
    ) -> Route:
        """Calculate empty driving route.
        
        Args:
            end_location: Current end location
            next_pickup: Next pickup location
            constraints: Optional routing constraints
            
        Returns:
            Empty driving route
            
        Raises:
            RouteServiceError: If calculation fails
            
        Implementation Notes:
            - Must optimize positioning
            - Should consider alternatives
            - Must track empty distance
            - Should minimize costs
        """
        pass

    @abstractmethod
    def validate_route(
        self,
        route: Route
    ) -> bool:
        """Validate a planned route.
        
        Args:
            route: Route to validate
            
        Returns:
            True if route is valid
            
        Raises:
            RouteServiceError: If validation fails
            
        Implementation Notes:
            - Must check all segments
            - Should verify restrictions
            - Must validate times
            - Should check feasibility
        """
        pass

    @abstractmethod
    def get_route_alternatives(
        self,
        route: Route,
        max_alternatives: int = 3
    ) -> List[Route]:
        """Get alternative routes.
        
        Args:
            route: Base route
            max_alternatives: Maximum number of alternatives
            
        Returns:
            List of alternative routes
            
        Raises:
            RouteServiceError: If alternatives calculation fails
            
        Implementation Notes:
            - Must vary parameters
            - Should optimize differently
            - Must maintain feasibility
            - Should explain differences
        """
        pass

    @abstractmethod
    def optimize_route(
        self,
        route: Route,
        optimization_type: str
    ) -> Route:
        """Optimize an existing route.
        
        Args:
            route: Route to optimize
            optimization_type: Type of optimization
            
        Returns:
            Optimized route
            
        Raises:
            RouteServiceError: If optimization fails
            
        Implementation Notes:
            - Must preserve constraints
            - Should improve efficiency
            - Must maintain feasibility
            - Should track improvements
        """
        pass

    @abstractmethod
    def create_route(self, 
        origin: Location, 
        destination: Location,
        via_points: Optional[List[Location]] = None
    ) -> Route:
        """Create a new route with optional via points.
        
        Args:
            origin: Starting location
            destination: End location
            via_points: Optional list of locations to visit
            
        Returns:
            Created route
            
        Raises:
            RouteServiceError: If route creation fails
        """
        pass

    @abstractmethod
    def optimize_empty_driving(self, route: Route) -> Route:
        """Optimize empty driving segments of a route.
        
        Args:
            route: Route to optimize
            
        Returns:
            Optimized route
            
        Raises:
            RouteServiceError: If optimization fails
        """
        pass

    @abstractmethod
    def get_route_details(self, route_id: UUID) -> Dict:
        """Get detailed information about a route.
        
        Args:
            route_id: Route ID
            
        Returns:
            Dictionary containing route details
            
        Raises:
            RouteServiceError: If route not found or details retrieval fails
        """
        pass

    @abstractmethod
    def update_route(self, route_id: UUID, updates: Dict) -> Route:
        """Update route information.
        
        Args:
            route_id: Route ID
            updates: Dictionary of fields to update
            
        Returns:
            Updated route
            
        Raises:
            RouteServiceError: If route not found or update fails
        """
        pass
