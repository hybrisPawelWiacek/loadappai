"""Settings blueprint for managing various application settings."""
from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_restful import Resource
from pydantic import ValidationError

from src.domain.models import (
    CostSettings, CostSettingsUpdateRequest, SystemSettings,
    TransportSettings
)
from src.domain.responses import (
    CostSettingsResponse, CostSettingsUpdateResponse, ErrorResponse
)
from src.infrastructure.repositories.cost_settings_repository import CostSettingsRepository
from src.infrastructure.database import get_db
from src.infrastructure.logging import get_logger

settings_bp = Blueprint('settings', __name__)

class CostSettingsResource(Resource):
    """Resource for managing cost settings."""

    def __init__(self):
        self.logger = get_logger(__name__)

    def get(self):
        """Get current cost settings."""
        logger = self.logger.bind(
            endpoint="cost_settings",
            method="GET",
            remote_ip=request.remote_addr
        )
        logger.info("Getting cost settings")
        
        try:
            with get_db() as db:
                cost_settings_repository = CostSettingsRepository(db=db)
                settings = cost_settings_repository.get_current_cost_settings()
                
                if not settings:
                    logger.error("cost_settings_not_found")
                    return ErrorResponse(
                        error="No cost settings found",
                        code="NOT_FOUND"
                    ).dict(), 404
                    
                logger.info("cost_settings_retrieved")
                return settings.dict(), 200
                
        except Exception as e:
            logger.exception("Error retrieving cost settings")
            return ErrorResponse(
                error="Internal server error",
                code="INTERNAL_ERROR",
                details=str(e)
            ).dict(), 500

    def post(self):
        """Create new cost settings."""
        return self._update_settings('POST')

    def put(self):
        """Update existing cost settings."""
        return self._update_settings('PUT')

    def _update_settings(self, method):
        """Internal method for updating settings."""
        logger = self.logger.bind(
            endpoint="cost_settings",
            method=method,
            remote_ip=request.remote_addr
        )
        logger.info("Updating cost settings")
        
        try:
            with get_db() as db:
                cost_settings_repository = CostSettingsRepository(db=db)
                data = request.get_json()
                
                if method == 'POST':
                    settings_data = CostSettings(**data)
                else:
                    settings_data = CostSettingsUpdateRequest(**data)
                
                updated = cost_settings_repository.update(settings_data)
                logger.info("cost_settings_updated",
                           countries=list(updated.fuel_prices.keys()))
                
                response = CostSettingsResponse(
                    settings=updated,
                    message="Cost settings updated successfully",
                    updated_at=datetime.utcnow()
                )
                
                return response.dict(), 200
                
        except ValidationError as e:
            logger.error("validation_error", errors=e.errors())
            return ErrorResponse(
                error=str(e),
                code="VALIDATION_ERROR"
            ).dict(), 400
            
        except Exception as e:
            logger.exception("Error updating cost settings")
            return ErrorResponse(
                error="Internal server error",
                code="INTERNAL_ERROR",
                details=str(e)
            ).dict(), 500

class TransportSettingsResource(Resource):
    """Resource for managing transport settings."""

    def __init__(self):
        self.logger = get_logger(__name__)

    def get(self):
        """Get current transport settings."""
        logger = self.logger.bind(
            endpoint="transport_settings",
            method="GET",
            remote_ip=request.remote_addr
        )
        logger.info("Getting transport settings")
        
        try:
            with get_db() as db:
                cost_settings_repository = CostSettingsRepository(db=db)
                settings = cost_settings_repository.get_transport_settings()
                
                logger.info("transport_settings_retrieved")
                return settings.dict(), 200
                
        except Exception as e:
            logger.exception("Error retrieving transport settings")
            return ErrorResponse(
                error="Internal server error",
                code="INTERNAL_ERROR",
                details=str(e)
            ).dict(), 500

    def put(self):
        """Update transport settings."""
        logger = self.logger.bind(
            endpoint="transport_settings",
            method="PUT",
            remote_ip=request.remote_addr
        )
        logger.info("Updating transport settings")
        
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
                
                logger.info("transport_settings_updated")
                return response.dict(), 200
                
        except ValidationError as e:
            logger.error("validation_error", errors=e.errors())
            return ErrorResponse(
                error=str(e),
                code="VALIDATION_ERROR"
            ).dict(), 400
            
        except Exception as e:
            logger.exception("Error updating transport settings")
            return ErrorResponse(
                error="Internal server error",
                code="INTERNAL_ERROR",
                details=str(e)
            ).dict(), 500

class SystemSettingsResource(Resource):
    """Resource for managing system settings."""

    def __init__(self):
        self.logger = get_logger(__name__)

    def get(self):
        """Get current system settings."""
        logger = self.logger.bind(
            endpoint="system_settings",
            method="GET",
            remote_ip=request.remote_addr
        )
        logger.info("Getting system settings")
        
        try:
            with get_db() as db:
                cost_settings_repository = CostSettingsRepository(db=db)
                settings = cost_settings_repository.get_system_settings()
                
                logger.info("system_settings_retrieved")
                return settings.dict(), 200
                
        except Exception as e:
            logger.exception("Error retrieving system settings")
            return ErrorResponse(
                error="Internal server error",
                code="INTERNAL_ERROR",
                details=str(e)
            ).dict(), 500

    def put(self):
        """Update system settings."""
        logger = self.logger.bind(
            endpoint="system_settings",
            method="PUT",
            remote_ip=request.remote_addr
        )
        logger.info("Updating system settings")
        
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
                
                logger.info("system_settings_updated")
                return response.dict(), 200
                
        except ValidationError as e:
            logger.error("validation_error", errors=e.errors())
            return ErrorResponse(
                error=str(e),
                code="VALIDATION_ERROR"
            ).dict(), 400
            
        except Exception as e:
            logger.exception("Error updating system settings")
            return ErrorResponse(
                error="Internal server error",
                code="INTERNAL_ERROR",
                details=str(e)
            ).dict(), 500

# Register resources
settings_bp.add_url_rule('/cost', view_func=CostSettingsResource.as_view('cost_settings'))
settings_bp.add_url_rule('/transport', view_func=TransportSettingsResource.as_view('transport_settings'))
settings_bp.add_url_rule('/system', view_func=SystemSettingsResource.as_view('system_settings'))
