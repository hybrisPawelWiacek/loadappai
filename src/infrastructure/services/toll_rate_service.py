"""Implementation of toll rate service."""
from decimal import Decimal
from typing import Dict, Optional
from functools import lru_cache

from src.domain.interfaces.toll_rate_service import TollRateService
from src.domain.value_objects import CountrySegment


class DefaultTollRateService(TollRateService):
    """Default implementation of toll rate service using static data."""

    def __init__(self):
        # Default toll rates per km by country and vehicle type
        # In a real implementation, this would come from an API or database
        self._toll_rates = {
            "DE": {  # Germany
                "truck": {
                    "highway": Decimal("0.17"),  # €/km for highways
                    "national": Decimal("0.12"),  # €/km for national roads
                },
                "van": {
                    "highway": Decimal("0.11"),
                    "national": Decimal("0.08"),
                },
            },
            "FR": {  # France
                "truck": {
                    "highway": Decimal("0.20"),
                    "national": Decimal("0.15"),
                },
                "van": {
                    "highway": Decimal("0.12"),
                    "national": Decimal("0.09"),
                },
            },
            # Add more countries as needed
        }

    @lru_cache(maxsize=128)
    def get_toll_rates(self, country_code: str, vehicle_type: str) -> Dict[str, Decimal]:
        """Get toll rates for a specific country and vehicle type."""
        country_rates = self._toll_rates.get(country_code, {})
        return country_rates.get(vehicle_type, {})

    def calculate_segment_toll_rates(
        self, segment: CountrySegment, vehicle_type: str
    ) -> Dict[str, Decimal]:
        """Calculate toll rates for a specific country segment."""
        rates = self.get_toll_rates(segment.country_code, vehicle_type)
        
        # Assume 70% of distance is on highways and 30% on national roads
        # In a real implementation, this would be determined by actual route data
        highway_distance = segment.distance * Decimal("0.7")
        national_distance = segment.distance * Decimal("0.3")
        
        return {
            "highway": highway_distance * rates.get("highway", Decimal("0")),
            "national": national_distance * rates.get("national", Decimal("0")),
        }
