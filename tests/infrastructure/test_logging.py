"""Tests for the logging configuration and utilities."""
import json
import logging
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import structlog
from structlog.stdlib import BoundLogger
from flask import Flask, request

from src.infrastructure.logging import (
    setup_logging,
    get_logger,
    add_timestamp,
    add_request_info,
    add_environment_info,
    log_request_lifecycle,
)


@pytest.fixture(autouse=True)
def reset_logging():
    """Reset logging configuration before each test."""
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    structlog.reset_defaults()
    yield


def test_add_timestamp():
    """Test timestamp processor adds ISO format timestamp."""
    event_dict = {}
    result = add_timestamp(None, None, event_dict)
    assert "timestamp" in result
    # Verify ISO format (should not raise ValueError)
    from datetime import datetime
    datetime.fromisoformat(result["timestamp"])


def test_add_environment_info(test_settings):
    """Test environment info processor adds correct environment data."""
    with patch("src.infrastructure.logging.get_settings", return_value=test_settings):
        event_dict = {}
        result = add_environment_info(None, None, event_dict)
        assert result["environment"] == test_settings.env
        assert "app_version" in result


@pytest.mark.parametrize("has_context", [True, False])
def test_add_request_info(has_context):
    """Test request info processor with and without request context."""
    app = Flask(__name__)
    event_dict = {}
    
    if has_context:
        with app.test_request_context("/test?param=value", 
                                    method="POST",
                                    headers={"X-Request-ID": "test-id"}):
            result = add_request_info(None, None, event_dict)
            assert result["method"] == "POST"
            assert result["path"] == "/test"
            assert result["args"] == {"param": "value"}
            assert result["request_id"] == "test-id"
    else:
        result = add_request_info(None, None, event_dict)
        assert result == event_dict  # No changes when no request context


def test_setup_logging_console_only(reset_logging):
    """Test logging setup without file output."""
    setup_logging()
    root_logger = logging.getLogger()
    
    # Verify console handler
    console_handlers = [h for h in root_logger.handlers 
                       if isinstance(h, logging.StreamHandler)]
    assert len(console_handlers) == 1
    
    # Verify no file handlers
    file_handlers = [h for h in root_logger.handlers 
                    if isinstance(h, logging.FileHandler)]
    assert len(file_handlers) == 0


def test_setup_logging_with_file(tmp_path, reset_logging):
    """Test logging setup with file output."""
    log_file = tmp_path / "test.log"
    setup_logging(str(log_file))
    
    # Verify file exists and is writable
    assert log_file.exists()
    assert os.access(log_file, os.W_OK)
    
    # Verify both console and file handlers
    root_logger = logging.getLogger()
    handlers = root_logger.handlers
    assert any(isinstance(h, logging.StreamHandler) for h in handlers)
    assert any(isinstance(h, logging.FileHandler) for h in handlers)


def test_get_logger(reset_logging):
    """Test logger factory creates correct logger instance."""
    setup_logging()  # Ensure structlog is configured
    logger = get_logger("test_module")
    
    # Log a message and verify it contains the module name
    with patch("structlog.get_logger") as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        logger = get_logger("test_module")
        logger.info("test_message")
        
        mock_get_logger.assert_called_once_with("test_module")


def test_log_request_lifecycle(reset_logging):
    """Test request lifecycle logging functions."""
    app = Flask(__name__)
    
    with app.test_request_context("/test"):
        mock_logger = MagicMock()
        mock_logger.info = MagicMock()
        
        with patch("structlog.get_logger", return_value=mock_logger):
            start_request, end_request = log_request_lifecycle()
            
            # Test start_request
            start_request()
            
            # Verify request attributes were set
            assert hasattr(request, "start_time")
            assert hasattr(request, "request_id")
            
            # Verify start request logging
            mock_logger.info.assert_called_with(
                "request_start",
                request_id=request.request_id,
                method=request.method,
                path=request.path,
                remote_addr=request.remote_addr,
                args=dict(request.args),
                headers=dict(request.headers),
                endpoint=request.endpoint
            )
            
            # Reset mock for end_request test
            mock_logger.info.reset_mock()
            
            # Test end_request
            end_request()
            
            # Verify end request logging
            assert mock_logger.info.call_count == 1
            last_call = mock_logger.info.call_args
            assert last_call[0][0] == "request_completed"
            assert "duration_ms" in last_call[1]
            assert "request_id" in last_call[1]


def test_log_output_format(tmp_path, reset_logging):
    """Test structured log output format."""
    # Setup logging with file output
    log_file = tmp_path / "test.log"
    setup_logging(str(log_file))
    logger = get_logger("test_format")
    
    # Log a test message
    test_data = {"key": "value"}
    logger.info("test_message", **test_data)
    
    # Check file output format
    with open(log_file) as f:
        for line in f:
            try:
                log_data = json.loads(line)
                assert log_data["event"] == "test_message"
                assert log_data["key"] == "value"
                assert "timestamp" in log_data
                assert log_data["logger"] == "test_format"
                break
            except json.JSONDecodeError:
                continue  # Skip non-JSON lines
