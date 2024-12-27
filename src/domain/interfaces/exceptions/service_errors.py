"""Service error interfaces.

This module defines the base exceptions for service-layer errors.
These exceptions provide:
- Consistent error handling across services
- Clear error categorization
- Detailed error messages
- Error code support

Implementation Requirements:
1. Error Hierarchy:
   - Must extend from ServiceError
   - Should provide specific types
   - Must include messages
   - Should include codes

2. Error Details:
   - Must be descriptive
   - Should include context
   - Must be actionable
   - Should aid debugging

3. Error Handling:
   - Must be catchable
   - Should be loggable
   - Must preserve stack
   - Should support i18n

Example Usage:
    ```python
    try:
        result = service.perform_action()
    except ValidationError as e:
        logger.error(f"Validation failed: {e}")
        raise
    except ServiceError as e:
        logger.error(f"Service error: {e}")
        raise
    ```
"""
from typing import Any, Dict, Optional

class ServiceError(Exception):
    """Base exception for all service layer errors.
    
    This is the parent class for all service-specific exceptions.
    It provides a consistent interface for error handling across
    all services.
    
    Attributes:
        message: Error description
        code: Error code for categorization
        details: Additional error context
    """
    
    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize service error.
        
        Args:
            message: Error description
            code: Optional error code
            details: Optional error details
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}

class LocationServiceError(ServiceError):
    """Exception raised for errors in the location service."""
    
    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize location service error.
        
        Args:
            message: Error description
            code: Optional error code
            details: Optional error details
        """
        super().__init__(
            message,
            code=code,
            details=details
        )

class AIServiceError(ServiceError):
    """Exception raised for errors in the AI service."""
    
    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize AI service error.
        
        Args:
            message: Error description
            code: Optional error code
            details: Optional error details
        """
        super().__init__(
            message,
            code=code,
            details=details
        )

class CostServiceError(ServiceError):
    """Exception raised for errors in the cost calculation service."""
    
    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize cost service error.
        
        Args:
            message: Error description
            code: Optional error code
            details: Optional error details
        """
        super().__init__(
            message,
            code=code,
            details=details
        )

class OfferServiceError(ServiceError):
    """Exception raised for errors in the offer generation service."""
    
    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize offer service error.
        
        Args:
            message: Error description
            code: Optional error code
            details: Optional error details
        """
        super().__init__(
            message,
            code=code,
            details=details
        )
