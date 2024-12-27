"""Logging configuration for LoadApp.AI."""
import logging
import sys
import uuid
from typing import Any, Dict, Optional, Tuple, Callable
from datetime import datetime
from pathlib import Path

import structlog
from flask import request, has_request_context
from src.settings import get_settings

def add_timestamp(_, __, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add timestamp to the event dict."""
    event_dict["timestamp"] = datetime.utcnow().isoformat()
    return event_dict


def add_request_info(_, __, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add request information to the event dict if available."""
    if has_request_context():
        event_dict.update({
            "method": request.method,
            "path": request.path,
            "remote_addr": request.remote_addr,
            "args": dict(request.args),
            "endpoint": request.endpoint,
            "request_id": request.headers.get("X-Request-ID", str(uuid.uuid4())),
        })
    return event_dict


def add_environment_info(_, __, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add environment information to the event dict."""
    settings = get_settings()  # Get settings on each call
    event_dict.update({
        "environment": settings.env,
        "app_version": "1.0.0",  # TODO: Get from version.py
    })
    return event_dict


def setup_logging(log_file: Optional[str] = None) -> None:
    """Configure structured logging.
    
    Args:
        log_file: Optional path to log file. If not provided, logs only to console.
    """
    settings = get_settings()  # Get settings on setup
    
    # Reset any existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Configure root logger
    root_logger.setLevel(logging.INFO if settings.env == "production" else logging.DEBUG)
    
    # Create console handler with formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO if settings.env == "production" else logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Add file handler if log file specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            add_timestamp,
            add_request_info,
            add_environment_info,
            structlog.processors.format_exc_info,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: Optional[str] = None) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance.
    
    Args:
        name: Optional logger name. If not provided, uses calling module name.
    
    Returns:
        A configured structlog logger instance.
    """
    return structlog.get_logger(name)


def log_request_lifecycle() -> Tuple[Callable[[], None], Callable[[], None]]:
    """Log request lifecycle and return start and end functions.
    
    Usage:
        start_request, end_request = log_request_lifecycle()
        
        @app.before_request
        def before_request():
            start_request()
            
        @app.after_request
        def after_request(response):
            end_request()
            return response
    
    Returns:
        Tuple of (start_request, end_request) functions.
    """
    logger = get_logger("request")

    def start_request() -> None:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.start_time = datetime.utcnow()
        request.request_id = request_id
        
        logger.info("request_start",
                   request_id=request_id,
                   method=request.method,
                   path=request.path,
                   remote_addr=request.remote_addr,
                   args=dict(request.args),
                   headers=dict(request.headers),
                   endpoint=request.endpoint)

    def end_request() -> None:
        if hasattr(request, "start_time"):
            duration_ms = (datetime.utcnow() - request.start_time).total_seconds() * 1000
            logger.info("request_completed",
                       request_id=getattr(request, "request_id", None),
                       duration_ms=duration_ms,
                       status_code=getattr(request, "status_code", None))

    return start_request, end_request
