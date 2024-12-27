"""Test fixtures for all tests."""
import os
import pytest
from flask import Flask
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine
from unittest.mock import Mock, patch

from src.api.app import app as flask_app
from src.domain.services import RoutePlanningService
from src.domain.interfaces.services.route_service import RouteService
from src.infrastructure.repositories.route_repository import RouteRepository
from src.infrastructure.services.google_maps_service import GoogleMapsService
from src.infrastructure.database import Base, Database

@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup test environment variables."""
    os.environ['OPENAI_API_KEY'] = 'test-key'
    os.environ['OPENAI_MODEL'] = 'gpt-3.5-turbo'
    yield
    # Clean up
    del os.environ['OPENAI_API_KEY']
    del os.environ['OPENAI_MODEL']

@pytest.fixture(scope="module")
def app() -> Flask:
    """Create test Flask app."""
    flask_app.config['TESTING'] = True
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    return flask_app

@pytest.fixture(scope="module")
def client(app):
    """Create test client."""
    with app.test_client() as client:
        yield client

@pytest.fixture(scope="module")
def engine():
    """Create database engine."""
    engine = create_engine('sqlite:///:memory:', echo=True)
    Base.metadata.create_all(bind=engine)
    return engine

@pytest.fixture(scope="module")
def db_session(engine) -> Session:
    """Create database session."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="module")
def test_db(engine) -> Database:
    """Create test database instance."""
    db = Database()
    db.engine = engine
    db.session_factory = sessionmaker(bind=engine)
    return db

@pytest.fixture(scope="module")
def mock_openai_service():
    """Create mock OpenAI service."""
    mock = Mock()
    mock.generate_response.return_value = "A helpful response about transportation."
    mock.generate_route_fact.return_value = "An interesting fact about the route."
    mock.enhance_route_description.return_value = "A scenic route through historic landmarks."
    return mock

@pytest.fixture(scope="module")
def location_service() -> GoogleMapsService:
    """Create location service."""
    return GoogleMapsService()

@pytest.fixture(scope="module")
def route_planning_service(route_repository, location_service) -> RouteService:
    """Create route planning service."""
    return RoutePlanningService(route_repository=route_repository, location_service=location_service)

@pytest.fixture(scope="module")
def app_with_mocked_services(app, mock_openai_service):
    """App fixture with mocked services."""
    app.config['TESTING'] = True
    app.config['OPENAI_SERVICE'] = mock_openai_service
    return app
