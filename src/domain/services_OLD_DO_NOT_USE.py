"""Domain services."""
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Set, Tuple
from uuid import UUID, uuid4

from src.domain.entities.route import Route, RouteStatus
from src.domain.entities.cost import Cost, CostSettings
from src.domain.interfaces.services.ai_service import AIService, AIServiceError
from src.domain.interfaces.services.location_service import LocationService
from src.domain.interfaces.repositories.cost_settings_repository import CostSettingsRepository
from src.domain.value_objects import Location, CountrySegment
from src.settings import get_settings

from src.domain.interfaces.services import AIService, AIServiceError
from src.domain.value_objects import (
    EmptyDriving, CostBreakdown,
    RouteMetadata, RouteSegment, CostComponent
)
from src.domain.entities.route import TransportType, TimelineEventType
from src.domain.entities.cost import Cost, CostSettings
from src.domain.entities.offer import Offer, OfferHistory
from src.domain.entities.cargo import Cargo, CargoSpecification
from src.domain.entities.vehicle import VehicleSpecification
from src.infrastructure.logging import get_logger

logger = get_logger()

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
    _cost_service: Optional['CostCalculationService'] = None
    
    @property
    def cost_service(self) -> 'CostCalculationService':
        """Get cost calculation service, creating it if needed."""
        if not self._cost_service:
            self._cost_service = CostCalculationService()
        return self._cost_service
    
    def create_route(
        self,
        origin: Location,
        destination: Location,
        pickup_time: datetime,
        delivery_time: datetime,
        transport_type: Optional[TransportType] = None,
        cargo_id: Optional[UUID] = None,
        metadata: Optional[Dict] = None
    ) -> Route:
        """Create a route with empty driving calculation."""
        logger = get_logger(__name__).bind(
            origin=origin.dict(),
            destination=destination.dict(),
            pickup_time=pickup_time,
            delivery_time=delivery_time,
            transport_type=transport_type
        )
        
        try:
            # Calculate main route distance and duration
            distance = self.location_service.calculate_distance(origin, destination)
            duration = self.location_service.calculate_duration(origin, destination)
            
            # Get country segments
            logger.info("Getting country segments")
            country_segments = self.location_service.get_country_segments(origin, destination)
            
            logger.info("Got country segments", count=len(country_segments))
            
            # Calculate empty driving if needed
            empty_driving = None
            if origin != destination:
                logger.info("Calculating empty driving")
                empty_distance = self.location_service.calculate_distance(destination, origin)
                empty_duration = self.location_service.calculate_duration(destination, origin)
                empty_driving = EmptyDriving(
                    distance_km=empty_distance,
                    duration_hours=empty_duration,
                    origin=origin.dict(),  # Convert to dict
                    destination=destination.dict()  # Convert to dict
                )
            
            # Create route
            route = Route(
                origin=origin.dict(),  # Convert to dict
                destination=destination.dict(),  # Convert to dict
                pickup_time=pickup_time,
                delivery_time=delivery_time,
                transport_type=transport_type or TransportType.TRUCK,
                distance_km=distance,
                duration_hours=duration,
                empty_driving=empty_driving,
                country_segments=country_segments,
                cargo_id=cargo_id,
                route_metadata=RouteMetadata(**metadata) if metadata else None
            )
            
            logger.info("Route created", 
                       distance=float(route.distance_km),
                       duration=float(route.duration_hours),
                       segments=len(route.country_segments))
            
            return route
            
        except Exception as e:
            logger.error("Route creation failed", error=str(e))
            raise
    
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
            distance=Decimal("500.0"),
            toll_rates={"standard": Decimal("0.15")}
        )]
    
    def _calculate_distance(self, origin: Location, destination: Location) -> Decimal:
        """
        Calculate distance between two locations.
        
        To be integrated with Google Maps API for accurate distance calculation.
        """
        # Placeholder implementation
        return Decimal("500.0")
    
    def _calculate_duration(self, pickup_time: datetime, delivery_time: datetime) -> Decimal:
        """Calculate duration in hours between pickup and delivery."""
        duration = delivery_time - pickup_time
        return Decimal(duration.total_seconds() / 3600)

    def calculate_costs(
        self,
        route: Route,
        settings: Optional[CostSettings] = None,
        cargo: Optional[Cargo] = None,
        transport_type: Optional[TransportType] = None,
        include_empty_driving: bool = True,
        include_country_breakdown: bool = True,
        validity_period: Optional[timedelta] = None
    ) -> Cost:
        """
        Calculate detailed costs for a route.
        
        Args:
            route: Route to calculate costs for
            settings: Optional cost settings (uses defaults if not provided)
            cargo: Optional cargo details for specialized costs
            transport_type: Optional transport type for consumption rates
            include_empty_driving: Whether to include empty driving costs
            include_country_breakdown: Whether to break down costs by country
            validity_period: Optional validity period for the cost calculation
            
        Returns:
            Cost: Detailed cost breakdown with all components
            
        Raises:
            ValueError: If required data is missing or invalid
        """
        try:
            # Calculate detailed cost breakdown
            cost_breakdown = self.cost_service.calculate_detailed_cost(
                route=route,
                settings=settings,
                cargo_spec=cargo.specifications if cargo else None,
                vehicle_spec=None,  # TODO: Add vehicle specifications
                include_empty_driving=include_empty_driving,
                include_country_breakdown=include_country_breakdown,
                validity_period=validity_period
            )
            
            # Create cost record
            return Cost(
                route_id=route.id,
                breakdown=cost_breakdown.dict(),
                calculated_at=datetime.now(timezone.utc),
                amount=cost_breakdown.total_cost,
                metadata={
                    "currency": cost_breakdown.currency,
                    "calculation_method": "detailed",
                    "include_empty_driving": include_empty_driving,
                    "include_country_breakdown": include_country_breakdown,
                    "cargo_id": str(cargo.id) if cargo else None,
                    "transport_type": transport_type.value if transport_type else None
                },
                version="2.0",
                is_final=True,
                calculation_method="detailed",
                validity_period=validity_period
            )
            
        except Exception as e:
            raise ValueError(f"Failed to calculate costs: {str(e)}")


@dataclass
class CostSettingsService:
    """Service for managing cost settings.
    
    Responsibilities:
    - Manage route-specific cost settings
    - Validate settings against routes
    - Provide default settings when needed
    - Track settings versions and changes
    """
    
    settings_repository: CostSettingsRepository
    route_repository: 'RouteRepository'
    
    def get_settings(self, route_id: UUID) -> CostSettings:
        """Get cost settings for a route.
        
        Args:
            route_id: UUID of the route
            
        Returns:
            CostSettings for the route
            
        Raises:
            ValueError: If settings not found and couldn't create defaults
        """
        settings = self.settings_repository.get_by_route_id(route_id)
        if not settings:
            # Create default settings if none exist
            route = self.route_repository.get_by_id(route_id)
            if not route:
                raise ValueError(f"Route {route_id} not found")
            settings = CostSettings.get_default(route_id)
            settings = self.settings_repository.save(settings)
        return settings
    
    def update_settings(
        self, 
        route_id: UUID, 
        settings: CostSettings,
        modified_by: Optional[str] = None
    ) -> CostSettings:
        """Update cost settings for a route.
        
        Args:
            route_id: UUID of the route
            settings: New settings to apply
            modified_by: Username of person making changes
            
        Returns:
            Updated CostSettings
            
        Raises:
            ValueError: If route not found or settings invalid
        """
        route = self.route_repository.get_by_id(route_id)
        if not route:
            raise ValueError(f"Route {route_id} not found")
            
        # Validate settings against route
        self._validate_settings(route, settings)
        
        # Update audit fields
        settings.modified_at = datetime.now(timezone.utc)
        settings.modified_by = modified_by
        
        # Save settings
        return self.settings_repository.save(settings)
    
    def create_settings(
        self, 
        route_id: UUID, 
        settings: CostSettings,
        created_by: Optional[str] = None
    ) -> CostSettings:
        """Create new cost settings for a route.
        
        Args:
            route_id: UUID of the route
            settings: Settings to create
            created_by: Username of person creating settings
            
        Returns:
            Created CostSettings
            
        Raises:
            ValueError: If route not found, settings invalid, or settings already exist
        """
        # Check if route exists
        route = self.route_repository.get_by_id(route_id)
        if not route:
            raise ValueError(f"Route {route_id} not found")
            
        # Check if settings already exist
        existing_settings = self.settings_repository.get_by_route_id(route_id)
        if existing_settings:
            raise ValueError(f"Settings already exist for route {route_id}")
            
        # Validate settings against route
        self._validate_settings(route, settings)
        
        # Set audit fields
        settings.route_id = route_id
        settings.created_at = datetime.now(timezone.utc)
        settings.created_by = created_by
        settings.modified_at = datetime.now(timezone.utc)
        settings.modified_by = created_by
        settings.version = 1  # Initial version
        
        # Save settings
        return self.settings_repository.save(settings)
    
    def _validate_settings(self, route: Route, settings: CostSettings) -> None:
        """Validate that settings are compatible with route.
        
        Args:
            route: Route to validate against
            settings: Settings to validate
            
        Raises:
            ValueError: If settings are invalid for route
        """
        # Get unique countries from route segments
        route_countries = {seg.country for seg in route.segments}
        if route.empty_driving:
            route_countries.update(seg.country for seg in route.empty_driving.segments)
            
        # Validate required rates exist
        if "fuel" in settings.enabled_components:
            missing_fuel = route_countries - set(settings.fuel_rates.keys())
            if missing_fuel:
                raise ValueError(f"Missing fuel rates for countries: {missing_fuel}")
                
        if "toll" in settings.enabled_components:
            missing_toll = route_countries - set(settings.toll_rates.keys())
            if missing_toll:
                raise ValueError(f"Missing toll rates for countries: {missing_toll}")
                
        if "driver" in settings.enabled_components:
            missing_driver = route_countries - set(settings.driver_rates.keys())
            if missing_driver:
                raise ValueError(f"Missing driver rates for countries: {missing_driver}")
                
        # Validate maintenance rates if enabled
        if "maintenance" in settings.enabled_components:
            if not settings.maintenance_rates:
                raise ValueError("Maintenance rates required but none provided")
                
        # Validate overhead rates if enabled
        if "overhead" in settings.enabled_components:
            if not settings.overhead_rates:
                raise ValueError("Overhead rates required but none provided")


class CostCalculationService:
    """Service for calculating transport costs.
    
    Responsibilities:
    - Calculate total transport costs
    - Break down costs by category and country
    - Handle different pricing strategies
    - Apply cargo-specific cost factors
    - Calculate empty driving costs
    """
    
    def __init__(self, settings_service: Optional[CostSettingsService] = None):
        self.settings_service = settings_service
        
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
            settings: Cost settings to use (fetched from service if None)
            cargo_spec: Cargo specifications affecting costs
            vehicle_spec: Vehicle specifications affecting costs
            include_empty_driving: Whether to include empty driving costs
            include_country_breakdown: Whether to break costs down by country
            validity_period: How long the cost calculation remains valid
            
        Returns:
            Cost object with detailed breakdown
            
        Raises:
            ValueError: If required settings not found
        """
        # Get settings if not provided
        if not settings and self.settings_service:
            settings = self.settings_service.get_settings(route.id)
        elif not settings:
            settings = CostSettings.get_default(route.id)
            
        # Initialize cost breakdown
        breakdown = CostBreakdown(
            route_id=route.id,
            currency=settings.currency if hasattr(settings, 'currency') else "EUR"
        )
        
        # Calculate enabled components
        components = []
        
        if "fuel" in settings.enabled_components:
            components.extend(self._calculate_fuel_costs(route, settings, vehicle_spec))
            
        if "toll" in settings.enabled_components:
            components.extend(self._calculate_toll_costs(route, settings, vehicle_spec))
            
        if "driver" in settings.enabled_components:
            components.extend(self._calculate_driver_costs(route, settings))
            
        if "maintenance" in settings.enabled_components:
            components.extend(self._calculate_maintenance_costs(route, settings, vehicle_spec))
            
        if "overhead" in settings.enabled_components:
            components.extend(self._calculate_overhead_costs(route, settings))
            
        # Add empty driving costs if enabled
        if include_empty_driving and route.empty_driving:
            empty_components = self._calculate_empty_driving_costs(route, settings, vehicle_spec)
            components.extend(empty_components)
            
        # Create cost record
        cost = Cost(
            route_id=route.id,
            breakdown=breakdown,
            calculation_method="detailed" if include_country_breakdown else "standard",
            validity_period=validity_period,
            version=settings.version
        )
        
        # Update totals
        self._update_cost_totals(cost, components)
        
        return cost
        
    def calculate_route_cost(
        self,
        route: Route,
        settings: Optional[CostSettings] = None,
        cargo: Optional[Cargo] = None,
        transport_type: TransportType = None,
        include_empty_driving: bool = True
    ) -> CostBreakdown:
        """Calculate costs for a given route (DEPRECATED).
        
        This method is deprecated and will be removed in a future version.
        Use calculate_detailed_cost() instead.
        
        Args:
            route: Route to calculate costs for
            settings: Cost settings to use (fetched from service if None)
            cargo: Cargo specifications
            transport_type: Type of transport vehicle
            include_empty_driving: Whether to include empty driving costs
            
        Returns:
            CostBreakdown with calculated costs
            
        Raises:
            ValueError: If required settings not found
        """
        warnings.warn(
            "calculate_route_cost() is deprecated and will be removed in a future version. "
            "Use calculate_detailed_cost() instead.",
            DeprecationWarning,
            stacklevel=2
        )

        logger = get_logger(__name__).bind(
            route_id=str(route.id),
            transport_type=str(transport_type),
            include_empty_driving=include_empty_driving
        )
        logger.info("Starting route cost calculation (legacy method)")
        
        try:
            # Get settings from service if available
            if not settings and self.settings_service:
                settings = self.settings_service.get_settings(route.id)
            elif not settings:
                settings = CostSettings.get_default(route.id)
            
            # Create vehicle spec from transport type
            vehicle_spec = None
            if transport_type:
                vehicle_spec = VehicleSpecification(
                    vehicle_type=transport_type.value,
                    fuel_consumption_rate=Decimal("0.35") if transport_type == TransportType.TRUCK else Decimal("0.15"),
                    empty_consumption_factor=Decimal("0.8")
                )
            
            # Create cargo spec from cargo
            cargo_spec = None
            if cargo:
                cargo_spec = CargoSpecification(
                    type=cargo.type,
                    weight=cargo.weight,
                    volume=cargo.volume,
                    special_requirements=cargo.special_requirements
                )
            
            # Calculate using new method
            cost = self.calculate_detailed_cost(
                route=route,
                settings=settings,
                cargo_spec=cargo_spec,
                vehicle_spec=vehicle_spec,
                include_empty_driving=include_empty_driving
            )
            
            # Convert new breakdown to old format
            return CostBreakdown(
                id=uuid4(),
                route_id=route.id,
                fuel_costs={c.country: c.amount for c in cost.components if c.type == "fuel"},
                toll_costs={c.country: c.amount for c in cost.components if c.type == "toll"},
                maintenance_costs={c.country: c.amount for c in cost.components if c.type == "maintenance"},
                driver_costs={c.country: c.amount for c in cost.components if c.type == "driver"},
                empty_driving_costs={
                    c.country: {"cost": c.amount, "details": c.details}
                    for c in cost.components 
                    if c.details.get("is_empty_driving", False)
                },
                overheads={
                    "distance": sum(c.amount for c in cost.components if c.type == "overhead" and c.details.get("overhead_type") == "distance"),
                    "time": sum(c.amount for c in cost.components if c.type == "overhead" and c.details.get("overhead_type") == "time"),
                    "fixed": sum(c.amount for c in cost.components if c.type == "overhead" and c.details.get("overhead_type") == "fixed")
                },
                subtotal_distance_based=cost.breakdown.subtotal_distance_based,
                subtotal_time_based=cost.breakdown.subtotal_time_based,
                subtotal_empty_driving=cost.breakdown.subtotal_empty_driving,
                total_cost=cost.breakdown.total_cost
            )
            
        except Exception as e:
            logger.error("Cost calculation failed", error=str(e), error_type=type(e).__name__)
            raise

    def _calculate_fuel_costs(
        self,
        route: Route,
        settings: CostSettings,
        vehicle_spec: Optional[VehicleSpecification]
    ) -> List[CostComponent]:
        """Calculate fuel costs for each country segment."""
        components = []
        consumption_rate = (
            vehicle_spec.fuel_consumption_rate
            if vehicle_spec
            else Decimal("0.3")  # Default 0.3L/km
        )
        
        # Calculate for each country segment
        for segment in route.segments:
            fuel_rate = settings.fuel_rates.get(segment.country)
            if not fuel_rate:
                continue
                
            amount = (
                Decimal(str(segment.distance_km)) *
                consumption_rate *
                fuel_rate
            )
            
            components.append(CostComponent(
                type="fuel",
                amount=amount,
                country=segment.country,
                details={
                    "distance_km": segment.distance_km,
                    "consumption_rate": float(consumption_rate),
                    "fuel_rate": float(fuel_rate)
                }
            ))
            
        return components
        
    def _calculate_toll_costs(
        self,
        route: Route,
        settings: CostSettings,
        vehicle_spec: Optional[VehicleSpecification]
    ) -> List[CostComponent]:
        """Calculate toll costs for each country segment."""
        components = []
        vehicle_type = (
            vehicle_spec.vehicle_type
            if vehicle_spec
            else "truck"  # Default to truck
        )
        
        # Calculate for each country segment
        for segment in route.segments:
            toll_rates = settings.toll_rates.get(segment.country, {})
            toll_rate = toll_rates.get(vehicle_type)
            if not toll_rate:
                continue
                
            amount = Decimal(str(segment.distance_km)) * toll_rate
            
            components.append(CostComponent(
                type="toll",
                amount=amount,
                country=segment.country,
                details={
                    "distance_km": segment.distance_km,
                    "toll_rate": float(toll_rate),
                    "vehicle_type": vehicle_type
                }
            ))
            
        return components
        
    def _calculate_driver_costs(
        self,
        route: Route,
        settings: CostSettings
    ) -> List[CostComponent]:
        """Calculate driver costs for each country segment."""
        components = []
        
        # Calculate for each country segment
        for segment in route.segments:
            driver_rate = settings.driver_rates.get(segment.country)
            if not driver_rate:
                continue
                
            amount = Decimal(str(segment.duration_hours)) * driver_rate
            
            components.append(CostComponent(
                type="driver",
                amount=amount,
                country=segment.country,
                details={
                    "duration_hours": segment.duration_hours,
                    "driver_rate": float(driver_rate)
                }
            ))
            
        return components
        
    def _calculate_maintenance_costs(
        self,
        route: Route,
        settings: CostSettings,
        vehicle_spec: Optional[VehicleSpecification]
    ) -> List[CostComponent]:
        """Calculate maintenance costs."""
        vehicle_type = (
            vehicle_spec.vehicle_type
            if vehicle_spec
            else "truck"  # Default to truck
        )
        
        maintenance_rate = settings.maintenance_rates.get(vehicle_type)
        if not maintenance_rate:
            return []
            
        total_distance = Decimal(str(route.total_distance()))
        amount = total_distance * maintenance_rate
        
        return [CostComponent(
            type="maintenance",
            amount=amount,
            details={
                "distance_km": float(total_distance),
                "maintenance_rate": float(maintenance_rate),
                "vehicle_type": vehicle_type
            }
        )]
        
    def _calculate_overhead_costs(
        self,
        route: Route,
        settings: CostSettings
    ) -> List[CostComponent]:
        """Calculate overhead costs."""
        components = []
        
        # Fixed overhead
        fixed_rate = settings.overhead_rates.get("fixed", Decimal("0"))
        if fixed_rate > 0:
            components.append(CostComponent(
                type="overhead",
                amount=fixed_rate,
                details={"overhead_type": "fixed"}
            ))
            
        # Distance-based overhead
        distance_rate = settings.overhead_rates.get("distance", Decimal("0"))
        if distance_rate > 0:
            total_distance = Decimal(str(route.total_distance()))
            amount = total_distance * distance_rate
            components.append(CostComponent(
                type="overhead",
                amount=amount,
                details={
                    "overhead_type": "distance",
                    "distance_km": float(total_distance),
                    "rate": float(distance_rate)
                }
            ))
            
        # Time-based overhead
        time_rate = settings.overhead_rates.get("time", Decimal("0"))
        if time_rate > 0:
            total_duration = Decimal(str(route.total_duration()))
            amount = total_duration * time_rate
            components.append(CostComponent(
                type="overhead",
                amount=amount,
                details={
                    "overhead_type": "time",
                    "duration_hours": float(total_duration),
                    "rate": float(time_rate)
                }
            ))
            
        return components
        
    def _calculate_empty_driving_costs(
        self,
        route: Route,
        settings: CostSettings,
        vehicle_spec: Optional[VehicleSpecification]
    ) -> List[CostComponent]:
        """Calculate costs for empty driving segments."""
        if not route.empty_driving:
            return []
            
        components = []
        empty_factor = Decimal("0.8")  # 80% of normal consumption
        
        # Calculate fuel costs
        if "fuel" in settings.enabled_components:
            consumption_rate = (
                vehicle_spec.fuel_consumption_rate * vehicle_spec.empty_consumption_factor
                if vehicle_spec
                else Decimal("0.24")  # Default 0.3 * 0.8
            )
            
            for segment in route.empty_driving.segments:
                fuel_rate = settings.fuel_rates.get(segment.country)
                if not fuel_rate:
                    continue
                    
                amount = (
                    Decimal(str(segment.distance_km)) *
                    consumption_rate *
                    fuel_rate
                )
                
                components.append(CostComponent(
                    type="fuel",
                    amount=amount,
                    country=segment.country,
                    details={
                        "distance_km": segment.distance_km,
                        "consumption_rate": float(consumption_rate),
                        "fuel_rate": float(fuel_rate),
                        "is_empty_driving": True
                    }
                ))
                
        # Calculate toll costs
        if "toll" in settings.enabled_components:
            vehicle_type = (
                vehicle_spec.vehicle_type
                if vehicle_spec
                else "truck"
            )
            
            for segment in route.empty_driving.segments:
                toll_rates = settings.toll_rates.get(segment.country, {})
                toll_rate = toll_rates.get(vehicle_type)
                if not toll_rate:
                    continue
                    
                amount = Decimal(str(segment.distance_km)) * toll_rate
                
                components.append(CostComponent(
                    type="toll",
                    amount=amount,
                    country=segment.country,
                    details={
                        "distance_km": segment.distance_km,
                        "toll_rate": float(toll_rate),
                        "vehicle_type": vehicle_type,
                        "is_empty_driving": True
                    }
                ))
                
        # Calculate driver costs
        if "driver" in settings.enabled_components:
            for segment in route.empty_driving.segments:
                driver_rate = settings.driver_rates.get(segment.country)
                if not driver_rate:
                    continue
                    
                amount = Decimal(str(segment.duration_hours)) * driver_rate
                
                components.append(CostComponent(
                    type="driver",
                    amount=amount,
                    country=segment.country,
                    details={
                        "duration_hours": segment.duration_hours,
                        "driver_rate": float(driver_rate),
                        "is_empty_driving": True
                    }
                ))
                
        return components
        
    def _update_cost_totals(self, cost: Cost, components: List[CostComponent]) -> None:
        """Update cost totals from components."""
        # Group components by type
        by_type: Dict[str, List[CostComponent]] = {}
        for component in components:
            by_type.setdefault(component.type, []).append(component)
            
        # Update breakdown totals
        for type_name, type_components in by_type.items():
            total = sum(c.amount for c in type_components)
            setattr(cost.breakdown, f"{type_name}_costs", total)
            
        # Update subtotals
        cost.breakdown.subtotal_distance_based = sum(
            c.amount for c in components
            if c.type in {"fuel", "toll", "maintenance"}
        )
        
        cost.breakdown.subtotal_time_based = sum(
            c.amount for c in components
            if c.type in {"driver", "overhead"}
        )
        
        cost.breakdown.subtotal_empty_driving = sum(
            c.amount for c in components
            if c.details.get("is_empty_driving", False)
        )
        
        # Update total
        cost.breakdown.total_cost = (
            cost.breakdown.subtotal_distance_based +
            cost.breakdown.subtotal_time_based
        )


@dataclass
class OfferGenerationService:
    """Service for generating transport offers.
    
    Responsibilities:
    - Generate commercial offers
    - Calculate final prices with margins
    - Integrate with AI for offer enhancement
    - Handle offer versioning and updates
    - Track offer history and status changes
    """
    cost_service: CostCalculationService
    ai_service: AIService
    
    def generate_offer(
        self,
        route: Route,
        margin: float,
        settings: Optional[CostSettings] = None,
        cargo: Optional[Cargo] = None,
        transport_type: Optional[TransportType] = None,
        metadata: Optional[Dict] = None,
        created_by: Optional[str] = None,
        status: str = "draft",  # Default status is draft
        total_cost: Optional[float] = None  # Add total_cost parameter
    ) -> Offer:
        """Generate an offer for a given route with specified margin."""
        offer_logger = logger.bind(
            service="offer_generation",
            route_id=str(route.id),
            margin=margin,
            transport_type=str(transport_type) if transport_type else None,
            cargo_id=str(cargo.id) if cargo else None,
            created_by=created_by
        )
        offer_logger.info("generating_new_offer")
        
        try:
            # Use provided total_cost or calculate it
            if total_cost is not None:
                base_cost = Decimal(str(total_cost))
                offer_logger.info("using_provided_base_cost", base_cost=str(base_cost))
                # Create a basic Cost entity for the provided total_cost
                breakdown_dict = {
                    "id": str(uuid4()),  # Convert UUID to string
                    "route_id": str(route.id),  # Convert UUID to string
                    "total_cost": base_cost,
                    "fuel_costs": {},
                    "toll_costs": {},
                    "driver_costs": {},
                    "maintenance_costs": {},
                    "rest_period_costs": Decimal("0"),
                    "loading_unloading_costs": Decimal("0"),
                    "empty_driving_costs": {},
                    "cargo_specific_costs": {},
                    "overheads": {},
                    "subtotal_distance_based": Decimal("0"),
                    "subtotal_time_based": Decimal("0"),
                    "subtotal_empty_driving": Decimal("0"),
                    "currency": "EUR"
                }
                
                cost = Cost(
                    id=uuid4(),
                    route_id=route.id,
                    breakdown=breakdown_dict,  # Pass as dict, let Pydantic handle conversion
                    calculated_at=datetime.now(timezone.utc),
                    version="1.0",
                    is_final=True,
                    calculation_method="provided"
                )
                offer_logger.info("created_cost_entity_from_total", cost_id=str(cost.id))
            else:
                # Calculate base cost
                offer_logger.debug("calculating_base_cost")
                cost = self.cost_service.calculate_detailed_cost(
                    route=route,
                    settings=settings,
                    cargo_spec=None,  # TODO: Create from cargo
                    vehicle_spec=None,  # TODO: Create from transport_type
                    include_empty_driving=True,
                    include_country_breakdown=True,
                    validity_period=timedelta(hours=24)  # Offers valid for 24h by default
                )
                base_cost = cost.total  # Keep as Decimal
                offer_logger.info("base_cost_calculated", base_cost=str(base_cost))
            
            # Apply margin and convert to float for storage
            margin_decimal = Decimal(str(margin))  # Store the original percentage
            margin_amount = base_cost * (margin_decimal / Decimal("100"))  # Calculate amount using percentage
            final_price = base_cost + margin_amount  # All operations between Decimals
            
            offer_logger.debug(
                "price_calculated",
                base_cost=str(base_cost),
                margin_amount=str(margin_amount),
                final_price=str(final_price)
            )
            
            # Generate fun fact using AI
            offer_logger.debug("generating_fun_fact")
            try:
                fun_fact = self.ai_service.generate_fun_fact(route)
                offer_logger.info("fun_fact_generated", length=len(fun_fact))
            except AIServiceError as e:
                offer_logger.warning("ai_fun_fact_failed", error=str(e))
                # Use safe dictionary access with fallbacks
                origin_city = route.origin.get('city', route.origin.get('address', 'Unknown Location'))
                dest_city = route.destination.get('city', route.destination.get('address', 'Unknown Location'))
                fun_fact = f"Transport from {origin_city} to {dest_city}"

            # Generate enhanced route description
            offer_logger.debug("generating_route_description")
            try:
                description = self.ai_service.generate_route_description(route)
                offer_logger.info("description_generated", length=len(description))
            except AIServiceError as e:
                offer_logger.warning("ai_description_failed", error=str(e))
                # Use safe dictionary access with fallbacks
                origin_addr = route.origin.get('address', route.origin.get('city', 'Unknown Location'))
                dest_addr = route.destination.get('address', route.destination.get('city', 'Unknown Location'))
                description = f"Transport from {origin_addr} to {dest_addr}"

            # Convert cost breakdown to JSON-serializable format
            cost_breakdown = cost.breakdown.dict() if 'cost' in locals() else {}
            for key, value in cost_breakdown.items():
                if isinstance(value, Decimal):
                    cost_breakdown[key] = float(value)
                elif isinstance(value, dict):
                    for subkey, subvalue in value.items():
                        if isinstance(subvalue, Decimal):
                            value[subkey] = float(subvalue)
                        elif isinstance(subvalue, UUID):
                            value[subkey] = str(subvalue)  # Convert UUIDs to strings
                elif isinstance(subvalue, UUID):
                    cost_breakdown[key] = str(value)  # Convert UUIDs to strings

            # Create offer object with float values for database storage
            offer = Offer(
                id=uuid4(),
                route_id=route.id,
                cost_id=cost.id if 'cost' in locals() else None,
                total_cost=base_cost,  # Store as Decimal in domain entity
                margin=margin_decimal,  # Store the original percentage
                final_price=final_price,  # Store as Decimal in domain entity
                fun_fact=fun_fact,
                description=description,
                status=status,
                metadata={
                    "cost_breakdown": cost_breakdown,
                    "route_metadata": route.route_metadata.dict() if route.route_metadata else {}
                },
                version="1.0",
                created_at=datetime.now(timezone.utc),
                modified_at=datetime.now(timezone.utc),
                created_by=created_by,
                modified_by=created_by
            )
            
            offer_logger.info(
                "offer_generated",
                offer_id=str(offer.id),
                final_price=str(offer.final_price),
                status=offer.status
            )
            
            return offer
            
        except Exception as e:
            offer_logger.error(
                "offer_generation_failed",
                error=str(e),
                error_type=type(e).__name__,
                traceback=True
            )
            raise
    
    def update_offer(
        self,
        offer: Offer,
        margin: Optional[float] = None,
        status: Optional[str] = None,
        metadata: Optional[Dict] = None,
        modified_by: Optional[str] = None,
        change_reason: Optional[str] = None
    ) -> Offer:
        """Update an existing offer with new details."""
        offer_logger = logger.bind(
            service="offer_generation",
            offer_id=str(offer.id),
            modified_by=modified_by,
            change_reason=change_reason
        )
        offer_logger.info("updating_offer")
        
        try:
            # Validate status transition if status is changing
            if status and status != offer.status:
                offer_logger.debug(
                    "validating_status_transition",
                    current=offer.status,
                    new=status
                )
                self._validate_status_transition(offer.status, status)
                offer_logger.info("status_transition_valid")
            
            # Calculate new price if margin is changing
            if margin is not None and margin != float(offer.margin):
                offer_logger.debug(
                    "recalculating_price",
                    old_margin=float(offer.margin),
                    new_margin=margin
                )
                margin_amount = offer.base_cost * Decimal(str(margin))
                final_price = offer.base_cost + margin_amount
                
                offer_logger.info(
                    "price_recalculated",
                    new_price=str(final_price)
                )
            else:
                margin = float(offer.margin)
                final_price = offer.final_price
            
            # Create history record
            history = OfferHistory(
                offer_id=offer.id,
                previous_version=offer.version,
                change_type="update",
                modified_at=datetime.now(timezone.utc),
                modified_by=modified_by,
                change_reason=change_reason,
                previous_status=offer.status,
                new_status=status if status else offer.status,
                previous_margin=float(offer.margin),
                new_margin=margin
            )
            
            # Update version number
            version_parts = offer.version.split(".")
            new_version = f"{version_parts[0]}.{int(version_parts[1]) + 1}"
            
            # Create updated offer
            updated_offer = Offer(
                id=offer.id,
                route_id=offer.route_id,
                cost_id=offer.cost_id,
                total_cost=offer.total_cost,
                margin=margin_decimal,  # Store as Decimal in domain entity
                final_price=final_price,  # Store as Decimal in domain entity
                fun_fact=offer.fun_fact,
                description=offer.description,
                status=status if status else offer.status,
                created_at=offer.created_at,
                created_by=offer.created_by,
                modified_at=datetime.now(timezone.utc),
                modified_by=modified_by,
                metadata=metadata or {},
                version=new_version,
                history=[*offer.history, history] if offer.history else [history]
            )
            
            offer_logger.info(
                "offer_updated",
                new_version=new_version,
                new_status=updated_offer.status,
                new_price=str(updated_offer.final_price)
            )
            
            return updated_offer
            
        except Exception as e:
            offer_logger.error(
                "offer_update_failed",
                error=str(e),
                error_type=type(e).__name__,
                traceback=True
            )
            raise
    
    def archive_offer(
        self,
        offer: Offer,
        archived_by: Optional[str] = None,
        archive_reason: Optional[str] = None
    ) -> Offer:
        """Archive an offer, making it inactive."""
        offer_logger = logger.bind(
            service="offer_generation",
            offer_id=str(offer.id),
            archived_by=archived_by,
            archive_reason=archive_reason
        )
        offer_logger.info("archiving_offer")
        
        try:
            # Update the offer with archived status
            archived_offer = self.update_offer(
                offer=offer,
                status="archived",
                modified_by=archived_by,
                change_reason=archive_reason or "Offer archived"
            )
            
            offer_logger.info("offer_archived")
            return archived_offer
            
        except Exception as e:
            offer_logger.error(
                "offer_archive_failed",
                error=str(e),
                error_type=type(e).__name__,
                traceback=True
            )
            raise
    
    def _validate_status_transition(self, current_status: str, new_status: str) -> None:
        """Validate if a status transition is allowed."""
        valid_transitions = {
            "draft": {"active", "archived"},
            "active": {"archived"},
            "archived": set()  # No transitions allowed from archived
        }
        
        if new_status not in valid_transitions.get(current_status, set()):
            logger.error(
                "invalid_status_transition",
                current=current_status,
                new=new_status,
                valid_transitions=list(valid_transitions.get(current_status, set()))
            )
            raise ValueError(
                f"Invalid status transition from '{current_status}' to '{new_status}'. "
                f"Valid transitions: {valid_transitions.get(current_status, set())}"
            )


class HelloWorldService:
    """Simple service for testing API connectivity."""
    
    def get_greeting(self) -> str:
        """Return a simple greeting message.
        
        Returns:
            Greeting message
        """
        return "Hello from LoadApp.AI!"
