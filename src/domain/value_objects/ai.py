"""AI-related value objects."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID
from pydantic import Field

from .common import BaseValueObject


class AIModelResponse(BaseValueObject):
    """Response from an AI model."""

    model_id: str
    model_version: str = Field(default="1.0")
    request_id: UUID
    timestamp: datetime
    response_text: str
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    tokens_used: Optional[int] = None
    processing_time_ms: Optional[int] = None
    metadata: Dict[str, str] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    notes: Optional[str] = None


class OptimizationResult(BaseValueObject):
    """Result of an optimization operation."""

    optimization_id: UUID
    timestamp: datetime
    objective_value: float
    optimization_type: str = Field(default="cost")
    iterations: int = Field(default=1)
    convergence_status: str = Field(default="completed")
    execution_time_ms: Optional[int] = None
    constraints_satisfied: bool = Field(default=True)
    optimization_parameters: Dict[str, Any] = Field(default_factory=dict)
    solution_quality: float = Field(default=1.0, ge=0.0, le=1.0)
    improvement_percentage: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None


class RouteOptimization(OptimizationResult):
    """Result of route optimization."""

    route_id: UUID
    original_distance: float
    optimized_distance: float
    original_duration: float
    optimized_duration: float
    distance_saved: float = Field(default=0.0)
    time_saved: float = Field(default=0.0)
    fuel_saved: Optional[float] = None
    co2_reduced: Optional[float] = None
    waypoints_reordered: bool = Field(default=False)
    alternative_routes: List[Dict[str, Any]] = Field(default_factory=list)
    constraints_applied: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None
