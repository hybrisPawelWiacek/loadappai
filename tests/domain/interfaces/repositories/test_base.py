"""Tests for base repository interface."""
import pytest
from uuid import UUID
from typing import Optional, List, Dict

from src.domain.interfaces.repositories.base import Repository
from src.domain.interfaces.exceptions.repository_errors import EntityNotFoundError, ValidationError

class DummyEntity:
    """Dummy entity for testing."""
    def __init__(self, id: UUID, name: str):
        self.id = id
        self.name = name

class TestRepository(Repository[DummyEntity]):
    """Test implementation of Repository interface."""
    
    def __init__(self):
        self.storage: Dict[str, DummyEntity] = {}
    
    def create(self, entity: DummyEntity) -> DummyEntity:
        """Create a new entity."""
        self.storage[str(entity.id)] = entity
        return entity
    
    def get(self, id: UUID) -> Optional[DummyEntity]:
        """Get entity by ID."""
        return self.storage.get(str(id))
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[DummyEntity]:
        """Get all entities with pagination."""
        items = list(self.storage.values())
        return items[skip:skip + limit]
    
    def update(self, id: UUID, entity: DummyEntity) -> Optional[DummyEntity]:
        """Update an entity."""
        if str(id) not in self.storage:
            return None
        self.storage[str(id)] = entity
        return entity
    
    def delete(self, id: UUID) -> bool:
        """Delete an entity."""
        if str(id) not in self.storage:
            return False
        del self.storage[str(id)]
        return True
        
    def count(self) -> int:
        """Get total number of entities."""
        return len(self.storage)

@pytest.fixture
def repository():
    """Create test repository."""
    return TestRepository()

def test_repository_create(repository):
    """Test creating an entity."""
    entity = DummyEntity(UUID('00000000-0000-0000-0000-000000000000'), 'test')
    created = repository.create(entity)
    assert created.id == entity.id
    assert created.name == entity.name

def test_repository_get(repository):
    """Test getting an entity."""
    entity = DummyEntity(UUID('00000000-0000-0000-0000-000000000000'), 'test')
    created = repository.create(entity)
    
    retrieved = repository.get(entity.id)
    assert retrieved is not None
    assert retrieved.id == entity.id
    assert retrieved.name == entity.name
    
    # Test getting non-existent entity
    assert repository.get(UUID('00000000-0000-0000-0000-000000000001')) is None

def test_repository_get_all(repository):
    """Test getting all entities."""
    entities = [
        DummyEntity(UUID('00000000-0000-0000-0000-000000000001'), 'test1'),
        DummyEntity(UUID('00000000-0000-0000-0000-000000000002'), 'test2'),
        DummyEntity(UUID('00000000-0000-0000-0000-000000000003'), 'test3')
    ]
    
    for entity in entities:
        repository.create(entity)
    
    # Test without pagination
    all_entities = repository.get_all()
    assert len(all_entities) == 3
    
    # Test with pagination
    paginated = repository.get_all(skip=1, limit=1)
    assert len(paginated) == 1
    assert paginated[0].name == 'test2'

def test_repository_update(repository):
    """Test updating an entity."""
    entity = DummyEntity(UUID('00000000-0000-0000-0000-000000000000'), 'test')
    created = repository.create(entity)
    
    # Update entity
    updated_entity = DummyEntity(entity.id, 'updated')
    updated = repository.update(entity.id, updated_entity)
    assert updated is not None
    assert updated.id == entity.id
    assert updated.name == 'updated'
    
    # Test updating non-existent entity
    assert repository.update(UUID('00000000-0000-0000-0000-000000000001'), updated_entity) is None

def test_repository_delete(repository):
    """Test deleting an entity."""
    entity = DummyEntity(UUID('00000000-0000-0000-0000-000000000000'), 'test')
    created = repository.create(entity)
    
    # Delete entity
    assert repository.delete(entity.id) is True
    assert repository.get(entity.id) is None
    
    # Test deleting non-existent entity
    assert repository.delete(UUID('00000000-0000-0000-0000-000000000001')) is False

def test_repository_count(repository):
    """Test counting entities."""
    assert repository.count() == 0
    
    entities = [
        DummyEntity(UUID('00000000-0000-0000-0000-000000000001'), 'test1'),
        DummyEntity(UUID('00000000-0000-0000-0000-000000000002'), 'test2'),
        DummyEntity(UUID('00000000-0000-0000-0000-000000000003'), 'test3')
    ]
    
    for entity in entities:
        repository.create(entity)
        
    assert repository.count() == 3
    
    repository.delete(entities[0].id)
    assert repository.count() == 2
