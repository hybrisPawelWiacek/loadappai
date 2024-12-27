"""Cost component value object."""

from decimal import Decimal
from typing import Dict, Optional

from pydantic import BaseModel, Field, field_validator


class CostComponent(BaseModel):
    """Value object representing a cost component."""

    amount: Decimal = Field(ge=0, description="Amount in the specified currency")
    currency: str = Field(default="EUR", description="Currency code (ISO 4217)")
    description: Optional[str] = Field(None, description="Description of the cost component")
    category: Optional[str] = Field(None, description="Category of the cost component")
    metadata: Optional[Dict] = Field(None, description="Additional metadata")

    model_config = {
        "frozen": True,
    }

    @field_validator("amount")
    def validate_amount(cls, v: Decimal) -> Decimal:
        """Validate amount is non-negative."""
        if v < 0:
            raise ValueError("Amount must be non-negative")
        return v

    @field_validator("currency")
    def validate_currency(cls, v: str) -> str:
        """Validate currency code."""
        if len(v) != 3:
            raise ValueError("Currency code must be 3 characters")
        return v.upper()
