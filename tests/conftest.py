"""Test fixtures for all tests."""
import pytest
from flask import Flask
from sqlalchemy.orm import Session

from src.api.app import app as flask_app
from src.domain.services import RoutePlanningService
from src.infrastructure.repositories.route_repository import RouteRepository
from src.infrastructure.services.google_maps_service import GoogleMapsService


@pytest.fixture
def app() -> Flask:
    """Create test Flask app."""
    flask_app.config['TESTING'] = True
    return flask_app


@pytest.fixture
def client(app):
    """Create test client."""
    with app.test_client() as client:
        yield client


@pytest.fixture
def db_session(engine, tables) -> Session:
    """Create database session."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def location_service() -> GoogleMapsService:
    """Create location service."""
    return GoogleMapsService()


@pytest.fixture
def route_planning_service(location_service) -> RoutePlanningService:
    """Create route planning service."""
    return RoutePlanningService(location_service=location_service)


@pytest.fixture
def route_repository(db_session) -> RouteRepository:
    """Create route repository."""
    return RouteRepository(db=db_session)
