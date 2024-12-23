"""Domain services for LoadApp.AI."""
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from uuid import UUID, uuid4

from src.domain.interfaces import AIService, AIServiceError, LocationService
from src.domain.value_objects import (
    Location, CountrySegment, EmptyDriving, CostBreakdown,
    RouteMetadata, RouteSegment
)
from src.domain.entities import (
    Route, Cost, CostSettings, Offer, OfferHistory,
    TransportType, Cargo, TimelineEventType,
    CargoSpecification, VehicleSpecification
)
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
            country_segments = []
            
            # For now, split the distance 50/50 between origin and destination countries
            # TODO: Use Google Maps API to get accurate country segments
            half_distance = distance / 2
            half_duration = duration / 2
            
            # Add origin country segment
            country_segments.append(CountrySegment(
                country_code=origin.country,
                distance=half_distance,
                duration_hours=half_duration,
                toll_rates={"highway": Decimal("0.15"), "national": Decimal("0.10")}  # Default rates, will be overridden by cost settings
            ))
            
            # Add destination country segment if different from origin
            if destination.country != origin.country:
                country_segments.append(CountrySegment(
                    country_code=destination.country,
                    distance=half_distance,
                    duration_hours=half_duration,
                    toll_rates={"highway": Decimal("0.15"), "national": Decimal("0.10")}  # Default rates, will be overridden by cost settings
                ))
            
            logger.info("Got country segments", count=len(country_segments))
            
            # Calculate empty driving if needed
            empty_driving = None
            if origin != destination:
                logger.info("Calculating empty driving")
                empty_distance = Decimal("0.1")  # Example value
                empty_duration = Decimal("0.1")  # Example value
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
class CostCalculationService:
    """
    Service for calculating transport costs.
    
    Responsibilities:
    - Calculate total transport costs
    - Break down costs by category and country
    - Handle different pricing strategies
    - Apply cargo-specific cost factors
    - Calculate empty driving costs
    """
    
    def calculate_route_cost(
        self,
        route: Route,
        settings: Optional[CostSettings] = None,
        cargo: Optional[Cargo] = None,
        transport_type: TransportType = None,
        include_empty_driving: bool = True
    ) -> CostBreakdown:
        """Calculate costs for a given route."""
        logger = get_logger(__name__).bind(
            route_id=str(route.id),
            transport_type=str(transport_type),
            include_empty_driving=include_empty_driving
        )
        logger.info("Starting route cost calculation")
        
        try:
            # Use default settings if not provided
            if settings is None:
                settings = self._get_default_settings()
                logger.info("Using default cost settings", 
                           fuel_prices={k: float(v) for k, v in settings.fuel_prices.items()},
                           driver_rates={k: float(v) for k, v in settings.driver_rates.items()},
                           toll_rates={k: {sk: float(sv) for sk, sv in v.items()} for k, v in settings.toll_rates.items()})
            
            # Log route details
            logger.info("Route details", 
                       distance_km=float(route.distance_km),
                       duration_hours=float(route.duration_hours),
                       country_segments=[{
                           "country": s.country_code,
                           "distance": float(s.distance),
                           "duration": float(s.duration_hours)
                       } for s in route.country_segments])

            # Initialize costs for each country
            fuel_costs = {}
            toll_costs = {}
            maintenance_costs = {}
            driver_costs = {}
            empty_driving_costs = {}
            cargo_specific_costs = {}

            # Process each country segment
            for segment in route.country_segments:
                country = segment.country_code
                distance = segment.distance  # Keep as Decimal
                duration = segment.duration_hours  # Keep as Decimal
                
                logger.info("Processing country segment", 
                           country=country,
                           distance=float(distance),
                           duration=float(duration))

                # Get consumption rates for the transport type
                consumption_rates = self._get_consumption_rates(transport_type)
                logger.info("Using consumption rates", rates={k: float(v) for k, v in consumption_rates.items()})

                # Calculate fuel costs
                fuel_price = settings.fuel_prices[country]  # Use direct access
                fuel_rate = consumption_rates["fuel"]
                fuel_cost = fuel_price * fuel_rate * distance
                fuel_costs[country] = fuel_cost
                logger.info("Calculated fuel cost", 
                           country=country,
                           fuel_price=float(fuel_price),
                           fuel_rate=float(fuel_rate),
                           distance=float(distance),
                           fuel_cost=float(fuel_cost))

                # Calculate toll costs using country's toll rates from settings
                toll_rates = settings.toll_rates.get(country, {})
                logger.info("Retrieved toll rates for country", 
                           country=country,
                           toll_rates={k: float(v) for k, v in toll_rates.items()})

                # Get highway and national rates with defaults
                highway_rate = toll_rates.get("highway", Decimal("0.15"))
                national_rate = toll_rates.get("national", Decimal("0.10"))

                # Assume 70% highway, 30% national roads
                toll_cost = (highway_rate * distance * Decimal("0.7")) + (national_rate * distance * Decimal("0.3"))
                toll_costs[country] = toll_cost
                
                logger.info("Calculated toll cost", 
                           country=country,
                           highway_rate=float(highway_rate),
                           national_rate=float(national_rate),
                           distance=float(distance),
                           toll_cost=float(toll_cost),
                           highway_portion=float(highway_rate * distance * Decimal("0.7")),
                           national_portion=float(national_rate * distance * Decimal("0.3")))

                # Calculate maintenance costs
                maintenance_rate = consumption_rates["maintenance"]
                maintenance_cost = maintenance_rate * distance
                maintenance_costs[country] = maintenance_cost
                logger.info("Calculated maintenance cost", 
                           country=country,
                           maintenance_rate=float(maintenance_rate),
                           distance=float(distance),
                           maintenance_cost=float(maintenance_cost))

                # Calculate driver costs
                driver_rate = settings.driver_rates[country]  # Use direct access
                driver_cost = driver_rate * duration
                driver_costs[country] = driver_cost
                logger.info("Calculated driver cost", 
                           country=country,
                           driver_rate=float(driver_rate),
                           duration=float(duration),
                           driver_cost=float(driver_cost))

            # Calculate empty driving costs if requested
            if include_empty_driving and route.empty_driving:
                logger.info("Calculating empty driving costs", 
                           empty_distance=float(route.empty_driving.distance_km),
                           empty_duration=float(route.empty_driving.duration_hours))
                
                for empty_segment in route.empty_driving.segments:
                    country = empty_segment.country_code
                    distance = Decimal(str(empty_segment.distance_km))
                    duration = Decimal(str(empty_segment.duration_hours))
                    
                    # Get rates for the country
                    fuel_price = settings.fuel_prices.get(country, settings.default_fuel_rate)
                    toll_rates = settings.toll_rates.get(country, {})
                    driver_rate = settings.driver_rates.get(country, settings.default_driver_rate)
                    
                    # Calculate costs
                    empty_fuel_cost = fuel_price * distance * consumption_rates["fuel"]
                    empty_toll_cost = (
                        toll_rates.get("highway", Decimal("0.15")) * distance * Decimal("0.7") +
                        toll_rates.get("national", Decimal("0.10")) * distance * Decimal("0.3")
                    )
                    empty_driver_cost = driver_rate * duration
                    
                    empty_driving_costs[country] = empty_fuel_cost + empty_toll_cost + empty_driver_cost
                    
                    logger.info("Calculated empty driving costs for country",
                              country=country,
                              distance=float(distance),
                              duration=float(duration),
                              fuel_cost=float(empty_fuel_cost),
                              toll_cost=float(empty_toll_cost),
                              driver_cost=float(empty_driver_cost),
                              total_cost=float(empty_fuel_cost + empty_toll_cost + empty_driver_cost))

            # Calculate cargo-specific costs
            if cargo:
                logger.info("Calculating cargo-specific costs", 
                           cargo_type=cargo.type,
                           cargo_weight=float(cargo.weight),
                           cargo_volume=float(cargo.volume))
                cargo_specific_costs = self._calculate_cargo_specific_costs(
                    route=route,
                    cargo=cargo,
                    settings=settings
                )

            # Calculate overhead costs
            logger.info("Calculating overhead costs")
            total_overhead = self._calculate_overhead_costs(
                route=route,
                settings=settings
            )

            # Create cost breakdown
            breakdown = CostBreakdown(
                fuel_costs=fuel_costs,
                toll_costs=toll_costs,
                maintenance_costs=maintenance_costs,
                driver_costs=driver_costs,
                empty_driving_costs=empty_driving_costs,
                cargo_specific_costs=cargo_specific_costs,
                overheads={
                    "distance": total_overhead["distance"],
                    "time": total_overhead["time"],
                    "fixed": total_overhead["fixed"],
                    "total": total_overhead["total"]
                },
                rest_period_costs=self._calculate_rest_period_costs(route, settings),
                loading_unloading_costs=self._calculate_loading_unloading_costs(route, settings),
                subtotal_distance_based=sum(fuel_costs.values()) + sum(toll_costs.values()) + sum(maintenance_costs.values()),
                subtotal_time_based=sum(driver_costs.values()),
                subtotal_empty_driving=sum(empty_driving_costs.values())
            )

            # Log final cost breakdown with proper float conversion
            logger.info("Cost calculation completed", 
                       fuel_costs={k: float(v) for k, v in fuel_costs.items()},
                       toll_costs={k: float(v) for k, v in toll_costs.items()},
                       maintenance_costs={k: float(v) for k, v in maintenance_costs.items()},
                       driver_costs={k: float(v) for k, v in driver_costs.items()},
                       empty_driving_costs={k: float(v) for k, v in empty_driving_costs.items()},
                       overheads={k: float(v) for k, v in total_overhead.items()},
                       total_cost=float(breakdown.total_cost))
            return breakdown

        except Exception as e:
            logger.error("Cost calculation failed", error=str(e), error_type=type(e).__name__)
            raise
    
    def _calculate_empty_driving_costs(
        self,
        route: Route,
        settings: CostSettings,
        costs: Dict[str, Dict[str, Decimal]]
    ) -> None:
        """Calculate costs for empty driving segments."""
        if not route.empty_driving:
            return
            
        logger = get_logger(__name__).bind(
            route_id=str(route.id),
            empty_distance=float(route.empty_driving.distance_km),
            empty_duration=float(route.empty_driving.duration_hours)
        )
        logger.info("Starting empty driving cost calculation")

        # Get empty driving factors from settings
        factors = settings.empty_driving_factors
        fuel_factor = factors.get("fuel", Decimal("0.8"))  # 80% of normal fuel consumption
        toll_factor = factors.get("toll", Decimal("1.0"))  # Same toll rates
        driver_factor = factors.get("driver", Decimal("1.0"))  # Same driver rates
        
        logger.info("Using empty driving factors",
                   fuel_factor=float(fuel_factor),
                   toll_factor=float(toll_factor),
                   driver_factor=float(driver_factor))

        # Calculate costs for each country segment
        for segment in route.country_segments:
            country = segment.country_code
            distance = segment.distance  # Keep as Decimal
            duration = segment.duration_hours  # Keep as Decimal

            logger.info("Processing country segment for empty driving",
                       country=country,
                       distance=float(distance),
                       duration=float(duration))

            # Get rates for the country
            fuel_price = settings.fuel_prices.get(country, Decimal("0"))
            driver_rate = settings.driver_rates.get(country, Decimal("0"))
            
            logger.info("Retrieved country rates",
                       country=country,
                       fuel_price=float(fuel_price),
                       driver_rate=float(driver_rate))

            # Calculate fuel costs with empty driving factors
            fuel_rate = Decimal("0.35")  # L/km for empty truck
            fuel_cost = fuel_price * fuel_rate * distance * fuel_factor
            costs[country]["fuel"] += fuel_cost
            
            logger.info("Calculated empty driving fuel cost",
                       country=country,
                       fuel_rate=float(fuel_rate),
                       fuel_cost=float(fuel_cost))
            
            # Calculate toll costs with improved rate handling
            toll_rates = settings.toll_rates.get(country, {})
            highway_rate = Decimal(str(toll_rates.get("highway", "0.15")))
            national_rate = Decimal(str(toll_rates.get("national", "0.10")))
            
            highway_toll = highway_rate * distance * Decimal("0.7") * toll_factor
            national_toll = national_rate * distance * Decimal("0.3") * toll_factor
            total_toll = highway_toll + national_toll
            costs[country]["toll"] += total_toll
            
            logger.info("Calculated empty driving toll cost",
                       country=country,
                       highway_rate=float(highway_rate),
                       national_rate=float(national_rate),
                       highway_toll=float(highway_toll),
                       national_toll=float(national_toll),
                       total_toll=float(total_toll))
            
            # Calculate driver costs
            driver_cost = driver_rate * duration * driver_factor
            costs[country]["driver"] += driver_cost
            
            logger.info("Calculated empty driving driver cost",
                       country=country,
                       driver_rate=float(driver_rate),
                       duration=float(duration),
                       driver_cost=float(driver_cost))

        logger.info("Empty driving cost calculation completed",
                   total_fuel_costs=sum(float(costs[c]["fuel"]) for c in costs),
                   total_toll_costs=sum(float(costs[c]["toll"]) for c in costs),
                   total_driver_costs=sum(float(costs[c]["driver"]) for c in costs))

    def _calculate_overhead_costs(
        self,
        route: Route,
        settings: CostSettings
    ) -> Dict[str, Decimal]:
        """Calculate overhead costs for the route."""
        logger.info("Calculating overhead costs", route_id=str(route.id))
        
        # Calculate distance-based overhead
        distance = Decimal(str(route.distance_km))
        distance_overhead = distance * settings.overhead_rates.get("distance", Decimal("0.15"))
        logger.debug("Distance overhead", distance=float(distance), rate=float(settings.overhead_rates.get("distance", Decimal("0.15"))))
        
        # Calculate time-based overhead
        duration = Decimal(str(route.duration_hours))
        time_overhead = duration * settings.overhead_rates.get("time", Decimal("25.00"))
        logger.debug("Time overhead", duration=float(duration), rate=float(settings.overhead_rates.get("time", Decimal("25.00"))))
        
        # Get fixed overhead
        fixed_overhead = settings.overhead_rates.get("fixed", Decimal("50.00"))
        logger.debug("Fixed overhead", fixed=float(fixed_overhead))
        
        overheads = {
            "distance": distance_overhead,
            "time": time_overhead,
            "fixed": fixed_overhead,
            "total": distance_overhead + time_overhead + fixed_overhead
        }
        
        logger.info(
            "Calculated overhead costs",
            route_id=str(route.id),
            distance=float(distance_overhead),
            time=float(time_overhead),
            fixed=float(fixed_overhead),
            total=float(overheads["total"])
        )
        
        return overheads

    def _calculate_rest_period_costs(
        self,
        route: Route,
        settings: CostSettings
    ) -> Decimal:
        """Calculate costs for mandatory rest periods."""
        logger.info("Calculating rest period costs", route_id=str(route.id))

        # Get duration in hours
        duration = Decimal(str(route.duration_hours))
        logger.debug("Route duration", duration=float(duration))

        # Calculate number of short breaks (15 min every 4.5 hours)
        short_breaks = (duration / Decimal("4.5")).to_integral_value()
        logger.debug("Number of short breaks", short_breaks=int(short_breaks))

        # Calculate number of long breaks (11 hours after 9 hours of driving)
        long_breaks = (duration / Decimal("9.0")).to_integral_value()
        logger.debug("Number of long breaks", long_breaks=int(long_breaks))

        # Calculate total rest period cost
        rest_period_rate = settings.rest_period_rate
        total_cost = (
            short_breaks * Decimal("0.25") + long_breaks * Decimal("11.0")
        ) * rest_period_rate

        logger.info(
            "Calculated rest period costs",
            route_id=str(route.id),
            short_breaks=int(short_breaks),
            long_breaks=int(long_breaks),
            rest_period_rate=float(rest_period_rate),
            total_cost=float(total_cost)
        )

        return total_cost

    def _calculate_loading_unloading_costs(
        self,
        route: Route,
        settings: CostSettings
    ) -> Decimal:
        """Calculate loading and unloading costs."""
        # Get the rate from settings
        rate = settings.loading_unloading_rate
        
        # Assume 1 hour for loading and 1 hour for unloading
        total_cost = rate * Decimal('2')
        
        logger = get_logger(__name__).bind(route_id=str(route.id))
        logger.info("Calculated loading/unloading costs", 
                   rate=float(rate), 
                   total_cost=float(total_cost))
        
        return total_cost

    def _get_consumption_rates(self, transport_type: Optional[TransportType] = None) -> Dict[str, Decimal]:
        """Get consumption rates for a transport type."""
        # Default rates for trucks
        rates = {
            TransportType.TRUCK: {
                "fuel": Decimal("0.35"),  # L/km
                "maintenance": Decimal("0.15"),  # €/km
                "driver": Decimal("25.0")  # €/hour
            },
            TransportType.VAN: {
                "fuel": Decimal("0.15"),  # L/km
                "maintenance": Decimal("0.10"),  # €/km
                "driver": Decimal("20.0")  # €/hour
            }
        }
        
        if transport_type and transport_type in rates:
            return rates[transport_type]
        return rates[TransportType.TRUCK]  # Default to truck rates

    def _create_route_segment(
        self,
        start_location: Location,
        end_location: Location,
        distance_km: float,
        duration_hours: float,
        country: str,
        is_empty_driving: bool = False,
        timeline_event: Optional[TimelineEventType] = None
    ) -> RouteSegment:
        """Create a route segment."""
        return RouteSegment(
            start_location=start_location,
            end_location=end_location,
            distance_km=distance_km,
            duration_hours=duration_hours,
            country=country,
            is_empty_driving=is_empty_driving,
            timeline_event=timeline_event.value if timeline_event else None
        )

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
        """Calculate detailed cost breakdown for a route."""
        logger = get_logger(__name__).bind(
            route_id=str(route.id),
            transport_type=str(vehicle_spec.vehicle_type if vehicle_spec else None),
            include_empty_driving=include_empty_driving
        )
        
        try:
            # Use default settings if none provided
            if not settings:
                settings = CostSettings.get_default()
            
            # Calculate base costs
            base_cost_breakdown = self.calculate_route_cost(
                route=route,
                settings=settings,
                cargo=None,  # TODO: Create cargo from cargo_spec
                transport_type=None,  # TODO: Get from vehicle_spec
                include_empty_driving=include_empty_driving
            )
            
            # Extract costs from the base cost breakdown
            fuel_costs = base_cost_breakdown.fuel_costs
            toll_costs = base_cost_breakdown.toll_costs
            maintenance_costs = base_cost_breakdown.maintenance_costs
            driver_costs = base_cost_breakdown.driver_costs
            empty_driving_costs = base_cost_breakdown.empty_driving_costs
            
            # Calculate loading/unloading costs
            loading_costs = self._calculate_loading_unloading_costs(route, settings)
            logger.info("Loading/unloading costs calculated", costs=float(loading_costs))
            
            # Calculate rest period costs
            rest_costs = self._calculate_rest_period_costs(route, settings)
            logger.info("Rest period costs calculated", costs=float(rest_costs))
            
            # Calculate overhead costs
            logger.info("Calculating overhead costs")
            total_overhead = self._calculate_overhead_costs(route, settings)
            logger.info("Overhead costs calculated", costs=float(sum(total_overhead.values())))

            # Create overheads dictionary with proper structure
            overheads = {
                "distance": total_overhead["distance"],
                "time": total_overhead["time"],
                "fixed": total_overhead["fixed"],
                "total": total_overhead["total"]
            }

            # Create cost breakdown
            breakdown = CostBreakdown(
                fuel_costs=fuel_costs,
                toll_costs=toll_costs,
                maintenance_costs=maintenance_costs,
                driver_costs=driver_costs,
                empty_driving_costs=empty_driving_costs,
                loading_unloading_costs=loading_costs,
                rest_period_costs=rest_costs,
                overheads=overheads,
                total_cost=sum([
                    sum(fuel_costs.values()),
                    sum(toll_costs.values()),
                    sum(maintenance_costs.values()),
                    sum(driver_costs.values()),
                    sum(c["cost"] for c in empty_driving_costs.values()),
                    loading_costs,
                    rest_costs,
                    overheads["total"]
                ])
            )
            
            logger.info("Cost calculation completed", 
                       fuel_costs={k: float(v) for k, v in fuel_costs.items()},
                       toll_costs={k: float(v) for k, v in toll_costs.items()},
                       maintenance_costs={k: float(v) for k, v in maintenance_costs.items()},
                       driver_costs={k: float(v) for k, v in driver_costs.items()},
                       empty_driving_costs={k: {sk: float(sv) if isinstance(sv, Decimal) else sv 
                                              for sk, sv in v.items()} 
                                          for k, v in empty_driving_costs.items()},
                       overheads={k: float(v) for k, v in overheads.items()},
                       total_cost=float(breakdown.total_cost))
            
            # Convert all Decimal values to floats
            breakdown_dict = breakdown.dict()
            for key, value in breakdown_dict.items():
                if isinstance(value, Decimal):
                    breakdown_dict[key] = float(value)

            return Cost(
                route_id=route.id,
                cost_id=uuid4(),
                breakdown=breakdown_dict,
                calculation_method="detailed",
                validity_period=validity_period,
                amount=float(breakdown.total_cost),
                metadata={
                    "vehicle_spec": vehicle_spec.dict() if vehicle_spec else None,
                    "include_empty_driving": include_empty_driving,
                    "include_country_breakdown": include_country_breakdown
                },
                version="1.0"
            )
            
        except Exception as e:
            logger.error(
                "Cost calculation failed",
                error=str(e),
                error_type=type(e).__name__
            )
            raise

    def _calculate_cargo_specific_costs(
        self,
        route: Route,
        cargo: Cargo,
        settings: CostSettings
    ) -> Dict[str, Decimal]:
        """Calculate cargo-specific costs based on type and requirements."""
        cargo_factors = {
            "general": {
                "weight": Decimal("1.0"),
                "volume": Decimal("1.0"),
            },
            "refrigerated": {
                "weight": Decimal("1.2"),
                "volume": Decimal("1.1"),
                "temperature": Decimal("1.3"),
            },
            "hazmat": {
                "weight": Decimal("1.3"),
                "volume": Decimal("1.2"),
                "risk": Decimal("1.4"),
            }
        }
        costs = {}
        
        # Weight-based costs
        if "weight" in cargo_factors[cargo.type]:
            costs["weight"] = Decimal(str(cargo.weight)) * cargo_factors[cargo.type]["weight"]
        
        # Special requirements costs
        for req, value in cargo.special_requirements.items():
            if req in cargo_factors[cargo.type]:
                costs[req] = Decimal(str(value)) * cargo_factors[cargo.type][req]
        
        # Hazmat costs
        if cargo.hazmat and "hazmat" in cargo_factors[cargo.type]:
            costs["hazmat"] = cargo_factors[cargo.type]["hazmat"]
        
        return costs

    def _get_default_settings(self) -> CostSettings:
        """Get default cost settings."""
        return CostSettings(
            fuel_prices={
                "PL": Decimal("1.5"),  # €/L for Poland
                "DE": Decimal("1.7"),  # €/L for Germany
                "FR": Decimal("1.6"),  # €/L for France
                "ES": Decimal("1.4"),  # €/L for Spain
                "IT": Decimal("1.6"),  # €/L for Italy
                "NL": Decimal("1.8"),  # €/L for Netherlands
                "BE": Decimal("1.7"),  # €/L for Belgium
                "AT": Decimal("1.6"),  # €/L for Austria
                "CH": Decimal("1.9"),  # €/L for Switzerland
                "CZ": Decimal("1.4")   # €/L for Czech Republic
            },
            driver_rates={
                "PL": Decimal("20"),  # €/hour for Poland
                "DE": Decimal("35"),  # €/hour for Germany
                "FR": Decimal("32"),  # €/hour for France
                "ES": Decimal("25"),  # €/hour for Spain
                "IT": Decimal("30"),  # €/hour for Italy
                "NL": Decimal("35"),  # €/hour for Netherlands
                "BE": Decimal("33"),  # €/hour for Belgium
                "AT": Decimal("32"),  # €/hour for Austria
                "CH": Decimal("40"),  # €/hour for Switzerland
                "CZ": Decimal("22")   # €/hour for Czech Republic
            },
            toll_rates={
                "PL": {"highway": Decimal("0.15"), "national": Decimal("0.10")},  # €/km for Poland
                "DE": {"highway": Decimal("0.25"), "national": Decimal("0.18")},  # €/km for Germany
                "FR": {"highway": Decimal("0.22"), "national": Decimal("0.15")},  # €/km for France
                "ES": {"highway": Decimal("0.18"), "national": Decimal("0.12")},  # €/km for Spain
                "IT": {"highway": Decimal("0.20"), "national": Decimal("0.14")},  # €/km for Italy
                "NL": {"highway": Decimal("0.23"), "national": Decimal("0.16")},  # €/km for Netherlands
                "BE": {"highway": Decimal("0.21"), "national": Decimal("0.15")},  # €/km for Belgium
                "AT": {"highway": Decimal("0.24"), "national": Decimal("0.17")},  # €/km for Austria
                "CH": {"highway": Decimal("0.28"), "national": Decimal("0.20")},  # €/km for Switzerland
                "CZ": {"highway": Decimal("0.16"), "national": Decimal("0.11")}   # €/km for Czech Republic
            },
            rest_period_rate=Decimal("20.00"),  # €/hour for rest periods
            loading_unloading_rate=Decimal("30.00"),  # €/hour for loading/unloading
            empty_driving_factors={
                "fuel": Decimal("0.8"),  # 80% of normal fuel consumption
                "toll": Decimal("1.0"),  # Same toll rates
                "driver": Decimal("1.0")  # Same driver rates
            },
            overhead_rates={
                "distance": Decimal("0.15"),  # €/km overhead
                "time": Decimal("25.00"),     # €/hour overhead
                "fixed": Decimal("50.00"),   # € fixed overhead per route
            },
            default_fuel_rate=Decimal("1.5"),  # Default fuel price if country not found
            default_driver_rate=Decimal("25.0")  # Default driver rate if country not found
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
                base_cost = total_cost
                offer_logger.info("using_provided_base_cost", base_cost=str(base_cost))
                # Create a basic Cost entity for the provided total_cost
                cost = Cost(
                    id=uuid4(),
                    route_id=route.id,
                    breakdown=CostBreakdown(
                        total=Decimal(str(base_cost)),
                        fuel=Decimal("0.0"),  # Initialize all monetary values as Decimal
                        driver=Decimal("0.0"),
                        toll=Decimal("0.0"),
                        overhead=Decimal("0.0"),
                        empty_driving=Decimal("0.0"),
                        loading_unloading=Decimal("0.0"),
                        rest_periods=Decimal("0.0")
                    ),
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
                base_cost = float(cost.total)
                offer_logger.info("base_cost_calculated", base_cost=str(base_cost))
            
            # Apply margin and convert to float for storage
            margin_decimal = Decimal(str(margin)) / Decimal("100")  # Convert percentage to decimal
            margin_amount = base_cost * float(margin_decimal)
            final_price = base_cost + margin_amount
            
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

            # Create offer object with float values for database storage
            offer = Offer(
                id=uuid4(),
                route_id=route.id,
                cost_id=cost.id if 'cost' in locals() else None,
                total_cost=Decimal(str(base_cost)),  # Store as Decimal in domain entity
                margin=margin_decimal,  # Store as Decimal in domain entity
                final_price=Decimal(str(final_price)),  # Store as Decimal in domain entity
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
                final_price=Decimal(str(final_price)),  # Store as Decimal in domain entity
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
