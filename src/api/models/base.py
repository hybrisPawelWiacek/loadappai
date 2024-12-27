"""Base models and utilities for API request/response handling."""
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field, validator
from decimal import Decimal


def ensure_timezone(cls, v):
    """Ensure datetime has timezone information."""
    if v.tzinfo is None:
        v = v.replace(tzinfo=timezone.utc)
    return v


class ValidationResult(BaseModel):
    """Validation result model."""
    is_valid: bool
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    validation_date: datetime = Field(default_factory=datetime.utcnow)

    _ensure_timezone = validator('validation_date', allow_reuse=True)(ensure_timezone)


class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str
    code: Optional[str] = None
    details: Optional[str] = None
