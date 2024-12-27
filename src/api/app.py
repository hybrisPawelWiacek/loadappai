"""Flask application setup and routes."""
from datetime import datetime
from decimal import Decimal
import json
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy.orm import Session

from src.domain.entities.route import Route
from src.domain.entities.cost import Cost, CostSettings
from src.domain.interfaces.repositories.cost_settings_repository import CostSettingsRepository
from src.domain.interfaces.services.location_service import LocationServiceError
from src.infrastructure.repositories.cost_settings_repository import CostSettingsRepository as CostSettingsRepositoryImpl
from src.infrastructure.database import get_db
from src.infrastructure.logging import get_logger, setup_logging
from src.settings import get_settings

from src.infrastructure.repositories.route_repository import RouteRepository
from src.infrastructure.repositories.offer_repository import OfferRepository
from src.infrastructure.services.google_maps_service import GoogleMapsService
from tests.mocks.mock_location_service import MockLocationService
from src.infrastructure.services.openai_service import OpenAIService
from src.api.models import (
    RouteCreateRequest, RouteResponse, ErrorResponse,
    OfferCreateRequest, OfferResponse, CostBreakdown,
    CostSettings, CostSettingsUpdateResponse
)
from src.domain.value_objects import Location
from src.domain.services import (
    RoutePlanningService, HelloWorldService, CostCalculationService,
    OfferGenerationService
)

# Import blueprints
from src.api.blueprints import register_blueprints

class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for handling datetime and UUID objects."""

    def default(self, obj):
        """Handle special types during JSON serialization."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, Decimal):
            return float(obj)
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
        
        return response

    # Register blueprints
    register_blueprints(app)

    return app

# Create the default application instance
app = create_app()
