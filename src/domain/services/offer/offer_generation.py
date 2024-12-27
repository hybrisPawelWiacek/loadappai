"""Offer generation service implementation.

This module implements the offer generation service interface.
It provides functionality for:
- Generating commercial offers
- Calculating final prices with margins
- Integrating with AI for offer enhancement
- Handling offer versioning and updates
- Tracking offer history and status changes
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID

from src.domain.entities.offer import Offer, OfferStatus, OfferHistory
from src.domain.entities.route import Route, TransportType
from src.domain.entities.cost import Cost, CostSettings
from src.domain.entities.cargo import Cargo
from src.domain.interfaces.services.ai_service import AIService
from src.domain.services.common.base import BaseService
from src.domain.services.cost.cost_calculation import CostCalculationService
from src.domain.services.offer.pricing import PricingService
from src.domain.value_objects import PricePrediction

class OfferGenerationService(BaseService):
    """Service for generating transport offers.
    
    This service is responsible for:
    - Generating commercial offers
    - Calculating final prices with margins
    - Integrating with AI for offer enhancement
    - Handling offer versioning and updates
    - Tracking offer history and status changes
    """
    
    def __init__(
        self,
        repository: 'OfferRepository',
        route_service: 'RoutePlanningService',
        cost_service: Optional[CostCalculationService] = None,
        pricing_service: Optional[PricingService] = None,
        ai_service: Optional[AIService] = None
    ):
        """Initialize offer generation service.
        
        Args:
            repository: Repository for offer storage
            route_service: Service for route planning
            cost_service: Optional service for cost calculation
            pricing_service: Optional service for pricing
            ai_service: Optional service for AI integration
        """
        super().__init__()
        self.repository = repository
        self.route_service = route_service
        self.cost_service = cost_service or CostCalculationService()
        self.pricing_service = pricing_service or PricingService()
        self.ai_service = ai_service
    
    def generate_offer(
        self,
        route: Route,
        margin: float,
        settings: Optional[CostSettings] = None,
        cargo: Optional[Cargo] = None,
        transport_type: Optional[TransportType] = None,
        metadata: Optional[Dict] = None,
        created_by: Optional[str] = None,
        status: str = "draft",
        total_cost: Optional[float] = None
    ) -> Offer:
        """Generate an offer for a given route with specified margin.
        
        Args:
            route: Route for the offer
            margin: Profit margin percentage
            settings: Optional cost settings
            cargo: Optional cargo details
            transport_type: Optional transport type
            metadata: Optional metadata
            created_by: Optional username of creator
            status: Initial status (default: draft)
            total_cost: Optional pre-calculated total cost
            
        Returns:
            Generated offer
            
        Raises:
            ValueError: If offer generation fails
        """
        try:
            # Calculate costs if not provided
            if total_cost is None:
                cost_breakdown = self.cost_service.calculate_detailed_cost(
                    route=route,
                    settings=settings,
                    cargo_spec=cargo.specifications if cargo else None,
                    vehicle_spec=None,  # TODO: Add vehicle specs
                    include_empty_driving=True,
                    include_country_breakdown=True
                )
                total_cost = float(cost_breakdown.total)
            
            # Calculate price with margin
            price = self.pricing_service.calculate_price(
                total_cost=total_cost,
                margin=margin
            )
            
            # Get AI price prediction if available
            ai_prediction = None
            if self.ai_service:
                try:
                    ai_prediction = self.ai_service.predict_price(
                        route=route,
                        cargo_type=cargo.type if cargo else None
                    )
                except Exception as e:
                    self.logger.warning(
                        "AI price prediction failed",
                        error=str(e)
                    )
            
            # Create offer
            offer = Offer(
                route_id=route.id,
                total_cost=total_cost,
                price=price,
                margin=margin,
                status=status,
                created_by=created_by,
                valid_until=datetime.utcnow() + timedelta(days=7),
                metadata=metadata or {},
                ai_prediction=ai_prediction.dict() if ai_prediction else None
            )
            
            # Save offer
            saved_offer = self.repository.save(offer)
            
            self.logger.info(
                "Offer generated",
                offer_id=str(saved_offer.id),
                route_id=str(route.id),
                total_cost=total_cost,
                price=price
            )
            
            return saved_offer
            
        except Exception as e:
            self.logger.error(
                "Offer generation failed",
                error=str(e),
                route_id=str(route.id)
            )
            raise ValueError(f"Failed to generate offer: {str(e)}")
    
    def update_offer(
        self,
        offer: Offer,
        margin: Optional[float] = None,
        status: Optional[str] = None,
        metadata: Optional[Dict] = None,
        modified_by: Optional[str] = None,
        change_reason: Optional[str] = None
    ) -> Offer:
        """Update an existing offer with new details.
        
        Args:
            offer: Offer to update
            margin: Optional new margin
            status: Optional new status
            metadata: Optional new metadata
            modified_by: Optional username of modifier
            change_reason: Optional reason for change
            
        Returns:
            Updated offer
            
        Raises:
            ValueError: If update fails
        """
        try:
            # Validate status transition
            if status and status != offer.status:
                self._validate_status_transition(
                    current_status=offer.status,
                    new_status=status
                )
            
            # Update offer
            offer.margin = margin if margin is not None else offer.margin
            offer.status = status if status else offer.status
            offer.metadata.update(metadata or {})
            offer.modified_by = modified_by
            offer.modified_at = datetime.utcnow()
            
            # Recalculate price if margin changed
            if margin is not None:
                offer.price = self.pricing_service.calculate_price(
                    total_cost=offer.total_cost,
                    margin=margin
                )
            
            # Create history entry
            history = OfferHistory(
                offer_id=offer.id,
                change_type="update",
                old_status=offer.status,
                new_status=status if status else offer.status,
                modified_by=modified_by,
                change_reason=change_reason
            )
            
            # Save changes
            updated_offer = self.repository.save(offer)
            self.repository.save_history(history)
            
            self.logger.info(
                "Offer updated",
                offer_id=str(offer.id),
                status=status,
                modified_by=modified_by
            )
            
            return updated_offer
            
        except Exception as e:
            self.logger.error(
                "Offer update failed",
                error=str(e),
                offer_id=str(offer.id)
            )
            raise ValueError(f"Failed to update offer: {str(e)}")
    
    def archive_offer(
        self,
        offer: Offer,
        archived_by: Optional[str] = None,
        archive_reason: Optional[str] = None
    ) -> Offer:
        """Archive an offer, making it inactive.
        
        Args:
            offer: Offer to archive
            archived_by: Optional username of archiver
            archive_reason: Optional reason for archiving
            
        Returns:
            Archived offer
            
        Raises:
            ValueError: If archiving fails
        """
        try:
            # Update offer status
            return self.update_offer(
                offer=offer,
                status="archived",
                modified_by=archived_by,
                change_reason=archive_reason
            )
            
        except Exception as e:
            self.logger.error(
                "Offer archiving failed",
                error=str(e),
                offer_id=str(offer.id)
            )
            raise ValueError(f"Failed to archive offer: {str(e)}")
    
    def _validate_status_transition(
        self,
        current_status: str,
        new_status: str
    ) -> None:
        """Validate if a status transition is allowed.
        
        Args:
            current_status: Current offer status
            new_status: New offer status
            
        Raises:
            ValueError: If transition is not allowed
        """
        # Define allowed transitions
        allowed_transitions = {
            "draft": {"active", "archived"},
            "active": {"expired", "archived"},
            "expired": {"archived"},
            "archived": set()  # No transitions from archived
        }
        
        # Check if transition is allowed
        if new_status not in allowed_transitions.get(current_status, set()):
            raise ValueError(
                f"Invalid status transition from {current_status} to {new_status}"
            )

    def validate_offer(self, offer: Offer) -> Dict[str, Any]:
        """Validate an offer.
        
        Args:
            offer: Offer to validate
            
        Returns:
            Dict with validation results
            
        Raises:
            ValueError: If validation fails
        """
        try:
            errors = []
            
            # Check required fields
            if not offer.route_id:
                errors.append("Missing route ID")
            if offer.total_cost <= 0:
                errors.append("Invalid total cost")
            if offer.price <= 0:
                errors.append("Invalid price")
            if offer.margin < 0:
                errors.append("Invalid margin")
                
            # Check dates
            if offer.valid_until <= datetime.utcnow():
                errors.append("Offer has expired")
            
            # Check status
            if offer.status not in {"draft", "active", "expired", "archived"}:
                errors.append("Invalid status")
            
            return {
                "valid": len(errors) == 0,
                "errors": errors
            }
            
        except Exception as e:
            self.logger.error(
                "Offer validation failed",
                error=str(e),
                offer_id=str(offer.id)
            )
            raise ValueError(f"Failed to validate offer: {str(e)}")

    def generate_alternatives(
        self,
        offer: Offer,
        count: int = 3
    ) -> List[Offer]:
        """Generate alternative offers.
        
        Args:
            offer: Base offer
            count: Number of alternatives to generate
            
        Returns:
            List of alternative offers
            
        Raises:
            ValueError: If generation fails
        """
        try:
            alternatives = []
            
            # Get route and cost details
            route = self.route_service.get_route(offer.route_id)
            
            # Generate alternatives with different margins
            margins = [
                offer.margin * 0.9,  # 10% lower
                offer.margin * 1.1,  # 10% higher
                offer.margin * 1.2   # 20% higher
            ]
            
            for margin in margins[:count]:
                alt = self.generate_offer(
                    route=route,
                    margin=margin,
                    total_cost=offer.total_cost,
                    metadata={
                        "alternative_for": str(offer.id),
                        "original_margin": offer.margin
                    }
                )
                alternatives.append(alt)
            
            return alternatives
            
        except Exception as e:
            self.logger.error(
                "Alternative generation failed",
                error=str(e),
                offer_id=str(offer.id)
            )
            raise ValueError(f"Failed to generate alternatives: {str(e)}")

    def create_version(self, offer: Offer) -> Offer:
        """Create a new version of an offer.
        
        Args:
            offer: Offer to version
            
        Returns:
            New version of the offer
            
        Raises:
            ValueError: If versioning fails
        """
        try:
            # Create new version
            new_version = Offer(
                route_id=offer.route_id,
                total_cost=offer.total_cost,
                price=offer.price,
                margin=offer.margin,
                status="draft",
                created_by=offer.modified_by or offer.created_by,
                valid_until=datetime.utcnow() + timedelta(days=7),
                metadata=offer.metadata.copy(),
                parent_id=offer.id,
                version=offer.version + 1
            )
            
            # Save new version
            return self.repository.save(new_version)
            
        except Exception as e:
            self.logger.error(
                "Offer versioning failed",
                error=str(e),
                offer_id=str(offer.id)
            )
            raise ValueError(f"Failed to create version: {str(e)}")

    def generate_bulk(
        self,
        requests: List[Dict]
    ) -> List[Offer]:
        """Generate multiple offers in bulk.
        
        Args:
            requests: List of offer generation requests
            
        Returns:
            List of generated offers
            
        Raises:
            ValueError: If bulk generation fails
        """
        try:
            offers = []
            
            for request in requests:
                try:
                    # Create route
                    route = self.route_service.create_route(
                        origin=request['origin'],
                        destination=request['destination'],
                        pickup_time=request['pickup_time'],
                        delivery_time=request['delivery_time'],
                        transport_type=request.get('transport_type')
                    )
                    
                    # Generate offer
                    offer = self.generate_offer(
                        route=route,
                        margin=request['margin'],
                        metadata=request.get('metadata')
                    )
                    
                    offers.append(offer)
                    
                except Exception as e:
                    self.logger.warning(
                        "Failed to generate offer in bulk",
                        error=str(e),
                        request=request
                    )
            
            if not offers:
                raise ValueError("No offers were generated")
                
            return offers
            
        except Exception as e:
            self.logger.error(
                "Bulk generation failed",
                error=str(e)
            )
            raise ValueError(f"Failed to generate offers in bulk: {str(e)}")

    def optimize_offer(self, offer: Offer) -> Offer:
        """Optimize an offer using AI.
        
        Args:
            offer: Offer to optimize
            
        Returns:
            Optimized offer
            
        Raises:
            ValueError: If optimization fails
        """
        try:
            if not self.ai_service:
                raise ValueError("AI service not available")
                
            # Get route
            route = self.route_service.get_route(offer.route_id)
            
            # Optimize route
            optimized_route = self.ai_service.optimize_route(route)
            
            # Calculate new costs
            cost_breakdown = self.cost_service.calculate_detailed_cost(
                route=optimized_route
            )
            
            # Generate new offer
            return self.generate_offer(
                route=optimized_route,
                margin=offer.margin,
                total_cost=float(cost_breakdown.total),
                metadata={
                    "optimized_from": str(offer.id),
                    "optimization_time": datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            self.logger.error(
                "Offer optimization failed",
                error=str(e),
                offer_id=str(offer.id)
            )
            raise ValueError(f"Failed to optimize offer: {str(e)}")

    def is_expired(self, offer: Offer) -> bool:
        """Check if an offer has expired.
        
        Args:
            offer: Offer to check
            
        Returns:
            True if expired, False otherwise
        """
        return offer.valid_until <= datetime.utcnow()
