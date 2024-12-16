Below is a proposed "Domain Entities and Services Design" document that complements the existing PRD and System Architecture documents. It provides a blueprint for how the AI Agent should structure and implement domain entities and services in a way that supports the current PoC scope and leaves room for future growth and enhancements.

---

# LoadApp.AI Domain Entities & Services Design

**Version:** 1.0  
**Date:** December 2024

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

### 4.1 Route Entity

**Responsibility**: Represents a transport route with origin/destination, schedule, and associated data.

**PoC Fields**:
- `id: UUID`
- `origin: Location`
- `destination: Location`
- `pickup_time: datetime`
- `delivery_time: datetime`
- `is_feasible: bool` (PoC: always true)
- `country_segments: List[CountrySegment]` (derived from external API)
- `transport_type: str` (future: TransportType object)
- `cargo: Optional[Cargo]`
- `metadata: RouteMetadata` (JSON-friendly structure for extensibility)

**Future Extensions**:
- Weather impact, traffic conditions, compliance checks, AI-based optimization metadata.

### 4.2 Offer Entity

**Responsibility**: Represents a commercial proposition derived from a route’s costs plus margin.

**PoC Fields**:
- `id: UUID`
- `route_id: UUID`
- `total_cost: Decimal`
- `margin: float`
- `final_price: Decimal`
- `fun_fact: str` (from AI integration)
- `created_at: datetime`

**Future Extensions**:
- Versioning for multiple offer revisions, market adjustments, dynamic validity periods, multi-currency support.

### 4.3 Cost Entity & CostBreakdown

**Responsibility**: Encapsulate route-related cost calculations.

**PoC Fields**:
- `fuel_cost: Decimal`
- `toll_cost: Decimal`
- `driver_cost: Decimal`
- `overheads: Decimal`
- `cargo_specific_costs: Dict[str, Decimal]`
- `total: Decimal`

**Value Objects**:
- `CostBreakdown` as a dictionary-like structure or dedicated class that can be easily extended with new cost categories.

**Future Extensions**:
- Weather adjustments, traffic-based surcharges, resource optimization discounts, integration with external pricing APIs.

### 4.4 Cargo, TransportType, and Driver Entities

**Cargo**:
- Weight, value, special requirements, hazmat flags.
- Future: dynamic insurance calculations, advanced handling fees.

**TransportType**:
- Capacity, emissions class, fuel consumption rates.
- Future: availability tracking, maintenance schedules, compatibility checks with special cargo.

**Driver**:
- Daily salary, certifications, rest requirements.
- Future: driver assignment optimization, compliance with labor regulations.

## 5. Value Objects & Enums

**Examples**:
- `Location(latitude: float, longitude: float, address: str)`
- `CountrySegment(country_code: str, distance: float, toll_rates: Dict[str, Decimal])`
- `Currency(code: str)` (future: handle exchange rates)
- `CostType` enum: `FUEL`, `TOLL`, `DRIVER`, `OVERHEAD`, `CARGO_SPECIFIC`, `MISC`

These immutable, self-contained units clarify domain concepts and can be extended or refined as needs grow.

## 6. Domain Services

### 6.1 CostCalculationService

**Responsibility**:  
Given a `Route` and associated data (e.g., cargo, transport_type, cost settings), compute the total cost.

**PoC Methods**:
- `calculate_route_cost(route: Route) -> Cost`
- `get_cost_breakdown(route: Route) -> Dict[str, Decimal]`

**Future Enhancements**:
- Accept feature flags (weather_enabled, traffic_enabled).
- Pluggable strategies for fuel pricing, toll calculations.
- Incorporate external services (market data, compliance rules).

### 6.2 OfferService

**Responsibility**:  
Given a route and margin, generate a commercial offer with an AI fun fact.

**PoC Methods**:
- `generate_offer(route: Route, margin: float) -> Offer`

**Future Enhancements**:
- Integrate market-based adjustments.
- Versioning and audit of offers.
- Advanced compliance (validity periods, contract terms).

### 6.3 RoutePlanningService

**Responsibility**:  
Encapsulate logic for generating and validating routes. Currently minimal, but future-proofed.

**PoC Methods**:
- `create_route(origin: Location, destination: Location, pickup: datetime, delivery: datetime) -> Route`

**Future Enhancements**:
- Apply feasibility logic.
- Integrate weather, traffic, and compliance factors.
- Suggest alternative routes or timings.

### 6.4 SettingsService (Optional at PoC)

**Responsibility**:
Manage retrieval and updates of cost settings, overhead configurations, and feature toggles.

**PoC Methods**:
- `get_cost_settings() -> CostSettings`
- `update_cost_settings(settings: CostSettings) -> None`

**Future Enhancements**:
- Hierarchical settings for different business entities.
- Automated updates from external data sources.

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