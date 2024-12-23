"""OpenAI service implementation."""
from typing import Any, Dict, Optional
import time
import httpx

from openai import OpenAI
from openai.types.chat import ChatCompletion
from openai._exceptions import OpenAIError

from src.domain.interfaces import AIService, AIServiceError
from src.domain.value_objects import Location
from src.domain.entities import Route
from src.config import get_settings
from src.infrastructure.logging import get_logger

logger = get_logger()

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
            # Initialize with a custom httpx client
            http_client = httpx.Client(timeout=30.0)
            self.client = OpenAI(
                api_key=self.api_key,
                http_client=http_client
            )
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
        """Generate an enhanced description of a route with logistics-relevant information.
        
        Args:
            origin: Origin location
            destination: Destination location
            distance_km: Distance of the route in kilometers
            duration_hours: Duration of the route in hours
            context: Optional additional context with keys like:
                    - transport_type: Type of transport being used
                    - cargo_type: Type of cargo being transported
                    - special_requirements: Any special transport requirements
                    
        Returns:
            str: Enhanced route description with logistics insights
            
        Raises:
            AIServiceError: If description generation fails
        """
        system_prompt = (
            "You are a logistics route analyst specializing in freight transport routes. "
            "Provide detailed route descriptions that focus on logistics-relevant information such as:"
            "\n- Major highways and transport corridors"
            "\n- Known traffic patterns or bottlenecks"
            "\n- Rest stops and refueling points"
            "\n- Border crossings if international"
            "\n- Terrain and weather considerations"
            "\nKeep descriptions concise but informative for transport planning."
        )
        
        user_prompt = (
            f"Analyze the transport route from {origin.address} to {destination.address}.\n"
            f"Route metrics:\n"
            f"- Distance: {distance_km:.1f} km\n"
            f"- Duration: {duration_hours:.1f} hours\n"
        )
        
        if context:
            user_prompt += "\nAdditional context:\n"
            for key, value in context.items():
                user_prompt += f"- {key}: {value}\n"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = self._make_request(
                messages,
                temperature=0.7,  # Slightly higher for more varied descriptions
                max_tokens=300,   # Allow longer responses
                presence_penalty=0.6,  # Encourage covering different aspects
                frequency_penalty=0.4   # Reduce repetition
            )
            return response.choices[0].message.content or ""
        except AIServiceError as e:
            raise AIServiceError(f"Failed to enhance route description: {str(e)}")
        except Exception as e:
            raise AIServiceError(f"Unexpected error in route description enhancement: {str(e)}")

    def generate_route_description(self, route: Route) -> str:
        """Generate an enhanced description of the route using AI."""
        ai_logger = logger.bind(service="openai", route_id=str(route.id))
        ai_logger.info("generating_route_description")
        ai_logger.debug("route_data", origin=route.origin, destination=route.destination)
        
        try:
            # Extract location info safely with fallbacks
            origin_addr = route.origin.get('address', route.origin.get('city', 'Unknown Location'))
            dest_addr = route.destination.get('address', route.destination.get('city', 'Unknown Location'))
            
            messages = [
                {"role": "system", "content": "You are a helpful assistant that generates concise route descriptions for a logistics company."},
                {"role": "user", "content": f"Generate a brief, professional description for a transport route from {origin_addr} to {dest_addr}. Distance: {route.distance_km:.1f} km, Duration: {route.duration_hours:.1f} hours"}
            ]
            
            response = self._make_request(messages)
            description = response.choices[0].message.content.strip()
            ai_logger.info("description_generated", length=len(description))
            return description
        except Exception as e:
            ai_logger.error("description_generation_failed", error=str(e))
            raise AIServiceError(f"Failed to generate route description: {str(e)}")

    def generate_fun_fact(self, route: Route) -> str:
        """Generate an interesting fact about the route using AI."""
        ai_logger = logger.bind(service="openai", route_id=str(route.id))
        ai_logger.info("generating_fun_fact")
        ai_logger.debug("route_data", origin=route.origin, destination=route.destination)
        
        try:
            # Extract location info safely with fallbacks
            origin_city = route.origin.get('city', route.origin.get('address', 'Unknown City'))
            origin_country = route.origin.get('country', 'Unknown Country')
            dest_city = route.destination.get('city', route.destination.get('address', 'Unknown City'))
            dest_country = route.destination.get('country', 'Unknown Country')
            
            messages = [
                {"role": "system", "content": "You are a helpful assistant that generates interesting facts about transport routes."},
                {"role": "user", "content": f"Generate a brief, interesting fact about a transport route from {origin_city}, {origin_country} to {dest_city}, {dest_country}. Make it relevant to logistics or transportation."}
            ]
            
            response = self._make_request(messages)
            fun_fact = response.choices[0].message.content.strip()
            ai_logger.info("fun_fact_generated", length=len(fun_fact))
            return fun_fact
        except Exception as e:
            ai_logger.error("fun_fact_generation_failed", error=str(e))
            raise AIServiceError(f"Failed to generate fun fact: {str(e)}")
