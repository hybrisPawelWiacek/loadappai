Below is a proposed **API Specification & Contract Document** for the PoC scope of LoadApp.AI. This document defines the core endpoints, request/response structures, and expected behaviors. It is designed to be used by both human developers and the AI Dev Agent to ensure consistent implementation and integration.

---

# LoadApp.AI API Specification & Contract Document (PoC)

**Version:** 2.0  
**Date:** December 24, 2024  
**Last Updated:** December 24, 2024

## 1. Overview

This document specifies the API contract for LoadApp.AI, focusing on route planning, cost calculation, offer generation, and system settings management. The API is organized into four main domains:

1. Routes: Managing transportation routes and segments
2. Costs: Handling cost calculations and settings
3. Offers: Managing price offers and versions
4. Settings: System-wide configuration

## 2. API Standards

### 2.1 Base URL

All endpoints are prefixed with `/api/v1`

### 2.2 Authentication

Authentication is handled via API keys in the request header:
```
Authorization: Bearer <api_key>
```

### 2.3 Common Headers

**Request Headers:**
```
Content-Type: application/json
Accept: application/json
X-Request-ID: uuid
```

**Response Headers:**
```
Content-Type: application/json
X-Request-ID: uuid (echo)
X-Response-Time-Ms: number
```

### 2.4 Error Response Format

```json
{
  "error": "Human readable error message",
  "code": "ERROR_CODE",
  "details": {
    "field": "validation details",
    "context": "additional context"
  }
}
```

Common Error Codes:
- `NOT_FOUND`: Resource not found
- `VALIDATION_ERROR`: Invalid input data
- `INTERNAL_ERROR`: Server error
- `GEOCODING_ERROR`: Address geocoding failed

## 3. Routes API

### 3.1 Create Route
**POST** `/routes`

Creates a new route with origin and destination.

**Request:**
```json
{
  "origin": "Warsaw, Poland",
  "destination": "Berlin, Germany",
  "cargo_weight": 1000,
  "cargo_volume": 500,
  "metadata": {
    "customer_id": "string",
    "reference": "string"
  }
}
```

**Response:** (201 Created)
```json
{
  "id": "uuid",
  "origin": "Warsaw, Poland",
  "destination": "Berlin, Germany",
  "distance": 575.0,
  "duration": 6.5,
  "segments": [],
  "created_at": "2024-12-24T10:00:00Z",
  "modified_at": "2024-12-24T10:00:00Z",
  "metadata": {
    "cargo_weight": 1000,
    "cargo_volume": 500,
    "customer_id": "string",
    "reference": "string"
  }
}
```

### 3.2 Get Route
**GET** `/routes/{route_id}`

Retrieves a route by ID.

**Response:** (200 OK)
```json
{
  "id": "uuid",
  "origin": "Warsaw, Poland",
  "destination": "Berlin, Germany",
  "distance": 575.0,
  "duration": 6.5,
  "segments": [
    {
      "start_address": "Warsaw, Poland",
      "end_address": "Poznan, Poland",
      "distance": 310.0,
      "duration": 3.5,
      "type": "LOADED"
    }
  ],
  "created_at": "2024-12-24T10:00:00Z",
  "modified_at": "2024-12-24T10:00:00Z",
  "metadata": {
    "cargo_weight": 1000,
    "cargo_volume": 500
  }
}
```

### 3.3 Update Route
**PUT** `/routes/{route_id}`

Updates an existing route.

**Request:**
```json
{
  "destination": "Frankfurt, Germany",
  "cargo_weight": 1200,
  "metadata": {
    "priority": "high"
  }
}
```

**Response:** (200 OK)
```json
{
  "id": "uuid",
  "origin": "Warsaw, Poland",
  "destination": "Frankfurt, Germany",
  "distance": 1000.0,
  "duration": 9.5,
  "segments": [],
  "modified_at": "2024-12-24T11:00:00Z",
  "metadata": {
    "cargo_weight": 1200,
    "cargo_volume": 500,
    "priority": "high"
  }
}
```

### 3.4 Delete Route
**DELETE** `/routes/{route_id}`

Deletes a route.

**Response:** (200 OK)
```json
{
  "message": "Route deleted successfully"
}
```

### 3.5 List Routes
**GET** `/routes`

Lists routes with optional filtering.

**Query Parameters:**
- `origin`: Filter by origin city/country
- `destination`: Filter by destination city/country
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 10)

**Response:** (200 OK)
```json
{
  "items": [
    {
      "id": "uuid",
      "origin": "Warsaw, Poland",
      "destination": "Berlin, Germany",
      "distance": 575.0,
      "duration": 6.5
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total": 100
  }
}
```

### 3.6 Calculate Empty Driving
**POST** `/routes/{route_id}/empty-driving`

Calculates empty driving segments for a route.

**Response:** (200 OK)
```json
{
  "segments": [
    {
      "start_address": "Berlin, Germany",
      "end_address": "Warsaw, Poland",
      "distance": 575.0,
      "duration": 6.5,
      "type": "EMPTY"
    }
  ]
}
```

## 4. Costs API

### 4.1 Calculate Route Costs
**POST** `/costs/routes/{route_id}/calculate`

Calculates costs for a route.

**Response:** (200 OK)
```json
{
  "id": "uuid",
  "route_id": "uuid",
  "total_cost": 1000.0,
  "fuel_cost": 400.0,
  "maintenance_cost": 150.0,
  "driver_cost": 450.0,
  "currency": "EUR",
  "created_at": "2024-12-24T10:00:00Z",
  "metadata": {
    "fuel_consumption": 28.5,
    "total_distance": 575.0,
    "total_duration": 6.5
  }
}
```

### 4.2 Get Route Cost Settings
**GET** `/costs/routes/{route_id}/settings`

Gets cost settings for a specific route.

**Response:** (200 OK)
```json
{
  "route_id": "uuid",
  "fuel_consumption": 28.5,
  "additional_cost_per_km": 0.05,
  "custom_driver_cost_per_hour": 30.0,
  "currency": "EUR",
  "created_at": "2024-12-24T10:00:00Z",
  "modified_at": "2024-12-24T10:00:00Z"
}
```

### 4.3 Update Route Cost Settings
**PUT** `/costs/routes/{route_id}/settings`

Updates cost settings for a specific route.

**Request:**
```json
{
  "fuel_consumption": 30.0,
  "additional_cost_per_km": 0.06,
  "custom_driver_cost_per_hour": 32.0
}
```

**Response:** (200 OK)
```json
{
  "route_id": "uuid",
  "fuel_consumption": 30.0,
  "additional_cost_per_km": 0.06,
  "custom_driver_cost_per_hour": 32.0,
  "currency": "EUR",
  "modified_at": "2024-12-24T11:00:00Z"
}
```

## 5. Offers API

### 5.1 Get Offer
**GET** `/offers/{offer_id}`

Retrieves an offer by ID.

**Query Parameters:**
- `version`: Specific version to retrieve
- `include_history`: Include version history (boolean)

**Response:** (200 OK)
```json
{
  "id": "uuid",
  "route_id": "uuid",
  "status": "DRAFT",
  "margin": 0.15,
  "total_cost": 1000.0,
  "offer_price": 1150.0,
  "currency": "EUR",
  "version": 1,
  "created_at": "2024-12-24T10:00:00Z",
  "modified_at": "2024-12-24T10:00:00Z",
  "metadata": {
    "key": "value"
  },
  "history": [
    {
      "version": 1,
      "status": "DRAFT",
      "margin": 0.15,
      "offer_price": 1150.0,
      "modified_at": "2024-12-24T10:00:00Z",
      "modified_by": "user1",
      "change_reason": "Initial creation"
    }
  ]
}
```

### 5.2 Update Offer
**PUT** `/offers/{offer_id}`

Updates an existing offer.

**Request:**
```json
{
  "margin": 0.18,
  "status": "SENT",
  "modified_by": "user2",
  "change_reason": "Price adjustment"
}
```

**Response:** (200 OK)
```json
{
  "id": "uuid",
  "status": "SENT",
  "margin": 0.18,
  "total_cost": 1000.0,
  "offer_price": 1180.0,
  "version": 2,
  "modified_at": "2024-12-24T11:00:00Z"
}
```

### 5.3 Archive Offer
**POST** `/offers/{offer_id}/archive`

Archives an offer.

**Request:**
```json
{
  "archived_by": "user1",
  "archive_reason": "No longer needed"
}
```

**Response:** (200 OK)
```json
{
  "id": "uuid",
  "status": "ARCHIVED",
  "version": 3,
  "modified_at": "2024-12-24T12:00:00Z"
}
```

### 5.4 List Offers
**GET** `/offers`

Lists offers with filtering and pagination.

**Query Parameters:**
- `status`: Filter by status
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 10)

**Response:** (200 OK)
```json
{
  "items": [
    {
      "id": "uuid",
      "route_id": "uuid",
      "status": "DRAFT",
      "offer_price": 1150.0,
      "version": 1
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total": 100
  }
}
```

## 6. Settings API

### 6.1 Cost Settings

#### GET `/settings/cost`
Retrieves current cost settings.

**Response:** (200 OK)
```json
{
  "fuel_prices": {
    "PL": 1.5,
    "DE": 1.8,
    "FR": 1.7
  },
  "maintenance_cost_per_km": 0.15,
  "driver_cost_per_hour": 25.0,
  "base_cost_multiplier": 1.2,
  "currency": "EUR"
}
```

#### PUT `/settings/cost`
Updates cost settings.

**Request:**
```json
{
  "fuel_prices": {
    "PL": 1.6
  },
  "maintenance_cost_per_km": 0.16
}
```

### 6.2 Transport Settings

#### GET `/settings/transport`
Retrieves transport settings.

**Response:** (200 OK)
```json
{
  "max_driving_time": 9,
  "max_working_time": 13,
  "break_duration": 0.75,
  "daily_rest_duration": 11,
  "speed_empty": 75,
  "speed_loaded": 68
}
```

#### PUT `/settings/transport`
Updates transport settings.

**Request:**
```json
{
  "speed_empty": 80,
  "speed_loaded": 70
}
```

### 6.3 System Settings

#### GET `/settings/system`
Retrieves system settings.

**Response:** (200 OK)
```json
{
  "default_currency": "EUR",
  "distance_unit": "km",
  "time_zone": "UTC",
  "language": "en"
}
```

#### PUT `/settings/system`
Updates system settings.

**Request:**
```json
{
  "language": "pl",
  "time_zone": "Europe/Warsaw"
}
```

## 7. Versioning

The API uses semantic versioning (MAJOR.MINOR) and is currently at version 2.0. Breaking changes will increment the MAJOR version, while backward-compatible changes will increment the MINOR version.

## 8. Rate Limiting

- 1000 requests per minute per API key
- Rate limit headers included in responses:
  ```
  X-RateLimit-Limit: 1000
  X-RateLimit-Remaining: 999
  X-RateLimit-Reset: 1640390400
  ```