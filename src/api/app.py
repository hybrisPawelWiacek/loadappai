"""Flask application module."""
from datetime import datetime
from uuid import uuid4
from functools import wraps
from time import time
import uuid
import traceback
import json
from flask import Flask, jsonify, request, Blueprint, make_response
from flask_cors import CORS
from flask_restful import Api, Resource
from pydantic import ValidationError
from enum import Enum
from decimal import Decimal
from datetime import timedelta

from src.infrastructure.database import Database, get_db, init_db
from src.infrastructure.logging import setup_logging, get_logger
from src.api.models import (
    RouteCreateRequest, RouteResponse, ErrorResponse,
    OfferCreateRequest, OfferResponse, CostBreakdown,
    CostSettings, CostSettingsUpdateResponse
)
from src.domain.entities import Route, TransportType
from src.domain.value_objects import Location
from src.domain.services import (
    RoutePlanningService, HelloWorldService, CostCalculationService,
    OfferGenerationService
)
from src.infrastructure.repositories.route_repository import RouteRepository
from src.infrastructure.repositories.offer_repository import OfferRepository
from src.infrastructure.repositories.cost_settings_repository import CostSettingsRepository
from src.infrastructure.services.google_maps_service import GoogleMapsService
from src.infrastructure.services.mock_location_service import MockLocationService
from src.infrastructure.services.openai_service import OpenAIService
from src.config import get_settings

class RouteResource(Resource):
    """Resource for managing routes."""

    def __init__(self):
        self.logger = get_logger(__name__)

    def options(self):
        """Handle OPTIONS requests."""
        return {'Allow': 'GET, POST, PUT, DELETE'}, 200, {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-API-Key'
        }

    def post(self):
        """Create a new route with empty driving calculation."""
        logger = self.logger.bind(
            endpoint="route_resource",
            method="POST",
            remote_ip=request.remote_addr
        )
        
        try:
            logger.info("Getting JSON data")
            data = request.get_json()
            logger.info("received_route_request",
                       origin=data.get('origin'),
                       destination=data.get('destination'),
                       pickup_time=data.get('pickup_time'),
                       delivery_time=data.get('delivery_time'),
                       transport_type=data.get('transport_type'),
                       cargo_id=data.get('cargo_id'))
            
            with get_db() as db:
                # Initialize services
                settings = get_settings()
                try:
                    location_service = GoogleMapsService()
                    logger.info("GoogleMapsService initialized successfully")
                except Exception as e:
                    logger.error("Failed to initialize GoogleMapsService", error=str(e))
                    raise RuntimeError(f"Failed to initialize GoogleMapsService: {str(e)}")
                    
                route_planning_service = RoutePlanningService(location_service=location_service)
                route_repository = RouteRepository(db=db)
                
                # Validate request data
                request_data = RouteCreateRequest(**data)
                
                # Create route
                route = route_planning_service.create_route(
                    origin=request_data.origin,
                    destination=request_data.destination,
                    pickup_time=request_data.pickup_time,
                    delivery_time=request_data.delivery_time,
                    transport_type=request_data.transport_type,
                    cargo_id=request_data.cargo_id,
                    metadata={"cargo_specs": request_data.cargo_specs.dict() if request_data.cargo_specs else None}
                )
                
                try:
                    # Save route
                    saved_route = route_repository.create(route)
                    
                    # Convert to response model
                    response = RouteResponse.from_domain(saved_route)
                    
                    # Create response dictionary
                    response_data = {
                        'id': str(response.id),
                        'cargo_id': str(response.cargo_id) if response.cargo_id else None,
                        'origin': response.origin.dict(),
                        'destination': response.destination.dict(),
                        'transport_type': response.transport_type,
                        'pickup_time': response.pickup_time.isoformat(),
                        'delivery_time': response.delivery_time.isoformat(),
                        'distance_km': float(response.distance_km),
                        'duration_hours': float(response.duration_hours),
                        'empty_driving': response.empty_driving.dict() if response.empty_driving else None,
                        'is_feasible': response.is_feasible,
                        'segments': [segment.dict() for segment in response.segments],
                        'cargo_specs': response.cargo_specs.dict() if response.cargo_specs else None,
                        'feasibility_notes': response.feasibility_notes
                    }
                    
                    return response_data, 201
                    
                except Exception as e:
                    logger.error(f"Failed to create route: {str(e)}", 
                               error=str(e),
                               error_type=type(e).__name__,
                               traceback=traceback.format_exc())
                    return {'error': 'Internal Server Error', 'details': str(e)}, 500
                
        except ValidationError as e:
            logger.error("Validation error", 
                        error=str(e),
                        error_type=type(e).__name__,
                        traceback=traceback.format_exc())
            return {'error': 'Validation Error', 'details': str(e)}, 400
            
        except Exception as e:
            logger.error("Unexpected error", 
                        error=str(e),
                        error_type=type(e).__name__,
                        traceback=traceback.format_exc())
            return {'error': 'Internal Server Error', 'details': str(e)}, 500


class HelloWorldResource(Resource):
    """Resource for testing API connectivity."""
    
    def __init__(self):
        self.service = HelloWorldService()
        self.logger = get_logger(__name__)
    
    def get(self):
        """Return a test greeting message."""
        logger = self.logger.bind(
            endpoint="hello_world",
            method="GET",
            remote_ip=request.remote_addr
        )
        
        logger.info("hello_world.request.received", 
                   headers=dict(request.headers))
        
        message = self.service.get_greeting()
        
        logger.info("hello_world.response.sending",
                   message=message,
                   status_code=200)
        
        return {"message": message}, 200

    def post(self):
        """Handle POST request with test data."""
        logger = self.logger.bind(
            endpoint="hello_world",
            method="POST",
            remote_ip=request.remote_addr
        )
        
        logger.info("hello_world.request.received",
                   headers=dict(request.headers))
        
        try:
            data = request.get_json()
            logger.info("hello_world.request.json_parsed",
                       data=data)
        except Exception as e:
            logger.error("hello_world.request.json_parse_error",
                        error=str(e),
                        error_type=type(e).__name__)
            data = None
        
        message = f"{self.service.get_greeting()} Received data: {data}"
        
        logger.info("hello_world.response.sending",
                   message=message,
                   received_data=data,
                   status_code=200)
        
        return {"message": message}, 200


class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for handling datetime and UUID objects."""

    def default(self, obj):
        """Handle special types during JSON serialization."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, timedelta):
            return obj.total_seconds()
        if hasattr(obj, 'dict') and callable(getattr(obj, 'dict')):
            return obj.dict()
        return super().default(obj)


def create_app(testing=False):
    """Create and configure Flask application."""
    app = Flask(__name__)
    logger = get_logger(__name__)
    
    # Configure JSON encoder
    app.json_encoder = CustomJSONEncoder
    
    # Configure CORS for development
    CORS(app, resources={
        r"/*": {  # Allow all routes
            "origins": "*",  # Allow all origins
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-API-Key"],
            "expose_headers": ["Content-Type"],
            "supports_credentials": True
        }
    })

    # Set up logging
    setup_logging()

    @app.before_request
    def log_request_info():
        """Log details about every request."""
        logger.info("request.received",
                   method=request.method,
                   url=request.url,
                   headers=dict(request.headers))

    @app.after_request
    def after_request(response):
        """Add CORS headers to every response."""
        origin = request.headers.get('Origin')
        
        # Log CORS-related information
        logger.info("cors.headers.processing",
                   origin=origin,
                   request_method=request.method,
                   request_headers=dict(request.headers))
        
        if origin in ["http://localhost:8501", "http://127.0.0.1:8501"]:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-API-Key"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Max-Age"] = "3600"  # Cache preflight for 1 hour
            
            logger.info("cors.headers.added",
                       origin=origin,
                       cors_headers=dict(response.headers))
        else:
            logger.warning("cors.origin.not_allowed",
                         origin=origin,
                         allowed_origins=["http://localhost:8501", "http://127.0.0.1:8501"])
        
        logger.info("response.sending",
                   status_code=response.status_code,
                   headers=dict(response.headers),
                   data=response.get_data(as_text=True))
        
        return response

    def get_services():
        """Initialize and return all required services."""
        logger = get_logger(__name__)
        logger.info("Initializing services")
        
        # Initialize database
        db = Database()
        logger.info("Database initialized")
        
        # Initialize location service
        settings = get_settings()
        try:
            location_service = GoogleMapsService()
            logger.info("GoogleMapsService initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize GoogleMapsService", error=str(e))
            raise RuntimeError(f"Failed to initialize GoogleMapsService: {str(e)}")
        
        # Initialize route planning service
        route_planning_service = RoutePlanningService(location_service=location_service)
        logger.info("RoutePlanningService initialized")
        
        # Initialize repositories
        route_repository = RouteRepository(db=db)
        logger.info("RouteRepository initialized")
        
        offer_repository = OfferRepository(db=db)
        logger.info("OfferRepository initialized")
        
        openai_service = OpenAIService()
        logger.info("OpenAIService initialized")
        
        cost_settings_repository = CostSettingsRepository(db=db)
        logger.info("CostSettingsRepository initialized")
        
        logger.info("All services initialized successfully")
        
        services = {
            'location_service': location_service,
            'route_planning_service': route_planning_service,
            'route_repository': route_repository,
            'offer_repository': offer_repository,
            'openai_service': openai_service,
            'cost_settings_repository': cost_settings_repository,
        }
        
        logger.info(f"Services initialized successfully: {len(services)} services")
        
        return services

    def with_services(f):
        """Decorator to inject services into route handlers."""
        @wraps(f)
        def wrapper(*args, **kwargs):
            services = get_services()
            return f(**services, **kwargs)
        return wrapper

    @app.route('/api/v1/routes/<route_id>', methods=['GET'])
    def get_route(route_id):
        """Get route details with segments."""
        route_logger = get_logger(__name__).bind(endpoint='route')
        route_logger.info("route_endpoint_initialized")
        
        try:
            with get_db() as db:
                route_repository = RouteRepository(db=db)
                route_logger.info("Getting route by ID", route_id=route_id)
                route = route_repository.get_by_id(route_id)
                
                if not route:
                    route_logger.error("route_not_found",
                                     route_id=route_id)
                    return jsonify(ErrorResponse(
                        error=f"Route with ID {route_id} not found",
                        code="NOT_FOUND"
                    ).dict()), 404
                    
                # Convert to response model and then to dict
                response = RouteResponse(
                    id=route.id,
                    origin=route.origin,
                    destination=route.destination,
                    pickup_time=route.pickup_time,
                    delivery_time=route.delivery_time,
                    transport_type=route.transport_type,
                    cargo_id=route.cargo_id,
                    cargo_specs=route.cargo_specs,
                    distance_km=route.distance_km,
                    duration_hours=route.duration_hours,
                    empty_driving=route.empty_driving,
                    segments=route.segments,
                    is_feasible=route.is_feasible,
                    feasibility_notes=route.feasibility_notes,
                    created_at=route.created_at
                )
                
                route_logger.info("route_retrieved",
                                 route_id=route_id,
                                 segments_count=len(response.segments))
                return jsonify(response.dict()), 200
                
        except Exception as e:
            route_logger.error("route_retrieval_failed",
                              error=str(e),
                              error_type=type(e).__name__)
            return jsonify(ErrorResponse(
                error="Failed to retrieve route",
                code="INTERNAL_ERROR",
                details=str(e)
            ).dict()), 500

    @app.route('/api/v1/routes/<route_id>/cost', methods=['GET'])
    def get_route_cost(route_id):
        """Get cost calculation for a route."""
        costs_logger = get_logger(__name__).bind(endpoint='route_cost', route_id=route_id)
        costs_logger.info("Starting cost calculation request")
        
        try:
            with get_db() as db:
                # Get route
                route_repository = RouteRepository(db=db)
                costs_logger.info("Fetching route")
                route = route_repository.get_by_id(route_id)
                
                if not route:
                    costs_logger.error("Route not found")
                    return jsonify({
                        "error": "Route not found",
                        "route_id": route_id
                    }), 404
                
                costs_logger.info("Route found", 
                                distance_km=route.distance_km,
                                duration_hours=route.duration_hours,
                                country_segments_count=len(route.country_segments))
                
                # Get cost settings
                cost_settings_repository = CostSettingsRepository(db=db)
                costs_logger.info("Fetching cost settings")
                settings = cost_settings_repository.get_current_cost_settings()
                
                if not settings:
                    costs_logger.info("No custom settings found, using defaults")
                    settings = CostSettings.get_default()
                
                costs_logger.info("Cost settings loaded",
                                fuel_prices=settings.fuel_prices,
                                driver_rates=settings.driver_rates,
                                toll_rates=settings.toll_rates)
                
                # Initialize location service
                try:
                    location_service = GoogleMapsService()
                    costs_logger.info("GoogleMapsService initialized")
                except LocationServiceError as e:
                    costs_logger.error("Failed to initialize GoogleMapsService", error=str(e))
                    return jsonify({
                        "error": "Service initialization failed",
                        "message": str(e)
                    }), 500
                    
                # Calculate costs with enhanced breakdown
                route_planning_service = RoutePlanningService(location_service=location_service)
                costs_logger.info("Calculating costs")
                
                try:
                    # Get country segments if not present
                    if not route.country_segments:
                        costs_logger.info("Getting country segments", 
                                        origin_type=type(route.origin).__name__,
                                        dest_type=type(route.destination).__name__)
                        
                        # Convert to Location only if needed
                        origin = route.origin if isinstance(route.origin, Location) else Location(**route.origin)
                        destination = route.destination if isinstance(route.destination, Location) else Location(**route.destination)
                        
                        costs_logger.info("Getting country segments")
                        route.country_segments = location_service.get_country_segments(origin, destination)
                        costs_logger.info("Got country segments", count=len(route.country_segments))
                    
                    # Get transport type from route
                    transport_type = TransportType(route.transport_type) if route.transport_type else TransportType.TRUCK
                    costs_logger.info("Using transport type", type=transport_type)
                    
                    cost_breakdown = route_planning_service.cost_service.calculate_route_cost(
                        route=route,
                        settings=settings,
                        include_empty_driving=True
                    )
                    
                    costs_logger.info("Cost calculation successful",
                                    total_cost=float(cost_breakdown.total_cost),
                                    has_fuel_costs=bool(cost_breakdown.fuel_costs),
                                    has_toll_costs=bool(cost_breakdown.toll_costs),
                                    has_driver_costs=bool(cost_breakdown.driver_costs),
                                    has_maintenance_costs=bool(cost_breakdown.maintenance_costs))
                    
                    # Convert to JSON-safe format
                    response_data = {
                        "route_id": str(route_id),
                        "total_cost": float(cost_breakdown.total_cost),
                        "breakdown": {
                            "fuel_costs": {k: float(v) for k, v in cost_breakdown.fuel_costs.items()},
                            "toll_costs": {k: float(v) for k, v in cost_breakdown.toll_costs.items()},
                            "maintenance_costs": {k: float(v) for k, v in cost_breakdown.maintenance_costs.items()},
                            "driver_costs": {k: float(v) for k, v in cost_breakdown.driver_costs.items()},
                            "rest_period_costs": float(cost_breakdown.rest_period_costs),
                            "loading_unloading_costs": float(cost_breakdown.loading_unloading_costs),
                            "empty_driving_costs": {
                                k: {sk: float(sv) for sk, sv in v.items()}
                                for k, v in cost_breakdown.empty_driving_costs.items()
                            },
                            "overheads": {k: float(v) for k, v in cost_breakdown.overheads.items()}
                        },
                        "currency": cost_breakdown.currency
                    }
                    
                    costs_logger.info("Sending cost response",
                                    response_data=response_data)
                    
                    return jsonify(response_data)
                    
                except Exception as e:
                    costs_logger.error("Cost calculation failed",
                                     error=str(e),
                                     error_type=type(e).__name__,
                                     traceback=traceback.format_exc())
                    return jsonify({
                        "error": "Cost calculation failed",
                        "message": str(e)
                    }), 500
                
        except Exception as e:
            costs_logger.error("Unexpected error",
                             error=str(e),
                             error_type=type(e).__name__,
                             traceback=traceback.format_exc())
            return jsonify({
                "error": "Internal server error",
                "message": str(e)
            }), 500

    @app.route('/api/v1/routes/<route_id>/costs', methods=['POST'])
    def calculate_route_costs(route_id):
        """Calculate detailed costs for a route with enhanced breakdown.
        
        Features:
        - Country-specific cost calculations
        - Time-based cost tracking
        - Empty driving cost calculation
        - Cargo-specific cost factors
        """
        costs_logger = get_logger(__name__).bind(endpoint='costs', route_id=route_id)
        costs_logger.info("cost_calculation_started")
        
        try:
            with get_db() as db:
                route_repository = RouteRepository(db=db)
                cost_settings_repository = CostSettingsRepository(db=db)
                
                # Get route details
                route = route_repository.get(route_id)
                if not route:
                    costs_logger.error("route_not_found")
                    return jsonify(ErrorResponse(
                        error="Not Found",
                        details=f"Route {route_id} not found"
                    ).dict()), 404
                    
                # Get current cost settings
                cost_settings = cost_settings_repository.get_current_cost_settings()
                
                # Initialize location service
                settings = get_settings()
                try:
                    location_service = GoogleMapsService()
                except Exception as e:
                    costs_logger.error("Failed to initialize GoogleMapsService", error=str(e))
                    raise RuntimeError(f"Failed to initialize GoogleMapsService: {str(e)}")
                    
                # Calculate costs with enhanced breakdown
                route_planning_service = RoutePlanningService(location_service=location_service)
                costs_logger.info("Calculating costs")
                
                try:
                    # Get country segments if not present
                    if not route.country_segments:
                        costs_logger.info("Getting country segments", 
                                        origin_type=type(route.origin).__name__,
                                        dest_type=type(route.destination).__name__)
                        
                        # Convert to Location only if needed
                        origin = route.origin if isinstance(route.origin, Location) else Location(**route.origin)
                        destination = route.destination if isinstance(route.destination, Location) else Location(**route.destination)
                        
                        costs_logger.info("Getting country segments")
                        route.country_segments = location_service.get_country_segments(origin, destination)
                        costs_logger.info("Got country segments", count=len(route.country_segments))
                    
                    # Get transport type from route
                    transport_type = TransportType(route.transport_type) if route.transport_type else TransportType.TRUCK
                    costs_logger.info("Using transport type", type=transport_type)
                    
                    cost_breakdown = route_planning_service.cost_service.calculate_costs(
                        route=route,
                        settings=cost_settings,
                        calculation_options=request.get_json() or {}
                    )
                    
                    costs_logger.info("Costs calculated successfully")
                    return jsonify(cost_breakdown.dict()), 200
                    
                except Exception as e:
                    costs_logger.error("Cost calculation failed",
                                      error=str(e),
                                      error_type=type(e).__name__)
                    return jsonify(ErrorResponse(
                        error="Cost Calculation Failed",
                        details=str(e)
                    ).dict()), 500
                
        except Exception as e:
            costs_logger.error("Unexpected error",
                              error=str(e),
                              error_type=type(e).__name__)
            return jsonify(ErrorResponse(
                error="Internal Server Error",
                details=str(e)
            ).dict()), 500

    @app.route('/api/v1/routes/<route_id>/costs/history', methods=['GET'])
    def get_route_cost_history(route_id):
        """Get cost calculation history for a route."""
        history_logger = get_logger(__name__).bind(endpoint='cost_history', route_id=route_id)
        history_logger.info("cost_history_retrieval_started")
        
        try:
            with get_db() as db:
                cost_settings_repository = CostSettingsRepository(db=db)
                
                # Validate route exists
                route_repository = RouteRepository(db=db)
                route = route_repository.get(route_id)
                if not route:
                    history_logger.error("route_not_found")
                    return jsonify(ErrorResponse(
                        error="Not Found",
                        details=f"Route {route_id} not found"
                    ).dict()), 404
                    
                # Get cost history
                history = cost_settings_repository.get_cost_history(route_id)
                
                history_logger.info("cost_history_retrieved",
                                   history_count=len(history))
                return jsonify(history), 200
                
        except Exception as e:
            history_logger.error("cost_history_retrieval_failed",
                               error=str(e),
                               error_type=type(e).__name__)
            return jsonify(ErrorResponse(
                error="History Retrieval Failed",
                details=str(e)
            ).dict()), 500

    @app.route('/api/v1/offers', methods=['POST'])
    def create_offer():
        """Generate an offer for a route with version tracking and status management."""
        offer_logger = get_logger(__name__).bind(endpoint='offer')
        offer_logger.info("offer_endpoint_initialized")
        
        try:
            with get_db() as db:
                offer_repository = OfferRepository(db=db)
                route_repository = RouteRepository(db=db)
                
                offer_logger.info("Getting JSON data")
                data = request.get_json()
                offer_logger.info("received_offer_request", data=data)
                
                # Validate request data
                offer_data = OfferCreateRequest(**data)
                
                offer_logger.info("Getting route")
                route = route_repository.get_by_id(offer_data.route_id)
                if not route:
                    offer_logger.error("route_not_found",
                                      route_id=offer_data.route_id)
                    return jsonify(ErrorResponse(
                        error=f"Route with ID {offer_data.route_id} not found",
                        code="NOT_FOUND"
                    ).dict()), 404
                    
                # Initialize services
                settings = get_settings()
                try:
                    location_service = GoogleMapsService()
                except Exception as e:
                    offer_logger.error("Failed to initialize GoogleMapsService", error=str(e))
                    raise RuntimeError(f"Failed to initialize GoogleMapsService: {str(e)}")
                    
                cost_service = CostCalculationService()
                offer_generation_service = OfferGenerationService(
                    cost_service=cost_service,
                    ai_service=OpenAIService()
                )
                
                # Generate offer
                offer = offer_generation_service.generate_offer(
                    route=route,
                    margin=offer_data.margin,
                    total_cost=offer_data.total_cost,  # Pass total_cost from request
                    metadata=offer_data.metadata,
                    created_by=offer_data.created_by,
                    status=offer_data.status or "draft"
                )
                
                # Save offer
                saved_offer = offer_repository.create(offer)
                
                offer_logger.info("offer_created",
                                 offer_id=offer.id,
                                 version=offer.version,
                                 status=offer.status)
                return jsonify(OfferResponse.from_domain(saved_offer).dict()), 201
                
        except Exception as e:
            offer_logger.error("offer_creation_failed",
                              error=str(e),
                              error_type=type(e).__name__)
            return jsonify(ErrorResponse(
                error="Failed to create offer",
                code="INTERNAL_ERROR",
                details=str(e)
            ).dict()), 500

    @app.route('/api/v1/offers/<offer_id>', methods=['GET'])
    def get_offer(offer_id):
        """Get offer by ID with version history."""
        offer_logger = get_logger(__name__).bind(endpoint='offer')
        offer_logger.info("offer_endpoint_initialized")
        
        try:
            with get_db() as db:
                offer_repository = OfferRepository(db=db)
                
                # Get query parameters
                version = request.args.get('version')
                include_history = request.args.get('include_history', 'false').lower() == 'true'
                
                offer_logger.info("Getting offer by ID",
                                version=version,
                                include_history=include_history)
                
                # Get offer
                if version:
                    offer = offer_repository.get_version(offer_id, version)
                else:
                    offer = offer_repository.get_by_id(offer_id)
                    
                if not offer:
                    offer_logger.error("offer_not_found",
                                      offer_id=offer_id,
                                      version=version)
                    return jsonify(ErrorResponse(
                        error=f"Offer with ID {offer_id} not found",
                        code="NOT_FOUND"
                    ).dict()), 404
                    
                # Get history if requested
                history = []
                if include_history:
                    history = offer_repository.get_history(offer_id)
                
                # Prepare response
                response = OfferResponse.from_domain(offer).dict()
                if include_history:
                    response['history'] = [OfferHistoryResponse.from_domain(h).dict() for h in history]
                    
                offer_logger.info("offer_retrieved",
                                 offer_id=offer_id,
                                 version=offer.version,
                                 history_count=len(history) if include_history else 0)
                return jsonify(response), 200
                
        except Exception as e:
            offer_logger.error("offer_retrieval_failed",
                              error=str(e),
                              error_type=type(e).__name__)
            return jsonify(ErrorResponse(
                error="Failed to retrieve offer",
                code="INTERNAL_ERROR",
                details=str(e)
            ).dict()), 500

    @app.route('/api/v1/offers/<offer_id>', methods=['PUT'])
    def update_offer(offer_id):
        """Update offer with version tracking."""
        offer_logger = get_logger(__name__).bind(endpoint='offer')
        offer_logger.info("offer_update_started")
        
        try:
            with get_db() as db:
                offer_repository = OfferRepository(db=db)
                
                # Get request data
                data = request.get_json()
                offer_logger.info("received_update_request",
                                offer_id=offer_id,
                                data=data)
                
                # Get existing offer
                offer = offer_repository.get_by_id(offer_id)
                if not offer:
                    offer_logger.error("offer_not_found",
                                      offer_id=offer_id)
                    return jsonify(ErrorResponse(
                        error=f"Offer with ID {offer_id} not found",
                        code="NOT_FOUND"
                    ).dict()), 404
                    
                # Initialize services
                settings = get_settings()
                try:
                    location_service = GoogleMapsService()
                except Exception as e:
                    offer_logger.error("Failed to initialize GoogleMapsService", error=str(e))
                    raise RuntimeError(f"Failed to initialize GoogleMapsService: {str(e)}")
                    
                cost_service = CostCalculationService()
                offer_generation_service = OfferGenerationService(
                    cost_service=cost_service,
                    ai_service=OpenAIService()
                )
                
                # Update offer
                updated_offer, history_entry = offer_generation_service.update_offer(
                    offer=offer,
                    margin=data.get('margin'),
                    status=data.get('status'),
                    metadata=data.get('metadata'),
                    modified_by=data.get('modified_by'),
                    change_reason=data.get('change_reason')
                )
                
                # Save changes
                saved_offer = offer_repository.update(updated_offer)
                offer_repository.add_history(history_entry)
                
                offer_logger.info("offer_updated",
                                 offer_id=offer_id,
                                 new_version=updated_offer.version,
                                 new_status=updated_offer.status)
                return jsonify(OfferResponse.from_domain(saved_offer).dict()), 200
                
        except Exception as e:
            offer_logger.error("offer_update_failed",
                              error=str(e),
                              error_type=type(e).__name__)
            return jsonify(ErrorResponse(
                error="Failed to update offer",
                code="INTERNAL_ERROR",
                details=str(e)
            ).dict()), 500

    @app.route('/api/v1/offers/<offer_id>/archive', methods=['POST'])
    def archive_offer(offer_id):
        """Archive an offer."""
        offer_logger = get_logger(__name__).bind(endpoint='offer')
        offer_logger.info("offer_archive_started")
        
        try:
            with get_db() as db:
                offer_repository = OfferRepository(db=db)
                
                # Get request data
                data = request.get_json() or {}
                
                # Get existing offer
                offer = offer_repository.get_by_id(offer_id)
                if not offer:
                    offer_logger.error("offer_not_found",
                                      offer_id=offer_id)
                    return jsonify(ErrorResponse(
                        error=f"Offer with ID {offer_id} not found",
                        code="NOT_FOUND"
                    ).dict()), 404
                    
                # Initialize services
                settings = get_settings()
                try:
                    location_service = GoogleMapsService()
                except Exception as e:
                    offer_logger.error("Failed to initialize GoogleMapsService", error=str(e))
                    raise RuntimeError(f"Failed to initialize GoogleMapsService: {str(e)}")
                    
                cost_service = CostCalculationService()
                offer_generation_service = OfferGenerationService(
                    cost_service=cost_service,
                    ai_service=OpenAIService()
                )
                
                # Archive offer
                archived_offer = offer_generation_service.archive_offer(
                    offer=offer,
                    archived_by=data.get('archived_by'),
                    archive_reason=data.get('archive_reason')
                )
                
                # Save changes
                saved_offer = offer_repository.update(archived_offer)
                
                offer_logger.info("offer_archived",
                                 offer_id=offer_id,
                                 version=archived_offer.version)
                return jsonify(OfferResponse.from_domain(saved_offer).dict()), 200
                
        except Exception as e:
            offer_logger.error("offer_archive_failed",
                              error=str(e),
                              error_type=type(e).__name__)
            return jsonify(ErrorResponse(
                error="Failed to archive offer",
                code="INTERNAL_ERROR",
                details=str(e)
            ).dict()), 500

    @app.route('/api/v1/offers', methods=['GET'])
    def list_offers():
        """List offers with filtering and pagination."""
        offer_logger = get_logger(__name__).bind(endpoint='offer_list')
        offer_logger.info("offer_list_started")
        
        try:
            with get_db() as db:
                offer_repository = OfferRepository(db=db)
                
                # Get query parameters
                page = int(request.args.get('page', 1))
                per_page = int(request.args.get('per_page', 10))
                status = request.args.get('status')
                route_id = request.args.get('route_id')
                created_by = request.args.get('created_by')
                created_after = request.args.get('created_after')
                created_before = request.args.get('created_before')
                
                # Build filters
                filters = {}
                if status:
                    filters['status'] = status
                if route_id:
                    filters['route_id'] = route_id
                if created_by:
                    filters['created_by'] = created_by
                if created_after:
                    filters['created_after'] = datetime.fromisoformat(created_after)
                if created_before:
                    filters['created_before'] = datetime.fromisoformat(created_before)
                
                # Get offers
                offers, total = offer_repository.list_with_filters(
                    page=page,
                    per_page=per_page,
                    filters=filters
                )
                
                # Prepare response
                response = {
                    'items': [OfferResponse.from_domain(o).dict() for o in offers],
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                    'pages': (total + per_page - 1) // per_page
                }
                
                offer_logger.info("offers_listed",
                                 total=total,
                                 page=page,
                                 filters=filters)
                return jsonify(response), 200
                
        except Exception as e:
            offer_logger.error("offer_list_failed",
                              error=str(e),
                              error_type=type(e).__name__)
            return jsonify(ErrorResponse(
                error="Failed to list offers",
                code="INTERNAL_ERROR",
                details=str(e)
            ).dict()), 500

    @app.route('/api/v1/cost-settings', methods=['GET', 'POST', 'PUT'])
    def get_or_update_cost_settings():
        """Get or update current cost settings."""
        settings_logger = get_logger(__name__).bind(endpoint='cost_settings')
        settings_logger.info("cost_settings_endpoint_initialized")
        
        try:
            with get_db() as db:
                cost_settings_repository = CostSettingsRepository(db=db)
                
                if request.method == 'GET':
                    settings = cost_settings_repository.get_current_cost_settings()
                    if not settings:
                        settings_logger.error("cost_settings_not_found")
                        return jsonify(ErrorResponse(
                            error="No cost settings found",
                            code="NOT_FOUND"
                        ).dict()), 404
                        
                    settings_logger.info("cost_settings_retrieved")
                    return jsonify(settings.dict()), 200
                    
                elif request.method == 'POST' or request.method == 'PUT':
                    data = request.get_json()
                    if request.method == 'POST':
                        settings_data = CostSettings(**data)
                    else:
                        settings_data = CostSettingsUpdateRequest(**data)
                    
                    updated = cost_settings_repository.update(settings_data)
                    settings_logger.info("cost_settings_updated",
                                        countries=list(updated.fuel_prices.keys()))
                    
                    response = CostSettingsResponse(
                        settings=updated,
                        message="Cost settings updated successfully",
                        updated_at=datetime.utcnow()
                    )
                    
                    return jsonify(response.dict()), 200
                    
        except ValidationError as e:
            settings_logger.error("validation_error",
                                  errors=e.errors())
            return jsonify(ErrorResponse(
                error=str(e),
                code="VALIDATION_ERROR"
            ).dict()), 400
            
        except Exception as e:
            settings_logger.error("cost_settings_update_failed",
                                  error=str(e),
                                  error_type=type(e).__name__)
            return jsonify(ErrorResponse(
                error="Failed to update cost settings",
                code="INTERNAL_ERROR"
            ).dict()), 500

    @app.route('/api/v1/settings/transport', methods=['GET'])
    def get_transport_settings():
        """Get current transport settings."""
        settings_logger = get_logger(__name__).bind(endpoint='transport_settings')
        settings_logger.info("transport_settings_retrieval_started")
        
        try:
            with get_db() as db:
                cost_settings_repository = CostSettingsRepository(db=db)
                
                settings = cost_settings_repository.get_transport_settings()
                settings_logger.info("transport_settings_retrieved")
                return jsonify(settings.dict()), 200
                
        except Exception as e:
            settings_logger.error("transport_settings_retrieval_failed",
                                error=str(e),
                                error_type=type(e).__name__)
            return jsonify(ErrorResponse(
                error="Settings Retrieval Failed",
                details=str(e)
            ).dict()), 500

    @app.route('/api/v1/settings/transport', methods=['PUT'])
    def update_transport_settings():
        """Update transport settings."""
        settings_logger = get_logger(__name__).bind(endpoint='transport_settings')
        settings_logger.info("transport_settings_update_started")
        
        try:
            with get_db() as db:
                cost_settings_repository = CostSettingsRepository(db=db)
                
                data = request.get_json()
                settings = TransportSettings(**data)
                
                # Update settings
                cost_settings_repository.update_transport_settings(settings)
                
                response = CostSettingsUpdateResponse(
                    message="Transport settings updated successfully",
                    updated_at=datetime.utcnow()
                )
                
                settings_logger.info("transport_settings_updated")
                return jsonify(response.dict()), 200
                
        except ValidationError as e:
            settings_logger.error("transport_settings_validation_failed",
                                errors=e.errors())
            return jsonify(ErrorResponse(
                error="Validation Error",
                details=str(e)
            ).dict()), 400
            
        except Exception as e:
            settings_logger.error("transport_settings_update_failed",
                                error=str(e),
                                error_type=type(e).__name__)
            return jsonify(ErrorResponse(
                error="Settings Update Failed",
                details=str(e)
            ).dict()), 500

    @app.route('/api/v1/settings/system', methods=['GET'])
    def get_system_settings():
        """Get current system settings."""
        settings_logger = get_logger(__name__).bind(endpoint='system_settings')
        settings_logger.info("system_settings_retrieval_started")
        
        try:
            with get_db() as db:
                cost_settings_repository = CostSettingsRepository(db=db)
                
                settings = cost_settings_repository.get_system_settings()
                settings_logger.info("system_settings_retrieved")
                return jsonify(settings.dict()), 200
                
        except Exception as e:
            settings_logger.error("system_settings_retrieval_failed",
                                error=str(e),
                                error_type=type(e).__name__)
            return jsonify(ErrorResponse(
                error="Settings Retrieval Failed",
                details=str(e)
            ).dict()), 500

    @app.route('/api/v1/settings/system', methods=['PUT'])
    def update_system_settings():
        """Update system settings."""
        settings_logger = get_logger(__name__).bind(endpoint='system_settings')
        settings_logger.info("system_settings_update_started")
        
        try:
            with get_db() as db:
                cost_settings_repository = CostSettingsRepository(db=db)
                
                data = request.get_json()
                settings = SystemSettings(**data)
                
                # Update settings
                cost_settings_repository.update_system_settings(settings)
                
                response = CostSettingsUpdateResponse(
                    message="System settings updated successfully",
                    updated_at=datetime.utcnow()
                )
                
                settings_logger.info("system_settings_updated")
                return jsonify(response.dict()), 200
                
        except ValidationError as e:
            settings_logger.error("system_settings_validation_failed",
                                errors=e.errors())
            return jsonify(ErrorResponse(
                error="Validation Error",
                details=str(e)
            ).dict()), 400
            
        except Exception as e:
            settings_logger.error("system_settings_update_failed",
                                error=str(e),
                                error_type=type(e).__name__)
            return jsonify(ErrorResponse(
                error="Settings Update Failed",
                details=str(e)
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

    # Create blueprint and API
    api_bp = Blueprint('api', __name__, url_prefix='/api/v1')
    api = Api(api_bp)

    # Add resources to API
    api.add_resource(RouteResource, '/routes')
    api.add_resource(HelloWorldResource, '/hello')  # Add the new resource

    # Register blueprint
    app.register_blueprint(api_bp)

    return app

# Create the default application instance
app = create_app()
