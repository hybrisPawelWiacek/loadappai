"""OpenAI service implementation."""
from typing import Any, Dict, Optional

from openai import OpenAI
from openai.types.chat import ChatCompletion
from openai._exceptions import OpenAIError

from src.domain.interfaces import AIService, AIServiceError
from src.domain.value_objects import Location
from src.config import get_settings
import time


class OpenAIService(AIService):
    """OpenAI API implementation of AIService."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize OpenAI service.
        
        Args:
            api_key: Optional API key (defaults to settings.OPENAI_API_KEY)
            
        Raises:
            AIServiceError: If API key is not found in settings or environment
        """
        settings = get_settings()
        self.api_key = api_key or settings.OPENAI_API_KEY
        if not self.api_key:
            raise AIServiceError("OpenAI API key not found in settings or environment")
        
        self.model = settings.OPENAI_MODEL
        self.max_retries = settings.OPENAI_MAX_RETRIES
        self.retry_delay = settings.OPENAI_RETRY_DELAY
        
        try:
            self.client = OpenAI(api_key=self.api_key)
        except Exception as e:
            raise AIServiceError(f"Failed to initialize OpenAI client: {str(e)}")

    def _make_request(self, messages: list[Dict[str, str]], **kwargs: Dict[str, Any]) -> ChatCompletion:
        """Make a request to OpenAI API with retry logic.
        
        Args:
            messages: List of message dictionaries
            **kwargs: Additional arguments for the API call
            
        Returns:
            ChatCompletion: API response
            
        Raises:
            AIServiceError: If request fails after retries
        """
        for attempt in range(self.max_retries):
            try:
                return self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    **kwargs
                )
            except OpenAIError as e:
                if attempt == self.max_retries - 1:
                    raise AIServiceError(f"OpenAI API error after {self.max_retries} retries: {str(e)}")
                time.sleep(self.retry_delay * (attempt + 1))
            except Exception as e:
                raise AIServiceError(f"Unexpected error in OpenAI request: {str(e)}")

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
        messages = [
            {"role": "system", "content": "You are a helpful assistant that provides informative and engaging responses about transportation routes."},
            {"role": "user", "content": prompt}
        ]
        try:
            response = self._make_request(messages, **kwargs)
            return response.choices[0].message.content or ""
        except AIServiceError as e:
            raise AIServiceError(f"Failed to generate response: {str(e)}")
        except Exception as e:
            raise AIServiceError(f"Unexpected error in response generation: {str(e)}")

    def generate_route_fact(self, origin: Location, destination: Location, context: Optional[Dict] = None) -> str:
        """Generate an interesting fact about a route.
        
        Args:
            origin: Origin location
            destination: Destination location
            context: Optional additional context
            
        Returns:
            str: An interesting fact about the route
            
        Raises:
            AIServiceError: If fact generation fails
        """
        prompt = (
            f"Generate a brief, interesting fact about a route from {origin.address} "
            f"to {destination.address}"
        )
        if context:
            prompt += f" considering: {context}"
        return self.generate_response(prompt, temperature=0.7, max_tokens=100)

    def enhance_route_description(self, origin: Location, destination: Location, distance_km: float, duration_hours: float, context: Optional[Dict] = None) -> str:
        """Generate an enhanced description of a route.
        
        Args:
            origin: Origin location
            destination: Destination location
            distance_km: Distance of the route in kilometers
            duration_hours: Duration of the route in hours
            context: Optional additional context
            
        Returns:
            str: Enhanced route description
            
        Raises:
            AIServiceError: If description generation fails
        """
        prompt = (
            f"Describe the transport route from {origin.address} to {destination.address} "
            f"with a distance of {distance_km:.1f} km and a duration of {duration_hours:.1f} hours, "
            "highlighting key points of interest and transport considerations."
        )
        if context:
            prompt += f"\nAdditional context: {context}"
        return self.generate_response(prompt, temperature=0.5, max_tokens=200)
