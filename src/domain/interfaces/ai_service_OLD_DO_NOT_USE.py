"""AI Service interface."""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class AIServiceError(Exception):
    """Base exception for AI service errors."""
    pass


class AIService(ABC):
    """Interface for AI services."""

    @abstractmethod
    def generate_response(self, prompt: str, **kwargs: Dict[str, Any]) -> str:
        """Generate a response from the AI model.

        Args:
            prompt: The input prompt for the AI model.
            **kwargs: Additional arguments to pass to the AI model.

        Returns:
            The generated response as a string.

        Raises:
            AIServiceError: If there is an error generating the response.
        """
        pass
