# OpenAI Service API Documentation

## Overview
The OpenAI Service provides AI-powered natural language processing capabilities for route descriptions, facts, and enhancements. This document outlines the available endpoints and their usage.

## Base URL
All endpoints are relative to the base API URL: `/api/v1/ai`

## Endpoints

### 1. Generate Route Description
Generate a natural language description of a route.

**Endpoint:** `POST /route/description`

**Request Body:**
```json
{
  "origin": {
    "latitude": number,
    "longitude": number,
    "address": string
  },
  "destination": {
    "latitude": number,
    "longitude": number,
    "address": string
  },
  "context": {
    "distance_km": number,
    "duration_hours": number,
    "countries": string[],
    "transport_type": string,
    "cargo_type": string
  }
}
```

**Response:**
```json
{
  "description": string,
  "status": "success" | "error",
  "error": string | null
}
```

### 2. Generate Route Facts
Generate interesting facts about a route.

**Endpoint:** `POST /route/facts`

**Request Body:**
```json
{
  "origin": {
    "latitude": number,
    "longitude": number,
    "address": string
  },
  "destination": {
    "latitude": number,
    "longitude": number,
    "address": string
  },
  "context": {
    "distance_km": number,
    "duration_hours": number,
    "countries": string[],
    "points_of_interest": string[]
  }
}
```

**Response:**
```json
{
  "facts": string[],
  "status": "success" | "error",
  "error": string | null
}
```

### 3. Enhance Route Description
Enhance a route description with additional context and details.

**Endpoint:** `POST /route/enhance`

**Request Body:**
```json
{
  "description": string,
  "context": {
    "distance_km": number,
    "duration_hours": number,
    "countries": string[],
    "transport_type": string,
    "cargo_type": string,
    "weather": object | null,
    "traffic": object | null
  }
}
```

**Response:**
```json
{
  "enhanced_description": string,
  "status": "success" | "error",
  "error": string | null
}
```

## Error Handling

All endpoints follow a consistent error response format:

```json
{
  "status": "error",
  "error": {
    "code": string,
    "message": string,
    "details": object | null
  }
}
```

Common error codes:
- `invalid_input`: Request validation failed
- `ai_service_error`: OpenAI API error
- `rate_limit`: Rate limit exceeded
- `internal_error`: Unexpected server error

## Rate Limiting
- Default rate limit: 60 requests per minute
- Enhanced rate limit for authenticated users: 120 requests per minute

## Best Practices
1. Always include relevant context in requests for better results
2. Handle rate limits with exponential backoff
3. Cache responses when possible
4. Use appropriate timeout settings (recommended: 30s)
5. Implement proper error handling for all possible response codes
