"""Routes blueprint for handling route-related operations."""
from datetime import datetime
from uuid import UUID
from flask import Blueprint, jsonify, request
from flask_restful import Resource

from src.domain.entities.route import Route
from src.domain.services import RoutePlanningService
from src.domain.value_objects import Location
from src.infrastructure.repositories.route_repository import RouteRepository
from src.infrastructure.services.google_maps_service import GoogleMapsService
from src.infrastructure.logging import get_logger
from src.api.models import RouteCreateRequest, RouteResponse, ErrorResponse

routes_bp = Blueprint('routes', __name__)

class RouteResource(Resource):
    """Resource for managing routes."""

    def __init__(self):
        self.logger = get_logger(__name__)
        self.route_repository = RouteRepository()
        self.location_service = GoogleMapsService()
        self.route_service = RoutePlanningService(
            route_repository=self.route_repository,
            location_service=self.location_service
        )

    def options(self):
        """Handle OPTIONS requests."""
        return {'Allow': 'GET, POST, PUT, DELETE'}, 200, {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-API-Key'
        }

    def post(self):
        """Create a new route with empty driving calculation."""
        try:
            data = request.get_json()
            route_request = RouteCreateRequest(**data)
            
            # Create locations
            pickup = Location(
                address=route_request.pickup_address,
                latitude=route_request.pickup_lat,
                longitude=route_request.pickup_lng
            )
            delivery = Location(
                address=route_request.delivery_address,
                latitude=route_request.delivery_lat,
                longitude=route_request.delivery_lng
            )
            
            # Create route
            route = self.route_service.create_route(
                pickup_location=pickup,
                delivery_location=delivery,
                cargo_weight=route_request.cargo_weight,
                cargo_volume=route_request.cargo_volume
            )
            
            return RouteResponse.from_entity(route).dict(), 201
            
        except Exception as e:
            self.logger.error(f"Error creating route: {str(e)}")
            return ErrorResponse(message=str(e)).dict(), 400

    def get(self, route_id: UUID = None):
        """Get route details."""
        try:
            if route_id:
                route = self.route_repository.get_by_id(route_id)
                if not route:
                    return ErrorResponse(message=f"Route {route_id} not found").dict(), 404
                return RouteResponse.from_entity(route).dict(), 200
            
            routes = self.route_repository.get_all()
            return [RouteResponse.from_entity(route).dict() for route in routes], 200
            
        except Exception as e:
            self.logger.error(f"Error retrieving route(s): {str(e)}")
            return ErrorResponse(message=str(e)).dict(), 400

    def delete(self, route_id: UUID):
        """Delete a route."""
        try:
            success = self.route_repository.delete(route_id)
            if not success:
                return ErrorResponse(message=f"Route {route_id} not found").dict(), 404
            return {"message": f"Route {route_id} deleted successfully"}, 200
            
        except Exception as e:
            self.logger.error(f"Error deleting route: {str(e)}")
            return ErrorResponse(message=str(e)).dict(), 400

# Register resources
routes_bp.add_url_rule('/', view_func=RouteResource.as_view('routes'))
routes_bp.add_url_rule('/<uuid:route_id>', view_func=RouteResource.as_view('route'))
