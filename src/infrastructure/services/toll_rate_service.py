"""Implementation of toll rate service."""
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID
from functools import lru_cache

from src.domain.value_objects import CountrySegment
from src.domain.interfaces.services.toll_rate_service import TollRateService, TollRateServiceError


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
        self._rate_history = {}  # Store rate history by region
        self._rate_updates = {}  # Store pending rate updates

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
        if not rates:
            raise TollRateServiceError(
                f"No toll rates found for country {segment.country_code} "
                f"and vehicle type {vehicle_type}"
            )
        return rates

    def calculate_toll(
        self,
        route_id: UUID,
        vehicle_type: str,
        time: Optional[datetime] = None
    ) -> Decimal:
        """Calculate toll for a route."""
        # In a real implementation, we would:
        # 1. Fetch route details from database
        # 2. Calculate toll based on segments and vehicle type
        # 3. Apply time-based adjustments
        # For now, return a dummy value
        return Decimal("50.00")

    def get_current_rates(self, region: str) -> Dict:
        """Get current toll rates for region."""
        if region not in self._toll_rates:
            raise TollRateServiceError(f"No rates found for region {region}")
        return self._toll_rates[region]

    def update_rates(
        self,
        region: str,
        new_rates: Dict,
        effective_date: datetime
    ) -> bool:
        """Update toll rates for region."""
        try:
            # Validate new rates
            if not self.validate_rates(new_rates):
                return False
            
            # Store current rates in history
            if region not in self._rate_history:
                self._rate_history[region] = []
            self._rate_history[region].append({
                'rates': self._toll_rates.get(region, {}),
                'effective_until': effective_date
            })
            
            # Update rates
            self._toll_rates[region] = new_rates
            self._rate_updates[region] = {
                'rates': new_rates,
                'effective_date': effective_date
            }
            
            # Clear cache to ensure new rates are used
            self.get_toll_rates.cache_clear()
            
            return True
        except Exception as e:
            raise TollRateServiceError(f"Failed to update rates: {str(e)}")

    def validate_rates(self, rates: Dict) -> bool:
        """Validate rate configuration."""
        try:
            # Check structure
            for vehicle_type, vehicle_rates in rates.items():
                if not isinstance(vehicle_type, str):
                    return False
                if not isinstance(vehicle_rates, dict):
                    return False
                
                # Check road types and values
                for road_type, rate in vehicle_rates.items():
                    if road_type not in ('highway', 'national'):
                        return False
                    if not isinstance(rate, (Decimal, float, int)):
                        return False
                    if rate < 0:
                        return False
            
            return True
        except Exception:
            return False

    def get_rate_history(
        self,
        region: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict]:
        """Get history of rate changes."""
        if region not in self._rate_history:
            raise TollRateServiceError(f"No rate history found for region {region}")
        
        # Filter history by date range
        history = []
        for entry in self._rate_history[region]:
            if start_date <= entry['effective_until'] <= end_date:
                history.append(entry)
        
        return history
