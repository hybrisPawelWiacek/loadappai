"""Tests for AI-related value objects."""

from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4
import pytest
from pydantic import ValidationError

from src.domain.value_objects.ai import (
    AIModelResponse,
    OptimizationResult,
    RouteOptimization
)
from src.domain.value_objects.pricing import PricePrediction


def test_ai_model_response_creation():
    """Test creating AIModelResponse with valid data."""
    request_id = uuid4()
    timestamp = datetime.now()
    
    response = AIModelResponse(
        model_id="gpt-4",
        model_version="2.0",
        request_id=request_id,
        timestamp=timestamp,
        response_text="Test response",
        confidence_score=0.95,
        tokens_used=150,
        processing_time_ms=234,
        metadata={"source": "api"},
        tags=["test", "v2"],
        notes="Test note"
    )
    
    assert response.model_id == "gpt-4"
    assert response.model_version == "2.0"
    assert response.request_id == request_id
    assert response.timestamp == timestamp
    assert response.response_text == "Test response"
    assert response.confidence_score == 0.95
    assert response.tokens_used == 150
    assert response.processing_time_ms == 234
    assert response.metadata == {"source": "api"}
    assert response.tags == ["test", "v2"]
    assert response.notes == "Test note"


def test_ai_model_response_defaults():
    """Test AIModelResponse default values."""
    request_id = uuid4()
    timestamp = datetime.now()
    
    response = AIModelResponse(
        model_id="gpt-4",
        request_id=request_id,
        timestamp=timestamp,
        response_text="Test response"
    )
    
    assert response.model_version == "1.0"
    assert response.confidence_score == 0.0
    assert response.tokens_used is None
    assert response.processing_time_ms is None
    assert response.metadata == {}
    assert response.tags == []
    assert response.notes is None


def test_ai_model_response_validation():
    """Test AIModelResponse validation."""
    request_id = uuid4()
    timestamp = datetime.now()
    
    # Test invalid confidence score
    with pytest.raises(ValidationError):
        AIModelResponse(
            model_id="gpt-4",
            request_id=request_id,
            timestamp=timestamp,
            response_text="Test",
            confidence_score=1.5  # Should be between 0 and 1
        )


def test_optimization_result_creation():
    """Test creating OptimizationResult with valid data."""
    optimization_id = uuid4()
    timestamp = datetime.now()
    
    result = OptimizationResult(
        optimization_id=optimization_id,
        timestamp=timestamp,
        objective_value=123.45,
        optimization_type="cost",
        iterations=5,
        convergence_status="completed",
        execution_time_ms=345,
        constraints_satisfied=True,
        optimization_parameters={"max_iterations": 10},
        solution_quality=0.98,
        improvement_percentage=15.5,
        metadata={"algorithm": "gradient_descent"},
        notes="Test optimization"
    )
    
    assert result.optimization_id == optimization_id
    assert result.timestamp == timestamp
    assert result.objective_value == 123.45
    assert result.optimization_type == "cost"
    assert result.iterations == 5
    assert result.convergence_status == "completed"
    assert result.execution_time_ms == 345
    assert result.constraints_satisfied is True
    assert result.optimization_parameters == {"max_iterations": 10}
    assert result.solution_quality == 0.98
    assert result.improvement_percentage == 15.5
    assert result.metadata == {"algorithm": "gradient_descent"}
    assert result.notes == "Test optimization"


def test_optimization_result_defaults():
    """Test OptimizationResult default values."""
    optimization_id = uuid4()
    timestamp = datetime.now()
    
    result = OptimizationResult(
        optimization_id=optimization_id,
        timestamp=timestamp,
        objective_value=100.0
    )
    
    assert result.optimization_type == "cost"
    assert result.iterations == 1
    assert result.convergence_status == "completed"
    assert result.execution_time_ms is None
    assert result.constraints_satisfied is True
    assert result.optimization_parameters == {}
    assert result.solution_quality == 1.0
    assert result.improvement_percentage is None
    assert result.metadata == {}
    assert result.notes is None


def test_route_optimization_creation():
    """Test creating RouteOptimization with valid data."""
    optimization_id = uuid4()
    route_id = uuid4()
    timestamp = datetime.now()
    
    optimization = RouteOptimization(
        optimization_id=optimization_id,
        timestamp=timestamp,
        objective_value=500.0,
        route_id=route_id,
        original_distance=1000.0,
        optimized_distance=900.0,
        original_duration=12.5,
        optimized_duration=11.0,
        distance_saved=100.0,
        time_saved=1.5,
        fuel_saved=10.5,
        co2_reduced=25.5,
        waypoints_reordered=True,
        alternative_routes=[{"distance": 950.0}],
        constraints_applied={"max_duration": 13.0},
        notes="Route optimized successfully"
    )
    
    assert optimization.optimization_id == optimization_id
    assert optimization.route_id == route_id
    assert optimization.timestamp == timestamp
    assert optimization.objective_value == 500.0
    assert optimization.original_distance == 1000.0
    assert optimization.optimized_distance == 900.0
    assert optimization.original_duration == 12.5
    assert optimization.optimized_duration == 11.0
    assert optimization.distance_saved == 100.0
    assert optimization.time_saved == 1.5
    assert optimization.fuel_saved == 10.5
    assert optimization.co2_reduced == 25.5
    assert optimization.waypoints_reordered is True
    assert optimization.alternative_routes == [{"distance": 950.0}]
    assert optimization.constraints_applied == {"max_duration": 13.0}
    assert optimization.notes == "Route optimized successfully"


def test_route_optimization_defaults():
    """Test RouteOptimization default values."""
    optimization_id = uuid4()
    route_id = uuid4()
    timestamp = datetime.now()
    
    optimization = RouteOptimization(
        optimization_id=optimization_id,
        timestamp=timestamp,
        objective_value=500.0,
        route_id=route_id,
        original_distance=1000.0,
        optimized_distance=900.0,
        original_duration=12.5,
        optimized_duration=11.0
    )
    
    assert optimization.distance_saved == 0.0
    assert optimization.time_saved == 0.0
    assert optimization.fuel_saved is None
    assert optimization.co2_reduced is None
    assert optimization.waypoints_reordered is False
    assert optimization.alternative_routes == []
    assert optimization.constraints_applied == {}
    assert optimization.notes is None


def test_route_optimization_inheritance():
    """Test that RouteOptimization inherits correctly from OptimizationResult."""
    optimization_id = uuid4()
    route_id = uuid4()
    timestamp = datetime.now()
    
    optimization = RouteOptimization(
        optimization_id=optimization_id,
        timestamp=timestamp,
        objective_value=500.0,
        route_id=route_id,
        original_distance=1000.0,
        optimized_distance=900.0,
        original_duration=12.5,
        optimized_duration=11.0,
        solution_quality=0.95,  # OptimizationResult field
        improvement_percentage=10.0  # OptimizationResult field
    )
    
    # Check inherited fields
    assert optimization.solution_quality == 0.95
    assert optimization.improvement_percentage == 10.0
    assert optimization.optimization_type == "cost"  # Default from parent
    assert optimization.constraints_satisfied is True  # Default from parent


def test_price_prediction_creation():
    """Test creating PricePrediction with valid data."""
    route_id = uuid4()
    prediction_date = datetime.now()
    valid_until = prediction_date + timedelta(hours=24)
    
    prediction = PricePrediction(
        predicted_price=Decimal("1234.56"),
        confidence_level=0.85,
        prediction_date=prediction_date,
        valid_until=valid_until,
        currency="EUR",
        route_id=route_id,
        model_version="2.0",
        features_used=["distance", "fuel_price"],
        prediction_interval={"lower": Decimal("1200.00"), "upper": Decimal("1300.00")},
        notes="Test prediction"
    )
    
    assert prediction.predicted_price == Decimal("1234.56")
    assert prediction.confidence_level == 0.85
    assert prediction.prediction_date == prediction_date
    assert prediction.valid_until == valid_until
    assert prediction.currency == "EUR"
    assert prediction.route_id == route_id
    assert prediction.model_version == "2.0"
    assert prediction.features_used == ["distance", "fuel_price"]
    assert prediction.prediction_interval == {
        "lower": Decimal("1200.00"),
        "upper": Decimal("1300.00")
    }
    assert prediction.notes == "Test prediction"


def test_price_prediction_defaults():
    """Test PricePrediction default values."""
    prediction_date = datetime.now()
    
    prediction = PricePrediction(
        predicted_price=Decimal("1000.00"),
        prediction_date=prediction_date
    )
    
    assert prediction.confidence_level == 0.0
    assert prediction.valid_until is None
    assert prediction.currency == "EUR"
    assert prediction.route_id is None
    assert prediction.offer_id is None
    assert prediction.model_version == "1.0"
    assert prediction.features_used == []
    assert prediction.prediction_interval is None
    assert prediction.notes is None


def test_price_prediction_validation():
    """Test PricePrediction validation."""
    prediction_date = datetime.now()
    
    # Test invalid confidence level
    with pytest.raises(ValidationError):
        PricePrediction(
            predicted_price=Decimal("1000.00"),
            prediction_date=prediction_date,
            confidence_level=2.0  # Should be between 0 and 1
        )
