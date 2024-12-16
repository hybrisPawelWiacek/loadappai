Below is an improved and more comprehensive version of the provided Product Requirements Document (PRD). The revisions focus on clarity, organization, and depth, while better integrating the details from the additional domain and technical specification files. This updated PRD also highlights where future enhancements or integrations with AI services could be applied, maintaining a structured, professional, and forward-looking tone.

---

# LoadApp.AI Product Requirements Document (Improved)

**Version:** 1.1  
**Date:** December 2024

## 1. Introduction & Vision

### Business Context

Transport managers face a recurring challenge: they must quickly determine if they can service a given cargo request and at what price, often with limited time and incomplete information. In the freight industry, margins are slim, and inefficiencies in cost calculation, route planning, or compliance checks can lead to lost opportunities or revenue leakage.

LoadApp.AI aims to streamline this process by providing a comprehensive solution for route planning, cost calculation, professional offer generation, and operational transparency. By integrating route data, cost structures, cargo requirements, and business overheads into an easy-to-use platform, LoadApp.AI shortens the decision-making cycle, ensures more accurate pricing, and improves offer quality.

### Core Problems Addressed

1. **Time-Consuming Manual Calculations**: Calculating route costs from scratch—fuel consumption, tolls, driver wages, compliance fees—is labor-intensive and prone to human error.

2. **Complex Decision Making**: Managers must consider multiple variables (driver availability, cargo constraints, empty driving repositioning, country-specific tolls, emissions classes, temperature controls) to ensure profitability and compliance.

3. **Professional Offer Generation**: Even after calculating costs, preparing a professional, clear, and value-adding offer for the customer is non-trivial.

4. **Inefficient Route Planning**: Factors like multi-country segments, adherence to pickup/delivery windows, and empty driving positioning remain difficult to integrate into route planning workflows.

5. **Limited Insight and AI-Powered Enhancements (Future)**: As companies scale, AI integration for dynamic cost optimization, route feasibility checks, and market-based pricing adjustments will become essential.

### Solution Overview

LoadApp.AI consolidates all critical inputs—truck/driver characteristics, route details, cargo specs, business overheads—into a single interface. Users can:

- Define the route (origin/destination) and input pickup/delivery constraints.
- Select truck and driver pairs from their fleet, factoring in vehicle emissions classes and driver costs.
- Automatically incorporate empty driving scenarios (e.g., a fixed 200 km/4h repositioning for PoC).
- Calculate costs in real-time, including fuel, tolls, maintenance, cargo-specific fees, and business overheads.
- Add a profit margin and generate a professional offer to send to customers, enhanced with an AI-powered fun fact about transport.
- Store and review historical offers for continuous improvement.

### PoC Goals

1. **Core Functionality**:
   - End-to-end route planning using Google Maps integration for distance and duration.
   - Comprehensive cost calculation with detailed breakdowns (fuel, tolls, driver salary, business overheads).
   - Offer generation with an AI-generated fun fact to differentiate the customer experience.
   - Persistent storage of route data, cost settings, and historical offers.

2. **Technical Implementation**:
   - Backend: Python/Flask for RESTful API.
   - Frontend: Streamlit-based UI for rapid iteration and user-friendliness.
   - Database: SQLite for simplicity in the PoC stage.
   - Integrations: Google Maps API for route data, OpenAI API for fun fact generation.

### Success Criteria

1. **Functional Success**:
   - Users can input route details (with empty driving scenario) and get accurate cost calculations.
   - Offers are generated within a few seconds and include a cost breakdown and AI fun fact.
   - Historical offers and cost configurations can be retrieved and reviewed.

2. **Technical Success**:
   - All core features operate reliably end-to-end.
   - Code is clean, maintainable, and sufficiently documented.
   - Basic logging and error handling are in place, and data persists across sessions.

---

## 2. User Workflow & Core Features

### Transport Manager Process Flow

1. **Route Input**:
   - Enter origin, destination, pickup, and delivery times.
   - Select truck/driver pair and transport type.
   - System automatically includes empty driving repositioning (200 km/4h in PoC).

2. **Route Planning & Visualization**:
   - View map with route segments and empty driving portion highlighted.
   - Timeline of events (pickup, delivery, possible breaks or stops).

3. **Cost Calculation**:
   - Review breakdown by component: fuel (differentiated for empty vs. loaded), tolls, parking, driver wages, cargo-specific fees (e.g., cleaning, insurance), and business overheads (e.g., leasing, depreciation).
   - Adjust cost settings (enable/disable components, modify base values, multipliers).

4. **Offer Generation**:
   - Input desired margin.
   - System calculates final price (cost + margin).
   - Generates a professional offer, including a fun fact from OpenAI.
   - Offer is stored for future reference and analytics.

### Route Planning & Calculation Details

1. **Basic Route**:
   - Google Maps integration for distance/duration.
   - Country segments automatically detected (enables country-specific tolls/fuel prices).
   - Timeline with key events (pickup, delivery).
   - Feasibility: Always true in PoC, but future versions will consider driver rest times, border crossings, compliance.

2. **Empty Driving**:
   - Fixed scenario: 200 km and 4 hours added before main route.
   - Impacts fuel, driver time, and potentially other costs.

### Cost Management System

1. **Cost Components**:
   - **Fuel Costs**: Based on empty vs. loaded consumption, country-specific fuel prices.
   - **Driver Costs**: Daily salary, possibly country-specific wage rules in the future.
   - **Tolls**: Country-specific tolls depending on truck’s Euro and CO2 class.
   - **Business Overheads**: Leasing, depreciation, stationary costs, insurance, etc.
   - **Cargo-Specific Costs**: Insurance, cleaning, customs, temperature control.

2. **Settings Management**:
   - Each cost component can be toggled on/off.
   - Base values, multipliers, and categories are configurable.
   - Users can simulate changes in cost structure.

### Offer Generation

1. **Cost Aggregation & Pricing**:
   - Sum all cost components to get total cost.
   - Apply margin (user input).
   - Compute final sell price per route and per tonne.
   
2. **AI-Enhanced Offer**:
   - Integrate OpenAI to produce a relevant transport-related fun fact.
   - Enhance professional feel and add unique differentiators to offers.

### Offer Review & History

1. **Offer Listing**:
   - Shows key details: route, transport type, total price, creation date.
   - Filter by transport type or date.

2. **Offer Detail View**:
   - Tabs for route visualization, cost breakdown, and final offer presentation.
   - Auditable historical data for analytical improvements in future iterations.

---

## 3. User Interface Design

### Homepage (Route Planning & Offer Creation)

**Inputs**:
- Origin/destination fields (Google Maps autocomplete)
- Pickup/delivery date-time selectors (simple validation)
- Transport type dropdown (predefined truck-driver pairs)
  
**Outputs**:
- Interactive map visualization of route + empty driving.
- Timeline display of key route events.
- Detailed cost breakdown by component and country.
- Margin input and "Generate Offer" button.
- Fun fact loading indicator and final offer display.

### Offer Review Page

- Historical offers listed in a sortable, filterable table.
- Clicking an offer shows route details, cost breakdown, and the finalized offer.

### Cost Settings Page

- Enables toggling and adjusting each cost component.
- Validation feedback if incompatible settings are chosen.
- Immediate effect on cost calculations after saving changes.

---

## 4. Technical Implementation Scope

### System Architecture

- **Frontend (Streamlit)**: Forms, visualization, cost settings UI.
- **Backend (Flask)**: REST endpoints, route and cost calculation logic, integration with external APIs.
- **Database (SQLite)**: Stores routes, offers, cost settings, truck/driver definitions, cargo profiles.
- **External Services**:
  - Google Maps API for route details.
  - OpenAI API for fun fact generation.
  - Static JSON or DB tables for cost factors (fuel prices, tolls, overheads).

### Data Flow

1. **Route Calculation**:
   - User input → Backend queries Google Maps → Compute route + empty driving → Store route entity in DB.
2. **Cost Calculation**:
   - Retrieve route data + cost settings → Perform calculations → Persist cost breakdown.
3. **Offer Generation**:
   - Apply margin to costs → Query OpenAI for fun fact → Generate and store final offer.

### Core Entities

- **Route**: Holds origin/destination, pickup/delivery, empty driving, main route details, and feasibility.
- **Cost**: Breaks down costs into components (fuel, tolls, cargo-specific, overheads).
- **Offer**: Ties a route’s total cost, margin, and final price together, including AI-generated fun fact.

(Refer to domain specification files for detailed @dataclass definitions.)

---

## 5. Implementation Constraints & Guidelines

### PoC Limitations

- Single mocked user and company profile.
- Always treat routes as feasible (no complex compliance checks).
- Empty driving scenario is fixed (200 km/4h).
- Basic error handling and no authentication.
- Limited test coverage (focus on functionality).

### Quality Requirements

- Code readability with type hints and inline comments.
- Minimal test coverage for core calculations.
- Basic logging of key events and errors.
- Maintainable architecture for easy enhancement.

---

## 6. Development & Deployment

### Development Environment

- Python virtual environment for backend.
- SQLite database with sample seed data (truck types, cargoes, cost settings).
- Environment variables for API keys (Google Maps, OpenAI).
- Manual UI testing for PoC.

### Deployment (e.g., Replit)

- Host backend + frontend on Replit.
- CI/CD from GitHub repository.
- Basic environment variable setup for API keys.
- Simple logging for monitoring.

---

## 7. Future Considerations

### Beyond PoC

- **Dynamic Route Feasibility**: Incorporate driver rest times, border crossings, hazard materials regulations, pickup/delivery time windows in calculations.
- **AI-Driven Cost Optimization**: Use historical data and market intelligence to optimize route choice, timing, and pricing.
- **Multiple User Support & Authentication**: Add role-based access and manage multiple business entities.
- **Advanced Integrations**: Fuel price updates via API, toll calculation webhooks, real-time traffic considerations.
- **Scalable Architecture**: Move to PostgreSQL, add caching, improve performance monitoring.

---

## 8. Additional Files Considered

**Domain Entities Specification** (November 30, 2024):  
Provides extended data classes for Trucks, Drivers, Cargo, BusinessEntities, detailed cost structures, route offers, and AI email offers. These definitions inform how various route and cost-related computations are structured and stored, ensuring a scalable model for future enhancements (multi-user support, AI-driven optimizations, compliance checks).

**Technical Documentation**:  
Covers user system domain, audit systems, entity relationships, and a detailed breakdown of how domain models, services, and repositories interact. The PoC will use a simplified version of these structures, but the architecture supports growth to a fully-featured MVP and beyond.

**CSV Data Structure**:  
An accompanying CSV defines variables, categories, and their states (MOCK, MVP, Target) to guide the incremental development strategy. This ensures that future improvements can smoothly progress from static inputs to more automated, AI-driven data sources.

---

# Conclusion

This improved PRD outlines the end-to-end vision for LoadApp.AI’s PoC: from route planning and cost calculation to professional offer generation, with a focus on extensibility and future AI-driven enhancements. It integrates the domain specifications and technical details into a cohesive roadmap, ensuring that the PoC can evolve into a robust, fully-featured solution that addresses the complex needs of transport managers.