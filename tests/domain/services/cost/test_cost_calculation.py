"""Test cases for cost calculation service.

This module contains tests for the cost calculation service.
"""
from datetime import datetime, timedelta
from typing import Dict, List
import pytest

from src.domain.entities.cost import CostBreakdown
from src.domain.services.cost.cost_calculation import CostCalculationService
from tests.infrastructure.base_test import BaseTestService
from tests.infrastructure.mock_factory import MockFactory

class TestCostCalculationService:
    """Test cases for cost calculation service."""
    
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
            fixture_path="tests/fixtures/cost"
        )
    
    @pytest.fixture
    def cost_service(
        self,
        mock_factory: MockFactory,
        test_service: BaseTestService
    ) -> CostCalculationService:
        """Create cost calculation service.
        
        Args:
            mock_factory: Mock factory
            test_service: Test service
            
        Returns:
            Cost calculation service
        """
        # Create mock settings service
        settings_service = mock_factory.create(
            'CostSettingsService',
            get_settings=lambda: test_service.load_fixture(
                'cost_settings_1'
            )
        )
        
        # Create mock toll service
        toll_service = mock_factory.create(
            'TollRateService',
            calculate_toll=lambda route, vehicle: 50.0
        )
        
        return CostCalculationService(
            settings_service=settings_service,
            toll_service=toll_service
        )
    
    def test_calculate_fuel_cost(
        self,
        cost_service: CostCalculationService,
        test_service: BaseTestService
    ) -> None:
        """Test fuel cost calculation.
        
        Args:
            cost_service: Cost calculation service
            test_service: Test service
        """
        # Load test data
        route_data = test_service.load_fixture('route_1')
        settings = test_service.load_fixture('cost_settings_1')
        
        # Calculate fuel cost
        cost = cost_service.calculate_fuel_cost(
            distance=route_data['total_distance'],
            vehicle_type=route_data['vehicle_type'],
            settings=settings
        )
        
        # Verify cost
        test_service.assert_true(cost > 0)
        test_service.assert_true(
            isinstance(cost, float)
        )
    
    def test_calculate_toll_cost(
        self,
        cost_service: CostCalculationService,
        test_service: BaseTestService,
        mock_factory: MockFactory
    ) -> None:
        """Test toll cost calculation.
        
        Args:
            cost_service: Cost calculation service
            test_service: Test service
            mock_factory: Mock factory
        """
        # Load test data
        route_data = test_service.load_fixture('route_1')
        
        # Calculate toll cost
        cost = cost_service.calculate_toll_cost(
            route=route_data,
            vehicle_type=route_data['vehicle_type']
        )
        
        # Verify cost
        test_service.assert_equal(cost, 50.0)
        
        # Verify toll service called
        toll_service = mock_factory.get_mocks()['TollRateService']
        test_service.assert_equal(
            len(toll_service.get_calls('calculate_toll')),
            1
        )
    
    def test_calculate_driver_cost(
        self,
        cost_service: CostCalculationService,
        test_service: BaseTestService
    ) -> None:
        """Test driver cost calculation.
        
        Args:
            cost_service: Cost calculation service
            test_service: Test service
        """
        # Load test data
        route_data = test_service.load_fixture('route_1')
        settings = test_service.load_fixture('cost_settings_1')
        
        # Calculate driver cost
        cost = cost_service.calculate_driver_cost(
            duration=timedelta(hours=8),
            driver_type="standard",
            settings=settings
        )
        
        # Verify cost
        test_service.assert_true(cost > 0)
        test_service.assert_true(
            isinstance(cost, float)
        )
    
    def test_calculate_maintenance_cost(
        self,
        cost_service: CostCalculationService,
        test_service: BaseTestService
    ) -> None:
        """Test maintenance cost calculation.
        
        Args:
            cost_service: Cost calculation service
            test_service: Test service
        """
        # Load test data
        route_data = test_service.load_fixture('route_1')
        settings = test_service.load_fixture('cost_settings_1')
        
        # Calculate maintenance cost
        cost = cost_service.calculate_maintenance_cost(
            distance=route_data['total_distance'],
            vehicle_type=route_data['vehicle_type'],
            settings=settings
        )
        
        # Verify cost
        test_service.assert_true(cost > 0)
        test_service.assert_true(
            isinstance(cost, float)
        )
    
    def test_calculate_overhead_cost(
        self,
        cost_service: CostCalculationService,
        test_service: BaseTestService
    ) -> None:
        """Test overhead cost calculation.
        
        Args:
            cost_service: Cost calculation service
            test_service: Test service
        """
        # Load test data
        route_data = test_service.load_fixture('route_1')
        settings = test_service.load_fixture('cost_settings_1')
        
        # Calculate overhead cost
        cost = cost_service.calculate_overhead_cost(
            base_cost=1000.0,
            settings=settings
        )
        
        # Verify cost
        test_service.assert_true(cost > 0)
        test_service.assert_true(
            isinstance(cost, float)
        )
    
    def test_calculate_total_cost(
        self,
        cost_service: CostCalculationService,
        test_service: BaseTestService
    ) -> None:
        """Test total cost calculation.
        
        Args:
            cost_service: Cost calculation service
            test_service: Test service
        """
        # Load test data
        route_data = test_service.load_fixture('route_1')
        
        # Calculate total cost
        breakdown = cost_service.calculate_total_cost(
            route=route_data
        )
        
        # Verify breakdown
        test_service.assert_true(
            isinstance(breakdown, CostBreakdown)
        )
        test_service.assert_true(breakdown.total > 0)
        test_service.assert_true(breakdown.fuel > 0)
        test_service.assert_true(breakdown.toll > 0)
        test_service.assert_true(breakdown.driver > 0)
        test_service.assert_true(breakdown.maintenance > 0)
        test_service.assert_true(breakdown.overhead > 0)
    
    def test_calculate_cost_with_empty_driving(
        self,
        cost_service: CostCalculationService,
        test_service: BaseTestService
    ) -> None:
        """Test cost calculation with empty driving.
        
        Args:
            cost_service: Cost calculation service
            test_service: Test service
        """
        # Load test data
        route_data = test_service.load_fixture('route_1')
        empty_data = test_service.load_fixture('empty_driving_1')
        
        # Calculate costs
        normal = cost_service.calculate_total_cost(
            route=route_data
        )
        with_empty = cost_service.calculate_total_cost(
            route=route_data,
            empty_driving=empty_data
        )
        
        # Verify costs
        test_service.assert_true(
            with_empty.total > normal.total
        )
        test_service.assert_true(
            with_empty.fuel > normal.fuel
        )
        test_service.assert_true(
            with_empty.toll > normal.toll
        )
    
    def test_invalid_cost_settings(
        self,
        cost_service: CostCalculationService,
        test_service: BaseTestService,
        mock_factory: MockFactory
    ) -> None:
        """Test cost calculation with invalid settings.
        
        Args:
            cost_service: Cost calculation service
            test_service: Test service
            mock_factory: Mock factory
        """
        # Setup mock to return invalid settings
        settings_service = mock_factory.create(
            'CostSettingsService',
            get_settings=lambda: test_service.load_fixture(
                'invalid_settings'
            )
        )
        cost_service._settings_service = settings_service
        
        # Load test data
        route_data = test_service.load_fixture('route_1')
        
        # Verify error raised
        with pytest.raises(ValueError):
            cost_service.calculate_total_cost(
                route=route_data
            )
