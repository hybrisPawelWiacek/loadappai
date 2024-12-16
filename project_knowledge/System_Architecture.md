Below is a suggested System Architecture Document designed to complement the PRD, focusing on the PoC scope. This architecture description outlines key components, data flows, technology choices, and integration points. It aims to provide the technical blueprint necessary for you and the AI Dev Agent to proceed with implementation.

---

# LoadApp.AI System Architecture Document

**Version:** 1.0  
**Date:** December 2024

## 1. Overview

This system architecture supports the PoC requirements outlined in the PRD. It focuses on a simplified yet scalable structure that can evolve into a full MVP and eventually a production-ready system. The architecture leverages a layered approach with clear separation of concerns:

- **Presentation Layer (Frontend/UI)**: Streamlit-based web interface for user interactions.
- **Service Layer (Backend)**: Python/Flask RESTful API for route planning, cost calculations, offer generation, and data management.
- **Data Layer (Persistence)**: SQLite database for lightweight, local data persistence.
- **Integration Layer (External Services)**: Google Maps API for route data and OpenAI API for generating transport-related fun facts.

## 2. Architectural Principles

1. **Modularity & Separation of Concerns**:  
   Each layer (Frontend, Backend, Database, Integrations) has a distinct responsibility. This makes it easier to maintain, test, and evolve.

2. **Simplicity & Extensibility**:  
   Start simple (e.g., SQLite, no complex caching), but design so it can scale to more advanced infrastructures (PostgreSQL, caching layers) in the future.

3. **API-Centric Design**:  
   The backend exposes a clear RESTful API consumed by the frontend. This facilitates future expansions, such as integrating external dashboards or mobile clients.

4. **Data-Driven Configuration**:  
   Cost settings, truck/driver profiles, cargo definitions, and route data are stored in the database, allowing runtime modifications without code changes.

## 3. High-Level Architecture Diagram (Conceptual)

```
+-------------------+         +-----------------------+
|     Frontend      |         |      Integrations     |
|  (Streamlit UI)   | <------>|  (Google Maps, OpenAI)|
|                   |         +-----------+-----------+
+---------+---------+                     |
          |                               |
          v                               |
+-------------------+                     |
|      Backend      |                     |
|    (Flask API)    |<--------------------+
|                   |
+---------+---------+
          |
          v
+-------------------+
|     Database      |
|     (SQLite)      |
+-------------------+
```

## 4. Component Breakdown

### 4.1 Frontend (Presentation Layer)

- **Technology**: Streamlit
- **Responsibilities**:
  - Renders a web-based UI for inputting route details, cargo info, pickup/delivery times, and cost settings.
  - Displays route maps, cost breakdowns, and final offers.
  - Manages user interactions such as generating offers and reviewing past offers.

- **Key Features**:
  - **Route Input Form**: Origin, Destination, Pickup/Delivery times, Transport Type selection.
  - **Offer Generation UI**: Margin input, "Generate Offer" button, loading indicator, and fun fact display.
  - **Settings Pages**: Adjust cost components (fuel, tolls, overheads) and preview changes.
  - **Historical Offers Page**: Lists previously generated offers and allows review.

- **Integration with Backend**:
  - Calls Flask API endpoints to fetch route details, calculate costs, and generate offers.
  - Sends updated cost settings to the backend for persistence.

### 4.2 Backend (Service Layer)

- **Technology**: Python, Flask
- **Responsibilities**:
  - Provides RESTful endpoints for route planning, cost calculation, and offer generation.
  - Orchestrates logic: queries Google Maps for route data, retrieves cost settings, calculates costs, and requests fun facts from OpenAI.
  - Performs CRUD operations on the SQLite database for routes, offers, and settings.

- **Key Services**:
  - **Route Service**:  
    Endpoint to process route input, query Google Maps for distance/duration, store route details.
  - **Cost Calculation Service**:  
    Uses route data, cost settings, and cargo info to compute costs and return a detailed breakdown.
  - **Offer Service**:  
    Applies margin, retrieves an AI-generated fun fact, aggregates data into a final offer, and stores it.
  - **Settings Management Service**:  
    Endpoints to update or retrieve cost settings and other configuration parameters.

- **Error Handling & Logging**:
  - Basic error handling for invalid inputs, API timeouts.
  - Logging of key actions (route creation, offer generation) to a file or console.

### 4.3 Database (Data Layer)

- **Technology**: SQLite
- **Responsibilities**:
  - Persists routes, offers, cost settings, truck/driver and cargo configurations.
  - Provides simple relational structures for querying historical data.

- **Schema Highlights**:
  - **Routes Table**: ID, origin, destination, pickup/delivery times, associated cost breakdowns.
  - **Offers Table**: ID, associated route_id, total cost, margin, final price, AI fun fact.
  - **Cost Settings Table**: Settings for fuel costs, toll rates, business overhead multipliers, etc.
  - **Trucks/Drivers** and **Cargo**: Basic tables to support PoC with a few predefined records.

- **Migrations & Seed Data**:
  - Initially create tables with a simple SQL script.
  - Seed the database with sample truck types, cargo data, and cost configurations at startup.

### 4.4 Integrations (External Services)

- **Google Maps API**:
  - Used by the backend to obtain route distance, duration, and possibly country segmentation.
  - The backend sends origin/destination and receives a structured response (distance, route polyline, country segments).

- **OpenAI API**:
  - Backend sends a prompt (e.g., “Fun fact about transporting cargo from [origin] to [destination]”).
  - Receives a short text snippet to be included in the offer.

- **Configuration**:
  - API keys stored as environment variables.
  - Simple retry logic and graceful error handling for API failures.

## 5. Data Flows

### 5.1 Route Creation Flow

1. User enters route details in Frontend.
2. Frontend calls `POST /route` endpoint in Backend.
3. Backend queries Google Maps API for route details.
4. Backend saves route to SQLite and returns route data to Frontend.

### 5.2 Cost Calculation Flow

1. Frontend requests updated costs from `GET /route/{id}/cost`.
2. Backend fetches route data, reads cost settings from DB.
3. Backend computes costs (fuel, tolls, overheads, cargo fees).
4. Backend returns JSON cost breakdown to Frontend.
5. Frontend displays results and allows adjustments via Settings page.

### 5.3 Offer Generation Flow

1. User sets margin in Frontend and clicks "Generate Offer."
2. Frontend calls `POST /offer` with route_id and margin.
3. Backend calculates final price = total cost + margin.
4. Backend calls OpenAI API for a fun fact.
5. Backend creates an Offer entry in DB and returns offer details to Frontend.
6. Frontend displays final offer with fun fact.

### 5.4 Historical Offer Review Flow

1. User navigates to Offers page.
2. Frontend calls `GET /offers` to list past offers.
3. Backend returns a list of offers (with minimal details).
4. User selects an offer; Frontend calls `GET /offer/{id}`.
5. Backend returns full details (route, cost breakdown, margin, fun fact).
6. Frontend displays the chosen offer’s details.

## 6. Non-Functional Considerations

- **Performance**:  
  PoC scale—no heavy optimization. Ensure route calculations complete within a few seconds.
- **Security**:  
  For PoC, minimal. No authentication. Basic input validation and secret handling for API keys.
- **Scalability**:  
  Designed to easily switch from SQLite to a more robust DB (PostgreSQL).
- **Logging & Monitoring**:  
  Basic logs to identify errors. No advanced monitoring in PoC.

## 7. Development & Deployment

- **Local Development**:
  - Python environment, `pip install -r requirements.txt`.
  - Environment variables for API keys.
  - Run backend Flask app, run Streamlit frontend, connect to local SQLite DB.
  
- **Deployment (e.g., Replit)**:
  - Single environment for both frontend and backend.
  - Store API keys as environment vars.
  - Minimal configuration steps for DB initialization (create tables if not existing).

## 8. Future Evolution

- Integrate a robust authentication layer once multiple user support is required.
- Add caching for route calculations if performance becomes critical.
- Introduce asynchronous tasks if long-running processes appear.
- Migrate from SQLite to PostgreSQL as usage scales.
- Add telemetry, metrics, and a CI/CD pipeline for continuous improvement.

---

# Conclusion

This system architecture document provides a clear blueprint for implementing the PoC solution described in the PRD. It defines how the frontend, backend, database, and external services interact, enabling a stable foundation for the LoadApp.AI initial development phase.