"""Error handling service implementation.

This module implements error handling functionality.
It provides:
- Error classification
- Error recovery
- Retry mechanisms
- Error reporting
"""
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union
import functools
import threading
import time
import traceback

from src.domain.services.common.base import BaseService

class ErrorHandlingService(BaseService):
    """Service for error handling and recovery.
    
    This service is responsible for:
    - Classifying errors
    - Managing recovery strategies
    - Implementing retry logic
    - Reporting errors
    """
    
    def __init__(
        self,
        monitoring_service: Optional['MonitoringService'] = None,
        error_client: Optional['ErrorClient'] = None,
        max_retries: int = 3,
        initial_delay: float = 1.0
    ):
        """Initialize error handling service.
        
        Args:
            monitoring_service: Optional monitoring service
            error_client: Optional error client
            max_retries: Maximum retry attempts
            initial_delay: Initial retry delay in seconds
        """
        super().__init__()
        self._monitoring = monitoring_service
        self._error_client = error_client
        self._max_retries = max_retries
        self._initial_delay = initial_delay
        
        # Error classification
        self._error_classes: Dict[str, Dict] = {}
        self._recovery_strategies: Dict[str, Callable] = {}
        
        # Error tracking
        self._error_counts: Dict[str, int] = {}
        self._last_errors: Dict[str, datetime] = {}
        self._error_windows: Dict[str, List[datetime]] = {}
        
        # Circuit breaker
        self._circuit_states: Dict[str, str] = {}
        self._circuit_attempts: Dict[str, int] = {}
        self._circuit_lock = threading.Lock()
    
    def handle_error(
        self,
        error: Exception,
        context: Optional[Dict] = None,
        retry_func: Optional[Callable] = None
    ) -> Optional[Any]:
        """Handle error with appropriate strategy.
        
        Args:
            error: Exception to handle
            context: Optional error context
            retry_func: Optional function to retry
            
        Returns:
            Result from recovery or None
            
        Raises:
            Exception: If handling fails
        """
        self._log_entry(
            "handle_error",
            error=error,
            context=context
        )
        
        try:
            error_type = error.__class__.__name__
            
            # Track error
            self._track_error(error_type, error, context)
            
            # Check circuit breaker
            if not self._check_circuit(error_type):
                raise Exception(
                    f"Circuit breaker open for {error_type}"
                )
            
            # Get error classification
            classification = self._classify_error(error)
            
            # Apply recovery strategy
            if classification.get("recoverable", False):
                result = self._apply_recovery(
                    error,
                    classification,
                    retry_func
                )
                if result is not None:
                    return result
            
            # Report error
            self._report_error(error, context, classification)
            
            # Raise if not recovered
            raise error
            
        except Exception as e:
            self._log_error("handle_error", e)
            raise
    
    def with_retry(
        self,
        max_attempts: Optional[int] = None,
        delay: Optional[float] = None,
        exceptions: Optional[List[Type[Exception]]] = None
    ) -> Callable:
        """Decorator for retry logic.
        
        Args:
            max_attempts: Maximum retry attempts
            delay: Delay between attempts
            exceptions: Exceptions to retry on
            
        Returns:
            Decorator function
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                attempts = max_attempts or self._max_retries
                retry_delay = delay or self._initial_delay
                last_error = None
                
                for attempt in range(attempts):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        if exceptions and not any(
                            isinstance(e, ex) for ex in exceptions
                        ):
                            raise
                        
                        last_error = e
                        if attempt < attempts - 1:
                            time.sleep(retry_delay * (2 ** attempt))
                
                if last_error:
                    raise last_error
                
            return wrapper
        return decorator
    
    def register_error_class(
        self,
        error_type: str,
        classification: Dict
    ) -> None:
        """Register error classification.
        
        Args:
            error_type: Type of error
            classification: Classification data
        """
        self._log_entry(
            "register_error_class",
            error_type=error_type
        )
        
        self._error_classes[error_type] = classification
    
    def register_recovery(
        self,
        error_type: str,
        strategy: Callable
    ) -> None:
        """Register recovery strategy.
        
        Args:
            error_type: Type of error
            strategy: Recovery function
        """
        self._log_entry(
            "register_recovery",
            error_type=error_type
        )
        
        self._recovery_strategies[error_type] = strategy
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics.
        
        Returns:
            Error statistics
        """
        self._log_entry("get_error_stats")
        
        return {
            "counts": self._error_counts,
            "last_occurrence": {
                t: d.isoformat()
                for t, d in self._last_errors.items()
            },
            "circuit_states": self._circuit_states,
            "classifications": self._error_classes
        }
    
    def _track_error(
        self,
        error_type: str,
        error: Exception,
        context: Optional[Dict]
    ) -> None:
        """Track error occurrence.
        
        Args:
            error_type: Type of error
            error: Exception instance
            context: Optional context
        """
        # Update counts
        self._error_counts[error_type] = (
            self._error_counts.get(error_type, 0) + 1
        )
        self._last_errors[error_type] = datetime.utcnow()
        
        # Update error window
        window = self._error_windows.setdefault(error_type, [])
        window.append(datetime.utcnow())
        
        # Trim old entries
        cutoff = datetime.utcnow() - timedelta(minutes=60)
        self._error_windows[error_type] = [
            t for t in window
            if t > cutoff
        ]
        
        # Update monitoring
        if self._monitoring:
            self._monitoring.track_error(error, context)
    
    def _classify_error(self, error: Exception) -> Dict:
        """Classify error type.
        
        Args:
            error: Exception to classify
            
        Returns:
            Error classification
        """
        error_type = error.__class__.__name__
        
        # Check registered classifications
        if error_type in self._error_classes:
            return self._error_classes[error_type]
        
        # Default classification
        return {
            "severity": "error",
            "recoverable": False,
            "retry_allowed": True,
            "requires_notification": True
        }
    
    def _apply_recovery(
        self,
        error: Exception,
        classification: Dict,
        retry_func: Optional[Callable]
    ) -> Optional[Any]:
        """Apply recovery strategy.
        
        Args:
            error: Exception to recover from
            classification: Error classification
            retry_func: Optional retry function
            
        Returns:
            Recovery result or None
        """
        error_type = error.__class__.__name__
        
        # Check for recovery strategy
        if error_type in self._recovery_strategies:
            try:
                return self._recovery_strategies[error_type](error)
            except Exception as e:
                self.logger.error(
                    f"Recovery failed: {str(e)}",
                    exc_info=True
                )
        
        # Try retry if allowed
        if classification.get("retry_allowed") and retry_func:
            return self._retry_with_backoff(
                retry_func,
                error_type
            )
        
        return None
    
    def _retry_with_backoff(
        self,
        func: Callable,
        error_type: str
    ) -> Optional[Any]:
        """Retry function with exponential backoff.
        
        Args:
            func: Function to retry
            error_type: Type of error
            
        Returns:
            Function result or None
        """
        attempts = self._circuit_attempts.get(error_type, 0)
        
        if attempts >= self._max_retries:
            return None
        
        try:
            delay = self._initial_delay * (2 ** attempts)
            time.sleep(delay)
            
            result = func()
            
            # Reset circuit on success
            with self._circuit_lock:
                self._circuit_states[error_type] = "closed"
                self._circuit_attempts[error_type] = 0
            
            return result
            
        except Exception as e:
            self.logger.warning(
                f"Retry failed: {str(e)}",
                exc_info=True
            )
            
            with self._circuit_lock:
                self._circuit_attempts[error_type] = attempts + 1
            
            return None
    
    def _check_circuit(self, error_type: str) -> bool:
        """Check circuit breaker state.
        
        Args:
            error_type: Type of error
            
        Returns:
            True if circuit allows operation
        """
        with self._circuit_lock:
            state = self._circuit_states.get(error_type, "closed")
            
            if state == "open":
                # Check if enough time has passed
                last_error = self._last_errors.get(error_type)
                if last_error:
                    if datetime.utcnow() - last_error > timedelta(minutes=5):
                        # Allow one attempt
                        self._circuit_states[error_type] = "half-open"
                        return True
                return False
            
            if state == "half-open":
                # Only allow one attempt
                self._circuit_states[error_type] = "open"
                return True
            
            # Check error frequency
            window = self._error_windows.get(error_type, [])
            recent_errors = len(window)
            
            if recent_errors > 10:  # More than 10 errors in window
                self._circuit_states[error_type] = "open"
                return False
            
            return True
    
    def _report_error(
        self,
        error: Exception,
        context: Optional[Dict],
        classification: Dict
    ) -> None:
        """Report error occurrence.
        
        Args:
            error: Exception to report
            context: Optional context
            classification: Error classification
        """
        if not classification.get("requires_notification", True):
            return
        
        # Build error report
        report = {
            "error_type": error.__class__.__name__,
            "message": str(error),
            "traceback": traceback.format_exc(),
            "context": context or {},
            "classification": classification,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Send to error client
        if self._error_client:
            self._error_client.report_error(report)
        
        # Log error
        self.logger.error(
            f"Error occurred: {str(error)}",
            extra=report,
            exc_info=True
        )
