"""Flask application module."""
from datetime import datetime
from uuid import uuid4
from functools import wraps
from flask import Flask, jsonify, request, current_app
from flask_cors import CORS
from pydantic import ValidationError

from src.infrastructure.database import get_db
from src.api.models import (
    RouteCreateRequest, RouteResponse, ErrorResponse,
    OfferCreateRequest, OfferResponse, CostBreakdown,
    CostSettings, CostSettingsUpdateResponse
)
from src.domain.services import RoutePlanningService
from src.infrastructure.repositories.route_repository import RouteRepository
from src.infrastructure.repositories.offer_repository import OfferRepository
from src.infrastructure.repositories.cost_settings_repository import CostSettingsRepository
from src.infrastructure.services.google_maps_service import GoogleMapsService
from src.infrastructure.services.openai_service import OpenAIService

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*", "methods": ["GET", "POST", "PUT", "DELETE"]}})

def get_services():
    """Get application services."""
    with get_db() as db:
        # Use mocked services in test environment
        if app.config.get('TESTING'):
            openai_service = app.config.get('OPENAI_SERVICE', OpenAIService())
        else:
            openai_service = OpenAIService()

        location_service = GoogleMapsService()
        route_planning_service = RoutePlanningService(location_service=location_service)
        route_repository = RouteRepository(db=db)
        offer_repository = OfferRepository(db=db)
        cost_settings_repository = CostSettingsRepository(db=db)
        
        return (
            location_service,
            route_planning_service,
            route_repository,
            offer_repository,
            openai_service,
            cost_settings_repository
        )

def with_services(f):
    """Decorator to inject services into route handlers."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        with get_db() as db:
            # Use mocked services in test environment
            if app.config.get('TESTING'):
                openai_service = app.config.get('OPENAI_SERVICE', OpenAIService())
            else:
                openai_service = OpenAIService()

            services = (
                GoogleMapsService(),
                RoutePlanningService(location_service=GoogleMapsService()),
                RouteRepository(db=db),
                OfferRepository(db=db),
                openai_service,
                CostSettingsRepository(db=db)
            )
            return f(*args, *services, **kwargs)
    return decorated_function

@app.route('/api/v1/routes', methods=['POST'])
@with_services
def create_route(location_service, route_planning_service, route_repository, offer_repository, openai_service, cost_settings_repository):
    """Create a new route."""
    try:
        # Validate request data
        try:
            route_data = RouteCreateRequest(**request.json)
        except ValidationError as e:
            return jsonify(ErrorResponse(
                error="Invalid input data",
                code="INVALID_INPUT",
                details=str(e)
            ).dict()), 400
        
        # Plan route using service
        try:
            route = route_planning_service.plan_route(
                origin=route_data.origin,
                destination=route_data.destination,
                pickup_time=route_data.pickup_time,
                delivery_time=route_data.delivery_time,
                transport_type=route_data.transport_type,
                cargo_id=route_data.cargo_id
            )
        except ValueError as e:
            return jsonify(ErrorResponse(
                error=str(e),
                code="VALIDATION_ERROR"
            ).dict()), 400
        except Exception as e:
            return jsonify(ErrorResponse(
                error="Failed to plan route",
                code="ROUTE_PLANNING_ERROR"
            ).dict()), 500
        
        # Save route to database
        try:
            route_id = route_repository.create(route)
        except Exception as e:
            return jsonify(ErrorResponse(
                error="Failed to save route",
                code="DATABASE_ERROR"
            ).dict()), 500
        
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
def get_route(location_service, route_planning_service, route_repository, offer_repository, openai_service, cost_settings_repository, route_id):
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
def get_route_cost(location_service, route_planning_service, route_repository, offer_repository, openai_service, cost_settings_repository, route_id):
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

@app.route('/api/v1/offers', methods=['POST'])
@with_services
def create_offer(location_service, route_planning_service, route_repository, offer_repository, openai_service, cost_settings_repository):
    """Generate an offer for a route."""
    try:
        # Validate request data
        offer_data = OfferCreateRequest(**request.json)
        
        # Get route
        route = route_repository.get_by_id(offer_data.route_id)
        if not route:
            return jsonify(ErrorResponse(
                error=f"Route with ID {offer_data.route_id} not found",
                code="NOT_FOUND"
            ).dict()), 404
            
        # Calculate costs
        cost_breakdown = route_planning_service.calculate_cost(route)
        
        # Calculate final price with margin
        final_price = cost_breakdown.total_cost * (1 + offer_data.margin)
        
        # Generate fun fact using OpenAI
        fun_fact = openai_service.generate_fun_fact(route)
        
        # Create offer
        offer_id = str(uuid4())
        offer = OfferResponse(
            id=offer_id,
            route_id=route.id,
            total_cost=cost_breakdown.total_cost,
            margin=offer_data.margin,
            final_price=final_price,
            fun_fact=fun_fact,
            created_at=datetime.utcnow()
        )
        
        # Save to database
        offer_repository.create(offer)
        
        return jsonify(offer.dict()), 201
        
    except Exception as e:
        return jsonify(ErrorResponse(
            error="Failed to create offer",
            code="INTERNAL_ERROR"
        ).dict()), 500

@app.route('/api/v1/offers/<offer_id>', methods=['GET'])
@with_services
def get_offer(location_service, route_planning_service, route_repository, offer_repository, openai_service, cost_settings_repository, offer_id):
    """Get offer by ID."""
    try:
        offer = offer_repository.get_by_id(offer_id)
        if not offer:
            return jsonify(ErrorResponse(
                error=f"Offer with ID {offer_id} not found",
                code="NOT_FOUND"
            ).dict()), 404
            
        return jsonify(offer.dict()), 200
        
    except Exception as e:
        return jsonify(ErrorResponse(
            error="Failed to retrieve offer",
            code="INTERNAL_ERROR"
        ).dict()), 500

@app.route('/api/v1/offers', methods=['GET'])
@with_services
def list_offers(location_service, route_planning_service, route_repository, offer_repository, openai_service, cost_settings_repository):
    """List all offers with optional filtering."""
    try:
        # Get query parameters
        transport_type = request.args.get('transport_type')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        # Convert date strings to datetime objects if provided
        from_date = datetime.fromisoformat(date_from.replace('Z', '+00:00')) if date_from else None
        to_date = datetime.fromisoformat(date_to.replace('Z', '+00:00')) if date_to else None
        
        # Get filtered offers from repository
        offers = offer_repository.list_offers(
            transport_type=transport_type,
            from_date=from_date,
            to_date=to_date
        )
        
        # Convert to simplified response format
        response = [{
            'id': offer.id,
            'route_id': offer.route_id,
            'final_price': offer.final_price,
            'created_at': offer.created_at
        } for offer in offers]
        
        return jsonify(response), 200
        
    except ValueError as e:
        return jsonify(ErrorResponse(
            error="Invalid date format. Use ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)",
            code="INVALID_DATE_FORMAT"
        ).dict()), 400
    except Exception as e:
        return jsonify(ErrorResponse(
            error="Failed to retrieve offers",
            code="INTERNAL_ERROR"
        ).dict()), 500

@app.route('/api/v1/cost-settings', methods=['GET'])
@with_services
def get_cost_settings(location_service, route_planning_service, route_repository, offer_repository, openai_service, cost_settings_repository):
    """Get current cost settings."""
    try:
        settings = cost_settings_repository.get_current()
        if not settings:
            return jsonify(ErrorResponse(
                error="No cost settings found",
                code="NOT_FOUND"
            ).dict()), 404
            
        return jsonify(settings.dict()), 200
        
    except Exception as e:
        return jsonify(ErrorResponse(
            error="Failed to retrieve cost settings",
            code="INTERNAL_ERROR"
        ).dict()), 500

@app.route('/api/v1/cost-settings', methods=['POST'])
@with_services
def update_cost_settings(location_service, route_planning_service, route_repository, offer_repository, openai_service, cost_settings_repository):
    """Update cost settings."""
    try:
        # Validate request data
        settings_data = CostSettings(**request.json)
        
        # Save settings
        cost_settings_repository.update(settings_data)
        
        # Prepare response
        response = CostSettingsUpdateResponse(
            message="Cost settings updated successfully",
            updated_at=datetime.utcnow()
        )
        
        return jsonify(response.dict()), 200
        
    except ValidationError as e:
        return jsonify(ErrorResponse(
            error=str(e),
            code="VALIDATION_ERROR"
        ).dict()), 400
        
    except Exception as e:
        return jsonify(ErrorResponse(
            error="Failed to update cost settings",
            code="INTERNAL_ERROR"
        ).dict()), 500

@app.route('/api/hello')
def hello_world():
    """Simple hello world endpoint for testing."""
    return jsonify({'message': 'Hello, World!'})

@app.errorhandler(ValidationError)
def handle_validation_error(exc):
    """Handle pydantic validation errors."""
    return jsonify(ErrorResponse(
        error="Invalid input data",
        code="INVALID_INPUT",
        details=str(exc)
    ).dict()), 400

@app.errorhandler(404)
def handle_not_found(exc):
    """Handle 404 errors."""
    return jsonify(ErrorResponse(error="Resource not found", code="NOT_FOUND").dict()), 404
