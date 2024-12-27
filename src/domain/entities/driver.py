"""Driver domain entity."""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, EmailStr, Field, constr, validator
from pytz import UTC

from src.domain.utils.datetime import utc_now


class Driver(BaseModel):
    """Driver entity representing a vehicle operator."""

    id: UUID = Field(default_factory=uuid4)
    first_name: constr(min_length=1, max_length=50)
    last_name: constr(min_length=1, max_length=50)
    license_number: constr(min_length=5, max_length=50)
    license_type: constr(min_length=1, max_length=20)
    license_expiry: datetime
    contact_number: constr(min_length=5, max_length=20)
    email: Optional[EmailStr] = None
    years_experience: int = Field(ge=0)
    is_active: bool = True
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @validator('license_expiry', 'created_at', 'updated_at')
    def ensure_timezone(cls, v):
        """Ensure datetime fields have timezone information."""
        if v.tzinfo is None:
            return v.replace(tzinfo=UTC)
        return v

    def update(self, **kwargs) -> None:
        """Update driver attributes."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = utc_now()

    @property
    def full_name(self) -> str:
        """Get driver's full name."""
        return f"{self.first_name} {self.last_name}"

    @property
    def is_license_valid(self) -> bool:
        """Check if driver's license is valid."""
        return self.license_expiry > utc_now()
