"""Tests for LocationService interface."""
import pytest
from abc import ABC, abstractmethod

from src.domain.interfaces import LocationService, LocationServiceError
from src.domain.value_objects import Location, CountrySegment


def test_location_service_is_abstract():
    """Test that LocationService is an abstract base class."""
    assert issubclass(LocationService, ABC)
    
    # Verify that abstract methods are defined
    abstract_methods = set()
    for method in dir(LocationService):
        if not method.startswith('_'):  # Skip private methods
            attr = getattr(LocationService, method)
            if getattr(attr, '__isabstractmethod__', False):
                abstract_methods.add(method)
    
    assert 'calculate_distance' in abstract_methods
    assert 'calculate_duration' in abstract_methods
    assert 'get_country_segments' in abstract_methods


class MockLocationService(LocationService):
    """Mock implementation of LocationService for testing."""
    
    def calculate_distance(self, origin: Location, destination: Location) -> float:
        if origin == destination:
            return 0.0
        return 100.0  # Mock distance
    
    def calculate_duration(self, origin: Location, destination: Location) -> float:
        if origin == destination:
            return 0.0
        return 2.0  # Mock duration in hours
    
    def get_country_segments(self, origin: Location, destination: Location) -> list[CountrySegment]:
        if origin == destination:
            return [CountrySegment(country_code="DE", distance=0.0, toll_rates={})]
        return [
            CountrySegment(country_code="DE", distance=50.0, toll_rates={}),
            CountrySegment(country_code="PL", distance=50.0, toll_rates={})
        ]


def test_mock_location_service_implementation():
    """Test that MockLocationService properly implements the interface."""
    service = MockLocationService()
    
    # Test locations
    berlin = Location(latitude=52.5200, longitude=13.4050, address="Berlin, Germany")
    warsaw = Location(latitude=52.2297, longitude=21.0122, address="Warsaw, Poland")
    
    # Test same location
    assert service.calculate_distance(berlin, berlin) == 0.0
    assert service.calculate_duration(berlin, berlin) == 0.0
    assert len(service.get_country_segments(berlin, berlin)) == 1
    assert service.get_country_segments(berlin, berlin)[0].country_code == "DE"
    
    # Test different locations
    assert service.calculate_distance(berlin, warsaw) == 100.0
    assert service.calculate_duration(berlin, warsaw) == 2.0
    segments = service.get_country_segments(berlin, warsaw)
    assert len(segments) == 2
    assert segments[0].country_code == "DE"
    assert segments[1].country_code == "PL"


def test_location_service_error():
    """Test LocationServiceError exception."""
    error = LocationServiceError("Test error message")
    assert str(error) == "Test error message"
    assert isinstance(error, Exception)
