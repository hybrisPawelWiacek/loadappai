"""Domain services for LoadApp.AI."""
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from src.domain.entities import Route, Offer, Cost, CostSettings, TransportType, Cargo
from src.domain.interfaces import LocationService, LocationServiceError
from src.domain.value_objects import (
    Location,
    CountrySegment,
    CostBreakdown,
    EmptyDriving,
    RouteMetadata
)


@dataclass
class RoutePlanningService:
    """
    Service for planning and validating transport routes.
    
    Responsibilities:
    - Create and validate transport routes
    - Calculate distances and durations
    - Handle empty driving calculations
    - Integrate with external mapping services
    """
    location_service: LocationService
    
    def create_route(
        self,
        origin: Location,
        destination: Location,
        pickup_time: datetime,
        delivery_time: datetime,
        transport_type: str,
        cargo_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Route:
        """
        Create a new route with the given parameters.
        
        Args:
            origin: Starting location with coordinates and address
            destination: End location with coordinates and address
            pickup_time: Scheduled pickup time
            delivery_time: Scheduled delivery time
            transport_type: Type of transport to use
            cargo_id: Optional ID of cargo to be transported
            metadata: Optional additional route metadata
            
        Returns:
            Route: Created route object with all necessary details
            
        Raises:
            ValueError: If route parameters are invalid
            LocationServiceError: If external service integration fails
        """
        # Validate input parameters
        self._validate_route_parameters(origin, destination, pickup_time, delivery_time)
        
        try:
            # Calculate route details using location service
            distance_km = self.location_service.calculate_distance(origin, destination)
            duration_hours = self.location_service.calculate_duration(origin, destination)
            country_segments = self.location_service.get_country_segments(origin, destination)
            
            # Calculate empty driving (placeholder for now)
            empty_driving = EmptyDriving(
                distance_km=0.0,
                duration_hours=0.0
            )
            
            # Prepare route metadata
            route_metadata = RouteMetadata(
                weather_data=metadata.get("weather_data") if metadata else None,
                traffic_data=metadata.get("traffic_data") if metadata else None,
                compliance_data=metadata.get("compliance_data") if metadata else None,
                optimization_data={
                    "distance_km": distance_km,
                    "duration_hours": duration_hours,
                    "transport_type": transport_type,
                    **(metadata.get("optimization_data", {}) if metadata else {})
                }
            )
            
            # Create and return route
            return Route(
                origin=origin,
                destination=destination,
                pickup_time=pickup_time,
                delivery_time=delivery_time,
                transport_type=transport_type,
                cargo_id=cargo_id,
                distance_km=distance_km,
                duration_hours=duration_hours,
                empty_driving=empty_driving,
                metadata=route_metadata
            )
            
        except LocationServiceError as e:
            raise ValueError(f"Failed to calculate route details: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error creating route: {str(e)}")
    
    def _validate_route_parameters(
        self,
        origin: Location,
        destination: Location,
        pickup_time: datetime,
        delivery_time: datetime
    ) -> None:
        """
        Validate route parameters.
        
        Raises:
            ValueError: If any validation fails
        """
        if pickup_time >= delivery_time:
            raise ValueError("Pickup time must be before delivery time")
        
        if origin == destination:
            raise ValueError("Origin and destination must be different")
        
        if pickup_time < datetime.now(timezone.utc):
            raise ValueError("Pickup time cannot be in the past")
    
    def _get_country_segments(self, origin: Location, destination: Location) -> List[CountrySegment]:
        """
        Get country segments for the route.
        
        To be integrated with Google Maps API for accurate country crossing data.
        """
        # Placeholder implementation
        return [CountrySegment(
            country_code="PL",
            distance=500.0,
            toll_rates={"standard": Decimal("0.15")}
        )]
    
    def _calculate_distance(self, origin: Location, destination: Location) -> float:
        """
        Calculate distance between two locations.
        
        To be integrated with Google Maps API for accurate distance calculation.
        """
        # Placeholder implementation
        return 500.0
    
    def _calculate_duration(self, pickup_time: datetime, delivery_time: datetime) -> float:
        """Calculate duration in hours between pickup and delivery."""
        duration = delivery_time - pickup_time
        return duration.total_seconds() / 3600


@dataclass
class CostCalculationService:
    """
    Service for calculating transport costs.
    
    Responsibilities:
    - Calculate total transport costs
    - Break down costs by category
    - Handle different pricing strategies
    - Apply cargo-specific cost factors
    """
    
    def calculate_route_cost(
        self,
        route: Route,
        settings: Optional[CostSettings] = None,
        cargo: Optional[Cargo] = None,
        transport_type: Optional[TransportType] = None
    ) -> CostBreakdown:
        """
        Calculate the total cost for a given route.
        
        Args:
            route: Route to calculate costs for
            settings: Optional cost settings (uses defaults if not provided)
            cargo: Optional cargo details for cargo-specific costs
            transport_type: Optional transport type for specific consumption rates
            
        Returns:
            CostBreakdown: Detailed breakdown of all costs
            
        Raises:
            ValueError: If required data is missing or invalid
        """
        if not settings:
            settings = self._get_default_settings()
        
        try:
            # Calculate base costs
            fuel_cost = self._calculate_fuel_cost(route, settings, transport_type)
            toll_cost = self._calculate_toll_cost(route, settings)
            driver_cost = self._calculate_driver_cost(route, settings)
            
            # Calculate cargo-specific costs if cargo provided
            cargo_costs = self._calculate_cargo_costs(cargo, settings) if cargo else {}
            
            # Calculate overhead
            base_cost = fuel_cost + toll_cost + driver_cost + sum(cargo_costs.values())
            overhead_cost = self._calculate_overhead_cost(base_cost, settings)
            
            return CostBreakdown(
                fuel_cost=fuel_cost,
                toll_cost=toll_cost,
                driver_cost=driver_cost,
                overheads=overhead_cost,
                cargo_specific_costs=cargo_costs,
                total_cost=base_cost + overhead_cost
            )
            
        except Exception as e:
            raise ValueError(f"Failed to calculate costs: {str(e)}") from e
    
    def get_cost_breakdown(self, route: Route, include_details: bool = False) -> Dict[str, Decimal]:
        """
        Get a detailed breakdown of costs for a route.
        
        Args:
            route: Route to get cost breakdown for
            include_details: If True, includes subcategories and metadata
            
        Returns:
            Dict[str, Decimal]: Cost breakdown by category
        """
        cost = self.calculate_route_cost(route)
        
        breakdown = {
            "fuel": cost.fuel_cost,
            "toll": cost.toll_cost,
            "driver": cost.driver_cost,
            "overhead": cost.overheads,
            "total": cost.total_cost
        }
        
        if include_details and cost.cargo_specific_costs:
            breakdown.update({
                f"cargo_{key}": value
                for key, value in cost.cargo_specific_costs.items()
            })
        
        return breakdown
    
    def _get_default_settings(self) -> CostSettings:
        """Get default cost calculation settings."""
        return CostSettings(
            fuel_price_per_liter=Decimal("2.0"),
            driver_daily_salary=Decimal("200.0"),
            toll_rates={"standard": Decimal("0.15")},
            overheads={"percentage": Decimal("0.15")},
            cargo_factors={}
        )
    
    def _calculate_fuel_cost(
        self,
        route: Route,
        settings: CostSettings,
        transport_type: Optional[TransportType] = None
    ) -> Decimal:
        """Calculate fuel cost based on distance and consumption rates."""
        total_distance = Decimal(str(route.total_distance))
        
        # Use transport-specific consumption if available
        if transport_type:
            loaded_consumption = Decimal(str(transport_type.fuel_consumption_loaded))
            empty_consumption = Decimal(str(transport_type.fuel_consumption_empty))
            
            loaded_distance = Decimal(str(route.distance_km))
            empty_distance = Decimal(str(route.empty_driving.distance_km))
            
            total_consumption = (loaded_distance * loaded_consumption +
                               empty_distance * empty_consumption)
            
            return total_consumption * settings.fuel_price_per_liter
        
        # Fallback to simple calculation
        return total_distance * settings.fuel_price_per_liter
    
    def _calculate_toll_cost(self, route: Route, settings: CostSettings) -> Decimal:
        """Calculate toll costs for the route."""
        total_toll_cost = Decimal("0")
        
        for segment in route.country_segments:
            segment_toll_cost = sum(segment.toll_rates.values())
            total_toll_cost += segment_toll_cost

        return total_toll_cost
    
    def _calculate_driver_cost(self, route: Route, settings: CostSettings) -> Decimal:
        """Calculate driver cost based on duration."""
        total_days = Decimal(str(route.total_duration)) / Decimal("24")
        return total_days * settings.driver_daily_salary
    
    def _calculate_overhead_cost(self, base_cost: Decimal, settings: CostSettings) -> Decimal:
        """Calculate overhead cost as percentage of base cost."""
        return base_cost * settings.overheads.get("percentage", Decimal("0.15"))
    
    def _calculate_cargo_costs(self, cargo: Cargo, settings: CostSettings) -> Dict[str, Decimal]:
        """
        Calculate cargo-specific costs based on cargo properties.
        
        Args:
            cargo: Cargo details
            settings: Cost settings with cargo factors
            
        Returns:
            Dict[str, Decimal]: Breakdown of cargo-specific costs
        """
        costs = {}
        
        # Apply hazmat fee if applicable
        if cargo.hazmat and "hazmat" in settings.cargo_factors:
            costs["hazmat"] = cargo.value * settings.cargo_factors["hazmat"]
        
        # Apply special requirements costs
        if cargo.special_requirements:
            for req, factor in settings.cargo_factors.items():
                if req in cargo.special_requirements:
                    costs[req] = cargo.value * factor
        
        return costs


@dataclass
class OfferGenerationService:
    """
    Service for generating transport offers.
    
    Responsibilities:
    - Generate commercial offers
    - Calculate final prices with margins
    - Integrate with AI for offer enhancement
    - Handle offer versioning and updates
    """
    
    cost_service: CostCalculationService
    
    def generate_offer(
        self,
        route: Route,
        margin: float,
        settings: Optional[CostSettings] = None,
        cargo: Optional[Cargo] = None,
        transport_type: Optional[TransportType] = None,
        metadata: Optional[Dict] = None
    ) -> Offer:
        """
        Generate an offer for a given route with specified margin.
        
        Args:
            route: Route to generate offer for
            margin: Profit margin as decimal (e.g., 0.15 for 15%)
            settings: Optional cost settings
            cargo: Optional cargo details
            transport_type: Optional transport type
            metadata: Optional offer metadata
            
        Returns:
            Offer: Generated offer with pricing and fun fact
            
        Raises:
            ValueError: If margin is invalid or cost calculation fails
        """
        if not 0 <= margin <= 1:
            raise ValueError("Margin must be between 0 and 1")
        
        try:
            # Calculate costs with all available details
            cost_breakdown = self.cost_service.calculate_route_cost(
                route=route,
                settings=settings,
                cargo=cargo,
                transport_type=transport_type
            )
            
            # Create cost record
            cost = Cost(
                route_id=route.id,
                breakdown=cost_breakdown,
                metadata=metadata
            )

            # Calculate final price with margin
            margin_decimal = Decimal(str(margin))
            final_price = cost_breakdown.total_cost * (1 + margin_decimal)

            # Generate AI fun fact
            fun_fact = self._generate_fun_fact(route)

            # Create and return offer
            return Offer(
                route_id=route.id,
                cost_id=cost.id,
                margin=margin_decimal,
                final_price=final_price,
                fun_fact=fun_fact,
                metadata=metadata
            )
            
        except Exception as e:
            raise ValueError(f"Failed to generate offer: {str(e)}") from e
    
    def _generate_fun_fact(self, route: Route) -> str:
        """
        Generate a fun fact about the route using AI.
        
        To be integrated with OpenAI for dynamic, contextual fun facts.
        """
        # Placeholder implementation
        return (
            f"Did you know? The {route.distance_km:.1f} km journey between "
            f"{route.origin.address} and {route.destination.address} is roughly "
            f"equivalent to {route.distance_km / 0.1:.0f} trucks lined up bumper to bumper!"
        )
