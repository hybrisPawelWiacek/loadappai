"""Test cases for route planning service.

This module contains tests for the route planning service.
"""
from datetime import datetime, timedelta
from typing import Dict, List
import pytest

from src.domain.entities.route import Route, RouteStatus
from src.domain.services.route.route_planning import RoutePlanningService
from tests.infrastructure.base_test import BaseTestService
from tests.infrastructure.mock_factory import MockFactory

class TestRoutePlanningService:
    """Test cases for route planning service."""
    
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
            fixture_path="tests/fixtures/route"
        )
    
    @pytest.fixture
    def route_service(
        self,
        mock_factory: MockFactory,
        test_service: BaseTestService
    ) -> RoutePlanningService:
        """Create route planning service.
        
        Args:
            mock_factory: Mock factory
            test_service: Test service
            
        Returns:
            Route planning service
        """
        # Create mock repository
        repository = mock_factory.create(
            'RouteRepository',
            save=lambda route: route,
            get=lambda id: test_service.load_fixture(
                'route_1'
            )
        )
        
        # Create mock location service
        location_service = mock_factory.create(
            'LocationService',
            calculate_distance=lambda start, end: 100.0,
            estimate_duration=lambda start, end: timedelta(hours=2)
        )
        
        return RoutePlanningService(
            repository=repository,
            location_service=location_service
        )
    
    def test_create_route(
        self,
        route_service: RoutePlanningService,
        test_service: BaseTestService
    ) -> None:
        """Test route creation.
        
        Args:
            route_service: Route planning service
            test_service: Test service
        """
        # Load test data
        route_data = test_service.load_fixture('route_1')
        
        # Create route
        route = route_service.create_route(
            start_location=route_data['start_location'],
            end_location=route_data['end_location'],
            vehicle_type=route_data['vehicle_type']
        )
        
        # Verify route
        test_service.assert_equal(
            route.start_location,
            route_data['start_location']
        )
        test_service.assert_equal(
            route.end_location,
            route_data['end_location']
        )
        test_service.assert_equal(
            route.vehicle_type,
            route_data['vehicle_type']
        )
        test_service.assert_equal(
            route.status,
            RouteStatus.CREATED
        )
    
    def test_validate_route(
        self,
        route_service: RoutePlanningService,
        test_service: BaseTestService
    ) -> None:
        """Test route validation.
        
        Args:
            route_service: Route planning service
            test_service: Test service
        """
        # Load test data
        route_data = test_service.load_fixture('route_1')
        
        # Create route
        route = Route(**route_data)
        
        # Validate route
        result = route_service.validate_route(route)
        
        # Verify result
        test_service.assert_true(result.valid)
        test_service.assert_equal(
            len(result.errors),
            0
        )
    
    def test_validate_invalid_route(
        self,
        route_service: RoutePlanningService,
        test_service: BaseTestService
    ) -> None:
        """Test invalid route validation.
        
        Args:
            route_service: Route planning service
            test_service: Test service
        """
        # Load test data
        route_data = test_service.load_fixture('invalid_route')
        
        # Create route
        route = Route(**route_data)
        
        # Validate route
        result = route_service.validate_route(route)
        
        # Verify result
        test_service.assert_false(result.valid)
        test_service.assert_true(len(result.errors) > 0)
    
    def test_update_route_status(
        self,
        route_service: RoutePlanningService,
        test_service: BaseTestService,
        mock_factory: MockFactory
    ) -> None:
        """Test route status update.
        
        Args:
            route_service: Route planning service
            test_service: Test service
            mock_factory: Mock factory
        """
        # Load test data
        route_data = test_service.load_fixture('route_1')
        
        # Create route
        route = Route(**route_data)
        
        # Update status
        updated = route_service.update_route_status(
            route,
            RouteStatus.IN_PROGRESS
        )
        
        # Verify update
        test_service.assert_equal(
            updated.status,
            RouteStatus.IN_PROGRESS
        )
        
        # Verify repository called
        repository = mock_factory.get_mocks()['RouteRepository']
        test_service.assert_equal(
            len(repository.get_calls('save')),
            1
        )
    
    def test_calculate_empty_driving(
        self,
        route_service: RoutePlanningService,
        test_service: BaseTestService,
        mock_factory: MockFactory
    ) -> None:
        """Test empty driving calculation.
        
        Args:
            route_service: Route planning service
            test_service: Test service
            mock_factory: Mock factory
        """
        # Load test data
        route_data = test_service.load_fixture('route_1')
        
        # Create route
        route = Route(**route_data)
        
        # Calculate empty driving
        result = route_service.calculate_empty_driving(route)
        
        # Verify result
        test_service.assert_true(result.distance > 0)
        test_service.assert_true(
            isinstance(result.duration, timedelta)
        )
        
        # Verify location service called
        location_service = mock_factory.get_mocks()['LocationService']
        test_service.assert_equal(
            len(location_service.get_calls('calculate_distance')),
            1
        )
    
    def test_optimize_route(
        self,
        route_service: RoutePlanningService,
        test_service: BaseTestService
    ) -> None:
        """Test route optimization.
        
        Args:
            route_service: Route planning service
            test_service: Test service
        """
        # Load test data
        route_data = test_service.load_fixture('route_1')
        
        # Create route
        route = Route(**route_data)
        
        # Optimize route
        optimized = route_service.optimize_route(route)
        
        # Verify optimization
        test_service.assert_true(
            optimized.total_distance <= route.total_distance
        )
        test_service.assert_true(
            optimized.total_duration <= route.total_duration
        )
    
    def test_get_route_history(
        self,
        route_service: RoutePlanningService,
        test_service: BaseTestService,
        mock_factory: MockFactory
    ) -> None:
        """Test route history retrieval.
        
        Args:
            route_service: Route planning service
            test_service: Test service
            mock_factory: Mock factory
        """
        # Load test data
        route_data = test_service.load_fixture('route_1')
        
        # Create route
        route = Route(**route_data)
        
        # Get history
        history = route_service.get_route_history(route.id)
        
        # Verify history
        test_service.assert_true(len(history) > 0)
        test_service.assert_equal(
            history[0].route_id,
            route.id
        )
        
        # Verify repository called
        repository = mock_factory.get_mocks()['RouteRepository']
        test_service.assert_equal(
            len(repository.get_calls('get_history')),
            1
        )
