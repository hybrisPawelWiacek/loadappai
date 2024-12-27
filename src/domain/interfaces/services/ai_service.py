"""AI Service interface.

This module defines the interface for AI-powered services in the application.
The AIService interface provides methods for:
- Natural language processing of user input
- Route optimization suggestions
- Cost estimation assistance
- Offer generation support

Implementation Requirements:
1. Error Handling:
   - Must handle API failures gracefully
   - Should implement retries for transient failures
   - Must provide clear error messages via AIServiceError

2. Rate Limiting:
   - Must respect API rate limits
   - Should implement backoff strategies
   - Must handle quota exhaustion

3. Input Validation:
   - Must sanitize all inputs before API calls
   - Should validate prompt length and content
   - Must handle malformed responses

4. Response Processing:
   - Must validate AI responses
   - Should handle partial or incomplete responses
   - Must format responses consistently

Example Usage:
    ```python
    try:
        # Get route optimization suggestions
        suggestions = ai_service.get_route_suggestions(
            origin="Berlin",
            destination="Paris",
            constraints={"avoid_tolls": True}
        )
        
        # Generate offer description
        description = ai_service.generate_offer_description(
            route=route,
            costs=costs,
            style="professional"
        )
    except AIServiceError as e:
        logger.error(f"AI service error: {str(e)}")
    ```
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional

from src.domain.value_objects import Location
from src.domain.interfaces.exceptions.service_errors import AIServiceError

class AIService(ABC):
    """Interface for AI-powered services."""

    @abstractmethod
    def generate_route_fact(self, 
            origin: Location, 
            destination: Location, 
            context: Optional[Dict] = None
        ) -> str:
        """Generate an interesting fact about a route.
        
        Args:
            origin: Starting location
            destination: End location
            context: Optional additional context about the route
            
        Returns:
            str: An interesting fact about the route
            
        Raises:
            AIServiceError: If fact generation fails
        """
        pass

    @abstractmethod
    def enhance_route_description(self,
            origin: Location,
            destination: Location,
            distance_km: float,
            duration_hours: float,
            context: Optional[Dict] = None
        ) -> str:
        """Generate an enhanced description of a route.
        
        Args:
            origin: Starting location
            destination: End location
            distance_km: Route distance in kilometers
            duration_hours: Route duration in hours
            context: Optional additional context
            
        Returns:
            str: Enhanced route description
            
        Raises:
            AIServiceError: If description generation fails
        """
        pass
