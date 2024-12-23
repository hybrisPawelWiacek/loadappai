"""Base repository interfaces."""
from abc import ABC, abstractmethod
from typing import Generic, List, Optional, TypeVar

from sqlalchemy.orm import Session
from src.infrastructure.database import Database

T = TypeVar("T")


class Repository(ABC, Generic[T]):
    """Base repository interface."""

    def __init__(self, db: Database):
        """Initialize repository with database."""
        self.db = db

    @abstractmethod
    def create(self, entity: T) -> T:
        """Create a new entity."""
        pass

    @abstractmethod
    def get(self, id: str) -> Optional[T]:
        """Get entity by ID."""
        pass

    @abstractmethod
    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all entities with pagination."""
        pass

    @abstractmethod
    def update(self, id: str, entity: T) -> Optional[T]:
        """Update an entity."""
        pass

    @abstractmethod
    def delete(self, id: str) -> bool:
        """Delete an entity."""
        pass
