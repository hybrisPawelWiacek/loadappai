"""Test fixtures for infrastructure tests."""
import os
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.infrastructure.config import Settings
from src.infrastructure.database import Base


@pytest.fixture(scope="session", autouse=True)
def test_settings():
    """Create test settings."""
    test_settings = Settings(
        DATABASE_URL="sqlite:///:memory:",
        SQL_ECHO=False,
        GOOGLE_MAPS_API_KEY="test_google_maps_key",
        OPENAI_API_KEY="test_openai_key",
        WEATHER_ENABLED=False,
        TRAFFIC_ENABLED=False,
        MARKET_DATA_ENABLED=False,
        BACKEND_HOST="localhost",
        BACKEND_PORT=5000,
        DEFAULT_FUEL_PRICE=1.50,
        DEFAULT_DRIVER_SALARY=138.0,
        DEFAULT_TOLL_RATES={"DE": 0.10, "FR": 0.12},
    )
    with patch("src.infrastructure.config.settings", test_settings):
        yield test_settings


@pytest.fixture(scope="session")
def engine():
    """Create a test database engine."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return engine


@pytest.fixture(scope="session")
def tables(engine):
    """Create all tables for testing."""
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session(engine, tables):
    """Create a new database session for a test."""
    connection = engine.connect()
    # Begin a non-ORM transaction
    transaction = connection.begin()
    # Bind an individual Session to the connection
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    # Rollback the transaction and close the session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(autouse=True)
def cleanup_tables(db_session):
    """Clean up tables after each test."""
    yield
    for table in reversed(Base.metadata.sorted_tables):
        db_session.execute(table.delete())
