"""Value objects for the offer domain."""
from enum import Enum
from typing import Optional, Dict, Annotated, TYPE_CHECKING, Any
from pydantic import Field, ConfigDict

from .common import BaseValueObject
from .cost import CostBreakdown

class OfferStatus(str, Enum):     
    """Status of an offer."""
 
    DRAFT = "draft"
    PENDING = "pending"
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class OfferMetadata(BaseValueObject):
    """Metadata for an offer."""

    version: str = Field(default="1.0")
    source: Optional[str] = None
    tags: Dict[str, str] = Field(default_factory=dict)
    notes: Optional[str] = None
    custom_fields: Dict[str, str] = Field(default_factory=dict)


class OfferGenerationResult(BaseValueObject):
    """Value object representing the result of offer generation."""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True,
        validate_assignment=True,
        use_enum_values=True,
        from_attributes=True,
    )

    if TYPE_CHECKING:
        from ..entities.offer import Offer
        from ..entities.route import Route
        offer: "Offer"
        route: "Route"
    else:
        offer: Any
        route: Any

    cost_breakdown: CostBreakdown = Field(description="Detailed breakdown of costs")
    fun_fact: Optional[str] = Field(
        None,
        description="Interesting fact about the route or offer"
    )
