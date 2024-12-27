"""Toll rate service implementation.

This module implements the toll rate service interface.
It provides functionality for:
- Calculating toll rates
- Managing toll settings
- Handling vehicle types
- Country-specific rates
"""
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from src.domain.entities.cost import CostSettings
from src.domain.entities.route import Route, TransportType
from src.domain.entities.vehicle import VehicleSpecification
from src.domain.interfaces.services.toll_rate_service import TollRateService
from src.domain.services.common.base import BaseService
from src.domain.value_objects import CountrySegment, TollRate

class TollRateServiceImpl(BaseService, TollRateService):
    """Service for calculating toll rates.
    
    This service is responsible for:
    - Calculating toll costs
    - Managing toll settings
    - Handling vehicle types
    - Country-specific rates
    """
    
    def __init__(
        self,
        settings_service: Optional['CostSettingsService'] = None,
        toll_api_client: Optional['TollAPIClient'] = None
    ):
        """Initialize toll rate service.
        
        Args:
            settings_service: Optional service for cost settings
            toll_api_client: Optional client for toll API
        """
        super().__init__()
        self.settings_service = settings_service
        self._toll_api_client = toll_api_client
    
    def calculate_toll(
        self,
        route_id: UUID,
        vehicle_type: str,
        country_code: Optional[str] = None,
        distance: Optional[float] = None,
        axles: Optional[int] = None,
        weight: Optional[float] = None
    ) -> Decimal:
        """Calculate toll cost for a route segment.
        
        Args:
            route_id: Route ID
            vehicle_type: Type of vehicle
            country_code: Optional country code
            distance: Optional distance in km
            axles: Optional number of axles
            weight: Optional vehicle weight
            
        Returns:
            Calculated toll cost
            
        Raises:
            ValueError: If calculation fails
        """
        self._log_entry(
            "calculate_toll",
            route_id=route_id,
            vehicle_type=vehicle_type,
            country_code=country_code
        )
        
        try:
            # Try external API first
            if self._toll_api_client:
                toll = self._calculate_toll_from_api(
                    route_id,
                    vehicle_type,
                    country_code,
                    distance,
                    axles,
                    weight
                )
                if toll is not None:
                    return toll
            
            # Fallback to internal calculation
            toll = self._calculate_toll_internal(
                route_id,
                vehicle_type,
                country_code,
                distance,
                axles,
                weight
            )
            
            self._log_exit("calculate_toll", toll)
            return toll
            
        except Exception as e:
            self._log_error("calculate_toll", e)
            raise ValueError(f"Failed to calculate toll: {str(e)}")
    
    def get_toll_rate(
        self,
        country_code: str,
        vehicle_type: str,
        axles: Optional[int] = None,
        weight: Optional[float] = None
    ) -> TollRate:
        """Get toll rate for specific parameters.
        
        Args:
            country_code: Country code
            vehicle_type: Type of vehicle
            axles: Optional number of axles
            weight: Optional vehicle weight
            
        Returns:
            Toll rate configuration
            
        Raises:
            ValueError: If rate not found
        """
        self._log_entry(
            "get_toll_rate",
            country_code=country_code,
            vehicle_type=vehicle_type
        )
        
        try:
            # Get current settings
            settings = (
                self.settings_service.get_current_settings()
                if self.settings_service
                else None
            )
            
            if not settings:
                return self._get_default_toll_rate(
                    country_code,
                    vehicle_type
                )
            
            # Get country settings
            country_settings = settings.country_settings.get(country_code)
            if not country_settings:
                return self._get_default_toll_rate(
                    country_code,
                    vehicle_type
                )
            
            # Apply vehicle multiplier
            base_rate = country_settings.toll_rate
            multiplier = self._get_vehicle_multiplier(
                vehicle_type,
                axles,
                weight
            )
            
            rate = TollRate(
                base_rate=base_rate,
                vehicle_multiplier=multiplier,
                effective_rate=base_rate * multiplier,
                country_code=country_code,
                vehicle_type=vehicle_type,
                metadata={
                    "axles": axles,
                    "weight": weight
                }
            )
            
            self._log_exit("get_toll_rate", rate)
            return rate
            
        except Exception as e:
            self._log_error("get_toll_rate", e)
            raise ValueError(f"Failed to get toll rate: {str(e)}")
    
    def _calculate_toll_from_api(
        self,
        route_id: UUID,
        vehicle_type: str,
        country_code: Optional[str],
        distance: Optional[float],
        axles: Optional[int],
        weight: Optional[float]
    ) -> Optional[Decimal]:
        """Calculate toll using external API.
        
        Args:
            route_id: Route ID
            vehicle_type: Type of vehicle
            country_code: Optional country code
            distance: Optional distance in km
            axles: Optional number of axles
            weight: Optional vehicle weight
            
        Returns:
            Calculated toll or None if API fails
        """
        if not self._toll_api_client:
            return None
            
        try:
            response = self._toll_api_client.calculate_toll(
                route_id=route_id,
                vehicle_type=vehicle_type,
                country_code=country_code,
                distance=distance,
                axles=axles,
                weight=weight
            )
            
            if response and "toll_amount" in response:
                return Decimal(str(response["toll_amount"]))
                
            return None
            
        except Exception as e:
            self.logger.warning(
                f"API toll calculation failed: {str(e)}",
                exc_info=True
            )
            return None
    
    def _calculate_toll_internal(
        self,
        route_id: UUID,
        vehicle_type: str,
        country_code: Optional[str],
        distance: Optional[float],
        axles: Optional[int],
        weight: Optional[float]
    ) -> Decimal:
        """Calculate toll using internal logic.
        
        Args:
            route_id: Route ID
            vehicle_type: Type of vehicle
            country_code: Optional country code
            distance: Optional distance in km
            axles: Optional number of axles
            weight: Optional vehicle weight
            
        Returns:
            Calculated toll
            
        Raises:
            ValueError: If calculation fails
        """
        if not country_code or not distance:
            raise ValueError("Country code and distance required for calculation")
        
        # Get toll rate
        rate = self.get_toll_rate(
            country_code,
            vehicle_type,
            axles,
            weight
        )
        
        # Calculate toll
        toll = Decimal(str(distance)) * rate.effective_rate
        
        return toll
    
    def _get_default_toll_rate(
        self,
        country_code: str,
        vehicle_type: str
    ) -> TollRate:
        """Get default toll rate for country and vehicle.
        
        Args:
            country_code: Country code
            vehicle_type: Type of vehicle
            
        Returns:
            Default toll rate
        """
        # Default rates by country (EUR/km)
        default_rates = {
            "DE": Decimal("0.20"),
            "FR": Decimal("0.25"),
            "IT": Decimal("0.22"),
            "ES": Decimal("0.18"),
            "PL": Decimal("0.15")
        }
        
        base_rate = default_rates.get(country_code, Decimal("0.20"))
        multiplier = self._get_vehicle_multiplier(vehicle_type)
        
        return TollRate(
            base_rate=base_rate,
            vehicle_multiplier=multiplier,
            effective_rate=base_rate * multiplier,
            country_code=country_code,
            vehicle_type=vehicle_type
        )
    
    def _get_vehicle_multiplier(
        self,
        vehicle_type: str,
        axles: Optional[int] = None,
        weight: Optional[float] = None
    ) -> Decimal:
        """Get toll multiplier for vehicle type.
        
        Args:
            vehicle_type: Type of vehicle
            axles: Optional number of axles
            weight: Optional vehicle weight
            
        Returns:
            Toll multiplier
        """
        # Base multipliers by vehicle type
        base_multipliers = {
            "truck": Decimal("1.0"),
            "bus": Decimal("0.8"),
            "van": Decimal("0.6"),
            "car": Decimal("0.4")
        }
        
        multiplier = base_multipliers.get(vehicle_type.lower(), Decimal("1.0"))
        
        # Adjust for axles
        if axles:
            if axles > 2:
                multiplier *= Decimal("1.2")
            if axles > 4:
                multiplier *= Decimal("1.3")
        
        # Adjust for weight
        if weight:
            if weight > 12000:  # 12 tonnes
                multiplier *= Decimal("1.2")
            if weight > 40000:  # 40 tonnes
                multiplier *= Decimal("1.4")
        
        return multiplier
