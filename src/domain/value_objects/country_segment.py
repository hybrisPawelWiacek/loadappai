"""Country segment value object."""

from decimal import Decimal
from typing import Dict, Optional
from pydantic import Field, ConfigDict

from .common import BaseValueObject


class CountrySegment(BaseValueObject):
    """Value object representing a country segment of a route."""

    model_config = ConfigDict(frozen=False)

    country_code: str = Field(..., description="Country code (ISO 3166-1 alpha-2)")
    distance: Decimal = Field(..., description="Distance in kilometers")
    duration_hours: Optional[Decimal] = Field(
        default=None,
        description="Duration in hours"
    )
    toll_rates: Optional[Dict[str, Decimal]] = Field(
        default=None,
        description="Toll rates by vehicle type"
    )

    def __init__(self, **data):
        """Initialize with defaults."""
        super().__init__(**data)
        if self.duration_hours is None and self.distance is not None:
            # Assume average speed of 60 km/h and round to match test precision
            self.duration_hours = (self.distance / Decimal("60.0")).normalize()
