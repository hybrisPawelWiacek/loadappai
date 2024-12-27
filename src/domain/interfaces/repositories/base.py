"""Base repository interface.

This module defines the base interface for all repository implementations.
The Repository interface provides common CRUD operations that all
repositories must implement.

Implementation Requirements:
1. Entity Management:
   - Must handle entity lifecycle
   - Should validate entities
   - Must generate IDs
   - Should handle versioning

2. Error Handling:
   - Must raise appropriate exceptions
   - Should provide clear messages
   - Must handle not found cases
   - Should handle duplicates

3. Persistence:
   - Must ensure data consistency
   - Should handle transactions
   - Must prevent data loss
   - Should optimize performance

4. Validation:
   - Must validate all inputs
   - Should check constraints
   - Must verify references
   - Should maintain integrity

Example Usage:
    ```python
    # Create new entity
    entity = repository.create(new_entity)
    
    # Retrieve entity
    entity = repository.get(entity_id)
    
    # Update entity
    updated = repository.update(modified_entity)
    
    # Delete entity
    repository.delete(entity_id)
    ```
"""
from abc import ABC, abstractmethod
from typing import Generic, List, Optional, TypeVar
from uuid import UUID

from src.domain.interfaces.exceptions.repository_errors import EntityNotFoundError, ValidationError

T = TypeVar('T')

class Repository(Generic[T], ABC):
    """Generic base interface for repositories.
    
    This interface defines the basic CRUD operations that all repositories
    must implement. It uses a generic type parameter T to represent the
    entity type being managed.
    
    Type Parameters:
        T: The entity type this repository manages
    """

    @abstractmethod
    def create(self, entity: T) -> T:
        """Create a new entity.
        
        Args:
            entity: Entity to create
            
        Returns:
            Created entity with ID
            
        Raises:
            ValidationError: If entity validation fails
            
        Implementation Notes:
            - Must generate unique ID
            - Should validate entity
            - Must handle duplicates
            - Should set timestamps
        """
        pass

    @abstractmethod
    def get(self, id: UUID) -> Optional[T]:
        """Get entity by ID.
        
        Args:
            id: Entity ID
            
        Returns:
            Entity if found, None otherwise
            
        Raises:
            EntityNotFoundError: If entity does not exist
            
        Implementation Notes:
            - Must handle not found case
            - Should cache common queries
            - Must verify ID format
            - Should load relationships
        """
        pass

    @abstractmethod
    def update(self, id: UUID, entity: T) -> Optional[T]:
        """Update an existing entity.
        
        Args:
            id: Entity ID
            entity: Entity to update
            
        Returns:
            Updated entity
            
        Raises:
            EntityNotFoundError: If entity does not exist
            ValidationError: If entity validation fails
            
        Implementation Notes:
            - Must verify entity exists
            - Should validate changes
            - Must handle concurrency
            - Should track modifications
        """
        pass

    @abstractmethod
    def delete(self, id: UUID) -> bool:
        """Delete an entity.
        
        Args:
            id: ID of entity to delete
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            EntityNotFoundError: If entity does not exist
            
        Implementation Notes:
            - Must handle cascading
            - Should backup data
            - Must verify references
            - Should track deletions
        """
        pass

    @abstractmethod
    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all entities with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of entities
            
        Implementation Notes:
            - Must implement pagination
            - Should optimize query
            - Must handle empty results
            - Should cache results
        """
        pass

    @abstractmethod
    def count(self) -> int:
        """Get total number of entities.
        
        Returns:
            Total count of entities
            
        Implementation Notes:
            - Must be efficient
            - Should cache result
            - Must be accurate
            - Should handle large sets
        """
        pass
