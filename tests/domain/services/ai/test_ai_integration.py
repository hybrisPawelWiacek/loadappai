"""Test cases for AI integration service.

This module contains tests for the AI integration service.
"""
from datetime import datetime, timedelta
from typing import Dict, List
import pytest

from src.domain.services.ai.ai_integration import AIIntegrationService
from tests.infrastructure.base_test import BaseTestService
from tests.infrastructure.mock_factory import MockFactory

class TestAIIntegrationService:
    """Test cases for AI integration service."""
    
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
            fixture_path="tests/fixtures/ai"
        )
    
    @pytest.fixture
    def ai_service(
        self,
        mock_factory: MockFactory,
        test_service: BaseTestService
    ) -> AIIntegrationService:
        """Create AI integration service.
        
        Args:
            mock_factory: Mock factory
            test_service: Test service
            
        Returns:
            AI integration service
        """
        # Create mock cache service
        cache_service = mock_factory.create(
            'CacheService',
            get=lambda key: None,
            set=lambda key, value, ttl: True
        )
        
        # Create mock model client
        model_client = mock_factory.create(
            'AIModelClient',
            predict=lambda input: test_service.load_fixture(
                'model_prediction_1'
            )
        )
        
        return AIIntegrationService(
            cache_service=cache_service,
            model_client=model_client
        )
    
    def test_optimize_route(
        self,
        ai_service: AIIntegrationService,
        test_service: BaseTestService
    ) -> None:
        """Test route optimization.
        
        Args:
            ai_service: AI integration service
            test_service: Test service
        """
        # Load test data
        route_data = test_service.load_fixture('route_1')
        
        # Optimize route
        optimized = ai_service.optimize_route(route_data)
        
        # Verify optimization
        test_service.assert_true(
            optimized['total_distance'] <= route_data['total_distance']
        )
        test_service.assert_true(
            optimized['total_duration'] <= route_data['total_duration']
        )
    
    def test_predict_price(
        self,
        ai_service: AIIntegrationService,
        test_service: BaseTestService,
        mock_factory: MockFactory
    ) -> None:
        """Test price prediction.
        
        Args:
            ai_service: AI integration service
            test_service: Test service
            mock_factory: Mock factory
        """
        # Load test data
        route_data = test_service.load_fixture('route_1')
        market_data = test_service.load_fixture('market_data_1')
        
        # Predict price
        prediction = ai_service.predict_price(
            route=route_data,
            market_data=market_data
        )
        
        # Verify prediction
        test_service.assert_true(prediction.price > 0)
        test_service.assert_true(
            0 <= prediction.confidence <= 1
        )
        
        # Verify model called
        model_client = mock_factory.get_mocks()['AIModelClient']
        test_service.assert_equal(
            len(model_client.get_calls('predict')),
            1
        )
    
    def test_cached_prediction(
        self,
        ai_service: AIIntegrationService,
        test_service: BaseTestService,
        mock_factory: MockFactory
    ) -> None:
        """Test cached price prediction.
        
        Args:
            ai_service: AI integration service
            test_service: Test service
            mock_factory: Mock factory
        """
        # Load test data
        route_data = test_service.load_fixture('route_1')
        market_data = test_service.load_fixture('market_data_1')
        cached_prediction = test_service.load_fixture(
            'model_prediction_1'
        )
        
        # Setup cache hit
        cache_service = mock_factory.create(
            'CacheService',
            get=lambda key: cached_prediction,
            set=lambda key, value, ttl: True
        )
        ai_service._cache_service = cache_service
        
        # Predict price
        prediction = ai_service.predict_price(
            route=route_data,
            market_data=market_data
        )
        
        # Verify prediction
        test_service.assert_equal(
            prediction.price,
            cached_prediction['price']
        )
        
        # Verify model not called
        model_client = mock_factory.get_mocks()['AIModelClient']
        test_service.assert_equal(
            len(model_client.get_calls('predict')),
            0
        )
    
    def test_process_query(
        self,
        ai_service: AIIntegrationService,
        test_service: BaseTestService
    ) -> None:
        """Test natural language query processing.
        
        Args:
            ai_service: AI integration service
            test_service: Test service
        """
        # Process query
        result = ai_service.process_query(
            "What is the estimated cost for a truck from Berlin to Paris?"
        )
        
        # Verify result
        test_service.assert_true('route' in result)
        test_service.assert_true('cost' in result)
        test_service.assert_true('confidence' in result)
    
    def test_invalid_query(
        self,
        ai_service: AIIntegrationService,
        test_service: BaseTestService
    ) -> None:
        """Test invalid query processing.
        
        Args:
            ai_service: AI integration service
            test_service: Test service
        """
        # Process invalid query
        with pytest.raises(ValueError):
            ai_service.process_query("Invalid query")
    
    def test_model_selection(
        self,
        ai_service: AIIntegrationService,
        test_service: BaseTestService
    ) -> None:
        """Test AI model selection.
        
        Args:
            ai_service: AI integration service
            test_service: Test service
        """
        # Test different tasks
        route_model = ai_service.select_model("route_optimization")
        price_model = ai_service.select_model("price_prediction")
        nlp_model = ai_service.select_model("query_processing")
        
        # Verify different models selected
        test_service.assert_not_equal(
            route_model.name,
            price_model.name
        )
        test_service.assert_not_equal(
            price_model.name,
            nlp_model.name
        )
    
    def test_model_versioning(
        self,
        ai_service: AIIntegrationService,
        test_service: BaseTestService
    ) -> None:
        """Test AI model versioning.
        
        Args:
            ai_service: AI integration service
            test_service: Test service
        """
        # Get model versions
        v1 = ai_service.get_model_version("route_optimization")
        v2 = ai_service.get_model_version("route_optimization")
        
        # Verify version consistency
        test_service.assert_equal(v1, v2)
    
    def test_model_fallback(
        self,
        ai_service: AIIntegrationService,
        test_service: BaseTestService,
        mock_factory: MockFactory
    ) -> None:
        """Test AI model fallback.
        
        Args:
            ai_service: AI integration service
            test_service: Test service
            mock_factory: Mock factory
        """
        # Setup failing model
        model_client = mock_factory.create(
            'AIModelClient',
            predict=lambda input: None
        )
        ai_service._model_client = model_client
        
        # Load test data
        route_data = test_service.load_fixture('route_1')
        
        # Verify fallback used
        result = ai_service.optimize_route(route_data)
        test_service.assert_true(result['fallback_used'])
    
    def test_confidence_threshold(
        self,
        ai_service: AIIntegrationService,
        test_service: BaseTestService
    ) -> None:
        """Test confidence threshold.
        
        Args:
            ai_service: AI integration service
            test_service: Test service
        """
        # Load test data
        route_data = test_service.load_fixture('route_1')
        market_data = test_service.load_fixture('market_data_1')
        
        # Test different thresholds
        prediction_90 = ai_service.predict_price(
            route=route_data,
            market_data=market_data,
            min_confidence=0.9
        )
        prediction_50 = ai_service.predict_price(
            route=route_data,
            market_data=market_data,
            min_confidence=0.5
        )
        
        # Verify confidence levels
        test_service.assert_true(
            prediction_90.confidence >= 0.9
        )
        test_service.assert_true(
            prediction_50.confidence >= 0.5
        )
