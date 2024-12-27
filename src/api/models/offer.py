"""Offer-related models for API request/response handling."""
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, validator

from src.domain.entities.offer import OfferHistory, Offer as DomainOffer
from .base import ensure_timezone


class OfferCreateRequest(BaseModel):
    """Request model for creating an offer."""
    route_id: str
    margin: float
    total_cost: Optional[float] = None
    metadata: Optional[Dict] = None
    created_by: Optional[str] = None
    status: Optional[str] = "draft"

    @validator('margin')
    def validate_margin(cls, v):
        """Validate margin is non-negative."""
        if v < 0:
            raise ValueError("Margin cannot be negative")
        return v


class OfferUpdateRequest(BaseModel):
    """Request model for updating an offer."""
    margin: Optional[float] = None
    status: Optional[str] = None
    metadata: Optional[Dict] = None
    modified_by: Optional[str] = None
    change_reason: Optional[str] = None

    @validator('margin')
    def validate_margin(cls, v):
        """Validate margin is non-negative if provided."""
        if v is not None and v < 0:
            raise ValueError("Margin cannot be negative")
        return v

    @validator('status')
    def validate_status(cls, v):
        """Validate status if provided."""
        if v is not None and v not in ["draft", "sent", "accepted", "rejected", "expired"]:
            raise ValueError("Invalid status value")
        return v


class OfferHistoryResponse(BaseModel):
    """Response model for offer history entries."""
    offer_id: str
    version: str
    status: str
    margin: float
    final_price: float
    fun_fact: Optional[str]
    extra_data: Optional[Dict]
    changed_at: datetime
    changed_by: Optional[str]
    change_reason: Optional[str]

    _ensure_changed_timezone = validator('changed_at', allow_reuse=True)(ensure_timezone)

    @classmethod
    def from_domain(cls, history: OfferHistory):
        """Convert domain model to response model."""
        return cls(
            offer_id=str(history.offer_id),
            version=history.version,
            status=history.status,
            margin=history.margin,
            final_price=history.final_price,
            fun_fact=history.fun_fact,
            extra_data=history.extra_data,
            changed_at=history.changed_at,
            changed_by=history.changed_by,
            change_reason=history.change_reason
        )


class OfferResponse(BaseModel):
    """Response model for offers."""
    id: str
    route_id: str
    version: str
    status: str
    total_cost: float
    margin: float
    final_price: float
    fun_fact: Optional[str]
    metadata: Optional[Dict]
    created_at: datetime
    created_by: Optional[str]
    modified_at: datetime
    modified_by: Optional[str]
    is_active: bool
    history: Optional[List[OfferHistoryResponse]] = None

    _ensure_created_timezone = validator('created_at', allow_reuse=True)(ensure_timezone)
    _ensure_modified_timezone = validator('modified_at', allow_reuse=True)(ensure_timezone)

    @classmethod
    def from_domain(cls, offer: DomainOffer):
        """Convert domain model to response model."""
        history = None
        if offer.history:
            history = [OfferHistoryResponse.from_domain(h) for h in offer.history]

        return cls(
            id=str(offer.id),
            route_id=str(offer.route_id),
            version=offer.version,
            status=offer.status,
            total_cost=offer.total_cost,
            margin=offer.margin,
            final_price=offer.final_price,
            fun_fact=offer.fun_fact,
            metadata=offer.extra_data,
            created_at=offer.created_at,
            created_by=offer.created_by,
            modified_at=offer.modified_at,
            modified_by=offer.modified_by,
            is_active=offer.is_active,
            history=history
        )
