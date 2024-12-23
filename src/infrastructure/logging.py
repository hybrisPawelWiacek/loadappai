"""Logging configuration for LoadApp.AI."""
import logging
import sys
import uuid
from typing import Any, Dict
from datetime import datetime

import structlog
from flask import request, has_request_context

def add_timestamp(_, __, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add timestamp to the event dict."""
    event_dict["timestamp"] = datetime.now().isoformat()
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
        })
    return event_dict

def setup_logging():
    """Configure structured logging."""
    # Configure root logger to output everything
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Create console handler with formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            add_timestamp,
            add_request_info,
            structlog.processors.format_exc_info,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Log test message to verify configuration
    logger = get_logger(__name__)
    logger.info("Logging system initialized", level="DEBUG")

def get_logger(name: str = None) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)

def log_request_lifecycle():
    """Log request lifecycle and return start and end functions."""
    request_id = str(uuid.uuid4())
    logger = get_logger(__name__)
    
    def start_request():
        """Log request start."""
        logger.info(
            "request_started",
            request_id=request_id,
            method=request.method,
            path=request.path,
            remote_addr=request.remote_addr
        )
    
    def end_request(response):
        """Log request end."""
        logger.info(
            "request_ended",
            request_id=request_id,
            status=response.status_code,
            content_length=response.content_length
        )
        return response
    
    return start_request, end_request
