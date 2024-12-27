"""Location-related value objects."""

from typing import Dict, List, Optional
from pydantic import Field, confloat, field_validator

from .common import BaseValueObject


class Address(BaseValueObject):
    """Address value object."""

    street: str = Field(..., description="Street name and number")
    city: str = Field(..., description="City name")
    postal_code: str = Field(..., description="Postal code")
    country: str = Field(..., description="Country code (ISO 3166-1 alpha-2)")
    state: Optional[str] = Field(None, description="State or region")
    formatted: Optional[str] = Field(None, description="Formatted address string")


class Location(BaseValueObject):
    """Location value object with address and coordinates."""

    address: str = Field(..., description="Full address of the location")
    latitude: confloat(ge=-90, le=90) = Field(
        ..., description="Latitude in decimal degrees"
    )
    longitude: confloat(ge=-180, le=180) = Field(
        ..., description="Longitude in decimal degrees"
    )
    country: str = Field(default="Unknown")

    @field_validator("latitude")
    def validate_latitude(cls, v: float) -> float:
        """Validate latitude."""
        if not -90 <= v <= 90:
            raise ValueError("Latitude must be between -90 and 90 degrees")
        return v

    @field_validator("longitude")
    def validate_longitude(cls, v: float) -> float:
        """Validate longitude."""
        if not -180 <= v <= 180:
            raise ValueError("Longitude must be between -180 and 180 degrees")
        return v


class DistanceMatrix(BaseValueObject):
    """Value object representing a distance matrix between locations."""

    origins: List[Location]
    destinations: List[Location]
    distances: List[List[float]] = Field(description="Matrix of distances in kilometers")
    durations: List[List[float]] = Field(description="Matrix of durations in hours")
    countries: List[List[str]] = Field(description="Matrix of country codes for each segment")
    status: str = Field(default="OK")
    error_message: Optional[str] = None

    @field_validator("distances")
    def validate_distances(cls, v: List[List[float]], info: Dict) -> List[List[float]]:
        """Validate distances matrix dimensions."""
        origins = len(info.data.get("origins", []))
        destinations = len(info.data.get("destinations", []))
        if len(v) != origins or any(len(row) != destinations for row in v):
            raise ValueError(
                f"Distances matrix must be {origins}x{destinations}"
            )
        return v

    @field_validator("durations")
    def validate_durations(cls, v: List[List[float]], info: Dict) -> List[List[float]]:
        """Validate durations matrix dimensions."""
        origins = len(info.data.get("origins", []))
        destinations = len(info.data.get("destinations", []))
        if len(v) != origins or any(len(row) != destinations for row in v):
            raise ValueError(
                f"Durations matrix must be {origins}x{destinations}"
            )
        return v

    @field_validator("countries")
    def validate_countries(cls, v: List[List[str]], info: Dict) -> List[List[str]]:
        """Validate countries matrix dimensions."""
        origins = len(info.data.get("origins", []))
        destinations = len(info.data.get("destinations", []))
        if len(v) != origins or any(len(row) != destinations for row in v):
            raise ValueError(
                f"Countries matrix must be {origins}x{destinations}"
            )
        return v

    def get_distance(self, origin_idx: int, destination_idx: int) -> float:
        """Get distance between origin and destination indices."""
        return self.distances[origin_idx][destination_idx]

    def get_duration(self, origin_idx: int, destination_idx: int) -> float:
        """Get duration between origin and destination indices."""
        return self.durations[origin_idx][destination_idx]

    def get_country(self, origin_idx: int, destination_idx: int) -> str:
        """Get country code for route between origin and destination indices."""
        return self.countries[origin_idx][destination_idx]
