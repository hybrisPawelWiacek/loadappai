"""Toll rate repository interface."""
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID

from src.domain.interfaces.repositories.base import Repository


class TollRateRepository(Repository, ABC):
    """Interface for toll rate data persistence."""

    @abstractmethod
    def get_rate(self, country: str, vehicle_type: str) -> Optional[Decimal]:
        """Get toll rate for a country and vehicle type."""
        pass

    @abstractmethod
    def get_rates_by_country(self, country: str) -> Dict[str, Decimal]:
        """Get all toll rates for a country."""
        pass

    @abstractmethod
    def get_countries(self) -> List[str]:
        """Get list of countries with toll rates."""
        pass

    @abstractmethod
    def get_vehicle_types(self) -> List[str]:
        """Get list of supported vehicle types."""
        pass

    @abstractmethod
    def get_metadata(self, rate_id: UUID) -> Dict[str, Any]:
        """Get metadata for a toll rate."""
        pass
