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
        original_error: The original exception that caused this error
    """
    
    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        """Initialize service error.
        
        Args:
            message: Error description
            code: Optional error code
            details: Optional error details
            original_error: Optional original exception
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
        self.original_error = original_error

    def __str__(self) -> str:
        """String representation of the error."""
        error_str = self.message
        if self.code:
            error_str = f"[{self.code}] {error_str}"
        if self.original_error:
            error_str = f"{error_str} (Original error: {str(self.original_error)})"
        return error_str

class LocationServiceError(ServiceError):
    """Exception raised for errors in the location service."""
    
    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        """Initialize location service error.
        
        Args:
            message: Error description
            code: Optional error code
            details: Optional error details
            original_error: Optional original exception
        """
        super().__init__(
            message,
            code=code,
            details=details,
            original_error=original_error
        )

class AIServiceError(ServiceError):
    """Exception raised for errors in the AI service."""
    
    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        """Initialize AI service error.
        
        Args:
            message: Error description
            code: Optional error code
            details: Optional error details
            original_error: Optional original exception
        """
        super().__init__(
            message,
            code=code,
            details=details,
            original_error=original_error
        )

class CostServiceError(ServiceError):
    """Exception raised for errors in the cost calculation service."""
    
    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        """Initialize cost service error.
        
        Args:
            message: Error description
            code: Optional error code
            details: Optional error details
            original_error: Optional original exception
        """
        super().__init__(
            message,
            code=code,
            details=details,
            original_error=original_error
        )

class OfferServiceError(ServiceError):
    """Exception raised for errors in the offer generation service."""
    
    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        """Initialize offer service error.
        
        Args:
            message: Error description
            code: Optional error code
            details: Optional error details
            original_error: Optional original exception
        """
        super().__init__(
            message,
            code=code,
            details=details,
            original_error=original_error
        )
