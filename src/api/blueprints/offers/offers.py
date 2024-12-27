"""Offers blueprint for handling offer-related operations."""
from uuid import UUID
from flask import Blueprint, jsonify, request
from flask_restful import Resource

from src.domain.services import OfferGenerationService, CostCalculationService
from src.infrastructure.repositories.offer_repository import OfferRepository
from src.infrastructure.services.google_maps_service import GoogleMapsService
from src.infrastructure.services.openai_service import OpenAIService
from src.infrastructure.database import get_db
from src.infrastructure.logging import get_logger
from src.settings import get_settings
from src.api.models import (
    OfferResponse, OfferHistoryResponse, ErrorResponse
)

offers_bp = Blueprint('offers', __name__)

class OfferResource(Resource):
    """Resource for managing offers."""

    def __init__(self):
        self.logger = get_logger(__name__)

    def get(self, offer_id: UUID):
        """Get offer by ID with version history."""
        logger = self.logger.bind(
            endpoint="offer",
            method="GET",
            remote_ip=request.remote_addr,
            offer_id=str(offer_id)
        )
        logger.info("Getting offer")
        
        try:
            with get_db() as db:
                offer_repository = OfferRepository(db=db)
                
                # Get query parameters
                version = request.args.get('version')
                include_history = request.args.get('include_history', 'false').lower() == 'true'
                
                logger.info("Getting offer by ID",
                           version=version,
                           include_history=include_history)
                
                # Get offer
                if version:
                    offer = offer_repository.get_version(offer_id, version)
                else:
                    offer = offer_repository.get_by_id(offer_id)
                    
                if not offer:
                    logger.error("offer_not_found",
                                offer_id=offer_id,
                                version=version)
                    return ErrorResponse(
                        error=f"Offer with ID {offer_id} not found",
                        code="NOT_FOUND"
                    ).dict(), 404
                    
                # Get history if requested
                history = []
                if include_history:
                    history = offer_repository.get_history(offer_id)
                
                # Prepare response
                response = OfferResponse.from_domain(offer).dict()
                if include_history:
                    response['history'] = [OfferHistoryResponse.from_domain(h).dict() for h in history]
                    
                logger.info("offer_retrieved",
                           offer_id=offer_id,
                           version=offer.version,
                           history_count=len(history) if include_history else 0)
                return response, 200
                
        except Exception as e:
            logger.exception("Error retrieving offer")
            return ErrorResponse(
                error="Internal server error",
                code="INTERNAL_ERROR",
                details=str(e)
            ).dict(), 500

    def put(self, offer_id: UUID):
        """Update offer with version tracking."""
        logger = self.logger.bind(
            endpoint="offer",
            method="PUT",
            remote_ip=request.remote_addr,
            offer_id=str(offer_id)
        )
        logger.info("Updating offer")
        
        try:
            with get_db() as db:
                offer_repository = OfferRepository(db=db)
                
                # Get request data
                data = request.get_json()
                logger.info("received_update_request",
                           offer_id=offer_id,
                           data=data)
                
                # Get existing offer
                offer = offer_repository.get_by_id(offer_id)
                if not offer:
                    logger.error("offer_not_found",
                                offer_id=offer_id)
                    return ErrorResponse(
                        error=f"Offer with ID {offer_id} not found",
                        code="NOT_FOUND"
                    ).dict(), 404
                    
                # Initialize services
                settings = get_settings()
                try:
                    location_service = GoogleMapsService()
                except Exception as e:
                    logger.error("Failed to initialize GoogleMapsService", error=str(e))
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
                
                logger.info("offer_updated",
                           offer_id=offer_id,
                           new_version=updated_offer.version,
                           new_status=updated_offer.status)
                return OfferResponse.from_domain(saved_offer).dict(), 200
                
        except Exception as e:
            logger.exception("Error updating offer")
            return ErrorResponse(
                error="Internal server error",
                code="INTERNAL_ERROR",
                details=str(e)
            ).dict(), 500

class OfferListResource(Resource):
    """Resource for managing offer collections."""

    def __init__(self):
        self.logger = get_logger(__name__)

    def get(self):
        """List offers with filtering and pagination."""
        logger = self.logger.bind(
            endpoint="offer_list",
            method="GET",
            remote_ip=request.remote_addr
        )
        logger.info("Listing offers")
        
        try:
            with get_db() as db:
                offer_repository = OfferRepository(db=db)
                
                # Get query parameters
                status = request.args.get('status')
                page = int(request.args.get('page', 1))
                per_page = int(request.args.get('per_page', 10))
                
                # Get offers
                offers = offer_repository.list_offers(
                    status=status,
                    page=page,
                    per_page=per_page
                )
                
                # Prepare response
                response = {
                    'items': [OfferResponse.from_domain(o).dict() for o in offers],
                    'pagination': {
                        'page': page,
                        'per_page': per_page,
                        'total': len(offers)  # This should be updated to get actual total count
                    }
                }
                
                logger.info("offers_listed",
                           count=len(offers),
                           page=page,
                           per_page=per_page)
                return response, 200
                
        except Exception as e:
            logger.exception("Error listing offers")
            return ErrorResponse(
                error="Internal server error",
                code="INTERNAL_ERROR",
                details=str(e)
            ).dict(), 500

class OfferArchiveResource(Resource):
    """Resource for archiving offers."""

    def __init__(self):
        self.logger = get_logger(__name__)

    def post(self, offer_id: UUID):
        """Archive an offer."""
        logger = self.logger.bind(
            endpoint="offer_archive",
            method="POST",
            remote_ip=request.remote_addr,
            offer_id=str(offer_id)
        )
        logger.info("Archiving offer")
        
        try:
            with get_db() as db:
                offer_repository = OfferRepository(db=db)
                
                # Get request data
                data = request.get_json() or {}
                
                # Get existing offer
                offer = offer_repository.get_by_id(offer_id)
                if not offer:
                    logger.error("offer_not_found",
                                offer_id=offer_id)
                    return ErrorResponse(
                        error=f"Offer with ID {offer_id} not found",
                        code="NOT_FOUND"
                    ).dict(), 404
                    
                # Initialize services
                settings = get_settings()
                try:
                    location_service = GoogleMapsService()
                except Exception as e:
                    logger.error("Failed to initialize GoogleMapsService", error=str(e))
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
                
                logger.info("offer_archived",
                           offer_id=offer_id,
                           version=archived_offer.version)
                return OfferResponse.from_domain(saved_offer).dict(), 200
                
        except Exception as e:
            logger.exception("Error archiving offer")
            return ErrorResponse(
                error="Internal server error",
                code="INTERNAL_ERROR",
                details=str(e)
            ).dict(), 500

# Register resources
offers_bp.add_url_rule('/', view_func=OfferListResource.as_view('offer_list'))
offers_bp.add_url_rule('/<uuid:offer_id>', view_func=OfferResource.as_view('offer'))
offers_bp.add_url_rule('/<uuid:offer_id>/archive', view_func=OfferArchiveResource.as_view('offer_archive'))
