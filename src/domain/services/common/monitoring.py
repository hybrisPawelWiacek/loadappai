"""Monitoring service implementation.

This module implements monitoring functionality.
It provides:
- Performance monitoring
- Error tracking
- Health checks
- Metrics collection
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Union
import threading
import time

from src.domain.services.common.base import BaseService

class MonitoringService(BaseService):
    """Service for system monitoring.
    
    This service is responsible for:
    - Performance tracking
    - Error monitoring
    - Health checking
    - Metrics collection
    """
    
    def __init__(
        self,
        metrics_client: Optional['MetricsClient'] = None,
        error_client: Optional['ErrorClient'] = None,
        check_interval: int = 60
    ):
        """Initialize monitoring service.
        
        Args:
            metrics_client: Optional metrics client
            error_client: Optional error tracking client
            check_interval: Health check interval in seconds
        """
        super().__init__()
        self._metrics = metrics_client
        self._error_client = error_client
        self._check_interval = check_interval
        
        # Performance tracking
        self._timers: Dict[str, float] = {}
        self._counters: Dict[str, int] = {}
        self._gauges: Dict[str, float] = {}
        
        # Health status
        self._health_status: Dict[str, Dict] = {}
        self._health_checks: Dict[str, callable] = {}
        
        # Error tracking
        self._error_counts: Dict[str, int] = {}
        self._last_errors: Dict[str, datetime] = {}
        
        # Start monitoring thread
        self._monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self._monitor_thread.start()
    
    def start_timer(self, name: str) -> None:
        """Start performance timer.
        
        Args:
            name: Timer name
        """
        self._log_entry("start_timer", name=name)
        self._timers[name] = time.time()
    
    def stop_timer(self, name: str) -> Optional[float]:
        """Stop performance timer.
        
        Args:
            name: Timer name
            
        Returns:
            Elapsed time in seconds
        """
        self._log_entry("stop_timer", name=name)
        
        try:
            if name not in self._timers:
                return None
            
            elapsed = time.time() - self._timers.pop(name)
            
            # Send to metrics client
            if self._metrics:
                self._metrics.timing(
                    f"timer.{name}",
                    elapsed * 1000  # Convert to ms
                )
            
            return elapsed
            
        except Exception as e:
            self._log_error("stop_timer", e)
            return None
    
    def increment_counter(
        self,
        name: str,
        value: int = 1,
        tags: Optional[Dict] = None
    ) -> None:
        """Increment counter metric.
        
        Args:
            name: Counter name
            value: Value to increment by
            tags: Optional metric tags
        """
        self._log_entry(
            "increment_counter",
            name=name,
            value=value
        )
        
        try:
            self._counters[name] = (
                self._counters.get(name, 0) + value
            )
            
            # Send to metrics client
            if self._metrics:
                self._metrics.increment(
                    f"counter.{name}",
                    value,
                    tags=tags
                )
            
        except Exception as e:
            self._log_error("increment_counter", e)
    
    def set_gauge(
        self,
        name: str,
        value: float,
        tags: Optional[Dict] = None
    ) -> None:
        """Set gauge metric value.
        
        Args:
            name: Gauge name
            value: Gauge value
            tags: Optional metric tags
        """
        self._log_entry("set_gauge", name=name, value=value)
        
        try:
            self._gauges[name] = value
            
            # Send to metrics client
            if self._metrics:
                self._metrics.gauge(
                    f"gauge.{name}",
                    value,
                    tags=tags
                )
            
        except Exception as e:
            self._log_error("set_gauge", e)
    
    def track_error(
        self,
        error: Exception,
        context: Optional[Dict] = None
    ) -> None:
        """Track error occurrence.
        
        Args:
            error: Exception to track
            context: Optional error context
        """
        self._log_entry(
            "track_error",
            error=error,
            context=context
        )
        
        try:
            error_type = error.__class__.__name__
            
            # Update error counts
            self._error_counts[error_type] = (
                self._error_counts.get(error_type, 0) + 1
            )
            self._last_errors[error_type] = datetime.utcnow()
            
            # Send to error client
            if self._error_client:
                self._error_client.capture_exception(
                    error,
                    extra=context
                )
            
            # Update metrics
            if self._metrics:
                self._metrics.increment(
                    "errors.count",
                    tags={"type": error_type}
                )
            
        except Exception as e:
            self._log_error("track_error", e)
    
    def register_health_check(
        self,
        name: str,
        check_func: callable
    ) -> None:
        """Register health check function.
        
        Args:
            name: Check name
            check_func: Check function
        """
        self._log_entry(
            "register_health_check",
            name=name
        )
        
        self._health_checks[name] = check_func
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get system health status.
        
        Returns:
            Health status data
        """
        self._log_entry("get_health_status")
        
        return {
            "status": self._get_overall_status(),
            "checks": self._health_status,
            "last_update": datetime.utcnow().isoformat(),
            "metrics": {
                "error_count": sum(self._error_counts.values()),
                "active_timers": len(self._timers),
                "counters": self._counters,
                "gauges": self._gauges
            }
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics.
        
        Returns:
            Metrics data
        """
        self._log_entry("get_metrics")
        
        return {
            "timers": {
                name: time.time() - start
                for name, start in self._timers.items()
            },
            "counters": self._counters,
            "gauges": self._gauges,
            "errors": {
                "counts": self._error_counts,
                "last_occurrence": {
                    t: d.isoformat()
                    for t, d in self._last_errors.items()
                }
            }
        }
    
    def _get_overall_status(self) -> str:
        """Get overall system status.
        
        Returns:
            Status string
        """
        if not self._health_status:
            return "unknown"
        
        if any(
            check.get("status") == "critical"
            for check in self._health_status.values()
        ):
            return "critical"
        
        if any(
            check.get("status") == "warning"
            for check in self._health_status.values()
        ):
            return "warning"
        
        return "healthy"
    
    def _run_health_checks(self) -> None:
        """Run registered health checks."""
        for name, check_func in self._health_checks.items():
            try:
                result = check_func()
                self._health_status[name] = {
                    "status": "healthy",
                    "timestamp": datetime.utcnow().isoformat(),
                    "result": result
                }
            except Exception as e:
                self._health_status[name] = {
                    "status": "critical",
                    "timestamp": datetime.utcnow().isoformat(),
                    "error": str(e)
                }
    
    def _monitoring_loop(self) -> None:
        """Background monitoring loop."""
        while True:
            try:
                # Sleep for check interval
                time.sleep(self._check_interval)
                
                # Run health checks
                self._run_health_checks()
                
                # Send metrics
                if self._metrics:
                    # Send error metrics
                    for error_type, count in self._error_counts.items():
                        self._metrics.gauge(
                            "errors.total",
                            count,
                            tags={"type": error_type}
                        )
                    
                    # Send counter metrics
                    for name, value in self._counters.items():
                        self._metrics.gauge(
                            f"counters.{name}",
                            value
                        )
                    
                    # Send gauge metrics
                    for name, value in self._gauges.items():
                        self._metrics.gauge(
                            f"gauges.{name}",
                            value
                        )
                
            except Exception as e:
                self.logger.error(
                    f"Monitoring error: {str(e)}",
                    exc_info=True
                )
