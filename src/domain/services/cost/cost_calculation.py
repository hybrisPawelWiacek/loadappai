"""Cost calculation service implementation.

This module implements the cost calculation service interface.
It provides functionality for:
- Calculating total transport costs
- Breaking down costs by category
- Handling different pricing strategies
- Managing cost components
"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from src.domain.entities.cost import Cost, CostSettings
from src.domain.entities.route import Route, TransportType
from src.domain.entities.cargo import CargoSpecification
from src.domain.entities.vehicle import VehicleSpecification
from src.domain.interfaces.services.cost_service import CostService
from src.domain.services.common.base import BaseService
from src.domain.value_objects import (
    CostBreakdown, CostComponent, CountrySegment
)

class CostCalculationService(BaseService, CostService):
    """Service for calculating transport costs.
    
    This service is responsible for:
    - Calculating total transport costs
    - Breaking down costs by category
    - Handling different pricing strategies
    - Managing cost components
    """
    
    def __init__(
        self,
        settings_service: Optional['CostSettingsService'] = None,
        toll_service: Optional['TollRateService'] = None
    ):
        """Initialize cost calculation service.
        
        Args:
            settings_service: Optional service for cost settings
            toll_service: Optional service for toll rates
        """
        super().__init__()
        self.settings_service = settings_service
        self.toll_service = toll_service
    
    def calculate_detailed_cost(
        self,
        route: Route,
        settings: Optional[CostSettings] = None,
        cargo_spec: Optional[CargoSpecification] = None,
        vehicle_spec: Optional[VehicleSpecification] = None,
        include_empty_driving: bool = True,
        include_country_breakdown: bool = True,
        validity_period: Optional[timedelta] = None
    ) -> Cost:
        """Calculate detailed cost breakdown for a route.
        
        Args:
            route: Route to calculate costs for
            settings: Optional cost settings to use
            cargo_spec: Optional cargo specifications
            vehicle_spec: Optional vehicle specifications
            include_empty_driving: Whether to include empty driving
            include_country_breakdown: Whether to break down by country
            validity_period: Optional validity period
            
        Returns:
            Detailed cost breakdown
            
        Raises:
            ValueError: If calculation fails
        """
        self._log_entry(
            "calculate_detailed_cost",
            route=route,
            settings=settings,
            cargo_spec=cargo_spec,
            vehicle_spec=vehicle_spec
        )
        
        try:
            # Get settings if not provided
            if not settings and self.settings_service:
                settings = self.settings_service.get_current_settings()
            
            if not settings:
                raise ValueError("Cost settings are required")
            
            # Initialize cost components
            components: List[CostComponent] = []
            
            # Calculate base costs
            components.extend(self._calculate_fuel_costs(
                route,
                settings,
                vehicle_spec
            ))
            
            components.extend(self._calculate_toll_costs(
                route,
                settings,
                vehicle_spec
            ))
            
            components.extend(self._calculate_driver_costs(
                route,
                settings
            ))
            
            components.extend(self._calculate_maintenance_costs(
                route,
                settings,
                vehicle_spec
            ))
            
            components.extend(self._calculate_overhead_costs(
                route,
                settings
            ))
            
            # Add empty driving costs if needed
            if include_empty_driving and route.metadata.get("empty_driving"):
                components.extend(self._calculate_empty_driving_costs(
                    route,
                    settings,
                    vehicle_spec
                ))
            
            # Create cost object
            cost = Cost(
                route_id=route.id,
                components=components,
                validity_period=validity_period or timedelta(hours=24),
                calculated_at=datetime.utcnow()
            )
            
            # Update totals
            self._update_cost_totals(cost, components)
            
            self._log_exit("calculate_detailed_cost", cost)
            return cost
            
        except Exception as e:
            self._log_error("calculate_detailed_cost", e)
            raise ValueError(f"Failed to calculate costs: {str(e)}")
    
    def _calculate_fuel_costs(
        self,
        route: Route,
        settings: CostSettings,
        vehicle_spec: Optional[VehicleSpecification]
    ) -> List[CostComponent]:
        """Calculate fuel costs for each country segment.
        
        Args:
            route: Route to calculate for
            settings: Cost settings to use
            vehicle_spec: Optional vehicle specifications
            
        Returns:
            List of fuel cost components
        """
        components = []
        
        # Get fuel consumption rate
        consumption = (
            vehicle_spec.fuel_consumption
            if vehicle_spec
            else settings.default_fuel_consumption
        )
        
        # Calculate for each segment
        for segment in route.metadata.get("country_segments", []):
            fuel_price = settings.get_fuel_price(segment["country_code"])
            distance = segment["distance_km"]
            
            cost = Decimal(str(distance * consumption * fuel_price))
            
            components.append(CostComponent(
                category="fuel",
                amount=cost,
                country_code=segment["country_code"],
                details={
                    "distance_km": distance,
                    "consumption_rate": consumption,
                    "fuel_price": fuel_price
                }
            ))
        
        return components
    
    def _calculate_toll_costs(
        self,
        route: Route,
        settings: CostSettings,
        vehicle_spec: Optional[VehicleSpecification]
    ) -> List[CostComponent]:
        """Calculate toll costs for each country segment.
        
        Args:
            route: Route to calculate for
            settings: Cost settings to use
            vehicle_spec: Optional vehicle specifications
            
        Returns:
            List of toll cost components
        """
        components = []
        
        # Use toll service if available
        if self.toll_service:
            for segment in route.metadata.get("country_segments", []):
                toll = self.toll_service.calculate_toll(
                    route.id,
                    vehicle_spec.vehicle_type if vehicle_spec else "truck"
                )
                
                components.append(CostComponent(
                    category="toll",
                    amount=toll,
                    country_code=segment["country_code"],
                    details={
                        "vehicle_type": (
                            vehicle_spec.vehicle_type
                            if vehicle_spec
                            else "truck"
                        )
                    }
                ))
        else:
            # Use simple estimation
            for segment in route.metadata.get("country_segments", []):
                distance = segment["distance_km"]
                rate = settings.get_toll_rate(segment["country_code"])
                
                cost = Decimal(str(distance * rate))
                
                components.append(CostComponent(
                    category="toll",
                    amount=cost,
                    country_code=segment["country_code"],
                    details={
                        "distance_km": distance,
                        "toll_rate": rate
                    }
                ))
        
        return components
    
    def _calculate_driver_costs(
        self,
        route: Route,
        settings: CostSettings
    ) -> List[CostComponent]:
        """Calculate driver costs for each country segment.
        
        Args:
            route: Route to calculate for
            settings: Cost settings to use
            
        Returns:
            List of driver cost components
        """
        components = []
        
        for segment in route.metadata.get("country_segments", []):
            duration = segment.get("duration_hours", 0)
            rate = settings.get_driver_rate(segment["country_code"])
            
            cost = Decimal(str(duration * rate))
            
            components.append(CostComponent(
                category="driver",
                amount=cost,
                country_code=segment["country_code"],
                details={
                    "duration_hours": duration,
                    "driver_rate": rate
                }
            ))
        
        return components
    
    def _calculate_maintenance_costs(
        self,
        route: Route,
        settings: CostSettings,
        vehicle_spec: Optional[VehicleSpecification]
    ) -> List[CostComponent]:
        """Calculate maintenance costs.
        
        Args:
            route: Route to calculate for
            settings: Cost settings to use
            vehicle_spec: Optional vehicle specifications
            
        Returns:
            List of maintenance cost components
        """
        components = []
        
        # Get maintenance rate
        rate = (
            vehicle_spec.maintenance_rate
            if vehicle_spec
            else settings.default_maintenance_rate
        )
        
        # Calculate for total distance
        distance = route.distance_km
        cost = Decimal(str(distance * rate))
        
        components.append(CostComponent(
            category="maintenance",
            amount=cost,
            details={
                "distance_km": distance,
                "maintenance_rate": rate
            }
        ))
        
        return components
    
    def _calculate_overhead_costs(
        self,
        route: Route,
        settings: CostSettings
    ) -> List[CostComponent]:
        """Calculate overhead costs.
        
        Args:
            route: Route to calculate for
            settings: Cost settings to use
            
        Returns:
            List of overhead cost components
        """
        components = []
        
        # Calculate based on duration
        duration = route.duration_hours
        rate = settings.overhead_rate
        
        cost = Decimal(str(duration * rate))
        
        components.append(CostComponent(
            category="overhead",
            amount=cost,
            details={
                "duration_hours": duration,
                "overhead_rate": rate
            }
        ))
        
        return components
    
    def _calculate_empty_driving_costs(
        self,
        route: Route,
        settings: CostSettings,
        vehicle_spec: Optional[VehicleSpecification]
    ) -> List[CostComponent]:
        """Calculate costs for empty driving segments.
        
        Args:
            route: Route to calculate for
            settings: Cost settings to use
            vehicle_spec: Optional vehicle specifications
            
        Returns:
            List of empty driving cost components
        """
        components = []
        
        empty_driving = route.metadata.get("empty_driving")
        if not empty_driving:
            return components
        
        # Calculate fuel costs
        consumption = (
            vehicle_spec.fuel_consumption
            if vehicle_spec
            else settings.default_fuel_consumption
        )
        
        distance = empty_driving["distance_km"]
        fuel_price = settings.get_fuel_price(
            empty_driving["origin"]["country_code"]
        )
        
        fuel_cost = Decimal(str(distance * consumption * fuel_price))
        
        components.append(CostComponent(
            category="empty_driving_fuel",
            amount=fuel_cost,
            details={
                "distance_km": distance,
                "consumption_rate": consumption,
                "fuel_price": fuel_price
            }
        ))
        
        # Calculate maintenance
        rate = (
            vehicle_spec.maintenance_rate
            if vehicle_spec
            else settings.default_maintenance_rate
        )
        
        maintenance_cost = Decimal(str(distance * rate))
        
        components.append(CostComponent(
            category="empty_driving_maintenance",
            amount=maintenance_cost,
            details={
                "distance_km": distance,
                "maintenance_rate": rate
            }
        ))
        
        return components
    
    def _update_cost_totals(
        self,
        cost: Cost,
        components: List[CostComponent]
    ) -> None:
        """Update cost totals from components.
        
        Args:
            cost: Cost object to update
            components: List of cost components
        """
        # Calculate totals
        cost.total_amount = sum(c.amount for c in components)
        
        # Calculate category subtotals
        cost.breakdown = {}
        for component in components:
            if component.category not in cost.breakdown:
                cost.breakdown[component.category] = Decimal("0")
            cost.breakdown[component.category] += component.amount
        
        # Calculate country breakdown
        cost.country_breakdown = {}
        for component in components:
            if not component.country_code:
                continue
                
            if component.country_code not in cost.country_breakdown:
                cost.country_breakdown[component.country_code] = Decimal("0")
            cost.country_breakdown[component.country_code] += component.amount
