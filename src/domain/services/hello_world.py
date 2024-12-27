"""Hello world service implementation."""

from src.domain.services.common.base import BaseService


class HelloWorldService(BaseService):
    """Simple service for testing and demonstration purposes."""

    def __init__(self):
        """Initialize hello world service."""
        super().__init__()

    def get_greeting(self, name: str = "World") -> str:
        """Get a greeting message.
        
        Args:
            name: Name to greet (defaults to "World")
            
        Returns:
            Greeting message
        """
        return f"Hello, {name}!"

    def get_status(self) -> dict:
        """Get service status.
        
        Returns:
            Service status information
        """
        return {
            "status": "healthy",
            "version": "1.0.0",
            "service": "HelloWorldService"
        }
