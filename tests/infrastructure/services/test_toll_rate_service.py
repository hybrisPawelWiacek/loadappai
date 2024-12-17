"""Tests for toll rate service."""
from decimal import Decimal
import pytest

from src.domain.value_objects import CountrySegment
from src.infrastructure.services.toll_rate_service import DefaultTollRateService


def test_get_toll_rates():
    """Test getting toll rates for a country and vehicle type."""
    service = DefaultTollRateService()
    
    # Test existing country and vehicle type
    rates = service.get_toll_rates("DE", "truck")
    assert rates["highway"] == Decimal("0.17")
    assert rates["national"] == Decimal("0.12")
    
    # Test non-existent country
    rates = service.get_toll_rates("XX", "truck")
    assert rates == {}
    
    # Test non-existent vehicle type
    rates = service.get_toll_rates("DE", "bicycle")
    assert rates == {}


def test_calculate_segment_toll_rates():
    """Test calculating toll rates for a country segment."""
    service = DefaultTollRateService()
    
    # Create a test segment
    segment = CountrySegment(
        country_code="DE",
        distance=Decimal("100"),  # 100 km
        toll_rates={}
    )
    
    # Calculate rates for a truck
    rates = service.calculate_segment_toll_rates(segment, "truck")
    
    # Expected: 70km highway at 0.17€/km + 30km national at 0.12€/km
    expected_highway = Decimal("70") * Decimal("0.17")
    expected_national = Decimal("30") * Decimal("0.12")
    
    assert rates["highway"] == expected_highway
    assert rates["national"] == expected_national
    
    # Test with non-existent country
    segment = CountrySegment(
        country_code="XX",
        distance=Decimal("100"),
        toll_rates={}
    )
    rates = service.calculate_segment_toll_rates(segment, "truck")
    assert rates["highway"] == Decimal("0")
    assert rates["national"] == Decimal("0")
