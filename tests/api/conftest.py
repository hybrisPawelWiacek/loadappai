"""Test fixtures for API tests."""
import pytest
from src.api.app import create_app
from src.infrastructure.database import init_db, get_db, clear_db

@pytest.fixture(scope="session")
def app():
    """Create a Flask test app."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    # Initialize database
    with app.app_context():
        init_db()
    
    yield app
    
    # Cleanup after all tests
    with app.app_context():
        clear_db()

@pytest.fixture(scope="session")
def client(app):
    """Create a test client."""
    return app.test_client()

@pytest.fixture(scope="function")
def db_session(app):
    """Create a database session."""
    with app.app_context():
        with get_db() as db:
            db.begin_nested()  # Start a SAVEPOINT
            yield db
            db.rollback()  # Rollback to the SAVEPOINT
