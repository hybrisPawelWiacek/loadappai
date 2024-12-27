"""Toll rate service interface.

This module defines the interface for toll rate calculations.
The TollRateService interface provides methods for:
- Calculating toll rates for routes
- Managing toll rate settings
- Handling toll rate updates
- Validating toll calculations

Implementation Requirements:
1. Rate Calculation:
   - Must handle different vehicle types
   - Should consider time of day
   - Must support multiple regions
   - Should handle currency conversion

2. Settings Management:
   - Must maintain rate tables
   - Should track rate changes
   - Must validate settings
   - Should support schedules

3. Updates:
   - Must handle rate updates
   - Should maintain history
   - Must validate changes
   - Should notify affected routes

4. Validation:
   - Must verify calculations
   - Should explain charges
   - Must handle edge cases
   - Should detect anomalies

Example Usage:
    ```python
    # Calculate toll for route
    toll = service.calculate_toll(
        route_id=route_id,
        vehicle_type="truck",
        time=datetime.now()
    )
    
    # Get current rates
    rates = service.get_current_rates("region_1")
    
    # Update rates
    success = service.update_rates(
        region="region_1",
        new_rates=rates_data,
        effective_date=date(2024, 1, 1)
    )
    ```
"""
from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from src.domain.interfaces.exceptions.service_errors import ServiceError

class TollRateServiceError(ServiceError):
    """Exception raised for errors in toll rate calculations.
    
    This includes:
    - Invalid rate configurations
    - Calculation errors
    - Missing rate data
    - Validation failures
    """
    pass

class TollRateService(ABC):
    """Interface for toll rate calculations.
    
    This interface defines the contract for calculating and managing
    toll rates for different routes, vehicle types, and times.
    """

    @abstractmethod
    def calculate_toll(
        self,
        route_id: UUID,
        vehicle_type: str,
        time: Optional[datetime] = None
    ) -> Decimal:
        """Calculate toll for a route.
        
        Args:
            route_id: ID of the route
            vehicle_type: Type of vehicle
            time: Optional time for rate calculation
            
        Returns:
            Calculated toll amount
            
        Raises:
            TollRateServiceError: If calculation fails
            
        Implementation Notes:
            - Must validate inputs
            - Should handle time zones
            - Must use current rates
            - Should cache results
        """
        pass

    @abstractmethod
    def get_current_rates(
        self,
        region: str
    ) -> Dict:
        """Get current toll rates for region.
        
        Args:
            region: Region code
            
        Returns:
            Current rate configuration
            
        Raises:
            TollRateServiceError: If rates not found
            
        Implementation Notes:
            - Must validate region
            - Should cache rates
            - Must handle updates
            - Should track access
        """
        pass

    @abstractmethod
    def update_rates(
        self,
        region: str,
        new_rates: Dict,
        effective_date: datetime
    ) -> bool:
        """Update toll rates for region.
        
        Args:
            region: Region code
            new_rates: New rate configuration
            effective_date: When rates become effective
            
        Returns:
            True if update successful
            
        Raises:
            TollRateServiceError: If update fails
            
        Implementation Notes:
            - Must validate rates
            - Should track changes
            - Must handle rollback
            - Should notify systems
        """
        pass

    @abstractmethod
    def validate_rates(
        self,
        rates: Dict
    ) -> bool:
        """Validate rate configuration.
        
        Args:
            rates: Rate configuration to validate
            
        Returns:
            True if rates are valid
            
        Raises:
            TollRateServiceError: If validation fails
            
        Implementation Notes:
            - Must check structure
            - Should verify values
            - Must ensure consistency
            - Should explain issues
        """
        pass

    @abstractmethod
    def get_rate_history(
        self,
        region: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict]:
        """Get history of rate changes.
        
        Args:
            region: Region code
            start_date: Start of period
            end_date: End of period
            
        Returns:
            List of historical changes
            
        Raises:
            TollRateServiceError: If history retrieval fails
            
        Implementation Notes:
            - Must validate dates
            - Should handle timezones
            - Must track access
            - Should cache results
        """
        pass

    @abstractmethod
    def has_toll_roads(self, country_code: str) -> bool:
        """Check if a country has toll roads.
        
        Args:
            country_code: ISO country code
            
        Returns:
            True if country has toll roads, False otherwise
            
        Implementation Notes:
            - Must validate country code
            - Should cache results
            - Must handle updates
            - Should track access
        """
        pass
