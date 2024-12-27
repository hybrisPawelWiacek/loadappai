"""Interface for toll rate services."""
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, Optional

from src.domain.value_objects import CountrySegment


class TollRateService(ABC):
    """Service interface for retrieving toll rates."""

    @abstractmethod
    def get_toll_rates(self, country_code: str, vehicle_type: str) -> Dict[str, Decimal]:
        """
        Get toll rates for a specific country and vehicle type.

        Args:
            country_code: ISO country code
            vehicle_type: Type of vehicle (e.g., 'truck', 'van')

        Returns:
            Dictionary mapping toll categories to rates
        """
        pass

    @abstractmethod
    def calculate_segment_toll_rates(
        self, segment: CountrySegment, vehicle_type: str
    ) -> Dict[str, Decimal]:
        """
        Calculate toll rates for a specific country segment.

        Args:
            segment: Country segment containing route information
            vehicle_type: Type of vehicle

        Returns:
            Dictionary mapping toll categories to calculated rates
        """
        pass
