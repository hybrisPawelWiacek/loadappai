"""Common base classes and utilities for value objects."""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict


class BaseValueObject(BaseModel):
    """Base class for all value objects in the domain.
    
    Provides common functionality and configuration for all value objects.
    """
    
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata for extensibility"
    )
    
    model_config = ConfigDict(
        frozen=True,  # Default to immutable
        arbitrary_types_allowed=True,
        populate_by_name=True,
        validate_assignment=True,
        use_enum_values=True,
        from_attributes=True,
    )
    
    def __eq__(self, other: Any) -> bool:
        """Compare value objects based on their attribute values."""
        if not isinstance(other, self.__class__):
            return False
        return self.model_dump() == other.model_dump()
    
    def __hash__(self) -> int:
        """Hash value objects based on their frozen state."""
        return hash(tuple(sorted(self.model_dump().items())))
