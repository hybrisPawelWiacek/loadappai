"""Flask application module."""
from datetime import datetime
from uuid import uuid4
from flask import Flask, jsonify, request
from pydantic import ValidationError
from functools import wraps
from src.infrastructure.database import get_db

from src.api.models import RouteCreateRequest, RouteResponse, ErrorResponse
from src.domain.services import RoutePlanningService
from src.infrastructure.repositories.route_repository import RouteRepository
from src.infrastructure.services.google_maps_service import GoogleMapsService

app = Flask(__name__)

def get_services():
    """Get application services."""
    db = next(get_db())
    location_service = GoogleMapsService()
    route_planning_service = RoutePlanningService(location_service=location_service)
    route_repository = RouteRepository(db=db)
    return location_service, route_planning_service, route_repository, db

def with_services(f):
    """Decorator to inject services into route handlers."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        location_service, route_planning_service, route_repository, db = get_services()
        try:
            return f(location_service, route_planning_service, route_repository, *args, **kwargs)
        finally:
            db.close()
    return decorated_function

@app.route('/api/v1/routes', methods=['POST'])
@with_services
def create_route(location_service, route_planning_service, route_repository):
    """Create a new route."""
    try:
        # Validate request data
        route_data = RouteCreateRequest(**request.json)
        
        # Plan route using service
        route = route_planning_service.plan_route(
            origin=route_data.origin,
            destination=route_data.destination,
            pickup_time=route_data.pickup_time,
            delivery_time=route_data.delivery_time,
            transport_type=route_data.transport_type,
            cargo_id=route_data.cargo_id
        )
        
        # Save route to database
        route_id = route_repository.create(route)
        
        # Prepare response
        response = RouteResponse(
            id=route_id,
            **route.dict(),
            created_at=datetime.utcnow()
        )
        
        return jsonify(response.dict()), 201
        
    except Exception as e:
        return jsonify(ErrorResponse(
            error="Failed to create route",
            code="INTERNAL_ERROR"
        ).dict()), 500

@app.route('/api/v1/routes/<route_id>', methods=['GET'])
@with_services
def get_route(location_service, route_planning_service, route_repository, route_id):
    """Get route by ID."""
    try:
        route = route_repository.get_by_id(route_id)
        if not route:
            return jsonify(ErrorResponse(
                error=f"Route with ID {route_id} not found",
                code="NOT_FOUND"
            ).dict()), 404
            
        response = RouteResponse(**route.dict())
        return jsonify(response.dict()), 200
        
    except Exception as e:
        return jsonify(ErrorResponse(
            error="Failed to retrieve route",
            code="INTERNAL_ERROR"
        ).dict()), 500

@app.route('/api/v1/routes/<route_id>/cost', methods=['GET'])
@with_services
def get_route_cost(location_service, route_planning_service, route_repository, route_id):
    """Get cost calculation for a route."""
    try:
        route = route_repository.get_by_id(route_id)
        if not route:
            return jsonify(ErrorResponse(
                error=f"Route with ID {route_id} not found",
                code="NOT_FOUND"
            ).dict()), 404
            
        # Calculate cost using cost calculation service
        cost = route_planning_service.calculate_cost(route)
        
        return jsonify(cost.dict()), 200
        
    except Exception as e:
        return jsonify(ErrorResponse(
            error="Failed to calculate route cost",
            code="INTERNAL_ERROR"
        ).dict()), 500

@app.route('/api/hello')
def hello_world():
    """Simple hello world endpoint for testing."""
    return jsonify({'message': 'Hello, World!'})

@app.errorhandler(ValidationError)
def handle_validation_error(exc):
    """Handle pydantic validation errors."""
    return jsonify(ErrorResponse(error=str(exc), code="VALIDATION_ERROR").dict()), 400

@app.errorhandler(404)
def handle_not_found(exc):
    """Handle 404 errors."""
    return jsonify(ErrorResponse(error="Resource not found", code="NOT_FOUND").dict()), 404
