# Phase 2: Cost Calculation Integration Checklist

**Version:** 1.0  
**Date:** December 21, 2024  
**Related Documents:**
- gameplan_backend_frontend_integration.md
- System_Architecture.md
- API_Specification.md
- prd20.md

## Progress Summary
- [x] Domain model updates completed
- [x] Frontend components implemented
- [x] API client methods added
- [x] Backend API endpoints implemented
- [ ] Integration testing needed
- [X] Repository implementation needed

## Implementation Checklist

### 1. Backend Implementation

#### API Endpoints
- [x] Implement `/api/routes/<route_id>/costs` endpoint:
  - [x] Set up POST method with proper route validation
  - [x] Integrate with CostCalculationService
  - [x] Add error handling for invalid routes
  - [x] Update to use enhanced CostBreakdown model
- [x] Implement `/api/settings/costs` endpoint:
  - [x] Set up GET method for retrieving current settings
  - [x] Set up PUT method for updating settings
  - [x] Add proper error responses
  - [x] Update to use enhanced CostSettings model
- [x] Implement `/api/settings/transport` endpoint:
  - [x] Set up GET method for retrieving transport settings
  - [x] Set up PUT method for updating transport settings
  - [x] Add proper error responses
  - [x] Update to use enhanced TransportSettings model
- [x] Implement `/api/settings/system` endpoint:
  - [x] Set up GET method for retrieving system settings
  - [x] Set up PUT method for updating system settings
  - [x] Add proper error responses
  - [x] Update to use enhanced SystemSettings model
- [x] Implement `/api/routes/<route_id>/costs/history` endpoint:
  - [x] Set up GET method for retrieving cost history
  - [x] Integrate with CostHistoryService
  - [x] Add error handling for invalid routes
  - [x] Update to use enhanced CostHistory model
- [x] Implement `/api/settings/costs/validate` endpoint:
  - [x] Set up POST method for validating cost settings
  - [x] Integrate with CostValidationService
  - [x] Add error handling for invalid settings
  - [x] Update to use enhanced CostValidation model

#### Cost Calculation Service
- [x] Enhance CostBreakdown implementation:
  - [x] Distance-based components:
    - [x] Fuel costs per country model
    - [x] Toll costs per country model
    - [x] Maintenance costs per country model
    - [x] Implement calculation logic
  - [x] Time-based components:
    - [x] Driver costs per country model
    - [x] Rest period costs model
    - [x] Loading/unloading costs model
    - [x] Implement calculation logic
  - [x] Empty driving components:
    - [x] Additional fuel consumption model
    - [x] Extra toll charges model
    - [x] Driver compensation model
    - [x] Implement calculation logic
  
- [x] Implement cost factors:
  - [x] Country-specific factors:
    - [x] Fuel prices per country model
    - [x] Toll rates per country model
    - [x] Driver rates per country model
    - [x] Implement rate application logic
  - [x] Cargo-specific factors:
    - [x] Weight-based fuel consumption model
    - [x] Special handling requirements model
    - [x] Temperature control costs model
    - [x] Implement factor application logic

#### Domain Model Updates
- [x] Update Route entity:
  - [x] Add support for country-specific segments
  - [x] Add time window constraints
  - [x] Add vehicle specifications
  - [x] Add helper methods for country-specific calculations
  - [x] Add cargo specifications

- [x] Update Cost entity:
  - [x] Align with new CostBreakdown model
  - [x] Add validation rules
  - [x] Add versioning support
  - [x] Add validity period tracking
  - [x] Add calculation method tracking

- [x] Update CostSettings entity:
  - [x] Align with new CostSettings model
  - [x] Add country-specific rates
  - [x] Add cargo-specific factors
  - [x] Add empty driving factors
  - [x] Add helper methods for rate retrieval

- [x] Add supporting entities:
  - [x] TimeWindow for time constraints
  - [x] VehicleSpecification for vehicle details
  - [x] CargoSpecification for cargo details

#### Repository Implementation
- [x] Cost Settings Repository
  - [x] Implement get_current() for active settings
  - [x] Implement update() with version tracking
  - [x] Implement get_cost_history() for route history
  - [x] Implement add_cost_history() for tracking
  - [x] Implement get_transport_settings()
  - [x] Implement update_transport_settings()
  - [x] Implement get_system_settings()
  - [x] Implement update_system_settings()
  - [x] Add entity-model conversion methods
  - [x] Add timezone handling
  - [x] Add decimal precision handling
  - [x] Add metadata support
- [x] Database Schema Updates
  - [x] Add cost_history table
  - [x] Add transport_settings table
  - [x] Add system_settings table
  - [x] Add version tracking columns
  - [x] Add metadata columns
  - [x] Add indexes for performance
  - [x] Add foreign key constraints
  - [x] Add validation constraints

#### Testing
- [x] Unit Tests:
  - [x] Test cost calculation service
    - [x] Distance-based cost calculations
    - [x] Time-based cost calculations
    - [x] Empty driving calculations
    - [x] Cargo-specific cost calculations
    - [x] Country-specific cost calculations
    - [x] Special equipment costs
    - [x] Time window constraints
    - [x] Cost validity periods
  - [x] Test cost settings validation
    - [x] Country-specific rates
    - [x] Cargo factors
    - [x] Empty driving factors
    - [x] Equipment costs
  - [x] Test route cost API endpoints
    - [x] Detailed cost breakdown
    - [x] Cost settings updates
    - [x] Error handling
- [x] Integration Tests:
  - [x] Test cost calculation with route planning
  - [x] Test cost settings persistence
  - [x] Test API response formats
  - [x] Test country-specific calculations
  - [x] Test cargo-specific calculations
- [ ] Integration Tests:
  - [ ] Test API endpoints with repositories
  - [ ] Test settings persistence
  - [ ] Test cost history tracking
  - [ ] Test version control
  - [ ] Test error scenarios

### 2. Frontend Implementation

#### Components
- [x] CostBreakdown component:
  - [x] Implement cost display structure:
    - [x] Distance-based costs section
    - [x] Time-based costs section
    - [x] Empty driving costs section
  - [x] Add country-specific cost breakdown
  - [x] Display empty driving costs separately
  - [x] Show totals and subtotals

- [x] CostSettings component:
  - [x] Form for updating cost factors:
    - [x] Country rates section
    - [x] Time-based rates section
    - [x] Vehicle costs section
    - [x] Empty driving factors section
  - [x] Country-specific settings inputs
  - [x] Validation for numeric inputs
  - [x] Success/error notifications

#### State Management
- [x] Cost Settings State:
  - [x] Add cost settings to global state
  - [x] Implement settings update actions
  - [x] Add persistence layer

- [x] Cost Display State:
  - [x] Add cost breakdown to route state
  - [x] Implement cost update actions
  - [x] Add caching layer

#### Testing
- [x] Component Tests:
  - [x] Test CostBreakdown rendering
  - [x] Test CostSettings form validation
  - [x] Test user interactions

- [x] Integration Tests:
  - [x] Test cost settings updates
  - [x] Test cost display updates
  - [x] Test error handling

### 3. Outstanding Tasks
#### Repository Implementation
- [x] Database Schema
  - [x] Create migration for cost_history table
  - [x] Create migration for transport_settings table
  - [x] Create migration for system_settings table
  - [x] Add indexes for efficient querying

- [x] Repository Methods
  - [x] Implement cost settings CRUD operations
  - [x] Implement transport settings CRUD operations
  - [x] Implement system settings CRUD operations
  - [x] Implement cost history tracking

#### Testing
- [ ] End-to-End Tests
  - [ ] Test complete cost calculation flow
  - [ ] Test settings management flow
  - [ ] Test error scenarios
  - [ ] Performance testing

#### Documentation
- [ ] API Documentation
  - [ ] Cost calculation endpoints
  - [ ] Settings management endpoints
  - [ ] Cost history endpoints
- [ ] User Documentation
  - [ ] Cost calculation guide
  - [ ] Settings configuration guide
  - [ ] Troubleshooting guide

### 4. Next Steps
1. Deploy and validate in staging environment
2. Plan for data migration strategy if needed
3. Consider adding monitoring for cost calculation performance
4. Review and refine documentation

### 5. Notes
- All frontend components and API endpoints are implemented
- Repository implementation is complete
- Need to ensure proper error handling in repositories
- Consider adding caching for frequently accessed settings
- Plan for data migration strategy if needed
- Consider adding monitoring for cost calculation performance

## Success Criteria
1. All cost calculations are accurate and match business rules
2. Settings changes are persisted correctly
3. Cost history is tracked and retrievable
4. API endpoints handle errors gracefully
5. Frontend displays all cost components clearly
6. Performance meets requirements (< 500ms for calculations)
7. All tests pass with >80% coverage
