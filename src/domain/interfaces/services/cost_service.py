"""Cost service interface.

This module defines the interface for cost calculation services.
The CostService interface provides methods for:
- Calculating route costs
- Managing cost settings
- Handling cost breakdowns
- Cost history tracking

Implementation Requirements:
1. Cost Calculation:
   - Must use current cost settings
   - Should handle currency conversions
   - Must calculate all cost components
   - Should round appropriately

2. Settings Management:
   - Must use latest valid settings
   - Should handle settings updates
   - Must validate settings before use

3. History Tracking:
   - Must track all calculations
   - Should store calculation context
   - Must handle version changes

4. Error Handling:
   - Must validate all inputs
   - Should provide detailed errors
   - Must handle missing data gracefully

Example Usage:
    ```python
    # Calculate route cost
    cost = cost_service.calculate_route_cost(
        route_id="123",
        distance_km=450,
        duration_hours=5,
        country_segments=[
            {"country": "DE", "distance": 200},
            {"country": "FR", "distance": 250}
        ]
    )
    
    # Get cost breakdown
    breakdown = cost_service.get_cost_breakdown(cost.id)
    ```
"""
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from src.domain.entities.cost import Cost, CostSettings
from src.domain.interfaces.exceptions.service_errors import ServiceError

class CostServiceError(ServiceError):
    """Exception raised for errors in the cost service.
    
    This includes:
    - Invalid cost calculations
    - Missing required data
    - Settings validation errors
    - History retrieval failures
    """
    pass

class CostService(ABC):
    """Interface for cost calculation services.
    
    This interface defines the contract for cost calculations and management.
    It provides methods for calculating costs, managing settings, and
    tracking cost history.
    """

    @abstractmethod
    def calculate_route_cost(
        self,
        route_id: UUID,
        distance_km: Decimal,
        duration_hours: Decimal,
        country_segments: List[Dict],
        settings: Optional[CostSettings] = None
    ) -> Cost:
        """Calculate cost for a route.
        
        Args:
            route_id: ID of the route
            distance_km: Total distance in kilometers
            duration_hours: Total duration in hours
            country_segments: List of country segments with distances
            settings: Optional specific settings to use
            
        Returns:
            Calculated cost with breakdown
            
        Raises:
            CostServiceError: If calculation fails
            
        Implementation Notes:
            - Must use current settings if none provided
            - Should calculate all cost components
            - Must handle currency conversions
            - Should round appropriately
        """
        pass

    @abstractmethod
    def get_cost_breakdown(
        self,
        cost_id: UUID
    ) -> Dict:
        """Get detailed breakdown of a cost calculation.
        
        Args:
            cost_id: ID of the cost calculation
            
        Returns:
            Detailed cost breakdown including:
            - Base costs
            - Distance costs
            - Time costs
            - Additional fees
            - Adjustments
            
        Raises:
            CostServiceError: If breakdown retrieval fails
            
        Implementation Notes:
            - Must show all cost components
            - Should explain calculations
            - Must maintain precision
            - Should format currency consistently
        """
        pass

    @abstractmethod
    def validate_cost(
        self,
        cost: Cost,
        settings: Optional[CostSettings] = None
    ) -> bool:
        """Validate a cost calculation.
        
        Args:
            cost: Cost to validate
            settings: Optional settings to validate against
            
        Returns:
            True if cost is valid, False otherwise
            
        Raises:
            CostServiceError: If validation fails
            
        Implementation Notes:
            - Must check all components
            - Should verify calculations
            - Must use correct settings version
            - Should explain validation failures
        """
        pass

    @abstractmethod
    def get_cost_history(
        self,
        route_id: UUID
    ) -> List[Cost]:
        """Get history of cost calculations for a route.
        
        Args:
            route_id: ID of the route
            
        Returns:
            List of historical costs
            
        Raises:
            CostServiceError: If history retrieval fails
            
        Implementation Notes:
            - Must order by calculation time
            - Should include settings versions
            - Must track changes
            - Should explain recalculations
        """
        pass
