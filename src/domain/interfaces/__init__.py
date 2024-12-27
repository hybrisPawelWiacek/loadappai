"""Domain interfaces package."""

# Service interfaces
from src.domain.interfaces.services.route_service import RouteService
from src.domain.interfaces.services.cost_service import CostService
from src.domain.interfaces.services.offer_service import OfferService
from src.domain.interfaces.services.cost_settings_service import CostSettingsService, CostSettingsServiceError
from src.domain.interfaces.services.location_service import LocationService
from src.domain.interfaces.services.toll_rate_service import TollRateService
from src.domain.interfaces.services.ai_service import AIService

# Repository interfaces
from src.domain.interfaces.repositories.base import Repository
from src.domain.interfaces.repositories.route_repository import RouteRepository
from src.domain.interfaces.repositories.cost_repository import CostRepository
from src.domain.interfaces.repositories.offer_repository import OfferRepository
from src.domain.interfaces.repositories.cost_settings_repository import CostSettingsRepository
from src.domain.interfaces.repositories.location_repository import LocationRepository
from src.domain.interfaces.repositories.toll_rate_repository import TollRateRepository

# Exception interfaces
from src.domain.interfaces.exceptions.repository_errors import (
    EntityNotFoundError,
    ValidationError,
    UniqueConstraintError,
    RepositoryError,
)
from src.domain.interfaces.exceptions.service_errors import (
    ServiceError,
    LocationServiceError,
    AIServiceError,
    CostServiceError,
    OfferServiceError,
)

__all__ = [
    # Services
    'RouteService',
    'CostService',
    'OfferService',
    'CostSettingsService',
    'LocationService',
    'TollRateService',
    'AIService',
    'CostSettingsServiceError',

    # Repositories
    'Repository',
    'RouteRepository',
    'CostRepository',
    'OfferRepository',
    'CostSettingsRepository',
    'LocationRepository',
    'TollRateRepository',

    # Exceptions
    'EntityNotFoundError',
    'ValidationError',
    'UniqueConstraintError',
    'RepositoryError',
    'ServiceError',
    'LocationServiceError',
    'AIServiceError',
    'CostServiceError',
    'OfferServiceError',
]
