Below is the **"Data Dictionary & Glossary Document"** draft, incorporating the requested purpose, key contents, and benefits. This document is intended to complement the existing domain, architecture, and interaction guidelines, serving as a centralized reference for terminology and data structures used throughout the LoadApp.AI system.

---

# 6. Data Dictionary & Glossary Document

**Version:** 1.0  
**Date:** December 2024

## Purpose

This document defines all domain terminology, acronyms, and data fields used throughout the LoadApp.AI system to prevent confusion, ensure consistency, and enable efficient onboarding for new team members and AI collaborators. By maintaining a shared, authoritative reference for all key terms, we reduce misinterpretations and maintain clarity as the system evolves.

## Key Contents

1. **Entity Field Definitions**:  
   Provides a table of all major entities (e.g., Route, Offer, Cost, Cargo) and clarifies each field’s meaning, acceptable ranges, data types, default values, and example values.  
   
2. **Acronym & Term Glossary**:  
   Lists domain-specific terminology and acronyms related to freight transport, logistics, compliance, and cost management, ensuring consistent use and understanding across teams.

3. **Cross-References**:  
   Points readers to relevant sections in the PRD, Domain Model, Architecture Document, and API Specification where these terms and fields are implemented. Helps locate where entities and fields are used in code (endpoints, services, or database schemas).

## Benefits

- **Prevents Misunderstandings**:  
  Having a single source of truth for entity definitions and terms reduces the risk of misinterpretation, ensuring the AI agent and human developers align on domain concepts.

- **Improves Consistency**:  
  Consistent terminology leads to clearer communication in code, documentation, and prompt interactions with the AI, maintaining high-quality outputs.

- **Accelerates Onboarding**:  
  New team members can quickly reference this dictionary and understand key concepts, saving ramp-up time and reducing the likelihood of errors due to unclear domain knowledge.

---

## Data Dictionary

### Example Entity: Route

| Field             | Type        | Description                                               | Constraints/Notes                              | Example Value                      |
|-------------------|-------------|-----------------------------------------------------------|------------------------------------------------|------------------------------------|
| `id`              | UUID        | Unique identifier for the route                          | Generated at creation; primary key in DB        | `f47ac10b-58cc-4372-a567-0e02b2c3d479` |
| `origin`          | Location    | Starting point of transport                              | Must have valid lat/long within real coordinates| `{ "address": "Paris, France", "latitude":48.8566,"longitude":2.3522 }` |
| `destination`     | Location    | Endpoint of transport                                    | Must have valid lat/long                        | `{ "address": "Frankfurt, Germany","latitude":50.1109,"longitude":8.6821 }` |
| `pickup_time`      | datetime (UTC) | Scheduled cargo pickup time                            | ISO 8601; pickup_time < delivery_time           | `2024-12-20T08:00:00Z`             |
| `delivery_time`    | datetime (UTC) | Scheduled cargo delivery time                          | ISO 8601; must be after pickup_time             | `2024-12-21T16:00:00Z`             |
| `transport_type`   | string      | Type of vehicle or transport mode (e.g. flatbed_truck)  | Must correspond to a predefined TransportType in DB | `flatbed_truck`                |
| `cargo_id`         | string?     | Reference to cargo entity associated with route          | Optional for PoC; can be null                   | `cargo_001`                       |
| `distance_km`      | float       | Total route distance in km                              | ≥ 0; derived from Google Maps API               | `500.5`                            |
| `duration_hours`    | float      | Estimated total route duration in hours                 | ≥ 0; derived from Google Maps API               | `7.5`                              |
| `empty_driving`     | object      | Details about empty repositioning (distance/duration)   | PoC: fixed 200 km/4h                           | `{ "distance_km":200.0,"duration_hours":4.0 }` |
| `is_feasible`       | boolean     | Route feasibility indicator                              | PoC: Always true                               | `true`                             |

*Note:* For full details of other entities (Offer, Cost, Cargo, BusinessEntity, Driver, TruckType), refer to the Domain Model Document. Each entity should have a similar table.

---

## Acronyms & Terms Glossary

| Term/Acronym | Definition                                                                | Reference              |
|--------------|----------------------------------------------------------------------------|------------------------|
| PRD          | Product Requirements Document: outlines features, success criteria, and scope | See PRD doc, Section 1 |
| PoC          | Proof of Concept: initial implementation to validate core feasibility       | General project usage  |
| MVP          | Minimum Viable Product: simplified version of product with essential features | Future stages          |
| Cargo         | Goods being transported, may have weight, value, special requirements       | Domain Model: Cargo    |
| Route         | The journey from origin to destination, including empty driving and main route | Domain Model: Route   |
| Offer         | A generated commercial proposal based on route costs plus margin             | Domain Model: Offer, PRD |
| TransportType | Classification of truck/vehicle used for route (e.g., flatbed, refrigerated)  | Domain Model: TransportType |
| Empty Driving | Repositioning the truck without cargo, affecting costs and route feasibility  | PRD, Domain Model (Route) |
| Timeline Events| Operational events during a route (pickup, delivery, break, refuel)         | Domain Model: Route    |
| AI Fun Fact   | A short interesting fact provided by OpenAI integration for marketing flair in offers | PRD (Offer Generation) |

*(Add more as needed, including logistic-specific terms like “hazmat” for hazardous materials, “temperature-controlled cargo,” or compliance-related acronyms.)*

---

## Cross-Reference to Models & APIs

- **Route Entity**:  
  - Defined in Domain Model Document, “Route” section.
  - Created and fetched via `/routes` endpoints (API Specification).
  - Cost calculations related to route: `/routes/{id}/cost` endpoint.

- **Offer Entity**:  
  - Defined in Domain Model Document, “Offer” section.
  - Generated via `/offers` endpoint (API Specification).
  - Relies on route cost breakdown and fun fact generation from OpenAI.

- **Cost Settings**:  
  - Defined in Domain Model Document & Config JSON files.
  - Managed via `/cost-settings` endpoints.
  - Referenced by CostCalculationService in backend layer.

---

# Conclusion

This Data Dictionary & Glossary Document provides a unified reference for terms, acronyms, and entity fields used throughout LoadApp.AI. As the product evolves, this living document should be updated to reflect changes in domain logic, data structures, and system terminology. Maintaining this resource ensures that both human and AI collaborators can consistently understand and apply domain concepts, improving productivity, clarity, and code quality.