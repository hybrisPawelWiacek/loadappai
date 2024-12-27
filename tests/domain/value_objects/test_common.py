"""Tests for common value object functionality."""

from typing import Dict, Optional
from pydantic import Field, ValidationError
import pytest

from src.domain.value_objects.common import BaseValueObject


class TestValueObject(BaseValueObject):
    """Test value object for testing BaseValueObject functionality."""
    
    name: str = Field(..., description="Test name")
    value: int = Field(..., description="Test value")
    metadata: Optional[Dict] = Field(None, description="Test metadata")


def test_base_value_object_creation():
    """Test creating a BaseValueObject."""
    obj = TestValueObject(name="test", value=42)
    assert obj.name == "test"
    assert obj.value == 42
    assert obj.metadata is None


def test_base_value_object_immutability():
    """Test that BaseValueObject is immutable."""
    obj = TestValueObject(name="test", value=42)
    
    # Verify that attributes cannot be modified
    with pytest.raises(ValidationError) as exc_info:
        obj.name = "new"  # type: ignore
    
    assert "frozen_instance" in str(exc_info.value)


def test_base_value_object_equality():
    """Test BaseValueObject equality comparison."""
    obj1 = TestValueObject(name="test", value=42)
    obj2 = TestValueObject(name="test", value=42)
    obj3 = TestValueObject(name="different", value=42)
    
    assert obj1 == obj2
    assert obj1 != obj3
    assert obj1 != "not a value object"
    assert obj1 != None  # Test comparison with None


def test_base_value_object_hash():
    """Test that BaseValueObject can be used in sets and as dict keys."""
    obj1 = TestValueObject(name="test", value=42)
    obj2 = TestValueObject(name="test", value=42)
    obj3 = TestValueObject(name="different", value=42)
    
    # Test set operations
    value_set = {obj1, obj2, obj3}
    assert len(value_set) == 2  # obj1 and obj2 are equal
    
    # Test dict operations
    value_dict = {obj1: "value1", obj3: "value3"}
    assert len(value_dict) == 2
    assert value_dict[obj2] == "value1"  # obj2 equals obj1


def test_base_value_object_metadata():
    """Test metadata handling in BaseValueObject."""
    metadata = {"key": "value", "number": 42}
    obj = TestValueObject(name="test", value=42, metadata=metadata)
    
    assert obj.metadata == metadata
    assert obj.metadata["key"] == "value"
    assert obj.metadata["number"] == 42


def test_base_value_object_empty_metadata():
    """Test BaseValueObject with empty metadata."""
    obj = TestValueObject(name="test", value=42, metadata={})
    assert obj.metadata == {}


def test_base_value_object_model_dump():
    """Test model_dump method of BaseValueObject."""
    metadata = {"key": "value"}
    obj = TestValueObject(name="test", value=42, metadata=metadata)
    
    dumped = obj.model_dump()
    assert dumped["name"] == "test"
    assert dumped["value"] == 42
    assert dumped["metadata"] == metadata
