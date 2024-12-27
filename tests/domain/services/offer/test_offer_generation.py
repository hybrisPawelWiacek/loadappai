"""Test cases for offer generation service.

This module contains tests for the offer generation service.
"""
from datetime import datetime, timedelta
from typing import Dict, List
import pytest
import uuid

from src.domain.entities.offer import Offer, OfferStatus
from src.domain.services.offer.offer_generation import OfferGenerationService
from tests.infrastructure.base_test import BaseTestService
from tests.infrastructure.mock_factory import MockFactory

class TestOfferGenerationService:
    """Test cases for offer generation service."""
    
    @pytest.fixture
    def mock_factory(self) -> MockFactory:
        """Create mock factory.
        
        Returns:
            Mock factory
        """
        return MockFactory()
    
    @pytest.fixture
    def test_service(self) -> BaseTestService:
        """Create test service.
        
        Returns:
            Test service
        """
        return BaseTestService(
            fixture_path="tests/fixtures/offer"
        )
    
    @pytest.fixture
    def offer_service(
        self,
        mock_factory: MockFactory,
        test_service: BaseTestService
    ) -> OfferGenerationService:
        """Create offer generation service.
        
        Args:
            mock_factory: Mock factory
            test_service: Test service
            
        Returns:
            Offer generation service
        """
        # Create mock repository
        repository = mock_factory.create(
            'OfferRepository',
            save=lambda offer: offer,
            get=lambda id: test_service.load_fixture(
                'offer_1'
            )
        )
        
        # Create mock route service
        route_service = mock_factory.create(
            'RoutePlanningService',
            create_route=lambda **kwargs: test_service.load_fixture(
                'route_1'
            ),
            validate_route=lambda route: {
                'valid': True,
                'errors': []
            }
        )
        
        # Create mock cost service
        cost_service = mock_factory.create(
            'CostCalculationService',
            calculate_total_cost=lambda **kwargs: test_service.load_fixture(
                'cost_breakdown_1'
            )
        )
        
        # Create mock pricing service
        pricing_service = mock_factory.create(
            'PricingService',
            calculate_price=lambda **kwargs: test_service.load_fixture(
                'price_calculation_1'
            )
        )
        
        # Create mock AI service
        ai_service = mock_factory.create(
            'AIIntegrationService',
            predict_price=lambda **kwargs: test_service.load_fixture(
                'price_prediction_1'
            )
        )
        
        return OfferGenerationService(
            repository=repository,
            route_service=route_service,
            cost_service=cost_service,
            pricing_service=pricing_service,
            ai_service=ai_service
        )
    
    def test_create_offer(
        self,
        offer_service: OfferGenerationService,
        test_service: BaseTestService
    ) -> None:
        """Test offer creation.
        
        Args:
            offer_service: Offer generation service
            test_service: Test service
        """
        # Load test data
        request_data = test_service.load_fixture('offer_request_1')
        
        # Create offer
        offer = offer_service.create_offer(
            start_location=request_data['start_location'],
            end_location=request_data['end_location'],
            vehicle_type=request_data['vehicle_type'],
            cargo_type=request_data['cargo_type'],
            weight=request_data['weight']
        )
        
        # Verify offer
        test_service.assert_equal(
            offer.start_location,
            request_data['start_location']
        )
        test_service.assert_equal(
            offer.end_location,
            request_data['end_location']
        )
        test_service.assert_equal(
            offer.status,
            OfferStatus.DRAFT
        )
    
    def test_validate_offer(
        self,
        offer_service: OfferGenerationService,
        test_service: BaseTestService
    ) -> None:
        """Test offer validation.
        
        Args:
            offer_service: Offer generation service
            test_service: Test service
        """
        # Load test data
        offer_data = test_service.load_fixture('offer_1')
        
        # Create offer
        offer = Offer(**offer_data)
        
        # Validate offer
        result = offer_service.validate_offer(offer)
        
        # Verify result
        test_service.assert_true(result.valid)
        test_service.assert_equal(
            len(result.errors),
            0
        )
    
    def test_calculate_costs(
        self,
        offer_service: OfferGenerationService,
        test_service: BaseTestService,
        mock_factory: MockFactory
    ) -> None:
        """Test cost calculation.
        
        Args:
            offer_service: Offer generation service
            test_service: Test service
            mock_factory: Mock factory
        """
        # Load test data
        offer_data = test_service.load_fixture('offer_1')
        
        # Create offer
        offer = Offer(**offer_data)
        
        # Calculate costs
        costs = offer_service.calculate_costs(offer)
        
        # Verify costs
        test_service.assert_true(costs.total > 0)
        test_service.assert_true(costs.margin > 0)
        
        # Verify services called
        cost_service = mock_factory.get_mocks()['CostCalculationService']
        test_service.assert_equal(
            len(cost_service.get_calls('calculate_total_cost')),
            1
        )
    
    def test_generate_price(
        self,
        offer_service: OfferGenerationService,
        test_service: BaseTestService,
        mock_factory: MockFactory
    ) -> None:
        """Test price generation.
        
        Args:
            offer_service: Offer generation service
            test_service: Test service
            mock_factory: Mock factory
        """
        # Load test data
        offer_data = test_service.load_fixture('offer_1')
        
        # Create offer
        offer = Offer(**offer_data)
        
        # Generate price
        price = offer_service.generate_price(offer)
        
        # Verify price
        test_service.assert_true(price.amount > 0)
        test_service.assert_true(
            0 <= price.confidence <= 1
        )
        
        # Verify services called
        pricing_service = mock_factory.get_mocks()['PricingService']
        ai_service = mock_factory.get_mocks()['AIIntegrationService']
        
        test_service.assert_equal(
            len(pricing_service.get_calls('calculate_price')),
            1
        )
        test_service.assert_equal(
            len(ai_service.get_calls('predict_price')),
            1
        )
    
    def test_finalize_offer(
        self,
        offer_service: OfferGenerationService,
        test_service: BaseTestService,
        mock_factory: MockFactory
    ) -> None:
        """Test offer finalization.
        
        Args:
            offer_service: Offer generation service
            test_service: Test service
            mock_factory: Mock factory
        """
        # Load test data
        offer_data = test_service.load_fixture('offer_1')
        
        # Create offer
        offer = Offer(**offer_data)
        
        # Finalize offer
        finalized = offer_service.finalize_offer(offer)
        
        # Verify finalization
        test_service.assert_equal(
            finalized.status,
            OfferStatus.ACTIVE
        )
        test_service.assert_true(
            finalized.valid_until > datetime.utcnow()
        )
        
        # Verify repository called
        repository = mock_factory.get_mocks()['OfferRepository']
        test_service.assert_equal(
            len(repository.get_calls('save')),
            1
        )
    
    def test_generate_alternatives(
        self,
        offer_service: OfferGenerationService,
        test_service: BaseTestService
    ) -> None:
        """Test alternative offer generation.
        
        Args:
            offer_service: Offer generation service
            test_service: Test service
        """
        # Load test data
        offer_data = test_service.load_fixture('offer_1')
        
        # Create offer
        offer = Offer(**offer_data)
        
        # Generate alternatives
        alternatives = offer_service.generate_alternatives(
            offer,
            count=3
        )
        
        # Verify alternatives
        test_service.assert_equal(len(alternatives), 3)
        for alt in alternatives:
            test_service.assert_not_equal(
                alt.id,
                offer.id
            )
            test_service.assert_true(
                alt.price != offer.price
            )
    
    def test_offer_expiration(
        self,
        offer_service: OfferGenerationService,
        test_service: BaseTestService
    ) -> None:
        """Test offer expiration.
        
        Args:
            offer_service: Offer generation service
            test_service: Test service
        """
        # Load test data
        offer_data = test_service.load_fixture('offer_1')
        
        # Create expired offer
        offer = Offer(**offer_data)
        offer.valid_until = datetime.utcnow() - timedelta(days=1)
        
        # Verify expired
        test_service.assert_true(
            offer_service.is_expired(offer)
        )
        
        # Verify can't finalize
        with pytest.raises(ValueError):
            offer_service.finalize_offer(offer)
    
    def test_offer_versioning(
        self,
        offer_service: OfferGenerationService,
        test_service: BaseTestService
    ) -> None:
        """Test offer versioning.
        
        Args:
            offer_service: Offer generation service
            test_service: Test service
        """
        # Load test data
        offer_data = test_service.load_fixture('offer_1')
        
        # Create offer
        offer = Offer(**offer_data)
        
        # Create new version
        new_version = offer_service.create_version(offer)
        
        # Verify versioning
        test_service.assert_not_equal(
            new_version.id,
            offer.id
        )
        test_service.assert_equal(
            new_version.parent_id,
            offer.id
        )
        test_service.assert_true(
            new_version.version > offer.version
        )
    
    def test_bulk_generation(
        self,
        offer_service: OfferGenerationService,
        test_service: BaseTestService
    ) -> None:
        """Test bulk offer generation.
        
        Args:
            offer_service: Offer generation service
            test_service: Test service
        """
        # Load test data
        requests = test_service.load_fixture('bulk_requests_1')
        
        # Generate offers
        offers = offer_service.generate_bulk(requests)
        
        # Verify generation
        test_service.assert_equal(
            len(offers),
            len(requests)
        )
        for offer in offers:
            test_service.assert_true(
                isinstance(offer, Offer)
            )
    
    def test_offer_optimization(
        self,
        offer_service: OfferGenerationService,
        test_service: BaseTestService,
        mock_factory: MockFactory
    ) -> None:
        """Test offer optimization.
        
        Args:
            offer_service: Offer generation service
            test_service: Test service
            mock_factory: Mock factory
        """
        # Load test data
        offer_data = test_service.load_fixture('offer_1')
        
        # Create offer
        offer = Offer(**offer_data)
        
        # Optimize offer
        optimized = offer_service.optimize_offer(offer)
        
        # Verify optimization
        test_service.assert_true(
            optimized.total_cost <= offer.total_cost
        )
        
        # Verify AI service called
        ai_service = mock_factory.get_mocks()['AIIntegrationService']
        test_service.assert_equal(
            len(ai_service.get_calls('optimize_route')),
            1
        )
