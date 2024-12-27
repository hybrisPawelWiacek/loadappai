# Cost Settings Implementation Gameplan

**Version:** 1.1  
**Date:** December 24, 2024  
**Status:** In Progress

## Overview

This document outlines the implementation plan for adding cost settings functionality to LoadApp.AI. The implementation follows a backend-first approach, ensuring proper domain modeling and business logic before UI development.

### Key Implementation Principles

1. **Code Preservation**
   - Existing functionality must be preserved
   - Any modifications to existing code require explicit permission
   - Changes should be isolated to new features when possible

2. **Requirements Alignment**
   - All feature implementations must align with specifications in `prd20.md`
   - Unclear requirements should be clarified before implementation
   - Regular validation against PRD during development

3. **API & Integration Integrity**
   - Maintain compatibility with current API endpoints
   - Ensure frontend API client continues to function correctly
   - Follow established API patterns and conventions

4. **Domain Model Stability**
   - Preserve existing domain entities and services functionality
   - Follow established domain patterns for new features
   - Maintain clean architecture principles

5. **Infrastructure Reliability**
   - Ensure database schema changes don't impact existing data
   - Maintain current infrastructure performance
   - Follow established patterns for infrastructure extensions

6. **Development Best Practices**
   - Use Python virtual environment
   - Maintain updated requirements.txt
   - Follow port usage guidelines (Backend: 5001, Frontend: 8501)
   - Include comprehensive testing
   - Document all significant changes

7. **PoC Implementation Approach**
   - Use real data and actual integrations between components
   - No mock data or simulated services
   - Keep implementation simple and focused
   - Prioritize working functionality over perfect architecture

## User Flow Specification

### 1. Route Form & Submission
- Form always displayed at top
- On submit:
  - Triggers route calculation
  - Saves route to database
  - Updates session state: `st.session_state.route_id`

### 2. Route Visualization (Immediate)
- Displays as soon as route data received
- Shows:
  - Interactive map
  - Timeline
  - Total distance
  - Duration
  - Empty driving metrics
- Updates session state: `st.session_state.route_visualized = True`

### 3. Cost Settings Component
- Appears after route visualization
- Features:
  - Cost type toggles
  - Rate editing per country/type
  - Submit button for calculation
- On submit:
  - Saves settings to database
  - Triggers cost calculation
  - Updates session state: `st.session_state.cost_settings_submitted = True`

### 4. Cost Display
- Appears after cost calculation
- Shows detailed breakdown
- Updates session state: `st.session_state.costs_calculated = True`

### 5. Offer Generation
- Only appears after costs calculated
- Dedicated bottom container
- Saves offer to database

## Implementation Checklist

### Phase 1: Backend Domain Model & Database
- [x] 1.1. Create Cost Settings Domain Entities
  - Implemented in `src/domain/entities.py`
  - Added route-specific `CostSettings` with:
    - Route ID tracking
    - Component-based cost calculation control
    - Simplified rate structure for fuel, toll, driver, maintenance
    - Version tracking and audit fields
    - Comprehensive validation
  - Added `CostComponent` for structured cost representation:
    - Type validation (fuel, toll, driver, etc.)
    - Amount validation with currency
    - Country-specific cost tracking
    - Detailed cost breakdown storage
    - Updated `Route.calculate_costs` to use new structure
  ```python
  @dataclass
  class CostSettings:
      """Cost settings for a specific route."""
      route_id: UUID
      fuel_rates: Dict[str, Decimal]  # By country
      toll_rates: Dict[str, Dict[str, Decimal]]  # By country and vehicle type
      driver_rates: Dict[str, Decimal]  # By country
      overhead_rates: Dict[str, Decimal]  # Fixed overheads
      maintenance_rates: Dict[str, Decimal]  # By vehicle type
      enabled_components: Set[str]  # Which cost components are enabled
      version: str = "1.0"
      created_at: datetime = field(default_factory=utc_now)
      modified_at: datetime = field(default_factory=utc_now)
      created_by: Optional[str] = None
      modified_by: Optional[str] = None

  @dataclass
  class CostComponent:
      """Individual cost component."""
      type: str  # fuel, toll, driver, etc.
      amount: Decimal
      currency: str
      country: Optional[str] = None
      details: Dict[str, Any] = field(default_factory=dict)
  ```

- [x] 1.2. Implement Domain Services
  ```python
  class CostSettingsService:
      """Service for managing cost settings."""
      
      def __init__(self, settings_repository, route_repository):
          self.settings_repository = settings_repository
          self.route_repository = route_repository
          
      def get_settings(self, route_id: UUID) -> CostSettings:
          """Get cost settings for a route."""
          return self.settings_repository.get_by_route_id(route_id)
          
      def update_settings(self, route_id: UUID, settings: CostSettings) -> CostSettings:
          """Update cost settings for a route."""
          route = self.route_repository.get_by_id(route_id)
          if not route:
              raise ValueError(f"Route {route_id} not found")
              
          # Validate settings against route
          self._validate_settings(route, settings)
          
          # Save settings
          return self.settings_repository.save(settings)
          
      def _validate_settings(self, route: Route, settings: CostSettings):
          """Validate settings against route."""
          # Check countries match route
          route_countries = {seg.country for seg in route.segments}
          settings_countries = set(settings.fuel_rates.keys())
          if not settings_countries.issuperset(route_countries):
              raise ValueError("Missing rates for some countries in route")

  class CostCalculationService:
      """Service for calculating route costs."""
      
      def __init__(self, settings_service, cost_repository):
          self.settings_service = settings_service
          self.cost_repository = cost_repository
          
      def calculate_costs(self, route_id: UUID) -> EnhancedCostBreakdown:
          """Calculate costs for a route using its current settings."""
          # Get route settings
          settings = self.settings_service.get_settings(route_id)
          if not settings:
              raise ValueError(f"No cost settings found for route {route_id}")
              
          # Calculate each enabled component
          components = []
          if "fuel" in settings.enabled_components:
              components.append(self._calculate_fuel_costs(route, settings))
          if "toll" in settings.enabled_components:
              components.append(self._calculate_toll_costs(route, settings))
          # ... etc for other components
          
          # Create and save cost breakdown
          breakdown = EnhancedCostBreakdown(components)
          return self.cost_repository.save(breakdown)
  ```

- [x] 1.3. Create Repository Interfaces
  - Added `CostSettingsRepository` interface in `src/domain/interfaces.py` with:
    - Route-specific settings retrieval
    - Settings persistence
    - Version history tracking
    - Default settings management
    - Version-specific retrieval
  ```python
  @abstractmethod
  def get_by_route_id(self, route_id: UUID) -> Optional[CostSettings]:
      """Get cost settings for a route."""
      pass
        
  @abstractmethod
  def save(self, settings: CostSettings) -> CostSettings:
      """Save cost settings."""
      pass

  @abstractmethod
  def get_history(self, route_id: UUID) -> List[CostSettings]:
      """Get history of cost settings for a route."""
      pass

  @abstractmethod
  def get_defaults(self) -> CostSettings:
      """Get default cost settings configuration."""
      pass

  @abstractmethod
  def get_by_version(self, route_id: UUID, version: str) -> Optional[CostSettings]:
      """Get specific version of cost settings."""
      pass
  ```

- [x] 1.4. Implement Repository
  - Updated `CostSettingsRepository` in `src/infrastructure/repositories/cost_settings_repository.py`:
    - Implemented core interface methods:
      - `get_by_route_id`: Gets latest settings for a route
      - `save`: Persists settings with metadata
      - `get_history`: Returns all versions for a route
      - `get_defaults`: Provides default configuration
      - `get_by_version`: Retrieves specific version
    - Added deprecation warnings for old methods:
      - `create` -> use `save`
      - `get` -> use `get_by_route_id`
      - `get_all` -> no replacement (not needed)
      - `update` -> use `save`
      - `delete` -> no replacement (soft delete via versions)
      - `get_current_cost_settings` -> use `get_defaults`
    - Updated entity-model conversion with proper metadata handling
    - Added error handling for invalid settings

- [x] 1.5. Database Schema Updates
  - Added `CostSettingsModel` in `src/infrastructure/models.py`:
    ```python
    class CostSettingsModel(Base):
        """SQLAlchemy model for cost settings."""
        __tablename__ = 'cost_settings'
        
        # Primary key and relations
        id = Column(UUID, primary_key=True, default=uuid4)
        route_id = Column(UUID, ForeignKey('routes.id'), nullable=False)
        version = Column(String, nullable=False)
        
        # Cost rates by country/type
        fuel_rates = Column(JSON, nullable=False)  # {country: rate}
        toll_rates = Column(JSON, nullable=False)  # {country: {vehicle_type: rate}}
        driver_rates = Column(JSON, nullable=False)  # {country: rate}
        overhead_rates = Column(JSON, nullable=False)  # {type: rate}
        maintenance_rates = Column(JSON, nullable=False)  # {vehicle_type: rate}
        
        # Component control
        enabled_components = Column(ARRAY(String), nullable=False)  # ["fuel", "toll", ...]
        
        # Audit fields
        created_at = Column(DateTime(timezone=True), nullable=False)
        modified_at = Column(DateTime(timezone=True), nullable=False)
        created_by = Column(String)
        modified_by = Column(String)
        
        # Relationships
        route = relationship("Route", back_populates="cost_settings")
    ```
  - Key features:
    - UUID primary key with route relation
    - JSON fields for flexible rate storage
    - Array field for component control
    - Timezone-aware timestamps
    - Audit fields for tracking changes
    - Bidirectional relationship with Route

- [x] 1.6. Database Migration
  
  Implemented database migration for cost settings with SQLite compatibility:

  1. Database Configuration:
     - Location: `/instance/loadapp.db`
     - SQLite-specific type adjustments:
       - UUID → VARCHAR(36)
       - JSONB → JSON
       - TIMESTAMP WITH TIME ZONE → DATETIME
       - VARCHAR[] → JSON (for enabled_components)

  2. Migration Chain:
     - 001: Initial schema
     - 004: Add cost_settings table
     - 002_update_toll_rates: Update toll rates format

  3. Implemented Schema:
  ```sql
  CREATE TABLE cost_settings (
      id VARCHAR(36) NOT NULL, 
      route_id VARCHAR(36) NOT NULL, 
      version VARCHAR NOT NULL, 
      fuel_rates JSON NOT NULL, 
      toll_rates JSON NOT NULL, 
      driver_rates JSON NOT NULL, 
      overhead_rates JSON NOT NULL, 
      maintenance_rates JSON NOT NULL, 
      enabled_components JSON NOT NULL, 
      created_at DATETIME NOT NULL, 
      modified_at DATETIME NOT NULL, 
      created_by VARCHAR, 
      modified_by VARCHAR, 
      PRIMARY KEY (id), 
      FOREIGN KEY(route_id) REFERENCES routes (id)
  );

  -- Index for faster route-based lookups
  CREATE INDEX idx_cost_settings_route_id ON cost_settings (route_id);
  -- Index for version history queries
  CREATE INDEX idx_cost_settings_version ON cost_settings (route_id, version);
  ```

  4. Migration Files:
     - Created `004_add_cost_settings.py` for table creation
     - Updated dependencies to ensure proper migration order
     - Added table drop safety check: `DROP TABLE IF EXISTS cost_settings`

  5. Verification:
     - Successfully created database in `/instance/loadapp.db`
     - Verified table creation and schema
     - Confirmed all indexes are in place
     - Tested foreign key constraints

### Phase 2: Backend API Endpoints
- [x] 2.1. Route Settings Endpoints
  - [x] Implement `RouteSettingsResource` class with:
    ```python
    class RouteSettingsResource(Resource):
        """Resource for managing route cost settings."""
        
        def __init__(self):
            self.logger = get_logger(__name__)

        def get(self, route_id: UUID):
            """Get cost settings for a route."""
            logger = self.logger.bind(
                endpoint="route_settings",
                method="GET",
                remote_ip=request.remote_addr,
                route_id=str(route_id)
            )
            
            try:
                with get_db() as db:
                    route_repository = RouteRepository(db=db)
                    cost_settings_repository = CostSettingsRepository(db=db)
                    cost_settings_service = CostSettingsService(
                        settings_repository=cost_settings_repository,
                        route_repository=route_repository
                    )
                    
                    settings = cost_settings_service.get_settings(route_id)
                    if not settings:
                        return ErrorResponse(
                            error=f"No settings found for route {route_id}",
                            code="NOT_FOUND"
                        ).dict(), 404
                        
                    return {
                        "route_id": str(route_id),
                        "settings": {
                            "fuel_rates": settings.fuel_rates,
                            "toll_rates": settings.toll_rates,
                            "driver_rates": settings.driver_rates,
                            "overhead_rates": settings.overhead_rates,
                            "maintenance_rates": settings.maintenance_rates,
                            "enabled_components": list(settings.enabled_components)
                        },
                        "metadata": {
                            "version": settings.version,
                            "created_at": settings.created_at.isoformat() if settings.created_at else None,
                            "modified_at": settings.modified_at.isoformat() if settings.modified_at else None
                        }
                    }, 200
                    
            except ValueError as e:
                return ErrorResponse(
                    error=str(e),
                    code="NOT_FOUND"
                ).dict(), 404
            
        def post(self, route_id: UUID):
            """Create initial cost settings for a route."""
            logger = self.logger.bind(
                endpoint="route_settings",
                method="POST",
                remote_ip=request.remote_addr,
                route_id=str(route_id)
            )
            
            try:
                data = request.get_json()
                if not data:
                    return ErrorResponse(
                        error="No data provided",
                        code="BAD_REQUEST"
                    ).dict(), 400
                    
                settings = CostSettings(
                    route_id=route_id,
                    fuel_rates=data.get('fuel_rates', {}),
                    toll_rates=data.get('toll_rates', {}),
                    driver_rates=data.get('driver_rates', {}),
                    overhead_rates=data.get('overhead_rates', {}),
                    maintenance_rates=data.get('maintenance_rates', {}),
                    enabled_components=set(data.get('enabled_components', []))
                )
                
                with get_db() as db:
                    route_repository = RouteRepository(db=db)
                    cost_settings_repository = CostSettingsRepository(db=db)
                    cost_settings_service = CostSettingsService(
                        settings_repository=cost_settings_repository,
                        route_repository=route_repository
                    )
                    created = cost_settings_service.create_settings(route_id, settings)
                    
                    return {
                        "route_id": str(route_id),
                        "settings": {
                            "fuel_rates": created.fuel_rates,
                            "toll_rates": created.toll_rates,
                            "driver_rates": created.driver_rates,
                            "overhead_rates": created.overhead_rates,
                            "maintenance_rates": created.maintenance_rates,
                            "enabled_components": list(created.enabled_components)
                        },
                        "metadata": {
                            "version": created.version,
                            "created_at": created.created_at.isoformat() if created.created_at else None,
                            "modified_at": created.modified_at.isoformat() if created.modified_at else None
                        }
                    }, 201
                    
            except (ValueError, KeyError) as e:
                return ErrorResponse(
                    error=str(e),
                    code="BAD_REQUEST"
                ).dict(), 400
            
        def put(self, route_id: UUID):
            """Update existing cost settings for a route."""
            logger = self.logger.bind(
                endpoint="route_settings",
                method="PUT",
                remote_ip=request.remote_addr,
                route_id=str(route_id)
            )
            
            try:
                data = request.get_json()
                if not data:
                    return ErrorResponse(
                        error="No data provided",
                        code="BAD_REQUEST"
                    ).dict(), 400
                    
                settings = CostSettings(
                    route_id=route_id,
                    fuel_rates=data.get('fuel_rates', {}),
                    toll_rates=data.get('toll_rates', {}),
                    driver_rates=data.get('driver_rates', {}),
                    overhead_rates=data.get('overhead_rates', {}),
                    maintenance_rates=data.get('maintenance_rates', {}),
                    enabled_components=set(data.get('enabled_components', []))
                )
                
                with get_db() as db:
                    route_repository = RouteRepository(db=db)
                    cost_settings_repository = CostSettingsRepository(db=db)
                    cost_settings_service = CostSettingsService(
                        settings_repository=cost_settings_repository,
                        route_repository=route_repository
                    )
                    updated = cost_settings_service.update_settings(route_id, settings)
                    
                    return {
                        "route_id": str(route_id),
                        "settings": {
                            "fuel_rates": updated.fuel_rates,
                            "toll_rates": updated.toll_rates,
                            "driver_rates": updated.driver_rates,
                            "overhead_rates": updated.overhead_rates,
                            "maintenance_rates": updated.maintenance_rates,
                            "enabled_components": list(updated.enabled_components)
                        },
                        "metadata": {
                            "version": updated.version,
                            "created_at": updated.created_at.isoformat() if updated.created_at else None,
                            "modified_at": updated.modified_at.isoformat() if updated.modified_at else None
                        }
                    }, 200
                    
            except ValueError as e:
                return ErrorResponse(
                    error=str(e),
                    code="NOT_FOUND" if "not found" in str(e) else "BAD_REQUEST"
                ).dict(), 404 if "not found" in str(e) else 400
    ```

  - [x] Write API tests
    ```python
    def test_route_settings_endpoints(client, route_id):
        """Test route settings endpoints."""
        # Test GET without settings
        response = client.get(f"/api/v1/routes/{route_id}/settings")
        assert response.status_code == 404
        assert response.get_json()["code"] == "NOT_FOUND"

        # Test POST to create settings
        settings_data = {
            "fuel_rates": {
                "DE": "1.50",
                "FR": "1.60"
            },
            "toll_rates": {
                "DE": {
                    "flatbed_truck": "0.20"
                },
                "FR": {
                    "flatbed_truck": "0.25"
                }
            },
            "driver_rates": {
                "DE": "30.00",
                "FR": "35.00"
            },
            "overhead_rates": {
                "DE": "100.00",
                "FR": "120.00"
            },
            "maintenance_rates": {
                "flatbed_truck": "0.15"
            },
            "enabled_components": ["fuel", "toll", "driver"]
        }
        
        response = client.post(
            f"/api/v1/routes/{route_id}/settings",
            json=settings_data
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["route_id"] == str(route_id)
        assert "settings" in data
        assert "metadata" in data
        assert data["settings"]["fuel_rates"] == settings_data["fuel_rates"]
        assert data["settings"]["toll_rates"] == settings_data["toll_rates"]
        assert set(data["settings"]["enabled_components"]) == set(settings_data["enabled_components"])

        # Test GET with settings
        response = client.get(f"/api/v1/routes/{route_id}/settings")
        assert response.status_code == 200
        data = response.get_json()
        assert data["route_id"] == str(route_id)
        assert data["settings"]["fuel_rates"] == settings_data["fuel_rates"]
        assert data["settings"]["toll_rates"] == settings_data["toll_rates"]
        assert set(data["settings"]["enabled_components"]) == set(settings_data["enabled_components"])

        # Test PUT to update settings
        updated_settings = settings_data.copy()
        updated_settings["fuel_rates"]["DE"] = "1.55"
        updated_settings["enabled_components"].append("maintenance")
        
        response = client.put(
            f"/api/v1/routes/{route_id}/settings",
            json=updated_settings
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["settings"]["fuel_rates"]["DE"] == "1.55"
        assert "maintenance" in data["settings"]["enabled_components"]

        # Test non-existent route
        response = client.get("/api/v1/routes/00000000-0000-0000-0000-000000000000/settings")
        assert response.status_code == 404
        assert response.get_json()["code"] == "NOT_FOUND"

        # Test invalid data
        invalid_settings = {
            "fuel_rates": "invalid",  # Should be a dict
            "enabled_components": "invalid"  # Should be a list
        }
        response = client.post(
            f"/api/v1/routes/{route_id}/settings",
            json=invalid_settings
        )
        assert response.status_code == 400
        assert response.get_json()["code"] == "BAD_REQUEST"
    ```

  - [x] Features implemented:
    - Proper error handling with ErrorResponse
    - Structured logging
    - Request validation
    - Comprehensive test coverage
    - Following Flask-RESTful patterns
    - Consistent response formatting

- [x] 2.2. Cost Calculation Endpoints
  - [x] POST `/api/v1/routes/{route_id}/calculate` and GET `/api/v1/routes/{route_id}/costs`
    ```python
    class RouteCalculationResource(Resource):
        """Resource for route cost calculations."""

        def __init__(self):
            self.logger = get_logger(__name__)

        def post(self, route_id: UUID):
            """Calculate costs for a route using current settings."""
            
        def get(self, route_id: UUID):
            """Get previously calculated costs for a route."""
    ```

  - [x] Write API tests
    ```python
    def test_calculate_route_costs(client, route_id):
        """Test calculate route costs endpoint."""
        # Test successful calculation
        # Test route with no costs calculated
    ```

- [ ] 2.3. API Documentation
  - [ ] Update OpenAPI/Swagger docs
    ```yaml
    paths:
      /api/v1/routes/{route_id}/settings:
        get:
          summary: Get route cost settings
          parameters:
            - name: route_id
              in: path
              required: true
              schema:
                type: string
                format: uuid
          responses:
            200:
              description: Success
              content:
                application/json:
                  schema:
                    $ref: '#/components/schemas/CostSettings'
        post:
          summary: Create route cost settings
          requestBody:
            required: true
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/CostSettingsInput'
        put:
          summary: Update route cost settings
          requestBody:
            required: true
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/CostSettingsInput'
    ```

  - [ ] Add example requests/responses
    ```yaml
    components:
      examples:
        CostSettingsExample:
          value:
            fuel_rates:
              DE: 1.8
              PL: 1.5
            toll_rates:
              DE:
                standard: 0.2
              PL:
                standard: 0.15
            enabled_components:
              - fuel
              - toll
              - driver
    ```

  - [ ] Document error cases
    ```yaml
    components:
      responses:
        404NotFound:
          description: Route or settings not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        400BadRequest:
          description: Invalid request data
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ValidationError'
    ```

### Phase 3: Frontend Components
- [ ] 3.1. API Client Updates
  - [ ] Add cost settings methods:
    ```python
    def update_route_cost_settings(self, route_id: str, settings: CostSettings):
        """Save cost settings for a route."""
        
    def calculate_route_costs(self, route_id: str):
        """Trigger cost calculation with current settings."""
    ```
  - [ ] Update cost calculation methods
  - [ ] Add error handling
  - [ ] Write client tests

  Implementation details:
  ```python
  def update_route_cost_settings(self, route_id: str, settings: CostSettings):
      """Save cost settings for a route."""
      return self._make_request(
          'POST',
          f'/api/v1/routes/{route_id}/settings',
          json_data=settings.to_dict()
      )
      
  def calculate_route_costs(self, route_id: str):
      """Trigger cost calculation with current settings."""
      return self._make_request(
          'POST',
          f'/api/v1/routes/{route_id}/calculate'
      )
  ```

- [ ] 3.2. Cost Settings Component
  - [ ] Create CostSettings dataclass:
    ```python
    @dataclass
    class CostSettings:
        route_id: UUID
        fuel_rates: Dict[str, Decimal]
        toll_rates: Dict[str, Dict[str, Decimal]]
        driver_rates: Dict[str, Decimal]
        overhead_rates: Dict[str, Decimal]
        maintenance_rates: Dict[str, Decimal]
        enabled_components: Set[str]
        version: str = "1.0"
    ```
  - [ ] Implement settings form
  - [ ] Add validation
  - [ ] Create submit handler:
    ```python
    def handle_cost_settings_submission(settings: CostSettings):
        if st.session_state.route_id:
            # Save settings
            api_client.update_route_cost_settings(
                st.session_state.route_id, 
                settings
            )
            # Trigger calculation
            costs = api_client.calculate_route_costs(
                st.session_state.route_id
            )
            if costs:
                st.session_state.costs_calculated = True
                display_cost_breakdown(costs)
    ```

  Implementation details:
  ```python
  def render_cost_settings():
      """Render cost settings form."""
      st.subheader("Cost Settings")
      
      # Get default settings if none exist
      if not st.session_state.cost_settings:
          st.session_state.cost_settings = get_default_settings()
          
      settings = st.session_state.cost_settings
      
      # Component toggles
      st.write("Enable/Disable Components")
      cols = st.columns(3)
      with cols[0]:
          settings.is_enabled['fuel'] = st.toggle("Fuel Costs", value=True)
      with cols[1]:
          settings.is_enabled['toll'] = st.toggle("Toll Costs", value=True)
      with cols[2]:
          settings.is_enabled['driver'] = st.toggle("Driver Costs", value=True)
          
      # Rate editors
      if settings.is_enabled['fuel']:
          st.write("Fuel Rates by Country")
          for country in get_route_countries():
              settings.fuel_rates[country] = st.number_input(
                  f"Fuel rate for {country}",
                  value=settings.fuel_rates.get(country, 0.0)
              )
              
      # Similar sections for other cost types...
      
      return settings
  ```

- [ ] 3.3. Cost Display Component
  - [ ] Create EnhancedCostBreakdown:
    ```python
    @dataclass
    class EnhancedCostBreakdown:
        fuel_costs: Dict[str, Decimal]
        toll_costs: Dict[str, Decimal]
        driver_costs: Dict[str, Decimal]
        maintenance_costs: Dict[str, Decimal]
        rest_period_costs: Decimal
        loading_unloading_costs: Decimal
        empty_driving_costs: Dict[str, Dict[str, Decimal]]
        cargo_specific_costs: Dict[str, Decimal]
        overheads: Dict[str, Decimal]
        calculation_method: str
        is_final: bool
    ```
  - [ ] Implement display logic
  - [ ] Add loading states
  - [ ] Handle errors

  Implementation details:
  ```python
  def display_cost_breakdown(costs: EnhancedCostBreakdown):
      """Display detailed cost breakdown."""
      st.subheader("Cost Breakdown")
      
      # Summary metrics
      cols = st.columns(3)
      with cols[0]:
          st.metric("Total Cost", f"€{costs.total_cost:.2f}")
      with cols[1]:
          st.metric("Cost per km", f"€{costs.cost_per_km:.2f}")
      with cols[2]:
          st.metric("Empty Driving Cost", f"€{costs.total_empty_driving_cost:.2f}")
          
      # Detailed breakdown
      with st.expander("View Details"):
          # Fuel costs by country
          if costs.fuel_costs:
              st.write("Fuel Costs")
              for country, amount in costs.fuel_costs.items():
                  st.write(f"{country}: €{amount:.2f}")
                  
          # Similar sections for other cost types...
  ```

### Phase 4: Frontend Integration
- [ ] 4.1. Main App Flow
  - [ ] Update app.py structure:
    ```python
    def main():
        # Form container (always visible)
        with st.container():
            handle_route_form()
            
        # Route visualization (after submission)
        if st.session_state.route_visualized:
            with st.container():
                display_route_details()
                
            # Cost settings (after route visualization)
            with st.container():
                cost_settings = render_cost_settings()
                if st.button("Calculate Costs"):
                    handle_cost_settings_submission(cost_settings)
                    
            # Cost display (after calculation)
            if st.session_state.costs_calculated:
                with st.container():
                    display_cost_breakdown()
                    
                # Offer generation (after costs)
                with st.container():
                    render_offer_controls()
    ```
  - [ ] Add state management:
    ```python
    # Initialize session state
    if 'route_id' not in st.session_state:
        st.session_state.route_id = None
    if 'route_visualized' not in st.session_state:
        st.session_state.route_visualized = False
    if 'cost_settings' not in st.session_state:
        st.session_state.cost_settings = None
    if 'costs_calculated' not in st.session_state:
        st.session_state.costs_calculated = False
    ```
  - [ ] Implement error handling
  - [ ] Write flow tests

### Phase 5: Testing & Documentation
- [ ] 5.1. End-to-End Testing
  - [ ] Write E2E test scenarios
  - [ ] Test full user flows
  - [ ] Performance testing
  - [ ] Load testing

- [ ] 5.2. Documentation
  - [ ] Update API docs
  - [ ] Add user guide
  - [ ] Document test coverage
  - [ ] Add deployment notes

## Dependencies

### Backend
- SQLAlchemy for ORM
- Alembic for migrations
- pytest for testing
- pydantic for validation

### Frontend
- Streamlit components
- pytest for testing
- requests for API calls

## Risk Assessment

### Technical Risks
1. Database migration complexity
   - Mitigation: Thorough testing of upgrade/downgrade scripts
   - Backup strategy for production data

2. Performance impact
   - Mitigation: Index critical fields
   - Monitor query performance
   - Cache frequently accessed data

3. UI State management
   - Mitigation: Clear state transitions
   - Comprehensive error handling
   - User feedback mechanisms

## Success Criteria

1. **Functional**
   - All CRUD operations work for cost settings
   - Cost calculations are accurate
   - UI flow is intuitive
   - Error handling is robust
