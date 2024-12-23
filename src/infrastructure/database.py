"""Database configuration and session management."""
import os
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

# Get database URL from environment variable or use default SQLite URL
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", "sqlite:///./loadapp.db"
)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # Needed for SQLite
    pool_pre_ping=True,  # Enable connection health checks
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


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def transaction_context() -> Generator[Session, None, None]:
    """Context manager for database transactions."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    """Initialize database schema."""
    Base.metadata.create_all(bind=engine)


def clear_db() -> None:
    """Clear all data from database."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
