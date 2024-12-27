"""Shared test fixtures for API blueprint tests."""
import pytest
from flask import Flask
from flask.testing import FlaskClient

from src.api.app import create_app

@pytest.fixture
def app():
    """Create and configure a Flask application for testing."""
    app = create_app(testing=True)
    return app

@pytest.fixture
def client(app):
    """Create a test client for the Flask application."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create a test CLI runner for the Flask application."""
    return app.test_cli_runner()
