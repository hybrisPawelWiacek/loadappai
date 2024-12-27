"""Database module."""
from contextlib import contextmanager
from typing import Generator, Optional
from urllib.parse import urlparse

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from src.settings import get_settings

settings = get_settings()

# Get database URL from settings
SQLALCHEMY_DATABASE_URL = settings.database.url

# Configure SQLAlchemy engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=settings.database.echo,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

Base = declarative_base()


class Database:
    """Database connection manager."""

    def __init__(self):
        """Initialize database connection."""
        self.engine = engine
        self.session_factory = SessionLocal

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """Get database session."""
        session = self.session_factory()
        try:
            yield session
        finally:
            session.close()

    def get_engine(self) -> Engine:
        """Get SQLAlchemy engine instance."""
        return self.engine


def get_db() -> Generator[Session, None, None]:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def transaction_context() -> Generator[Session, None, None]:
    """Context manager for database transactions.
    
    Automatically rolls back transaction on error and closes session.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """Initialize database schema."""
    Base.metadata.create_all(bind=engine)


def clear_db() -> None:
    """Clear all data from database.
    
    Warning: This will delete all data! Use only in tests.
    """
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
