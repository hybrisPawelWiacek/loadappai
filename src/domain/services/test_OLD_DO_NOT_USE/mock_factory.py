"""Mock factory service implementation.

This module implements mock object creation.
It provides:
- Mock object creation
- Mock configuration
- Mock verification
- Mock recording
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Type, Union
import inspect
import uuid

from src.domain.services.common.base import BaseService

class MockFactory(BaseService):
    """Service for creating mock objects.
    
    This service is responsible for:
    - Creating mock objects
    - Configuring mocks
    - Verifying mock calls
    - Recording mock usage
    """
    
    def __init__(
        self,
        strict: bool = True,
        record_calls: bool = True
    ):
        """Initialize mock factory.
        
        Args:
            strict: If True, verify all expected calls
            record_calls: If True, record all calls
        """
        super().__init__()
        self._strict = strict
        self._record_calls = record_calls
        self._mocks: Dict[str, 'MockObject'] = {}
        self._recordings: Dict[str, List[Dict]] = {}
    
    def create(
        self,
        class_type: Type,
        **kwargs
    ) -> 'MockObject':
        """Create mock object.
        
        Args:
            class_type: Class to mock
            **kwargs: Mock attributes
            
        Returns:
            Mock object
            
        Raises:
            ValueError: If mock creation fails
        """
        self._log_entry(
            "create",
            class_type=class_type.__name__
        )
        
        try:
            # Create mock object
            mock = MockObject(
                class_type,
                self,
                strict=self._strict,
                **kwargs
            )
            
            # Store mock
            mock_id = str(uuid.uuid4())
            self._mocks[mock_id] = mock
            
            if self._record_calls:
                self._recordings[mock_id] = []
            
            return mock
            
        except Exception as e:
            self._log_error("create", e)
            raise ValueError(f"Failed to create mock: {str(e)}")
    
    def verify(self) -> None:
        """Verify all mock expectations.
        
        Raises:
            AssertionError: If expectations not met
        """
        self._log_entry("verify")
        
        try:
            for mock in self._mocks.values():
                mock.verify()
                
        except AssertionError as e:
            self._log_error("verify", e)
            raise
    
    def reset(self) -> None:
        """Reset all mocks."""
        self._log_entry("reset")
        
        self._mocks.clear()
        self._recordings.clear()
    
    def record_call(
        self,
        mock_id: str,
        method: str,
        args: tuple,
        kwargs: dict,
        result: Any
    ) -> None:
        """Record mock method call.
        
        Args:
            mock_id: Mock identifier
            method: Method name
            args: Method arguments
            kwargs: Method keyword arguments
            result: Method result
        """
        if not self._record_calls:
            return
        
        self._recordings.setdefault(mock_id, []).append({
            "method": method,
            "args": args,
            "kwargs": kwargs,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def get_recordings(
        self,
        mock_id: Optional[str] = None
    ) -> Dict[str, List[Dict]]:
        """Get recorded mock calls.
        
        Args:
            mock_id: Optional mock identifier
            
        Returns:
            Recorded calls
        """
        if mock_id:
            return {
                mock_id: self._recordings.get(mock_id, [])
            }
        return self._recordings

class MockObject:
    """Mock object implementation."""
    
    def __init__(
        self,
        class_type: Type,
        factory: MockFactory,
        strict: bool = True,
        **kwargs
    ):
        """Initialize mock object.
        
        Args:
            class_type: Class being mocked
            factory: Parent factory
            strict: If True, verify all expected calls
            **kwargs: Mock attributes
        """
        self._class_type = class_type
        self._factory = factory
        self._strict = strict
        self._id = str(uuid.uuid4())
        
        # Mock configuration
        self._returns: Dict[str, Any] = {}
        self._raises: Dict[str, Exception] = {}
        self._calls: Dict[str, List[tuple]] = {}
        self._expected: Dict[str, int] = {}
        
        # Set attributes
        for name, value in kwargs.items():
            setattr(self, name, value)
        
        # Create mock methods
        self._create_methods()
    
    def _create_methods(self) -> None:
        """Create mock methods from class."""
        for name, member in inspect.getmembers(self._class_type):
            if not name.startswith('_') and callable(member):
                setattr(self, name, self._create_method(name))
    
    def _create_method(self, name: str) -> callable:
        """Create mock method.
        
        Args:
            name: Method name
            
        Returns:
            Mock method
        """
        def mock_method(*args, **kwargs):
            # Record call
            self._calls.setdefault(name, []).append(
                (args, kwargs)
            )
            
            # Check if should raise
            if name in self._raises:
                raise self._raises[name]
            
            # Get return value
            result = self._returns.get(
                name,
                MockObject(object, self._factory)
            )
            
            # Record in factory
            self._factory.record_call(
                self._id,
                name,
                args,
                kwargs,
                result
            )
            
            return result
            
        return mock_method
    
    def expect(
        self,
        method: str,
        times: int = 1
    ) -> 'MockObject':
        """Set method call expectation.
        
        Args:
            method: Method name
            times: Expected call count
            
        Returns:
            Self for chaining
        """
        self._expected[method] = times
        return self
    
    def returns(
        self,
        method: str,
        value: Any
    ) -> 'MockObject':
        """Set method return value.
        
        Args:
            method: Method name
            value: Return value
            
        Returns:
            Self for chaining
        """
        self._returns[method] = value
        return self
    
    def raises(
        self,
        method: str,
        exception: Exception
    ) -> 'MockObject':
        """Set method to raise exception.
        
        Args:
            method: Method name
            exception: Exception to raise
            
        Returns:
            Self for chaining
        """
        self._raises[method] = exception
        return self
    
    def verify(self) -> None:
        """Verify mock expectations.
        
        Raises:
            AssertionError: If expectations not met
        """
        if not self._strict:
            return
            
        for method, expected in self._expected.items():
            actual = len(self._calls.get(method, []))
            
            assert actual == expected, (
                f"Expected {expected} calls to {method}, "
                f"got {actual}"
            )
    
    def reset(self) -> None:
        """Reset mock state."""
        self._returns.clear()
        self._raises.clear()
        self._calls.clear()
        self._expected.clear()
    
    def get_calls(
        self,
        method: Optional[str] = None
    ) -> Dict[str, List[tuple]]:
        """Get recorded method calls.
        
        Args:
            method: Optional method name
            
        Returns:
            Recorded calls
        """
        if method:
            return {
                method: self._calls.get(method, [])
            }
        return self._calls
