# LoadApp.AI System Architecture

## 1. Overview

### System Purpose
LoadApp.AI is a proof-of-concept application designed to optimize logistics operations by providing intelligent route planning and cost calculation for transportation services. The system focuses on empty driving optimization and dynamic offer generation for logistics providers.

### Core Functionality
- Route Planning: Advanced route calculation with empty driving optimization
- Cost Calculation: Dynamic cost computation based on multiple parameters
- Offer Generation: Automated creation of transportation offers
- Settings Management: Flexible configuration of cost parameters and business rules

### Key User Flows
1. Route Planning Flow
   - Input pickup and delivery locations
   - Calculate optimal routes with empty driving consideration
   - Visualize route options on map interface

2. Cost Calculation Flow
   - Apply business rules and parameters
   - Calculate transportation costs
   - Factor in empty driving costs
   - Consider variable cost components

3. Offer Generation Flow
   - Combine route and cost calculations
   - Generate comprehensive transportation offers
   - Present offer details and breakdowns

### Technical Stack Summary
- Backend:
  - Python 3.11+
  - Flask (Port 5001)
  - SQLAlchemy ORM
  - SQLite Database
  
- Frontend:
  - Streamlit (Port 8501)
  - Streamlit Components
  - Map Visualization Libraries

- External Services:
  - Geocoding APIs
  - Route Optimization Services
  - Map Services Integration

## 2. High-Level Architecture

### System Components Diagram

                                +----------------+
                                |    User/UI     |
                                | (Streamlit App)|
                                +--------+-------+
                                         |
                                         | HTTP/REST
                                         |
                                +--------+-------+
                                |  Flask Backend |
                                +----------------+
                                |
                +---------------+---------------+
                |               |               |
        +-------+-----+ +-------+-----+ +-------+-----+
        |   Domain    | |  Application | |Infrastructure|
        |   Layer     | |    Layer     | |    Layer    |
        +-------------+ +-------------+ +-------------+
                |               |               |
                +---------------+---------------+
                                |
                                v
                        +---------------+
                        |    SQLite     |
                        |   Database    |
                        +---------------+

### Current Project Structure

The LoadApp.AI codebase follows a clean architecture pattern with clear separation of concerns. The structure is organized to support comprehensive testing at all layers:

```
loadapp3/                # Root directory
├── alembic.ini         # Database migration configuration
├── pyproject.toml      # Project metadata and build settings
├── pytest.ini          # Test configuration
├── requirements.txt    # Production dependencies
├── requirements-dev.txt # Development dependencies
├── run.py             # Application entry point
├── start_backend.sh   # Backend startup script
├── start_frontend.sh  # Frontend startup script
├── template.env       # Environment template
└── src/
    ├── settings.py    # Global application settings
    ├── api/          # API Layer
    │   ├── blueprints/
    │   │   ├── routes/
    │   │   │   └── routes.py
    │   │   ├── costs/
    │   │   │   └── costs.py
    │   │   ├── offers/
    │   │   │   └── offers.py
    │   │   └── settings/
    │   │       └── settings.py
    │   ├── models/
    │   │   ├── base.py
    │   │   ├── cargo.py
    │   │   ├── cost.py
    │   │   ├── offer.py
    │   │   ├── route.py
    │   │   └── settings.py
    │   └── app.py
    ├── domain/
    │   ├── entities/
    │   │   ├── cargo.py
    │   │   ├── cost.py
    │   │   ├── driver.py      # Driver entity definition
    │   │   ├── offer.py
    │   │   ├── route.py
    │   │   ├── transport.py   # Transport entity definition
    │   │   └── vehicle.py
    │   ├── interfaces/        # Abstract interfaces
    │   │   ├── repositories/  # Repository interfaces
    │   │   └── services/     # Service interfaces
    │   ├── services/
    │   │   ├── ai/
    │   │   │   └── ai_integration.py
    │   │   ├── common/
    │   │   │   ├── base.py
    │   │   │   ├── cache.py
    │   │   │   ├── error_handling.py
    │   │   │   └── monitoring.py
    │   │   ├── cost/
    │   │   │   ├── cost_calculation.py
    │   │   │   ├── cost_settings.py
    │   │   │   └── toll_rates.py
    │   │   ├── location/
    │   │   │   └── location_service.py
    │   │   ├── offer/
    │   │   │   ├── history.py
    │   │   │   ├── offer_generation.py
    │   │   │   └── pricing.py
    │   │   └── route/
    │   │       └── route_planning.py
    │   ├── value_objects/
    │   │   ├── ai.py
    │   │   ├── common.py
    │   │   ├── cost.py
    │   │   ├── cost_component.py  # Cost component value objects
    │   │   ├── country_segment.py # Country segment definitions
    │   │   ├── location.py
    │   │   ├── offer.py
    │   │   ├── pricing.py
    │   │   └── route.py
    │   ├── models/
    │   │   └── settings.py
    │   └── responses/
    │       └── settings.py
    ├── infrastructure/
    │   ├── config.py
    │   ├── database.py
    │   ├── logging.py
    │   ├── models.py
    │   ├── repositories/
    │   │   ├── base.py
    │   │   ├── cost_repository.py
    │   │   ├── cost_settings_repository.py
    │   │   ├── driver_repository.py
    │   │   ├── offer_repository.py
    │   │   ├── route_repository.py
    │   │   └── vehicle_repository.py
    │   ├── services/
    │   │   ├── google_maps_service.py  # Google Maps integration
    │   │   ├── openai_service.py      # OpenAI integration
    │   │   └── toll_rate_service.py
    │   └── utils.py
    └── frontend/
        ├── api_client.py
        ├── app.py
        ├── components/
        │   ├── cost_calculation.py
        │   ├── map_visualization.py
        │   ├── offer_form.py
        │   ├── offer_generation.py
        │   ├── offer_history.py
        │   ├── route_form.py
        │   └── settings_management.py
        ├── pages/
        │   └── offer_management.py
        └── state/
            ├── hooks.py
            └── offer_state.py

tests/                  # Test Suite
├── api/               # API tests
├── domain/
│   ├── entities/
│   ├── services/
│   └── value_objects/
├── infrastructure/
│   ├── repositories/
│   └── services/
│       ├── test_google_maps_service.py
│       └── test_openai_service.py
└── frontend/
    └── components/
```

Each component in this structure is designed to be independently testable, with clear boundaries and dependencies. The test coverage targets are:
- Critical Components (Core Infrastructure, Domain Model): 90%+
- Business Logic (Domain Services): 85%+
- Infrastructure Components: 80%+
- API Endpoints: 75%+

### Domain Layer Components

1. **Entities**
   - Core business objects with identity and lifecycle
   - Includes: Route, Cost, Offer, Cargo, Vehicle, Transport entities
   - Transport entity manages vehicle types, equipment, and cargo configurations
   - Implements business rules and validation logic

2. **Settings**
   - Business configuration and rules
   - Includes:
     - CostSettings: Cost calculation parameters and rates (persisted)
     - TransportSettings: Vehicle and cargo configuration (configuration-based)
     - SystemSettings: Global business rules and parameters (persisted)
   - Note: TransportSettings is handled as configuration rather than persisted entity for PoC

3. **Value Objects**
   - Immutable objects representing domain concepts
   - Includes location, cost components, pricing rules
   - Ensures data integrity and validation
   
### Key Components

#### Domain Layer
The domain layer contains the core business logic and rules of the application:

1. **Entities**
   - Core business objects with identity and lifecycle
   - Includes: Route, Cost, Offer, Cargo, Vehicle, Transport entities
   - Implements business rules and validation logic

2. **Value Objects**
   - Immutable objects representing domain concepts
   - Location, Cost Components, Pricing, Route Segments
   - Implements validation and calculation logic

3. **Domain Services**
   - Route Planning: Route optimization and validation
   - Cost Calculation: Toll rates, fuel costs, driver costs
   - Offer Generation: Pricing strategies and offer management
   - Location Services: Geocoding and location validation
   - AI Integration: AI-powered route and cost optimization
   - Common Services: Monitoring, caching, error handling

4. **Domain Models & Responses**
   - Domain-specific data structures
   - API response objects and DTOs
   - Settings and configuration models

#### Infrastructure Layer
Handles technical concerns and external integrations:

1. **Repositories**
   - Data access patterns for each domain entity
   - Implements CRUD operations and queries
   - Manages data persistence and retrieval

2. **Services**
   - External service integrations (e.g., toll rate services)
   - Technical service implementations

3. **Core Infrastructure**
   - Database configuration and management
   - Logging and monitoring setup
   - Configuration management
   - Utility functions and helpers

#### API Layer
RESTful API implementation using Flask:

1. **Blueprints**
   - Route Planning endpoints
   - Cost Calculation endpoints
   - Offer Generation endpoints
   - Settings Management endpoints

2. **API Models**
   - Request/Response data models
   - Input validation
   - Data transformation

#### Frontend Layer
Streamlit-based user interface:

## 4. Frontend Architecture

### Streamlit Application Structure

1. **Main Application (`app.py`)**
   - Application initialization
   - Page routing and navigation
   - Global state management
   - Error handling and logging

2. **Components**
   - **Route Form**
     - Location input and validation
     - Timeline management
     - Route visualization
     - Empty driving optimization

   - **Cost Calculation**
     - Cost component breakdown
     - Dynamic pricing updates
     - Currency handling
     - Business rule application

   - **Offer Generation**
     - Offer creation workflow
     - Template selection
     - Price customization
     - Document generation

   - **Map Visualization**
     - Interactive route display
     - Waypoint management
     - Distance calculations
     - Geographic data visualization

   - **Settings Management**
     - Cost parameter configuration
     - Business rule management
     - User preferences
     - System settings

   - **Offer History**
     - Historical offer viewing
     - Version comparison
     - Status tracking
     - Filter and search

3. **State Management**
   - **Offer State**
     - Current offer data
     - Offer history
     - Version tracking
     - Status management

   - **Custom Hooks**
     - State synchronization
     - Data persistence
     - Event handling
     - Cache management

4. **API Client**
   - REST API integration
   - Request/response handling
   - Error management
   - Data transformation

### User Interface Design

1. **Layout Organization**
   - Responsive grid system
   - Component hierarchy
   - Navigation structure
   - Modal dialogs

2. **Interactive Features**
   - Real-time updates
   - Form validation
   - Progress indicators
   - Error messages

3. **Data Visualization**
   - Cost breakdowns
   - Route maps
   - Timeline charts
   - Statistics displays

### Performance Optimizations

1. **State Management**
   - Efficient state updates
   - Caching strategies
   - Lazy loading
   - Data prefetching

2. **UI Responsiveness**
   - Component optimization
   - Event debouncing
   - Async operations
   - Resource loading

3. **Data Handling**
   - Batch processing
   - Pagination
   - Data compression
   - Local storage

### Error Handling

1. **User Feedback**
   - Error messages
   - Loading states
   - Success notifications
   - Warning alerts

2. **Error Recovery**
   - Form data persistence
   - Auto-save functionality
   - Session recovery
   - Offline support

3. **Logging**
   - Error tracking
   - Usage analytics
   - Performance monitoring
   - Debug information

### Component Interaction Flow

1. **Frontend → Backend Communication**
   - Frontend components use `api_client.py` to make HTTP requests
   - Requests are handled by Flask blueprints in the API layer
   - API models validate and transform request data

2. **API Layer Processing**
   - Blueprints route requests to appropriate domain services
   - Input validation using API models
   - Error handling and response formatting
   - Authentication and authorization checks

3. **Domain Layer Processing**
   - Domain services implement core business logic
   - Value objects ensure data integrity and validation
   - Domain entities maintain business rules
   - Common services provide cross-cutting concerns:
     - Monitoring and metrics
     - Caching for performance
     - Error handling and logging

4. **Infrastructure Layer Integration**
   - Repositories handle data persistence
   - External services integration (toll rates, geocoding)
   - Configuration and environment management
   - Logging and monitoring infrastructure

5. **Data Flow**
   ```
   Frontend (Streamlit)
        ↓
   API Client
        ↓
   API Layer (Flask Blueprints)
        ↓
   Domain Services
        ↓
   Infrastructure Layer
        ↓
   External Services/Database
   ```

### Development Workflow

1. **Local Development**
   - Backend (Flask) runs on port 5001
   - Frontend (Streamlit) runs on port 8501
   - SQLite database for local development
   - Environment variables in `.env` file

2. **Testing Strategy**
   - Unit tests for domain logic
   - Integration tests for API endpoints
   - Repository tests with test database
   - Frontend component testing

3. **Deployment Considerations**
   - Environment-specific configurations
   - Database migration management
   - Service dependencies (external APIs)
   - Monitoring and logging setup

## 3. Backend Architecture

### API Layer (Flask)

1. **Blueprint Organization**
   - `routes`: Route planning and optimization endpoints
   - `costs`: Cost calculation and toll rate endpoints
   - `offers`: Offer generation and management endpoints
   - `settings`: Application configuration endpoints

2. **API Models**
   - Base models with shared functionality
   - Entity-specific models (Route, Cost, Offer)
   - Input validation and transformation
   - Response formatting

### Domain Layer

1. **Core Services**
   - **Route Planning**
     - Route optimization and validation
     - Location geocoding and validation
     - Empty driving calculations
   
   - **Cost Calculation**
     - Toll rate calculations
     - Cost settings management
     - Dynamic pricing rules
   
   - **Offer Generation**
     - Pricing strategy implementation
     - Offer history management
     - AI-powered optimizations

   - **Location Services**
     - Geocoding and address validation
     - Distance calculations
     - Map data integration

2. **Common Services**
   - Monitoring and metrics collection
   - Caching and performance optimization
   - Error handling and logging
   - Base service functionality

3. **Value Objects**
   - Location and coordinates
   - Cost components and pricing
   - Route segments and waypoints
   - AI-related data structures

4. **Domain Entities**
   - Route: Transport route definition
   - Cost: Cost calculation models
   - Offer: Transport offer details
   - Vehicle: Vehicle specifications
   - Cargo: Cargo characteristics
   - Transport: Vehicle types, equipment, and cargo configurations

### Infrastructure Layer

1. **Data Access**
   - Repository pattern implementation
   - SQLAlchemy ORM integration
   - CRUD operations for all entities
   - Query optimization

2. **External Services**
   - Toll rate service integration
   - Geocoding service integration
   - Map service integration
   - AI service integration

3. **Core Infrastructure**
   - Database configuration
   - Logging setup
   - Environment management
   - Utility functions

### Database Schema

1. **Core Tables**
   - routes: Transport routes
   - costs: Cost calculations
   - offers: Transport offers
   - vehicles: Vehicle data
   - drivers: Driver information
   - settings: Application settings

2. **Relationships**
   - Offer → Route (1:1)
   - Route → Costs (1:N)
   - Vehicle → Driver (N:N)
   - Settings → Cost Components (1:N)

### Security & Performance

1. **Security Measures**
   - Input validation at all layers
   - API authentication
   - Data sanitization
   - Error handling

2. **Performance Optimizations**
   - Query optimization
   - Caching strategies
   - Lazy loading
   - Batch processing

3. **Monitoring**
   - Performance metrics
   - Error tracking
   - Usage statistics
   - Resource utilization

## 5. Development & Deployment

### Development Environment

1. **Prerequisites**
   - Python 3.11+
   - Virtual environment (venv)
   - Git version control
   - SQLite database

2. **Project Setup**
   ```bash
   # Create and activate virtual environment
   python -m venv venv
   source venv/bin/activate  # Unix
   .\venv\Scripts\activate   # Windows

   # Install dependencies
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```

3. **Configuration**
   - Environment variables in `.env`
   - Development settings
   - API keys and secrets
   - Database configuration

4. **Running Services**
   ```bash
   # Start backend (Flask)
   python -m flask run --port 5001

   # Start frontend (Streamlit)
   streamlit run src/frontend/app.py --server.port 8501
   ```

### Development Guidelines

1. **Code Organization**
   - Follow clean architecture principles
   - Maintain separation of concerns
   - Use type hints consistently
   - Document public interfaces

2. **Testing Strategy**
   - Unit tests for domain logic
   - Integration tests for API
   - Repository tests
   - Frontend component tests

3. **Version Control**
   - Feature branches
   - Pull request workflow
   - Code review process
   - Conventional commits

4. **Documentation**
   - Code documentation
   - API documentation
   - Architecture documentation
   - Development guides

### Deployment

1. **Environment Setup**
   - Production configuration
   - Environment variables
   - Security settings
   - Logging configuration

2. **Database Management**
   - Migration scripts
   - Backup procedures
   - Data validation
   - Performance tuning

3. **Service Deployment**
   - Backend service
   - Frontend application
   - Database setup
   - External services

4. **Monitoring & Maintenance**
   - Performance monitoring
   - Error tracking
   - Usage analytics
   - Regular backups

### Security Considerations

1. **Authentication & Authorization**
   - API authentication
   - User authentication
   - Role-based access
   - Session management

2. **Data Protection**
   - Input validation
   - Data encryption
   - Secure communication
   - Error handling

3. **Infrastructure Security**
   - Network security
   - Service isolation
   - Regular updates
   - Security audits

### Performance Optimization

1. **Application Level**
   - Query optimization
   - Caching strategies
   - Resource management
   - Load balancing

2. **Database Level**
   - Index optimization
   - Query tuning
   - Connection pooling
   - Data partitioning

3. **Frontend Level**
   - Code splitting
   - Asset optimization
   - State management
   - API request batching

## 6. Future Considerations

### Technical Enhancements

1. **AI Integration**
   - Enhanced route optimization
   - Dynamic pricing models
   - Predictive analytics
   - Natural language processing

2. **Infrastructure Improvements**
   - Containerization (Docker)
   - Cloud deployment
   - Microservices architecture
   - Message queues

3. **Database Evolution**
   - Migration to PostgreSQL
   - Data warehousing
   - Analytics integration
   - Caching layer

4. **API Enhancements**
   - GraphQL integration
   - WebSocket support
   - API versioning
   - Rate limiting

### Feature Roadmap

1. **Route Planning**
   - Multi-vehicle optimization
   - Real-time traffic integration
   - Weather impact analysis
   - Alternative route suggestions

2. **Cost Management**
   - Advanced pricing models
   - Dynamic rate cards
   - Cost prediction
   - Margin optimization

3. **Offer Generation**
   - Template customization
   - Automated negotiations
   - Contract management
   - Digital signatures

4. **Analytics & Reporting**
   - Business intelligence
   - Custom reporting
   - Data visualization
   - Performance metrics

### Scalability Considerations

1. **Performance**
   - Load balancing
   - Horizontal scaling
   - Cache optimization
   - Query performance

2. **Architecture**
   - Service decomposition
   - Event-driven design
   - CQRS pattern
   - Domain events

3. **Data Management**
   - Data partitioning
   - Backup strategies
   - Data retention
   - Archive policies

### Integration Opportunities

1. **External Systems**
   - ERP integration
   - CRM systems
   - Accounting software
   - Fleet management

2. **Third-party Services**
   - Payment gateways
   - Document management
   - Communication platforms
   - Analytics services

### User Experience

1. **Mobile Support**
   - Progressive web app
   - Mobile-first design
   - Offline capabilities
   - Touch optimization

2. **Accessibility**
   - WCAG compliance
   - Screen reader support
   - Keyboard navigation
   - Color contrast

3. **Localization**
   - Multi-language support
   - Regional settings
   - Currency handling
   - Time zone management
