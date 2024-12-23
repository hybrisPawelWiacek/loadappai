Below is a proposed "Domain Entities and Services Design" document that complements the existing PRD and System Architecture documents. It provides a blueprint for how the AI Agent should structure and implement domain entities and services in a way that supports the current PoC scope and leaves room for future growth and enhancements.

---

# LoadApp.AI Domain Entities & Services Design

**Version:** 1.3  
**Date:** December 22, 2024

## 1. Introduction

This document outlines the foundational design of domain entities and services for LoadApp.AI. Its goal is to provide clear guidelines for how the AI Agent should model, implement, and interact with core entities, ensuring the system can evolve over time without extensive refactoring.

The design adheres to clean architecture principles, separating domain logic from external concerns, and embedding extensibility into the domain model. While the initial focus is on the PoC requirements, this design anticipates future enhancements, integrations, and complexity.

## 2. Design Goals

1. **Separation of Concerns**: Domain entities represent core business logic and rules. Services orchestrate entity interactions, while repositories and external APIs are abstracted away.
   
2. **Extensibility & Scalability**: Entities and services should be easily adjustable to accommodate new features (e.g., market-based pricing, advanced compliance checks, resource optimization) without major structural changes.

3. **Domain-Driven Structure**: Entities use clear, expressive field names and data types that reflect business concepts. Services encapsulate business operations (e.g., calculating costs, generating offers, validating feasibility) in a way that’s easy to extend.

4. **Testability**: Entities and services should be testable in isolation. Most domain logic should live in pure functions/methods within the domain layer, enabling straightforward unit tests without complex mocking.

## 3. Domain Layer Overview

The domain layer consists of three main categories:

1. **Entities (Core Data Models)**:  
   Represent real-world concepts like Routes, Offers, Costs, Cargo, and Transport Resources. Entities are primarily data holders but may include simple validation or domain logic that doesn’t depend on external infrastructure.

2. **Value Objects & Enums**:  
   Represent small, immutable, domain-specific data concepts (e.g., Location coordinates, Currency, CostType enums). They add clarity and enforce constraints.

3. **Domain Services**:  
   Encapsulate business operations that span multiple entities. For example, the `CostCalculationService` fetches costs for a given route, and `OfferService` generates final offers. They do not know about database or API details, relying on abstractions or passed-in data.

### Architectural Layers in Context

```
+-------------------------+
|       Presentation      | (Streamlit UI)
+------------+------------+
             |
             v
+-------------------------+
|        Application      | (Flask endpoints)
+------------+------------+
             |
             v
+-------------------------+
|         Domain          | (Entities, Value Objects, Domain Services)
+------------+------------+
             |
             v
+-------------------------+
|       Infrastructure    | (Repositories, API clients)
+-------------------------+
```

## 4. Core Entities

### 4.1 Location

**Responsibility**: Represents a geographical location with address and coordinates.

**PoC Fields**:
- `address: str`
- `city: str`
- `country: str`
- `postal_code: str`
- `coordinates: Coordinates`

**Value Objects**:
- `Coordinates` class: `lat: float`, `lng: float`

**Business Rules**:
- Latitude must be between -90 and 90
- Longitude must be between -180 and 180
- Country must be valid ISO code

### 4.2 TimeWindow

**Responsibility**: Defines a time period for pickup or delivery.

**PoC Fields**:
- `earliest: datetime`
- `latest: datetime`
- `duration_minutes: int`

**Business Rules**:
- Latest must be after earliest
- Duration must be positive
- Time window must be within 24 hours

### 4.3 TransportType

**Responsibility**: Specifies vehicle type and capabilities.

**PoC Fields**:
- `type: str`
- `capacity_kg: int`
- `length_meters: float`
- `special_equipment: List[str]`

**Business Rules**:
- Type must be one of: "TRUCK", "VAN", "TRAILER"
- Capacity must be positive
- Length must be positive
- Special equipment must be from allowed list

### 4.4 CargoSpecification

**Responsibility**: Defines cargo requirements and constraints.

**PoC Fields**:
- `weight_kg: float`
- `volume_m3: float`
- `requires_cooling: bool`
- `hazmat_class: Optional[str]`
- `special_requirements: List[str]`

**Business Rules**:
- Weight must be positive and within vehicle capacity
- Volume must be positive
- Special requirements must match vehicle capabilities

### 4.5 Route

**Responsibility**: Represents a transport route with segments and timeline.

**PoC Fields**:
- `id: UUID`
- `pickup: RouteStop`
- `delivery: RouteStop`
- `transport_type: TransportType`
- `cargo: Optional[CargoSpecification]`
- `segments: List[RouteSegment]`
- `timeline: List[TimelineEvent]`
- `total_distance_km: float`
- `total_duration_minutes: int`
- `empty_driving_km: float`
- `empty_driving_minutes: int`
- `countries_crossed: List[str]`
- `feasibility: RouteFeasibility`
- `created_at: datetime`
- `created_by: str`

**Value Objects**:
- `RouteStop` class:
  - `location: Location`
  - `time_window: TimeWindow`

- `RouteSegment` class:
  - `id: UUID`
  - `start_location: Location`
  - `end_location: Location`
  - `distance_km: float`
  - `duration_minutes: int`
  - `country: str`
  - `is_empty_driving: bool`
  - `timeline_event: Optional[TimelineEvent]`

- `TimelineEvent` class:
  - `type: str`  # PICKUP, DELIVERY, REST, BORDER_CROSSING
  - `location: Location`
  - `planned_time: datetime`
  - `duration_minutes: int`
  - `notes: Optional[str]`

- `RouteFeasibility` class:
  - `is_feasible: bool`
  - `warnings: List[str]`

**Business Rules**:
- Delivery time must be after pickup time
- Empty driving must be detected for >200km/4h gaps
- Rest periods required after 4.5h driving
- Timeline events must be in chronological order
- All segments must connect (end = next start)
- Country changes must have border crossing events

## 5. Value Objects & Enums

**Examples**:
- `Location(latitude: float, longitude: float, address: str)`
- `CountrySegment(country_code: str, distance: float, toll_rates: Dict[str, Decimal])`
- `Currency(code: str)` (future: handle exchange rates)
- `CostType` enum: `FUEL`, `TOLL`, `DRIVER`, `OVERHEAD`, `CARGO_SPECIFIC`, `MISC`

These immutable, self-contained units clarify domain concepts and can be extended or refined as needs grow.

## 6. Domain Services

### 6.1 RoutePlanningService

**Responsibility**:  
Plans routes with empty driving detection, timeline generation, and feasibility checks.

**PoC Methods**:
```python
def plan_route(
    pickup: RouteStop,
    delivery: RouteStop,
    transport_type: TransportType,
    cargo: Optional[CargoSpecification] = None
) -> Route:
    """Plan a route with segments and timeline."""

def calculate_segments(
    route: Route
) -> List[RouteSegment]:
    """Calculate route segments with country info."""

def detect_empty_driving(
    segments: List[RouteSegment]
) -> List[RouteSegment]:
    """Detect empty driving segments (>200km/4h)."""

def generate_timeline(
    segments: List[RouteSegment]
) -> List[TimelineEvent]:
    """Generate timeline with all events."""

def check_feasibility(
    route: Route
) -> RouteFeasibility:
    """Check route feasibility and generate warnings."""

def get_route(
    route_id: UUID
) -> Optional[Route]:
    """Get route by ID with all details."""
```

**Future Enhancements**:
- Multiple stop support
- Alternative routes
- Real-time traffic
- Weather conditions
- Advanced rest periods
- Driver preferences

### 6.2 CostCalculationService

**Responsibility**:  
Calculates detailed cost breakdowns for routes based on current settings and factors.

**PoC Methods**:
```python
def calculate_costs(
    route: Route,
    settings: CostSettings,
    calculation_method: str = "standard"
) -> Cost:
    """Calculate detailed cost breakdown for a route."""

def calculate_distance_costs(
    route: Route,
    settings: CostSettings
) -> DistanceBasedCosts:
    """Calculate distance-based costs by country."""

def calculate_time_costs(
    route: Route,
    settings: CostSettings
) -> TimeBasedCosts:
    """Calculate time-based costs by country."""

def calculate_empty_driving_costs(
    route: Route,
    settings: CostSettings
) -> EmptyDrivingCosts:
    """Calculate empty driving costs by country."""

def calculate_cargo_costs(
    route: Route,
    settings: CostSettings
) -> CargoSpecificCosts:
    """Calculate cargo-specific costs."""

def validate_settings(
    settings: CostSettings
) -> Tuple[bool, List[str]]:
    """Validate cost settings and return warnings."""

def get_cost_history(
    route_id: UUID,
    page: int = 1,
    per_page: int = 10
) -> Tuple[List[CostHistory], int]:
    """Get paginated cost history for a route."""
```

**Future Enhancements**:
- Dynamic pricing models
- Cost optimization algorithms
- Market-based adjustments
- Real-time rate updates
- Advanced cargo cost models
- Multi-currency support

### 6.3 OfferService

**Responsibility**:  
Manages offer lifecycle, including version control, status transitions, and history tracking.

**PoC Methods**:
```python
def create_offer(
    route_id: UUID,
    margin: float,
    status: Optional[str] = "DRAFT",
    additional_services: Optional[List[str]] = None,
    notes: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Offer:
    """Create a new offer with initial version 1.0."""

def update_offer(
    offer_id: UUID,
    version: str,
    margin: Optional[float] = None,
    additional_services: Optional[List[str]] = None,
    notes: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    change_reason: str
) -> Offer:
    """Update an offer, incrementing version if successful."""

def update_status(
    offer_id: UUID,
    status: str,
    change_reason: str
) -> Offer:
    """Update offer status following allowed transitions."""

def archive_offer(
    offer_id: UUID,
    change_reason: str = "Archiving offer"
) -> Offer:
    """Archive an active offer."""

def get_offer_history(
    offer_id: UUID,
    page: int = 1,
    per_page: int = 10
) -> Tuple[List[OfferHistory], int]:
    """Get paginated offer history with total count."""

def get_offer_version(
    offer_id: UUID,
    version: str
) -> Optional[Dict[str, Any]]:
    """Get specific version of an offer."""

def list_offers(
    filters: Optional[OfferFilters] = None,
    page: int = 1,
    per_page: int = 10
) -> Tuple[List[Offer], int]:
    """List offers with filtering and pagination."""
```

**Future Enhancements**:
- Integrate market-based adjustments
- Advanced compliance (validity periods, contract terms)
- Bulk operations and version comparison
- Real-time collaboration
- Approval workflows
- Version branching and merging

### 6.4 RoutePlanningService

**Responsibility**:  
Encapsulate logic for generating and validating routes. Currently minimal, but future-proofed.

**PoC Methods**:
- `create_route(origin: Location, destination: Location, pickup: datetime, delivery: datetime) -> Route`

**Future Enhancements**:
- Apply feasibility logic.
- Integrate weather, traffic, and compliance factors.
- Suggest alternative routes or timings.

### 6.5 SettingsService (Optional at PoC)

**Responsibility**:
Manage retrieval and updates of cost settings, overhead configurations, and feature toggles.

**PoC Methods**:
- `get_cost_settings() -> CostSettings`
- `update_cost_settings(settings: CostSettings) -> None`

**Future Enhancements**:
- Hierarchical settings for different business entities.
- Automated updates from external data sources.

### 6.6 StateService

**Responsibility**:  
Manages frontend state, including form validation, loading states, and error handling.

**PoC Methods**:
```python
def get_state() -> State:
    """Get or create state container."""

def validate_form(data: Dict[str, Any]) -> bool:
    """Validate form data against business rules."""

def update_form(field: str, value: Any) -> None:
    """Update form field with validation."""

def load_offers(
    page: int = 1,
    filters: Optional[OfferFilters] = None
) -> None:
    """Load offers with loading state management."""

def load_offer(offer_id: UUID) -> None:
    """Load single offer with loading state."""

def update_offer(
    offer_id: UUID,
    data: Dict[str, Any]
) -> bool:
    """Update offer with error handling."""

def handle_error(error: Exception) -> None:
    """Handle and display user-friendly errors."""
```

**Future Enhancements**:
- State persistence
- Real-time updates
- Optimistic updates
- Undo/redo functionality
- Form autosave
- Collaborative editing

## 7. Interactions & Extensibility

Domain services are stateless and rely on data passed in or fetched via repository interfaces (implemented in the infrastructure layer). This design allows:

- Swapping out cost calculation strategies (e.g., a `CostCalculationStrategy` interface with multiple implementations).
- Adding new domain services without disrupting existing logic.
- Introducing advanced features (weather impact, AI-based route optimization) by passing additional parameters, injecting new services, or toggling feature flags.

## 8. Example Flow (PoC Mode)

1. **Route Creation**:  
   `RoutePlanningService` creates a `Route` entity from user input. Basic feasibility checks run (always true for PoC).

2. **Cost Calculation**:  
   `CostCalculationService` fetches current cost settings and applies simple calculations to produce a `Cost` entity.

3. **Offer Generation**:  
   `OfferService` takes the `Route` and computed `Cost`, applies a margin, calls an external AI service (through an adapter) for a fun fact, and returns a fully populated `Offer` entity.

In the PoC mode, everything is straightforward. As we add complexity (advanced feasibility checks, weather impact), we extend the services, not rewrite them.

## 9. Testing and Validation

- **Unit Tests**: For each service (CostCalculationService, OfferService, RoutePlanningService), mock dependencies and verify business logic.
- **Entity Validation**: Route, Offer, and other entities validate their own fields (e.g., ensure pickup_time < delivery_time).
- **Integration Tests**: Combined with repository mocks, ensure that domain logic functions end-to-end.

## 10. Guidelines for Future Growth

- Always introduce new features behind feature flags (e.g., `route._weather_enabled`).
- Use composition over inheritance: add new domain services or strategies rather than extending existing classes in a brittle way.
- Store extension data in JSON fields within entities to avoid schema lock-in (as described in the Future Extensibility Requirements).
- Keep domain services pure and pass in all necessary data. Use repositories or adapters injected as interfaces, so replacing or upgrading infrastructure later is simple.
- Document any new domain-level concepts thoroughly.

---

# Conclusion

This "Domain Entities and Services Design" document sets the foundation for how the AI Agent should model core business logic for LoadApp.AI. It supports the current PoC needs while maintaining a flexible structure for incorporating advanced features and integrations in the future. By adhering to these principles, the domain layer remains robust, testable, and ready for incremental evolution as the product grows.

### Core Domain Entities

### Route Entity
```python
@dataclass
class Route:
    id: UUID
    origin: Location
    destination: Location
    pickup_window: TimeWindow
    delivery_window: TimeWindow
    transport_type: TransportType
    cargo: CargoSpecification
    segments: List[RouteSegment] = field(default_factory=list)
    timeline: List[TimelineEvent] = field(default_factory=list)
    version: str = field(default="1.0")
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> List[ValidationError]:
        errors = []
        # Location validation
        if not self.origin.is_valid():
            errors.append(ValidationError("origin", "Invalid origin location"))
        if not self.destination.is_valid():
            errors.append(ValidationError("destination", "Invalid destination location"))
            
        # Time window validation
        if not self.pickup_window.is_valid():
            errors.append(ValidationError("pickup_window", "Invalid pickup window"))
        if not self.delivery_window.is_valid():
            errors.append(ValidationError("delivery_window", "Invalid delivery window"))
        if self.pickup_window.latest >= self.delivery_window.earliest:
            errors.append(ValidationError("time_windows", "Pickup must be before delivery"))
            
        # Minimum time between pickup and delivery
        min_duration = timedelta(hours=4)
        if (self.delivery_window.earliest - self.pickup_window.latest) < min_duration:
            errors.append(ValidationError("time_windows", "Minimum 4 hours between pickup and delivery"))
            
        # Transport type validation
        if not self.transport_type.can_handle_cargo(self.cargo):
            errors.append(ValidationError("transport_type", "Transport type cannot handle cargo"))
            
        return errors

    def add_timeline_event(self, event: TimelineEvent):
        """Add event and maintain chronological order"""
        self.timeline.append(event)
        self.timeline.sort(key=lambda x: x.scheduled_time)
        self.version = increment_version(self.version)

    def update_segments(self, segments: List[RouteSegment]):
        """Update segments and recalculate timeline"""
        self.segments = segments
        self._recalculate_timeline()
        self.version = increment_version(self.version)
```

### Timeline Events
```python
@dataclass
class TimelineEvent:
    type: Literal["PICKUP", "DELIVERY", "REST", "BORDER_CROSSING"]
    location: Location
    scheduled_time: datetime
    duration_minutes: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> List[ValidationError]:
        errors = []
        if not self.location.is_valid():
            errors.append(ValidationError("location", "Invalid location"))
        if self.duration_minutes < 0:
            errors.append(ValidationError("duration_minutes", "Duration cannot be negative"))
        return errors
```

### Route Segment
```python
@dataclass
class RouteSegment:
    start_location: Location
    end_location: Location
    distance_km: float
    duration_minutes: int
    empty_driving: bool
    country: str
    version: str = field(default="1.0")
    
    def validate(self) -> List[ValidationError]:
        errors = []
        if not self.start_location.is_valid():
            errors.append(ValidationError("start_location", "Invalid start location"))
        if not self.end_location.is_valid():
            errors.append(ValidationError("end_location", "Invalid end location"))
        if self.distance_km <= 0:
            errors.append(ValidationError("distance_km", "Distance must be positive"))
        if self.duration_minutes <= 0:
            errors.append(ValidationError("duration_minutes", "Duration must be positive"))
        return errors
```

### Cost Entity
```python
@dataclass
class Cost:
    route_id: UUID
    total: float
    breakdown: CostBreakdown
    by_country: List[CountryCost]
    settings_version: str
    version: str = field(default="1.0")
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> List[ValidationError]:
        errors = []
        if self.total < 0:
            errors.append(ValidationError("total", "Total cost cannot be negative"))
        if not self.breakdown.validate():
            errors.append(ValidationError("breakdown", "Invalid cost breakdown"))
        return errors
```

### Offer Entity
```python
@dataclass
class Offer:
    id: UUID
    route_id: UUID
    total_price: float
    breakdown: OfferBreakdown
    status: Literal["DRAFT", "SENT", "ACCEPTED", "REJECTED"]
    valid_until: datetime
    version: str = field(default="1.0")
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> List[ValidationError]:
        errors = []
        if self.total_price <= 0:
            errors.append(ValidationError("total_price", "Price must be positive"))
        if not self.breakdown.validate():
            errors.append(ValidationError("breakdown", "Invalid price breakdown"))
        if self.valid_until <= datetime.now():
            errors.append(ValidationError("valid_until", "Validity period expired"))
        return errors
        
    def can_transition_to(self, new_status: str) -> bool:
        """Validate status transitions"""
        valid_transitions = {
            "DRAFT": ["SENT"],
            "SENT": ["ACCEPTED", "REJECTED"],
            "ACCEPTED": [],
            "REJECTED": []
        }
        return new_status in valid_transitions.get(self.status, [])
```

## Domain Services

### Route Planning Service
```python
class RoutePlanningService:
    def create_route(self, request: RouteRequest) -> Route:
        # Validate request
        errors = request.validate()
        if errors:
            raise ValidationError(errors)
            
        # Create route with segments
        route = self._create_base_route(request)
        segments = self._calculate_segments(route)
        route.update_segments(segments)
        
        # Generate timeline
        self._generate_timeline(route)
        
        return route
        
    def _generate_timeline(self, route: Route):
        """Generate timeline events for route"""
        # Add pickup event
        route.add_timeline_event(TimelineEvent(
            type="PICKUP",
            location=route.origin,
            scheduled_time=route.pickup_window.earliest,
            duration_minutes=30
        ))
        
        # Add border crossings
        for segment in route.segments:
            if segment.country != previous_country:
                route.add_timeline_event(TimelineEvent(
                    type="BORDER_CROSSING",
                    location=segment.start_location,
                    scheduled_time=calculate_time(previous_event),
                    duration_minutes=15
                ))
                
        # Add rest periods
        rest_periods = self._calculate_rest_periods(route)
        for rest in rest_periods:
            route.add_timeline_event(TimelineEvent(
                type="REST",
                location=rest.location,
                scheduled_time=rest.time,
                duration_minutes=480  # 8 hours
            ))
            
        # Add delivery event
        route.add_timeline_event(TimelineEvent(
            type="DELIVERY",
            location=route.destination,
            scheduled_time=route.delivery_window.earliest,
            duration_minutes=30
        ))
```

### Cost Calculation Service
```python
class CostCalculationService:
    def calculate_cost(self, route: Route, settings: CostSettings) -> Cost:
        # Validate inputs
        if errors := route.validate():
            raise ValidationError(errors)
            
        # Calculate costs by segment
        segment_costs = []
        for segment in route.segments:
            cost = self._calculate_segment_cost(segment, settings)
            segment_costs.append(cost)
            
        # Aggregate by country
        country_costs = self._aggregate_by_country(segment_costs)
        
        # Calculate total
        total = sum(cost.total for cost in country_costs)
        
        return Cost(
            route_id=route.id,
            total=total,
            breakdown=self._create_breakdown(segment_costs),
            by_country=country_costs,
            settings_version=settings.version
        )
```

### Offer Service
```python
class OfferService:
    def create_offer(self, route_id: UUID, margin: float, 
                    additional_services: List[Service]) -> Offer:
        # Validate inputs
        route = self.route_repository.get(route_id)
        if errors := route.validate():
            raise ValidationError(errors)
            
        # Calculate costs
        cost = self.cost_service.calculate_cost(route)
        
        # Calculate final price
        base_price = cost.total
        margin_amount = base_price * margin
        services_cost = sum(service.cost for service in additional_services)
        total_price = base_price + margin_amount + services_cost
        
        # Create offer
        offer = Offer(
            id=uuid4(),
            route_id=route_id,
            total_price=total_price,
            breakdown=OfferBreakdown(
                base_cost=base_price,
                margin=margin_amount,
                additional_services=services_cost
            ),
            status="DRAFT",
            valid_until=datetime.now() + timedelta(hours=24)
        )
        
        # Validate offer
        if errors := offer.validate():
            raise ValidationError(errors)
            
        return offer
        
    def update_offer_status(self, offer_id: UUID, new_status: str,
                           current_version: str) -> Offer:
        # Get and validate offer
        offer = self.offer_repository.get(offer_id)
        if offer.version != current_version:
            raise VersionConflictError()
            
        # Validate status transition
        if not offer.can_transition_to(new_status):
            raise BusinessRuleViolation("Invalid status transition")
            
        # Update status and version
        offer.status = new_status
        offer.version = increment_version(offer.version)
        
        return offer
```

## Version Control

### Version Management
```python
def increment_version(version: str) -> str:
    """Increment the minor version number"""
    major, minor = version.split('.')
    return f"{major}.{int(minor) + 1}"

def validate_version(entity_version: str, provided_version: str) -> bool:
    """Validate version matches for updates"""
    return entity_version == provided_version
```

## Validation

### Validation Rules
```python
@dataclass
class ValidationError:
    field: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)

def validate_location(location: Location) -> List[ValidationError]:
    """Validate location data"""
    errors = []
    if not location.address:
        errors.append(ValidationError("address", "Address is required"))
    if not (-90 <= location.coordinates.lat <= 90):
        errors.append(ValidationError("coordinates.lat", "Invalid latitude"))
    if not (-180 <= location.coordinates.lng <= 180):
        errors.append(ValidationError("coordinates.lng", "Invalid longitude"))
    if not location.country:
        errors.append(ValidationError("country", "Country is required"))
    return errors

def validate_time_window(window: TimeWindow) -> List[ValidationError]:
    """Validate time window"""
    errors = []
    if window.earliest >= window.latest:
        errors.append(ValidationError("time_window", 
                                   "Earliest time must be before latest"))
    if window.duration_minutes <= 0:
        errors.append(ValidationError("duration_minutes",
                                   "Duration must be positive"))
    return errors