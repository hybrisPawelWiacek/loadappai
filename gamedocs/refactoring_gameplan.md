# LoadApp.AI Refactoring Gameplan

## Overview
This document outlines the step-by-step plan for refactoring the LoadApp.AI codebase to improve maintainability, readability, and testability.

### Key Implementation Principles

1. **Code Preservation**
   - Existing functionality must be preserved
   - Any modifications to existing code require explicit permission
   - Changes must be backward compatible
   - Each refactoring step must be atomic and reversible

2. **API & Integration Integrity**
   - Maintain compatibility with current API endpoints
   - Ensure frontend API client continues to function correctly
   - Follow established API patterns and conventions
   - No changes to API contracts or responses

3. **Domain Model Stability**
   - Preserve existing domain entities and services functionality
   - Follow established domain patterns
   - Maintain clean architecture principles
   - Keep domain logic unchanged during restructuring

4. **Infrastructure Reliability**
   - Ensure database schema changes don't impact existing data
   - Maintain current infrastructure performance
   - Follow established patterns for infrastructure
   - Keep database migrations reversible

5. **Development Best Practices**
   - Use Python virtual environment
   - Maintain updated requirements.txt
   - Follow port usage guidelines (Backend: 5001, Frontend: 8501)
   - Include comprehensive testing
   - Document all changes
   - Keep commit history clean and atomic

### Success Criteria
- [ ] All tests passing
- [ ] No functionality changes
- [ ] Improved code organization
- [ ] Better maintainability
- [ ] Clearer dependencies
- [ ] Updated documentation

### Timeline
- Phase 0: 1-2 days
- Phase 1: 6-9 days
- Phase 2: 3-5 days
- Phase 3: 2-3 days
Total: 12-19 days

### Key Risks and Mitigations
1. Breaking existing functionality
   - [ ] Maintain comprehensive test coverage
   - [ ] Implement gradual rollout by component
   - [ ] Keep git branches for each phase
   - [ ] Create backup of current working state

2. Complex dependency management
   - [ ] Enforce clear separation of concerns
   - [ ] Implement careful import management
   - [ ] Document all changes in commit messages

3. Test coverage gaps
   - [ ] Add tests before refactoring
   - [ ] Maintain coverage metrics (>60%)
   - [ ] Add integration tests for new module interactions
   - [ ] Update test fixtures and mocks

## Current State
Large files that need refactoring:
1. src/api/app.py (82.8 KB)
2. src/domain/services.py (47.6 KB)
3. src/domain/entities.py (24.3 KB)
4. src/api/models.py (20.3 KB)
5. src/domain/value_objects.py (11.8 KB)

Current Issues:
1. Outdated and unused setup.py file
2. Inconsistent configuration management
3. Redundant imports of unused config module
4. Outdated setup.py with no corresponding requirements.txt
5. Missing dependency management files

### Git Workflow
- Main branch: main
- Feature branches:
  - [ ] refactor/value-objects
  - [ ] refactor/entities
  - [ ] refactor/services
  - [ ] refactor/api
  - [ ] refactor/models

### Commit Message Format
```
refactor(scope): description

- Detailed changes
- Migration steps
- Breaking changes
```

## Target Architecture

### 1. Value Objects (`src/domain/value_objects/`)
- [ ] Directory Structure:
  ```bash
  mkdir -p src/domain/value_objects
  touch src/domain/value_objects/__init__.py
  touch src/domain/value_objects/location.py
  touch src/domain/value_objects/cost.py
  touch src/domain/value_objects/route.py
  touch src/domain/value_objects/offer.py
  ```
- [ ] Location-related value objects:
  - Location
  - CountrySegment
  - RouteSegment
  - DistanceMatrix
- [ ] Cost-related value objects:
  - Cost
  - CostBreakdown
  - Currency
- [ ] Route-related value objects:
  - RouteMetadata
  - EmptyDriving
  - RouteOptimizationResult
- [ ] Offer-related value objects:
  - OfferGenerationResult

### 2. Entities (`src/domain/entities/`)
- [ ] Directory Structure:
  ```bash
  mkdir -p src/domain/entities
  touch src/domain/entities/__init__.py
  touch src/domain/entities/route.py
  touch src/domain/entities/cost.py
  touch src/domain/entities/cargo.py
  touch src/domain/entities/offer.py
  touch src/domain/entities/vehicle.py
  ```
- [ ] Route and transport entities:
  - Route
  - TransportType
- [ ] Cost and settings entities:
  - Cost
  - CostSettings
  - CostComponent
- [ ] Cargo-related entities:
  - Cargo
  - CargoSpecification
- [ ] Offer-related entities:
  - Offer
  - OfferHistory
- [ ] Vehicle-related entities:
  - VehicleSpecification

### 3. Services (`src/domain/services/`)
- [ ] Directory Structure:
  ```bash
  mkdir -p src/domain/services
  touch src/domain/services/__init__.py
  touch src/domain/services/route_planning.py
  touch src/domain/services/cost_calculation.py
  touch src/domain/services/offer_generation.py
  touch src/domain/services/settings.py
  ```
- [ ] Route planning service
- [ ] Cost calculation service
- [ ] Offer generation service
- [ ] Settings service

### 4. Interfaces (`src/domain/interfaces/`)
- [ ] Location service interface
- [ ] AI service interface
- [ ] Repository interfaces
- [ ] Toll rate service interface

### 5. API Endpoints (`src/api/blueprints/`)
- [ ] Route-related endpoints
- [ ] Cost calculation endpoints
- [ ] Offer generation endpoints
- [ ] Settings management endpoints

### 6. Database Models (`src/api/models/`)
- [ ] Route and transport models
- [ ] Cost and settings models
- [ ] Cargo models
- [ ] Offer models
- [ ] Vehicle models

## Implementation Plan

### Phase 0: Configuration and Dependencies Cleanup (1-2 days)

#### Step 0.1: Dependencies and Testing Setup
- [X] 1. Remove outdated setup.py (keep run.py as it's actively used in start_backend.sh)
- [X] 2. Update requirements.txt with any missing dependencies:
   - [X] Add flask-swagger-ui==4.11.1
   - [X] Add crewai enterprise package (if needed)
- [X] 3. Verify all versions in requirements.txt and requirements-dev.txt are up to date
- [X] 4. Keep pytest.ini for test organization:
   - [X] Maintains test markers (unit, integration, api, frontend)
   - [X] Configures test discovery patterns
   - [X] Sets test output format
- [X] 5. Clean up test configuration:
   - [X] Remove redundant root conftest.py (only adds project root to path)
   - [X] Keep tests/conftest.py as main fixture source (core test fixtures)
   - [X] Keep specialized conftest.py files in tests/api and tests/infrastructure
   - [X] Ensure PYTHONPATH is set correctly in pytest.ini
- [X] 6. Keep database-related files:
   - [X] alembic.ini for migration configuration
   - [X] /migrations/ directory with active migrations (001, 002, 004)
   - [X] /instance/ directory for SQLite database
   - [X] Add both directories to .gitignore (except migrations/*.py)
- [X] 7. Maintain pyproject.toml for tool configuration:
   - [X] Black settings (line length, Python version)
   - [X] isort settings (profile, multi-line output)
   - [X] mypy settings (type checking strictness)
   - [X] pytest settings (coverage, test paths)
- [X] 8. Clean up scripts directory:
   - [X] Remove scripts/seed_db.py (functionality exists in src/infrastructure/seed_data.py)
   - [X] Keep and document API test scripts:
     - [X] scripts/test_gmaps.py (Google Maps API testing)
     - [X] scripts/test_openai.py (OpenAI API testing)
   - [X] Add script usage to README.md
   - [X] Consider moving API test scripts to tests/manual/

#### Step 0.2: Configuration Audit
- [X] 1. Review all .env usage across the codebase
- [X] 2. Document current environment variables in use:
   - Database: DATABASE_URL, SQL_ECHO
   - API Keys: GOOGLE_MAPS_API_KEY, OPENAI_API_KEY
   - Environment: ENV
   - OpenAI: OPENAI_MODEL, OPENAI_MAX_RETRIES, OPENAI_RETRY_DELAY
   - Google Maps: GMAPS_MAX_RETRIES, GMAPS_RETRY_DELAY, GMAPS_CACHE_TTL
   - CrewAI: CREWAI_BASE_URL, CREWAI_BEARER_TOKEN
   - Feature Flags: WEATHER_ENABLED, TRAFFIC_ENABLED, MARKET_DATA_ENABLED
   - Server: BACKEND_HOST
- [X] 3. Verify all settings are properly sourced from .env:
   - [X] Fixed database.py to use settings instead of direct os.getenv
   - [X] All other settings properly use pydantic_settings
- [X] 4. Identify any hardcoded configuration values:
   - [X] Found and fixed hardcoded database URL in database.py
   - [X] No other hardcoded values found
- [X] 5. Document all environment variables in template.env:
   - [X] Added all variables from Settings class
   - [X] Added descriptions and default values
   - [X] Organized by category (Database, Server, API Keys, etc.)
- [X] 6. Identify hardcoded configuration values:
   - [X] Found and fixed hardcoded database URL in database.py
   - [X] No other hardcoded values found
- [X] 7. Ensure all services use PORT=5001 (not 5000):
   - [X] run.py uses port 5001
   - [X] Fixed test settings to use port 5001
   - [X] No other port 5000 usage found
- [X] 8. Verify .gitignore settings:
   - [X] Ensure instance/ is ignored (except .gitkeep)
   - [X] Ensure migrations/__pycache__ is ignored
   - [X] Keep migrations/*.py in version control
   - [X] Add standard Python ignores (*.pyc, __pycache__, etc.)
   - [X] Add IDE ignores (.vscode/, .idea/)
   - [X] Add environment file ignores (.env, .env.local)

#### Step 0.3: Update and Rename Config
- [X] 1. Create backup of src/config.py
- [X] 2. Rename src/config.py to src/settings.py for better clarity
- [X] 3. Update settings with correct values:
   - [X] Change BACKEND_URL port to 5001
   - [X] Update OPENAI_MODEL to "gpt-4o-mini"
   - [X] Add explicit PORT setting
- [X] 4. Update imports in:
   - [X] src/infrastructure/services/google_maps_service.py
   - [X] src/infrastructure/services/openai_service.py
   - [X] src/frontend/components/map_visualization.py
   - [X] src/api/app.py
   - [X] run.py
- [X] 5. Update any tests that reference config.py

#### Step 0.4: Update Environment Configuration
- [X] 1. Remove redundant .env.example (template.env is our source of truth)
- [X] 2. Update template.env with all required variables
- [X] 3. Document environment configuration in README.md
- [X] 4. Add validation for required environment variables

#### Step 0.5: Infrastructure Layer Review

- [X] 1. Essential Files Review:
   - Core:
     - [X] database.py - Database connection and session management
     - [X] models.py - SQLAlchemy models
     - [X] logging.py - Logging configuration
     - [X] utils.py - Shared utilities
   
   - Repositories:
     - [X] repositories/base.py - Base repository class
     - [X] repositories/cost_repository.py - Cost tracking
     - [X] repositories/cost_settings_repository.py - Cost settings
     - [X] repositories/offer_repository.py - Offer management
     - [X] repositories/route_repository.py - Route handling
   
   - Services:
     - [X] services/google_maps_service.py - Maps integration
     - [X] services/openai_service.py - AI integration
     - [X] services/toll_rate_service.py - Toll calculations

- [X] 2. Files to Move/Update:
   - [X] Move seed_data.py to tests/fixtures/
   - [X] Move mock_location_service.py to tests/mocks/
   - [X] Remove config.py (after Step 0.3)

- [X] 3. Review Points:
   - [X] Verify all __init__.py files export correct symbols
   - [X] Check for any circular dependencies
   - [X] Ensure consistent error handling
   - [X] Verify logging usage
   - [X] Check SQLAlchemy session management
   - [X] Review API service error handling
   - [X] Validate repository pattern consistency

### Phase 1: Domain Layer Refactoring

#### Step 1: Value Objects (1-2 days)
- [X] 1. Create value_objects directory structure
- [X] 2. Move and split value objects into respective files:
   - [X] location.py - Geography-related value objects
   - [X] cost.py - Cost-related value objects
   - [X] route.py - Route-related value objects
   - [X] offer.py - Offer-related value objects
- [X] 3. Update imports and dependencies
- [X] 4. Add/update tests for value objects
- [ ] 5. Verify all tests pass

#### Step 2: Entities (2-3 days)
- [X] 1. Create entities directory structure
- [X] 2. Move and split entities into respective files:
   - [X] route.py - Route and transport entities
   - [X] cost.py - Cost and settings entities
   - [X] cargo.py - Cargo-related entities
   - [X] offer.py - Offer-related entities
   - [X] vehicle.py - Vehicle-related entities
- [X] 3. Update imports and dependencies
- [X] 4. Add/update tests for entities
- [ ] 5. Verify all tests pass

#### Step 2.5: Interfaces (1-2 days)
- [X] 1. Move all interfaces from interfaces.py to interfaces/ directory
- [X] 2. Split into domain-specific files:
   - [X] route_service.py - Route planning and location services
   - [X] cost_service.py - Cost calculation services
   - [X] offer_service.py - Offer generation and management
   - [X] settings_service.py - Settings management
   - [X] ai_service.py - AI integration services
   - [X] repositories/
     - [X] route_repository.py - Route data access
     - [X] cost_repository.py - Cost data access
     - [X] offer_repository.py - Offer data access
     - [X] settings_repository.py - Settings data access
- [X] 3. Update imports and dependencies
- [X] 4. Add interface documentation
- [ ] 5. Add interface tests
- [ ] 6. Verify all tests pass

#### Step 3: Services (3-4 days)
- [X] 1. Create services directory structure
- [X] 2. Move and split services into respective files:
   - [X] route_planning.py - Route planning service
   - [X] cost_calculation.py - Cost calculation service
   - [X] offer_generation.py - Offer generation service
   - [X] settings.py - Settings service
- [X] 3. Update imports and dependencies
- [X] 4. Add/update tests for services
- [ ] 5. Verify all tests pass

### Phase 2: API Layer Refactoring

#### Step 4: API Blueprints (2-3 days)
- [X] 1. Create blueprints directory structure
- [X] 2. Split app.py into blueprint modules:
   - [X] routes.py - Route-related endpoints
   - [X] costs.py - Cost calculation endpoints
   - [X] offers.py - Offer generation endpoints
   - [X] settings.py - Settings management endpoints
- [X] 3. Update imports and dependencies
- [X] 4. Add/update tests for API endpoints
- [ ] 5. Verify all tests pass

#### Step 5: API Models (1-2 days)
- [X] 1. Create models directory structure
- [X] 2. Split models.py into domain-specific files:
   - [X] route.py - Route and transport models
   - [X] cost.py - Cost and settings models
   - [X] cargo.py - Cargo models
   - [X] offer.py - Offer models
   - [X] vehicle.py - Vehicle models
- [X] 3. Update imports and dependencies
- [X] 4. Add/update tests for models
- [ ] 5. Verify all tests pass

### Phase 3: Integration and Testing

#### Step 6: Integration (2-3 days)
- [ ] 1. Update main application configuration
- [ ] 2. Verify all components work together:
   - [ ] Route planning flow
   - [ ] Cost calculation flow
   - [ ] Offer generation flow
   - [ ] Settings management flow
- [ ] 3. Run full test suite
- [ ] 4. Fix any integration issues
- [ ] 5. Performance testing:
   - [ ] Route calculation latency
   - [ ] Cost calculation performance
   - [ ] Database query optimization
   - [ ] API response times

#### Step 7: Documentation and Cleanup
- [ ] 1. Update API documentation
- [ ] 2. Update README files
- [ ] 3. Review and clean up TODOs
- [ ] 4. Update development guides
- [ ] 5. Final code review and cleanup

## Testing Strategy
1. Create unit tests for each new module
2. Maintain existing test coverage (>60%)
3. Add integration tests for new module interactions
4. Update test fixtures and mocks
5. Document test scenarios
6. Verify environment variable loading
7. Test fallback to default values
8. Validate error handling for missing required variables
9. Add environment configuration to test fixtures

## Rollback Plan
1. Maintain git branches for each phase
2. Create backup of current working state
3. Document all changes in commit messages
4. Keep old files until new structure is verified
5. Plan for quick rollback if needed

## Success Criteria
1. All tests passing
2. No functionality changes
3. Improved code organization
4. Better maintainability
5. Clearer dependencies
6. Updated documentation

## Timeline
- Phase 0: 1-2 days
- Phase 1: 6-9 days
- Phase 2: 3-5 days
- Phase 3: 2-3 days
Total: 12-19 days

## Risks and Mitigations
1. Risk: Breaking existing functionality
   - Mitigation: Comprehensive test coverage
   - Mitigation: Gradual rollout by component

2. Risk: Complex dependency management
   - Mitigation: Clear separation of concerns
   - Mitigation: Careful import management

3. Risk: Timeline delays
   - Mitigation: Prioritize critical components
   - Mitigation: Regular progress tracking

4. Risk: Test coverage gaps
   - Mitigation: Add tests before refactoring
   - Mitigation: Maintain coverage metrics

5. Risk: Breaking environment configuration
   - Mitigation: Comprehensive environment variable documentation
   - Mitigation: Validation of all required variables on startup
   - Mitigation: Clear error messages for missing configuration

## Next Steps
1. Review and approve refactoring plan
2. Execute Configuration and Dependencies Cleanup (Phase 0)
3. Create new branch for refactoring
4. Begin with value objects refactoring
5. Schedule daily progress reviews
6. Update team on changes

## Implementation Details

### Phase 1: Value Objects

#### Step 1.1: Create Directory Structure
```bash
mkdir -p src/domain/value_objects
touch src/domain/value_objects/__init__.py
touch src/domain/value_objects/location.py
touch src/domain/value_objects/cost.py
touch src/domain/value_objects/route.py
touch src/domain/value_objects/offer.py
```

#### Step 1.2: Move Location-Related Objects
1. Move from value_objects.py to location.py:
   - Location
   - CountrySegment
   - RouteSegment
   - DistanceMatrix

2. Update imports and dependencies:
```python
# src/domain/value_objects/location.py
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Optional, List
from pydantic import BaseModel, Field, confloat
```

#### Step 1.3: Move Cost-Related Objects
1. Move from value_objects.py to cost.py:
   - Cost
   - CostBreakdown
   - Currency

#### Step 1.4: Move Route-Related Objects
1. Move from value_objects.py to route.py:
   - RouteMetadata
   - EmptyDriving
   - RouteOptimizationResult

#### Step 1.5: Move Offer-Related Objects
1. Move from value_objects.py to offer.py:
   - OfferGenerationResult

### Phase 2: Entities

#### Step 2.1: Create Directory Structure
```bash
mkdir -p src/domain/entities
touch src/domain/entities/__init__.py
touch src/domain/entities/route.py
touch src/domain/entities/cost.py
touch src/domain/entities/cargo.py
touch src/domain/entities/offer.py
touch src/domain/entities/vehicle.py
```

#### Step 2.2: Move Route Entities
1. Move from entities.py to route.py:
   - Route
   - TransportType

#### Step 2.3: Move Cost Entities
1. Move from entities.py to cost.py:
   - Cost
   - CostSettings
   - CostComponent

### Phase 3: Services

#### Step 3.1: Create Directory Structure
```bash
mkdir -p src/domain/services
touch src/domain/services/__init__.py
touch src/domain/services/route_planning.py
touch src/domain/services/cost_calculation.py
touch src/domain/services/offer_generation.py
touch src/domain/services/settings.py
```

#### Step 3.2: Move Route Planning Service
1. Move from services.py to route_planning.py:
   - RoutePlanningService
   - Related helper methods

#### Step 3.3: Move Cost Calculation Service
1. Move from services.py to cost_calculation.py:
   - CostCalculationService
   - Related helper methods

## Git Workflow

### Branch Strategy
1. Main branch: main
2. Feature branches:
   - [ ] refactor/value-objects
   - [ ] refactor/entities
   - [ ] refactor/services
   - [ ] refactor/api
   - [ ] refactor/models

### Commit Message Format
```
refactor(scope): description

- Detailed changes
- Migration steps
- Breaking changes
```

Example:
```
refactor(value-objects): split location-related objects

- Created value_objects/location.py
- Moved Location, CountrySegment classes
- Updated imports in dependent files
```

## Progress Tracking

### Daily Checklist
1. Morning:
   - Review previous day's changes
   - Run test suite
   - Plan day's refactoring tasks

2. Evening:
   - Commit changes
   - Document progress
   - Update test coverage report

### Weekly Review
1. Review completed components
2. Update timeline if needed
3. Address any blockers
4. Plan next week's tasks

## Documentation Updates

### Required Updates
1. Update module docstrings
2. Update import paths
3. Update API documentation
4. Update test documentation
5. Update README.md with new structure

## Remaining Considerations

### Testing Focus
- [ ] Document test scenarios
- [ ] Verify environment variable loading
- [ ] Test fallback to default values
- [ ] Validate error handling for missing required variables
- [ ] Add environment configuration to test fixtures

### Progress Tracking
- [ ] Schedule daily progress reviews
- [ ] Update team on changes
- [ ] Run test suite daily
- [ ] Update test coverage report weekly
- [ ] Address blockers promptly
