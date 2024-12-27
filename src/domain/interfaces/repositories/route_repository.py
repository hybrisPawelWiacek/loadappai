"""Route repository interface.

This module defines the interface for route data persistence.
The RouteRepository interface provides methods for:
- Managing route entities
- Route history tracking
- Route metadata management
- Route search and filtering

Implementation Requirements:
1. Route Management:
   - Must handle route lifecycle
   - Should track versions
   - Must store segments
   - Should manage metadata

2. History:
   - Must track modifications
   - Should store change reasons
   - Must maintain audit trail
   - Should handle versions

3. Search:
   - Must support filtering
   - Should enable sorting
   - Must handle pagination
   - Should optimize queries

4. Validation:
   - Must verify locations
   - Should check constraints
   - Must validate segments
   - Should verify references

Example Usage:
    ```python
    # Create new route
    route = repository.create(new_route)
    
    # Find routes by criteria
    routes = repository.find_routes(
        origin="Berlin",
        destination="Paris",
        vehicle_type="truck_40t"
    )
    
    # Get route history
    history = repository.get_route_history(route_id)
    ```
"""
from abc import abstractmethod
from typing import Dict, List, Optional
from uuid import UUID

from src.domain.entities.route import Route
from src.domain.value_objects import Location
from src.domain.interfaces.repositories.base import Repository
from src.domain.interfaces.exceptions.repository_errors import EntityNotFoundError

class RouteRepository(Repository[Route]):
    """Interface for route data persistence.
    
    This interface defines the contract for route data access and
    management. It extends the base Repository interface with
    route-specific operations.
    """

    @abstractmethod
    def find_routes(
        self,
        origin: Optional[Location] = None,
        destination: Optional[Location] = None,
        vehicle_type: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        per_page: int = 10
    ) -> List[Route]:
        """Find routes matching criteria.
        
        Args:
            origin: Optional origin location
            destination: Optional destination location
            vehicle_type: Optional vehicle type
            status: Optional route status
            page: Page number
            per_page: Results per page
            
        Returns:
            List of matching routes
            
        Implementation Notes:
            - Must support partial matches
            - Should optimize common queries
            - Must handle pagination
            - Should cache results
        """
        pass

    @abstractmethod
    def get_route_history(
        self,
        route_id: UUID
    ) -> List[Dict]:
        """Get history of route changes.
        
        Args:
            route_id: ID of the route
            
        Returns:
            List of historical changes
            
        Raises:
            EntityNotFoundError: If route not found
            
        Implementation Notes:
            - Must track all changes
            - Should include timestamps
            - Must store change reasons
            - Should handle versions
        """
        pass

    @abstractmethod
    def get_active_routes(
        self,
        page: int = 1,
        per_page: int = 10
    ) -> List[Route]:
        """Get currently active routes.
        
        Args:
            page: Page number
            per_page: Results per page
            
        Returns:
            List of active routes
            
        Implementation Notes:
            - Must filter by status
            - Should order by priority
            - Must handle pagination
            - Should cache results
        """
        pass

    @abstractmethod
    def update_route_status(
        self,
        route_id: UUID,
        status: str,
        reason: Optional[str] = None
    ) -> Route:
        """Update route status.
        
        Args:
            route_id: ID of the route
            status: New status
            reason: Optional reason for change
            
        Returns:
            Updated route
            
        Raises:
            EntityNotFoundError: If route not found
            
        Implementation Notes:
            - Must validate status
            - Should track change reason
            - Must update timestamp
            - Should notify listeners
        """
        pass

    @abstractmethod
    def get_route_metadata(
        self,
        route_id: UUID
    ) -> Dict:
        """Get route metadata.
        
        Args:
            route_id: ID of the route
            
        Returns:
            Route metadata
            
        Raises:
            EntityNotFoundError: If route not found
            
        Implementation Notes:
            - Must handle missing data
            - Should parse formats
            - Must validate schema
            - Should cache results
        """
        pass
