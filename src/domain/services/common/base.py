"""Base service classes and utilities.

This module provides base classes and utilities for all services.
It includes:
- Base service class with common functionality
- Service initialization utilities
- Common validation methods
- Error handling utilities
"""
from abc import ABC
from typing import Optional
from uuid import UUID

from src.infrastructure.logging import get_logger

class BaseService(ABC):
    """Base class for all services.
    
    This class provides common functionality used by all services:
    - Logging setup
    - Basic validation
    - Error handling
    - Resource management
    """
    
    def __init__(self):
        """Initialize base service."""
        self.logger = get_logger(self.__class__.__name__)
    
    def _validate_uuid(self, value: Optional[UUID], param_name: str) -> None:
        """Validate UUID parameter.
        
        Args:
            value: UUID to validate
            param_name: Name of parameter for error messages
            
        Raises:
            ValueError: If UUID is invalid
        """
        if not value:
            raise ValueError(f"{param_name} cannot be None")
        if not isinstance(value, UUID):
            raise ValueError(f"{param_name} must be a UUID")
    
    def _validate_required(self, value: any, param_name: str) -> None:
        """Validate required parameter.
        
        Args:
            value: Value to validate
            param_name: Name of parameter for error messages
            
        Raises:
            ValueError: If value is None
        """
        if value is None:
            raise ValueError(f"{param_name} is required")
    
    def _log_entry(self, method_name: str, **kwargs) -> None:
        """Log method entry with parameters.
        
        Args:
            method_name: Name of method being entered
            **kwargs: Method parameters to log
        """
        self.logger.info(
            f"Entering {method_name}",
            **{k: str(v) for k, v in kwargs.items()}
        )
    
    def _log_exit(self, method_name: str, result: any = None) -> None:
        """Log method exit with result.
        
        Args:
            method_name: Name of method being exited
            result: Optional result to log
        """
        self.logger.info(
            f"Exiting {method_name}",
            result=str(result) if result else None
        )
    
    def _log_error(self, method_name: str, error: Exception) -> None:
        """Log method error.
        
        Args:
            method_name: Name of method where error occurred
            error: Exception that was caught
        """
        self.logger.error(
            f"Error in {method_name}",
            error=str(error),
            error_type=error.__class__.__name__
        )
