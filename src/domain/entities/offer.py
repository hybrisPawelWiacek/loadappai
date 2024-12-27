"""Offer-related domain entities."""

from datetime import datetime
from decimal import Decimal
from typing import Dict, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, model_validator, ValidationInfo
from pytz import UTC

from .route import ExtensibleEntity
from ..value_objects.offer import OfferStatus


def utc_now() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(UTC)


class Offer(ExtensibleEntity):
    """Offer entity representing a commercial offer for a route."""
    id: UUID = Field(default_factory=uuid4)
    route_id: UUID
    cost_id: UUID
    total_cost: Decimal = Field(gt=0)
    margin: Decimal = Field(ge=0)
    final_price: Decimal = Field(gt=0)
    fun_fact: Optional[str] = None
    status: OfferStatus = Field(default=OfferStatus.DRAFT)
    is_active: bool = Field(default=True)
    valid_until: Optional[datetime] = None
    created_at: datetime = Field(default_factory=utc_now)
    modified_at: datetime = Field(default_factory=utc_now)

    @field_validator("final_price")
    def validate_final_price(cls, v: Decimal, info: ValidationInfo) -> Decimal:
        """Validate that final price is greater than total cost."""
        if "total_cost" in info.data and v <= info.data["total_cost"]:
            raise ValueError("Final price must be greater than total cost")
        return v

    @model_validator(mode='after')
    def validate_margin(self) -> 'Offer':
        """Validate margin calculation."""
        total_cost = self.total_cost
        final_price = self.final_price
        expected_margin = (final_price - total_cost) / total_cost
        # Round both margins to 4 decimal places before comparison to handle floating point precision
        if round(self.margin, 4) != round(expected_margin, 4):
            raise ValueError(f"Margin does not match the calculation from total cost and final price (expected {expected_margin:.4f}, got {self.margin})")
        return self

    def price(self) -> Decimal:
        """Get the final price."""
        return self.final_price

    def activate(self) -> None:
        """Activate the offer."""
        if self.status in [OfferStatus.CANCELLED, OfferStatus.EXPIRED, OfferStatus.REJECTED]:
            raise ValueError(f"Cannot activate {self.status.value} offer")
        self.status = OfferStatus.ACTIVE
        self.is_active = True
        self.modified_at = utc_now()

    def cancel(self) -> None:
        """Cancel the offer."""
        self.status = OfferStatus.CANCELLED
        self.is_active = False
        self.modified_at = utc_now()

    def accept(self) -> None:
        """Accept the offer."""
        if self.status != OfferStatus.ACTIVE:
            raise ValueError("Can only accept active offers")
        self.status = OfferStatus.ACCEPTED
        self.is_active = False
        self.modified_at = utc_now()

    def reject(self) -> None:
        """Reject the offer."""
        if self.status != OfferStatus.ACTIVE:
            raise ValueError("Can only reject active offers")
        self.status = OfferStatus.REJECTED
        self.is_active = False
        self.modified_at = utc_now()

    def expire(self) -> None:
        """Mark the offer as expired."""
        if self.status != OfferStatus.ACTIVE:
            raise ValueError("Can only expire active offers")
        self.status = OfferStatus.EXPIRED
        self.is_active = False
        self.modified_at = utc_now()


class OfferHistory(BaseModel):
    """Offer history entity for tracking changes."""
    id: UUID = Field(default_factory=uuid4)
    offer_id: UUID
    version: str
    status: OfferStatus
    margin: Decimal = Field(ge=0)
    final_price: Decimal = Field(gt=0)
    fun_fact: Optional[str] = None
    metadata: Optional[Dict] = None
    changed_at: datetime = Field(default_factory=utc_now)
    changed_by: Optional[str] = None
    change_reason: Optional[str] = None

    @field_validator("version")
    def validate_version(cls, v: str) -> str:
        """Validate version format."""
        if not v.replace(".", "").isdigit():
            raise ValueError("Version must be in format X.Y")
        return v
