"""Domain interfaces package."""
from src.domain.interfaces.ai_service import AIService, AIServiceError
from src.domain.interfaces.location_service import LocationService, LocationServiceError

__all__ = ['LocationService', 'LocationServiceError', 'AIService', 'AIServiceError']
