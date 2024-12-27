"""Repository error interfaces.

This module defines the base exceptions for repository-layer errors.
These exceptions provide:
- Consistent error handling across repositories
- Clear error categorization
- Detailed error messages
- Error code support

Implementation Requirements:
1. Error Hierarchy:
   - Must extend from RepositoryError
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
        entity = repository.get(entity_id)
    except EntityNotFoundError as e:
        logger.error(f"Entity not found: {e}")
        raise
    except RepositoryError as e:
        logger.error(f"Repository error: {e}")
        raise
    ```
"""
from typing import Any, Dict, Optional

class RepositoryError(Exception):
    """Base exception for all repository layer errors.
    
    This is the parent class for all repository-specific exceptions.
    It provides a consistent interface for error handling across
    all repositories.
    
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
        """Initialize repository error.
        
        Args:
            message: Error description
            code: Optional error code
            details: Optional error details
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}

class EntityNotFoundError(RepositoryError):
    """Exception raised when an entity is not found.
    
    This exception indicates that a requested entity does not
    exist in the repository.
    """
    
    def __init__(
        self,
        message: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        **kwargs
    ):
        """Initialize entity not found error.
        
        Args:
            message: Error description
            entity_type: Optional type of entity
            entity_id: Optional ID of entity
            **kwargs: Additional context
        """
        details = {
            "entity_type": entity_type,
            "entity_id": entity_id,
            **kwargs
        }
        super().__init__(
            message,
            code="ENTITY_NOT_FOUND",
            details=details
        )

class OfferNotFoundError(EntityNotFoundError):
    """Raised when an offer is not found in the repository."""
    pass

class ValidationError(RepositoryError):
    """Exception raised for entity validation errors.
    
    This exception indicates that an entity failed validation
    before being persisted.
    """
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        constraints: Optional[Dict] = None,
        **kwargs
    ):
        """Initialize validation error.
        
        Args:
            message: Error description
            field: Optional field that failed validation
            value: Optional invalid value
            constraints: Optional validation constraints
            **kwargs: Additional context
        """
        details = {
            "field": field,
            "value": value,
            "constraints": constraints,
            **kwargs
        }
        super().__init__(
            message,
            code="VALIDATION_ERROR",
            details=details
        )

class UniqueConstraintError(RepositoryError):
    """Exception raised for unique constraint violations.
    
    This exception indicates that an entity could not be persisted
    because it would violate a uniqueness constraint.
    """
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        **kwargs
    ):
        """Initialize unique constraint error.
        
        Args:
            message: Error description
            field: Optional field causing conflict
            value: Optional conflicting value
            **kwargs: Additional context
        """
        details = {
            "field": field,
            "value": value,
            **kwargs
        }
        super().__init__(
            message,
            code="UNIQUE_CONSTRAINT_ERROR",
            details=details
        )

class PersistenceError(RepositoryError):
    """Exception raised for general persistence failures.
    
    This exception indicates that an entity could not be persisted
    due to a storage layer error.
    """
    
    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        cause: Optional[Exception] = None,
        **kwargs
    ):
        """Initialize persistence error.
        
        Args:
            message: Error description
            operation: Optional operation that failed
            cause: Optional underlying exception
            **kwargs: Additional context
        """
        details = {
            "operation": operation,
            "cause": str(cause) if cause else None,
            **kwargs
        }
        super().__init__(
            message,
            code="PERSISTENCE_ERROR",
            details=details
        )
