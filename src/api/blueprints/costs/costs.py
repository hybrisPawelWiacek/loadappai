"""Costs blueprint for handling cost-related operations."""
from uuid import UUID
from flask import Blueprint, jsonify, request
from flask_restful import Resource

from src.domain.services.cost.cost_calculation import CostCalculationService
from src.domain.services.cost.cost_settings import CostSettingsServiceImpl as CostSettingsService
from src.infrastructure.repositories.route_repository import RouteRepository
from src.infrastructure.repositories.cost_settings_repository import CostSettingsRepository
from src.infrastructure.database import get_db
from src.infrastructure.logging import get_logger
from src.api.models import ErrorResponse

costs_bp = Blueprint('costs', __name__)

class RouteCalculationResource(Resource):
    """Resource for route cost calculations."""

    def __init__(self):
        self.logger = get_logger(__name__)

    def post(self, route_id: UUID):
        """Calculate costs for a route using current settings."""
        logger = self.logger.bind(
            endpoint="route_calculation",
            method="POST",
            remote_ip=request.remote_addr,
            route_id=str(route_id)
        )
        logger.info("Calculating costs for route")
        
        try:
            with get_db() as db:
                # Initialize repositories and services
                route_repository = RouteRepository(db=db)
                cost_settings_repository = CostSettingsRepository(db=db)
                cost_settings_service = CostSettingsService(
                    settings_repository=cost_settings_repository,
                    route_repository=route_repository
                )
                cost_calculation_service = CostCalculationService(
                    settings_service=cost_settings_service,
                    route_repository=route_repository
                )
                
                # Calculate costs
                try:
                    cost_breakdown = cost_calculation_service.calculate_costs(route_id)
                except ValueError as e:
                    if "not found" in str(e):
                        return ErrorResponse(
                            error=str(e),
                            code="NOT_FOUND"
                        ).dict(), 404
                    else:
                        return ErrorResponse(
                            error=str(e),
                            code="BAD_REQUEST"
                        ).dict(), 400
                
                # Convert to response format
                response = {
                    "route_id": str(route_id),
                    "breakdown": {
                        "components": [comp.dict() for comp in cost_breakdown.components],
                        "total": {
                            "amount": str(cost_breakdown.total_amount),
                            "currency": cost_breakdown.currency
                        }
                    },
                    "metadata": {
                        "version": cost_breakdown.version,
                        "created_at": cost_breakdown.created_at.isoformat() if cost_breakdown.created_at else None,
                        "created_by": cost_breakdown.created_by
                    }
                }
                
                logger.info("Successfully calculated costs")
                return response, 200
                
        except Exception as e:
            logger.exception("Error calculating costs")
            return ErrorResponse(
                error="Internal server error",
                code="INTERNAL_ERROR",
                details=str(e)
            ).dict(), 500

    def get(self, route_id: UUID):
        """Get previously calculated costs for a route."""
        logger = self.logger.bind(
            endpoint="route_calculation",
            method="GET",
            remote_ip=request.remote_addr,
            route_id=str(route_id)
        )
        logger.info("Retrieving costs for route")
        
        try:
            with get_db() as db:
                # Initialize repositories and services
                route_repository = RouteRepository(db=db)
                cost_settings_repository = CostSettingsRepository(db=db)
                cost_settings_service = CostSettingsService(
                    settings_repository=cost_settings_repository,
                    route_repository=route_repository
                )
                cost_calculation_service = CostCalculationService(
                    settings_service=cost_settings_service,
                    route_repository=route_repository
                )
                
                # Get latest costs
                try:
                    cost_breakdown = cost_calculation_service.get_latest_costs(route_id)
                    if not cost_breakdown:
                        return ErrorResponse(
                            error=f"No costs found for route {route_id}",
                            code="NOT_FOUND"
                        ).dict(), 404
                except ValueError as e:
                    return ErrorResponse(
                        error=str(e),
                        code="NOT_FOUND"
                    ).dict(), 404
                
                # Convert to response format
                response = {
                    "route_id": str(route_id),
                    "breakdown": {
                        "components": [comp.dict() for comp in cost_breakdown.components],
                        "total": {
                            "amount": str(cost_breakdown.total_amount),
                            "currency": cost_breakdown.currency
                        }
                    },
                    "metadata": {
                        "version": cost_breakdown.version,
                        "created_at": cost_breakdown.created_at.isoformat() if cost_breakdown.created_at else None,
                        "created_by": cost_breakdown.created_by
                    }
                }
                
                logger.info("Successfully retrieved costs")
                return response, 200
                
        except Exception as e:
            logger.exception("Error retrieving costs")
            return ErrorResponse(
                error="Internal server error",
                code="INTERNAL_ERROR",
                details=str(e)
            ).dict(), 500

class CostSettingsResource(Resource):
    """Resource for managing route cost settings."""

    def __init__(self):
        self.logger = get_logger(__name__)

    def get(self, route_id: UUID):
        """Get cost settings for a route."""
        logger = self.logger.bind(
            endpoint="route_settings",
            method="GET",
            remote_ip=request.remote_addr,
            route_id=str(route_id)
        )
        logger.info("Retrieving cost settings")
        
        try:
            with get_db() as db:
                repository = CostSettingsRepository(db=db)
                settings = repository.get_by_route_id(route_id)
                if not settings:
                    return ErrorResponse(
                        error=f"No settings found for route {route_id}",
                        code="NOT_FOUND"
                    ).dict(), 404
                
                return settings.dict(), 200
                
        except Exception as e:
            logger.exception("Error retrieving settings")
            return ErrorResponse(
                error="Internal server error",
                code="INTERNAL_ERROR",
                details=str(e)
            ).dict(), 500

    def post(self, route_id: UUID):
        """Create initial cost settings for a route."""
        logger = self.logger.bind(
            endpoint="route_settings",
            method="POST",
            remote_ip=request.remote_addr,
            route_id=str(route_id)
        )
        logger.info("Creating cost settings")
        
        try:
            data = request.get_json()
            with get_db() as db:
                repository = CostSettingsRepository(db=db)
                
                # Check if settings already exist
                existing = repository.get_by_route_id(route_id)
                if existing:
                    return ErrorResponse(
                        error=f"Settings already exist for route {route_id}",
                        code="CONFLICT"
                    ).dict(), 409
                
                # Create new settings
                settings = CostSettings(
                    route_id=route_id,
                    **data
                )
                repository.create(settings)
                
                return settings.dict(), 201
                
        except Exception as e:
            logger.exception("Error creating settings")
            return ErrorResponse(
                error="Internal server error",
                code="INTERNAL_ERROR",
                details=str(e)
            ).dict(), 500

    def put(self, route_id: UUID):
        """Update existing cost settings for a route."""
        logger = self.logger.bind(
            endpoint="route_settings",
            method="PUT",
            remote_ip=request.remote_addr,
            route_id=str(route_id)
        )
        logger.info("Updating cost settings")
        
        try:
            data = request.get_json()
            with get_db() as db:
                repository = CostSettingsRepository(db=db)
                
                # Check if settings exist
                existing = repository.get_by_route_id(route_id)
                if not existing:
                    return ErrorResponse(
                        error=f"No settings found for route {route_id}",
                        code="NOT_FOUND"
                    ).dict(), 404
                
                # Update settings
                for key, value in data.items():
                    setattr(existing, key, value)
                repository.update(existing)
                
                return existing.dict(), 200
                
        except Exception as e:
            logger.exception("Error updating settings")
            return ErrorResponse(
                error="Internal server error",
                code="INTERNAL_ERROR",
                details=str(e)
            ).dict(), 500

# Register resources
costs_bp.add_url_rule('/routes/<uuid:route_id>/calculate', 
                      view_func=RouteCalculationResource.as_view('route_calculation'))
costs_bp.add_url_rule('/routes/<uuid:route_id>/costs', 
                      view_func=RouteCalculationResource.as_view('route_costs'))
costs_bp.add_url_rule('/routes/<uuid:route_id>/settings', 
                      view_func=CostSettingsResource.as_view('route_settings'))
