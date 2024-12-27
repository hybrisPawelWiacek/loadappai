"""Settings response models."""
from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel, Field

from src.domain.models import CostSettings


class ErrorResponse(BaseModel):
    """Error response model."""
    
    message: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")
    details: Optional[Dict] = Field(None, description="Additional error details")


class CostSettingsResponse(BaseModel):
    """Response model for cost settings."""
    
    settings: CostSettings = Field(..., description="Cost settings")
    message: str = Field("Settings retrieved successfully")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class CostSettingsUpdateResponse(BaseModel):
    """Response model for cost settings update."""
    
    settings: CostSettings = Field(..., description="Updated cost settings")
    message: str = Field("Settings updated successfully")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
