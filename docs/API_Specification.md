Below is a proposed **API Specification & Contract Document** for the PoC scope of LoadApp.AI. This document defines the core endpoints, request/response structures, and expected behaviors. It is designed to be used by both human developers and the AI Dev Agent to ensure consistent implementation and integration.

---

# LoadApp.AI API Specification & Contract Document (PoC)

**Version:** 1.5  
**Date:** December 22, 2024  
**Last Updated:** December 22, 2024

## 1. Overview

This document specifies the API contract for the LoadApp.AI Proof of Concept, focusing on route planning, cost calculation, and offer generation.

## 2. API Standards

### 2.1 Request Headers

All requests must include:
```
X-API-Version: 1.5
X-Client-ID: string
X-Request-ID: uuid
X-Correlation-ID: uuid (optional)
If-Match: "entity-version" (for updates)
```

### 2.2 Response Headers

All responses include:
```
X-API-Version: 1.5
X-Request-ID: uuid (echo)
X-Response-Time-Ms: number
ETag: "entity-version"
```

### 2.3 Error Response Format

```json
{
  "status": "error",
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": {
      "field": "validation details",
      "context": "additional context"
    },
    "correlationId": "uuid",
    "timestamp": "ISO-8601"
  }
}
```

### 2.4 Validation Rules

All endpoints enforce:
- Required fields presence
- Data type correctness
- Value range constraints
- Business rule compliance
- Version control checks

## 2. Common Models

### 2.1 Location
```json
{
  "address": "Sample Street 123",
  "city": "Berlin",
  "country": "DE",
  "postal_code": "10115",
  "coordinates": {
    "lat": 52.52,
    "lng": 13.405
  }
}
```

### 2.2 TimeWindow
```json
{
  "earliest": "2024-12-22T08:00:00Z",
  "latest": "2024-12-22T18:00:00Z",
  "duration_minutes": 30
}
```

### 2.3 TransportType
```json
{
  "type": "TRUCK",
  "capacity_kg": 24000,
  "length_meters": 13.6,
  "special_equipment": ["TAIL_LIFT", "COOLING"]
}
```

### 2.4 CargoSpecification
```json
{
  "weight_kg": 18000,
  "volume_m3": 80,
  "requires_cooling": true,
  "hazmat_class": null,
  "special_requirements": ["TAIL_LIFT"]
}
```

### 2.5 RouteSegment
```json
{
  "id": "uuid",
  "start_location": {
    // Location object
  },
  "end_location": {
    // Location object
  },
  "distance_km": 450.5,
  "duration_minutes": 320,
  "country": "DE",
  "is_empty_driving": false,
  "timeline_event": {
    "type": "PICKUP",
    "planned_time": "2024-12-22T09:00:00Z",
    "duration_minutes": 30
  }
}
```

### 2.6 TimelineEvent
```json
{
  "type": "PICKUP | DELIVERY | REST | BORDER_CROSSING",
  "location": {
    // Location object
  },
  "planned_time": "2024-12-22T09:00:00Z",
  "duration_minutes": 30,
  "notes": "Optional event notes"
}
```

## 3. Endpoints

### 3.1 Route Planning

#### POST `/routes`

**Description:**  
Create a new route with detailed segments and timeline.

**Request Headers:**
```
Content-Type: application/json
X-API-Version: 1.5
X-Client-ID: string
X-Request-ID: uuid
```

**Request Body:**
```json
{
  "pickup": {
    "location": {
      "address": "string",
      "city": "string",
      "country": "string",
      "postal_code": "string",
      "coordinates": {
        "lat": "number",
        "lng": "number"
      }
    },
    "time_window": {
      "earliest": "ISO-8601",
      "latest": "ISO-8601",
      "duration_minutes": "number"
    }
  },
  "delivery": {
    "location": {
      // Location object
    },
    "time_window": {
      // TimeWindow object
    }
  },
  "transport_type": {
    "type": "string",
    "capacity_kg": "number",
    "length_meters": "number",
    "special_equipment": ["string"]
  },
  "cargo": {
    "weight_kg": "number",
    "volume_m3": "number",
    "requires_cooling": "boolean",
    "hazmat_class": "string?",
    "special_requirements": ["string"]
  },
  "metadata": {
    // Optional custom fields
  }
}
```

**Validation Rules:**
```json
{
  "pickup.location": {
    "required": true,
    "address": "non-empty string",
    "coordinates": {
      "lat": "number between -90 and 90",
      "lng": "number between -180 and 180"
    }
  },
  "time_windows": {
    "earliest": "must be future date",
    "latest": "must be after earliest",
    "duration": "positive number"
  },
  "transport_type": {
    "type": "must be valid enum value",
    "capacity": "positive number",
    "equipment": "valid equipment codes"
  },
  "cargo": {
    "weight": "positive number <= transport capacity",
    "volume": "positive number",
    "requirements": "must match transport equipment"
  }
}
```

**Response (201):**
```json
{
  "data": {
    "id": "uuid",
    "version": "string",
    "segments": [
      {
        "id": "uuid",
        "version": "string",
        "start_location": {
          // Location object
        },
        "end_location": {
          // Location object
        },
        "distance_km": "number",
        "duration_minutes": "number",
        "country": "string",
        "is_empty_driving": "boolean",
        "timeline_event": {
          "type": "string",
          "planned_time": "ISO-8601",
          "duration_minutes": "number"
        }
      }
    ],
    "timeline": [
      {
        "type": "string",
        "version": "string",
        "location": {
          // Location object
        },
        "planned_time": "ISO-8601",
        "duration_minutes": "number",
        "notes": "string?"
      }
    ],
    "metrics": {
      "total_distance_km": "number",
      "total_duration_minutes": "number",
      "empty_driving_km": "number",
      "empty_driving_minutes": "number",
      "countries_crossed": ["string"]
    },
    "feasibility": {
      "is_feasible": "boolean",
      "warnings": ["string"],
      "validation_details": {
        // Detailed validation results
      }
    },
    "metadata": {
      // Echo of request metadata
    },
    "created_at": "ISO-8601",
    "updated_at": "ISO-8601"
  }
}
```

**Error Responses:**

1. Invalid Request (400):
```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request data",
    "details": {
      "pickup.location.address": "Address is required",
      "time_window.earliest": "Must be future date"
    }
  }
}
```

2. Business Rule Violation (422):
```json
{
  "status": "error",
  "error": {
    "code": "BUSINESS_RULE_VIOLATION",
    "message": "Route planning failed",
    "details": {
      "rule": "MIN_DELIVERY_WINDOW",
      "required": "4 hours",
      "provided": "2 hours"
    }
  }
}
```

3. Version Conflict (409):
```json
{
  "status": "error",
  "error": {
    "code": "VERSION_CONFLICT",
    "message": "Entity has been modified",
    "details": {
      "current_version": "string",
      "provided_version": "string"
    }
  }
}
```

#### GET `/routes/{id}`

**Description:**  
Retrieve a route with all its details.

**Path Parameters:**
- `id`: Route UUID

**Request Headers:**
```
X-API-Version: 1.5
X-Client-ID: string
X-Request-ID: uuid
If-None-Match: "entity-version" (optional)
```

**Response Headers:**
```
ETag: "entity-version"
Last-Modified: "HTTP-date"
```

**Response (200):**
```json
{
  "data": {
    // Same as POST /routes response
  }
}
```

**Error Responses:**
- 304 Not Modified (if ETag matches)
- 404 Not Found (with error details)
- 500 Internal Server Error (with error details)

### 3.2 Cost Calculation

#### POST `/routes/{id}/cost`

**Description:**  
Calculate detailed cost breakdown for a route.

**Path Parameters:**
- `id`: Route UUID

**Request Headers:**
```
X-API-Version: 1.5
X-Client-ID: string
X-Request-ID: uuid
If-Match: "route-version"
```

**Request Body:**
```json
{
  "settings_version": "string",
  "cost_factors": {
    "fuel_price_per_liter": "number",
    "driver_cost_per_hour": "number",
    "empty_driving_factor": "number"
  },
  "metadata": {
    // Optional custom fields
  }
}
```

**Response (200):**
```json
{
  "data": {
    "id": "uuid",
    "version": "string",
    "route_id": "uuid",
    "route_version": "string",
    "settings_version": "string",
    "breakdown": {
      "fuel_cost": "number",
      "driver_cost": "number",
      "empty_driving_cost": "number",
      "additional_costs": [
        {
          "type": "string",
          "amount": "number",
          "description": "string"
        }
      ]
    },
    "total": "number",
    "currency": "string",
    "metadata": {
      // Echo of request metadata
    },
    "created_at": "ISO-8601"
  }
}
```

### 3.3 Offer Management

#### POST `/offers`

**Description:**  
Generate an offer based on route and cost calculation.

**Request Headers:**
```
X-API-Version: 1.5
X-Client-ID: string
X-Request-ID: uuid
If-Match: "cost-version"
```

**Request Body:**
```json
{
  "route_id": "uuid",
  "cost_id": "uuid",
  "margin_percentage": "number",
  "validity_hours": "number",
  "metadata": {
    // Optional custom fields
  }
}
```

**Response (201):**
```json
{
  "data": {
    "id": "uuid",
    "version": "string",
    "route_id": "uuid",
    "route_version": "string",
    "cost_id": "uuid",
    "cost_version": "string",
    "price": {
      "net_amount": "number",
      "tax_amount": "number",
      "total_amount": "number",
      "currency": "string"
    },
    "status": "string",
    "valid_until": "ISO-8601",
    "metadata": {
      // Echo of request metadata
    },
    "created_at": "ISO-8601",
    "updated_at": "ISO-8601"
  }
}
```

## 4. State Management

### 4.1 Entity Versioning

All entities include:
- `version`: Unique version identifier
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

Version control is enforced via:
- `If-Match` header for updates
- `If-None-Match` header for reads
- Version conflict errors (409)

### 4.2 Caching

Responses include:
- `ETag` header with entity version
- `Cache-Control` headers
- `Last-Modified` header

### 4.3 Idempotency

Guaranteed via:
- `X-Request-ID` header
- Idempotency keys in response
- 409 Conflict for duplicate requests

## 5. Error Codes

### 5.1 Validation Errors (400)
- `INVALID_INPUT`: General validation failure
- `MISSING_REQUIRED`: Required field missing
- `INVALID_FORMAT`: Wrong data format
- `INVALID_VALUE`: Value out of allowed range

### 5.2 Business Errors (422)
- `ROUTE_NOT_FEASIBLE`: Route cannot be planned
- `COST_CALCULATION_FAILED`: Cost calculation error
- `OFFER_GENERATION_FAILED`: Offer creation error

### 5.3 System Errors (500)
- `INTERNAL_ERROR`: Unexpected system error
- `EXTERNAL_SERVICE_ERROR`: Third-party service failure
- `DATABASE_ERROR`: Database operation failed

## 6. Future Extensions

Planned additions:
- Batch operations for routes and offers
- Real-time route updates
- Webhook notifications
- Advanced filtering and search
- Rate limiting and quotas

## 7. General Conventions

### 7.1 Date/Time Fields

- All date/time fields in ISO 8601 format with UTC time (`YYYY-MM-DDTHH:MM:SSZ`).

### 7.2 Currencies

- PoC: Fixed to `"EUR"`. In future versions, currency might be configurable or dynamic.

### 7.3 Pagination and Filtering

- All list endpoints support pagination with `page` and `per_page` parameters
- Filtering options vary by endpoint and are documented in the endpoint specifications

### 7.4 Validation Rules

- Coordinates: latitude must be between -90 and 90, longitude between -180 and 180
- Times: `pickup_time` must be before `delivery_time`
- Margin: must be >= 0 and <= 1.0
- Status transitions:
  - DRAFT → ACTIVE
  - ACTIVE → ARCHIVED
  - No other transitions allowed
- Version control:
  - Version must match current version when updating
  - Version conflicts return 409 Conflict
- Required fields must not be null or empty strings

## 8. Versioning & Deprecation

- PoC: Single version (`v1`).
- Future: Introduce `/api/v2` endpoints as needed. Older endpoints will remain functional for a defined deprecation period.

## 9. Examples & Curl Commands

**Create a Route:**
```bash
curl -X POST http://localhost:5000/api/v1/routes \
  -H "Content-Type: application/json" \
  -d '{
        "pickup": {
          "location": {"address": "Paris, France", "latitude":48.8566,"longitude":2.3522},
          "time_window": {"earliest": "2024-12-22T08:00:00Z", "latest": "2024-12-22T18:00:00Z", "duration_minutes": 30}
        },
        "delivery": {
          "location": {"address":"Frankfurt, Germany","latitude":50.1109,"longitude":8.6821},
          "time_window": {"earliest": "2024-12-22T09:00:00Z", "latest": "2024-12-22T19:00:00Z", "duration_minutes": 30}
        },
        "transport_type": {"type": "TRUCK", "capacity_kg": 24000, "length_meters": 13.6, "special_equipment": ["TAIL_LIFT", "COOLING"]},
        "cargo": {"weight_kg": 18000, "volume_m3": 80, "requires_cooling": true, "hazmat_class": null, "special_requirements": ["TAIL_LIFT"]}
      }'
```

**Get Route Cost:**
```bash
curl http://localhost:5000/api/v1/routes/<route_id>/cost
```

## 10. Conclusion

This API Specification & Contract Document provides a clear reference for how to interact with the LoadApp.AI backend in the PoC phase. By adhering to these definitions, both human developers and the AI Dev Agent can confidently implement and integrate the system’s frontend and backend components.