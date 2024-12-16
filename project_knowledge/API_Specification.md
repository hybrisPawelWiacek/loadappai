Below is a proposed **API Specification & Contract Document** for the PoC scope of LoadApp.AI. This document defines the core endpoints, request/response structures, and expected behaviors. It is designed to be used by both human developers and the AI Dev Agent to ensure consistent implementation and integration.

---

# LoadApp.AI API Specification & Contract Document (PoC)

**Version:** 1.0  
**Date:** December 2024

## 1. Overview

This document outlines the RESTful API endpoints for the LoadApp.AI PoC, focusing on route planning, cost calculation, offer generation, and settings management. It serves as the authoritative contract between the frontend (Streamlit UI) and the backend (Flask API).

Key principles for this PoC API:

- **Simplicity**: Focus on essential operations needed for the PoC.
- **Consistency**: Uniform naming conventions, request/response patterns, and use of JSON.
- **Extensibility**: Endpoints and data structures are designed so they can be extended in the future without breaking changes.

**Base URL:**  
For local development: `http://localhost:5000/api/v1`

**Authentication:**  
- PoC: No authentication required. In future versions, authentication and role-based permissions may be added.

**Response Format:**  
- All responses in JSON.
- Use standard HTTP status codes:
  - `2xx` for success
  - `4xx` for client errors (bad input, not found)
  - `5xx` for server errors

**Error Handling:**  
- On errors, return JSON with an `"error"` field containing a message and optionally a code:
  ```json
  {
    "error": "Invalid input data",
    "code": "INVALID_INPUT"
  }
  ```

---

## 2. Endpoints

### 2.1 Route Management

#### POST `/routes`

**Description:**  
Create a new route given origin/destination and schedule details. The backend fetches route info (distance/duration) from Google Maps and stores it.

**Request Body (JSON):**
```json
{
  "origin": {
    "address": "string",
    "latitude": 48.8566,
    "longitude": 2.3522
  },
  "destination": {
    "address": "string",
    "latitude": 50.1109,
    "longitude": 8.6821
  },
  "pickup_time": "2024-12-20T08:00:00Z",
  "delivery_time": "2024-12-21T16:00:00Z",
  "transport_type": "string",  // e.g. "flatbed_truck"
  "cargo_id": "string"          // optional, for PoC assume cargo_id references predefined cargo in DB
}
```

**Successful Response (201):**
```json
{
  "id": "uuid",
  "origin": {...},
  "destination": {...},
  "pickup_time": "2024-12-20T08:00:00Z",
  "delivery_time": "2024-12-21T16:00:00Z",
  "transport_type": "flatbed_truck",
  "cargo_id": "string",
  "distance_km": 500.5,
  "duration_hours": 7.5,
  "empty_driving": {
    "distance_km": 200.0,
    "duration_hours": 4.0
  },
  "is_feasible": true,
  "created_at": "2024-12-10T12:00:00Z"
}
```

**Error Responses:**
- 400 Bad Request: Missing or invalid fields.
- 500 Internal Server Error: If Google Maps integration fails.

---

#### GET `/routes/{id}`

**Description:**  
Retrieve details of a previously created route.

**Path Parameters:**
- `id`: Route UUID

**Response (200):**
```json
{
  "id": "uuid",
  "origin": {...},
  "destination": {...},
  "pickup_time": "2024-12-20T08:00:00Z",
  "delivery_time": "2024-12-21T16:00:00Z",
  "transport_type": "flatbed_truck",
  "cargo_id": "string",
  "distance_km": 500.5,
  "duration_hours": 7.5,
  "empty_driving": {
    "distance_km": 200.0,
    "duration_hours": 4.0
  },
  "is_feasible": true,
  "created_at": "2024-12-10T12:00:00Z"
}
```

**Error Responses:**
- 404 Not Found: If no route with the given ID exists.
- 500 Internal Server Error: Unexpected database error.

---

### 2.2 Cost Calculation

#### GET `/routes/{id}/cost`

**Description:**  
Calculate and return the cost breakdown for the specified route, considering current cost settings and cargo details.

**Path Parameters:**
- `id`: Route UUID

**Response (200):**
```json
{
  "route_id": "uuid",
  "fuel_cost": 123.45,
  "toll_cost": 89.10,
  "driver_cost": 200.00,
  "overheads": 50.00,
  "cargo_specific_costs": {
    "insurance": 30.00,
    "cleaning": 10.00
  },
  "total_cost": 502.55,
  "currency": "EUR"
}
```

**Error Responses:**
- 404 Not Found: If no route with the given ID exists.
- 500 Internal Server Error: Error during cost calculation (e.g., missing cost settings).

---

### 2.3 Offer Management

#### POST `/offers`

**Description:**  
Generate an offer for a given route by applying a margin and fetching an AI-powered fun fact.

**Request Body (JSON):**
```json
{
  "route_id": "uuid",
  "margin": 0.10   // 10% margin
}
```

**Successful Response (201):**
```json
{
  "id": "offer_uuid",
  "route_id": "uuid",
  "total_cost": 502.55,
  "margin": 0.10,
  "final_price": 552.81,  // total_cost * (1 + margin)
  "fun_fact": "Did you know that trucks transport over 70% of all freight in the EU?",
  "created_at": "2024-12-10T12:10:00Z"
}
```

**Error Responses:**
- 400 Bad Request: Missing route_id or margin out of acceptable range.
- 404 Not Found: If route not found.
- 500 Internal Server Error: If OpenAI API fails or cost calculation fails unexpectedly.

---

#### GET `/offers`

**Description:**  
List previously generated offers.

**Query Parameters (Optional):**
- `transport_type`: Filter offers by transport type
- `date_from`, `date_to`: Filter by creation date range (ISO timestamps)

**Response (200):**
```json
[
  {
    "id": "offer_uuid_1",
    "route_id": "uuid_1",
    "final_price": 552.81,
    "created_at": "2024-12-10T12:10:00Z"
  },
  {
    "id": "offer_uuid_2",
    "route_id": "uuid_2",
    "final_price": 420.00,
    "created_at": "2024-12-09T10:00:00Z"
  }
]
```

**Error Responses:**
- 500 Internal Server Error: Database query failure.

---

#### GET `/offers/{id}`

**Description:**  
Retrieve details of a specific offer, including the fun fact and full cost breakdown (queried from related route and cost data).

**Path Parameters:**
- `id`: Offer UUID

**Response (200):**
```json
{
  "id": "offer_uuid",
  "route_id": "uuid",
  "total_cost": 502.55,
  "margin": 0.10,
  "final_price": 552.81,
  "fun_fact": "Did you know that trucks transport over 70% of all freight in the EU?",
  "created_at": "2024-12-10T12:10:00Z"
}
```

**Error Responses:**
- 404 Not Found: Offer not found.
- 500 Internal Server Error: Unexpected database error.

---

### 2.4 Cost Settings Management

#### GET `/cost-settings`

**Description:**  
Retrieve current cost settings, including fuel price, toll rates, overhead multipliers, etc.

**Response (200):**
```json
{
  "fuel_price_per_liter": 1.50,
  "driver_daily_salary": 138.0,
  "toll_rates": {
    "DE": 0.10,
    "FR": 0.12
  },
  "overheads": {
    "leasing": 20.0,
    "depreciation": 10.0,
    "insurance": 15.0
  },
  "cargo_factors": {
    "cleaning": 10.0,
    "insurance_rate": 0.001
  }
}
```

**Error Responses:**
- 500 Internal Server Error: If loading settings fails.

---

#### POST `/cost-settings`

**Description:**  
Update cost settings. For PoC, this endpoint replaces entire settings rather than partial updates.

**Request Body (JSON):**
```json
{
  "fuel_price_per_liter": 1.60,
  "driver_daily_salary": 140.0,
  "toll_rates": {
    "DE": 0.11,
    "FR": 0.13
  },
  "overheads": {
    "leasing": 22.0,
    "depreciation": 11.0,
    "insurance": 15.0
  },
  "cargo_factors": {
    "cleaning": 12.0,
    "insurance_rate": 0.0012
  }
}
```

**Successful Response (200):**
```json
{
  "message": "Cost settings updated successfully",
  "updated_at": "2024-12-10T12:20:00Z"
}
```

**Error Responses:**
- 400 Bad Request: Invalid input (e.g., negative values).
- 500 Internal Server Error: Database write failure.

---

## 3. General Conventions

### 3.1 Date/Time Fields

- All date/time fields in ISO 8601 format with UTC time (`YYYY-MM-DDTHH:MM:SSZ`).

### 3.2 Currencies

- PoC: Fixed to `"EUR"`. In future versions, currency might be configurable or dynamic.

### 3.3 Pagination and Filtering

- PoC: For listing offers, no pagination is implemented. If needed, a `limit` and `offset` could be added in the future. Similarly, minimal filtering is supported.

### 3.4 Validation Rules

- Coordinates: latitude must be between -90 and 90, longitude between -180 and 180.
- Times: `pickup_time` must be before `delivery_time`.
- Margin: must be >= 0 and <= 1.0 for PoC.
- Negative cost values are invalid.

---

## 4. Versioning & Deprecation

- PoC: Single version (`v1`).
- Future: Introduce `/api/v2` endpoints as needed. Older endpoints will remain functional for a defined deprecation period.

---

## 5. Examples & Curl Commands

**Create a Route:**
```bash
curl -X POST http://localhost:5000/api/v1/routes \
  -H "Content-Type: application/json" \
  -d '{
        "origin": {"address": "Paris, France", "latitude":48.8566,"longitude":2.3522},
        "destination": {"address":"Frankfurt, Germany","latitude":50.1109,"longitude":8.6821},
        "pickup_time":"2024-12-20T08:00:00Z",
        "delivery_time":"2024-12-21T16:00:00Z",
        "transport_type":"flatbed_truck",
        "cargo_id":"cargo_001"
      }'
```

**Get Route Cost:**
```bash
curl http://localhost:5000/api/v1/routes/<route_id>/cost
```

**Generate an Offer:**
```bash
curl -X POST http://localhost:5000/api/v1/offers \
  -H "Content-Type: application/json" \
  -d '{"route_id":"<route_id>", "margin":0.1}'
```

---

## 6. Future Considerations

- Authentication and API keys when multi-user support and security are introduced.
- Pagination, sorting, and filtering for `/offers` and `/routes` lists.
- More granular partial updates for cost settings.
- Comprehensive error code catalog and internationalization of error messages.

---

# Conclusion

This API Specification & Contract Document provides a clear reference for how to interact with the LoadApp.AI backend in the PoC phase. By adhering to these definitions, both human developers and the AI Dev Agent can confidently implement and integrate the system’s frontend and backend components.