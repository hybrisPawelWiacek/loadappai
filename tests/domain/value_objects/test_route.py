"""Tests for route-related value objects."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from src.domain.value_objects.route import (
    CountrySegment,
    EmptyDriving,
    RouteMetadata,
    RouteOptimizationResult,
    RouteSegment,
)
from src.domain.value_objects.location import Location


def test_country_segment_creation():
    """Test creating CountrySegment."""
    segment = CountrySegment(
        country_code="DE",
        distance=Decimal("150.5"),
        duration_hours=Decimal("2.5"),
    )
    assert segment.country_code == "DE"
    assert segment.distance == Decimal("150.5")
    assert segment.duration_hours == Decimal("2.5")
    assert segment.toll_rates["highway"] == Decimal("0.15")
    assert segment.toll_rates["national"] == Decimal("0.10")


def test_country_segment_validation():
    """Test CountrySegment validation."""
    with pytest.raises(ValidationError):
        CountrySegment(
            country_code="DE",
            distance=Decimal("-150.5"),  # Negative distance
            duration_hours=Decimal("2.5"),
            _validation_mode="all",
        )

    with pytest.raises(ValidationError):
        CountrySegment(
            country_code="DE",
            distance=Decimal("150.5"),
            duration_hours=Decimal("0"),  # Zero duration
            _validation_mode="all",
        )


def test_country_segment_custom_toll_rates():
    """Test CountrySegment with custom toll rates."""
    custom_rates = {
        "highway": Decimal("0.25"),
        "national": Decimal("0.15"),
        "urban": Decimal("0.20")
    }
    segment = CountrySegment(
        country_code="FR",
        distance=Decimal("200.0"),
        duration_hours=Decimal("3.0"),
        toll_rates=custom_rates
    )
    assert segment.toll_rates == custom_rates
    assert segment.toll_rates["urban"] == Decimal("0.20")


def test_country_segment_edge_cases():
    """Test CountrySegment edge cases."""
    # Very large values
    large_segment = CountrySegment(
        country_code="US",
        distance=Decimal("9999999.999"),
        duration_hours=Decimal("1000.50"),
    )
    assert large_segment.distance == Decimal("9999999.999")
    assert large_segment.duration_hours == Decimal("1000.50")

    # Decimal precision
    precise_segment = CountrySegment(
        country_code="GB",
        distance=Decimal("150.12345"),
        duration_hours=Decimal("2.67890"),
    )
    assert precise_segment.distance == Decimal("150.12345")
    assert precise_segment.duration_hours == Decimal("2.67890")


def test_country_segment_invalid_inputs():
    """Test CountrySegment with invalid inputs."""
    # Empty country code
    with pytest.raises(ValidationError):
        CountrySegment(
            country_code="",
            distance=Decimal("100.0"),
            duration_hours=Decimal("2.0"),
        )

    # Invalid toll rates
    with pytest.raises(ValidationError):
        CountrySegment(
            country_code="DE",
            distance=Decimal("100.0"),
            duration_hours=Decimal("2.0"),
            toll_rates={"highway": Decimal("-0.15")}  # Negative toll rate
        )


def test_route_metadata_creation():
    """Test creating RouteMetadata."""
    metadata = RouteMetadata(
        weather_data={"temperature": 20, "conditions": "clear"},
        traffic_data={"congestion_level": "low"},
        compliance_data={"permits": ["eco_zone"]},
        optimization_data={"algorithm": "fastest_path"},
    )
    assert metadata.weather_data["temperature"] == 20
    assert metadata.traffic_data["congestion_level"] == "low"
    assert metadata.compliance_data["permits"] == ["eco_zone"]
    assert metadata.optimization_data["algorithm"] == "fastest_path"


def test_route_metadata_validation():
    """Test RouteMetadata validation with various optional fields."""
    # Test with all optional fields
    metadata = RouteMetadata(
        weather_data={"temperature": 20, "conditions": "sunny"},
        traffic_data={"congestion": "low", "incidents": []},
        compliance_data={"restrictions": None},
        optimization_data={"score": 0.95}
    )
    assert metadata.weather_data["temperature"] == 20
    assert metadata.traffic_data["congestion"] == "low"
    assert metadata.compliance_data["restrictions"] is None
    assert metadata.optimization_data["score"] == 0.95

    # Test with partial optional fields
    partial_metadata = RouteMetadata(
        weather_data={"temperature": 25},
        traffic_data=None
    )
    assert partial_metadata.weather_data["temperature"] == 25
    assert partial_metadata.traffic_data is None
    assert partial_metadata.compliance_data is None

    # Test with empty metadata
    empty_metadata = RouteMetadata()
    assert empty_metadata.weather_data is None
    assert empty_metadata.traffic_data is None
    assert empty_metadata.compliance_data is None
    assert empty_metadata.optimization_data is None


def test_route_segment_creation():
    """Test creating RouteSegment."""
    start = Location(address="Start", latitude=40.0, longitude=-74.0)
    end = Location(address="End", latitude=41.0, longitude=-75.0)
    
    segment = RouteSegment(
        start_location=start,
        end_location=end,
        distance_km=100.5,
        duration_hours=2.0,
        country="US",
        is_empty_driving=False,
        timeline_event="pickup",
    )
    assert segment.start_location == start
    assert segment.end_location == end
    assert segment.distance_km == 100.5
    assert segment.duration_hours == 2.0
    assert segment.country == "US"
    assert segment.timeline_event == "pickup"


def test_route_segment_edge_cases():
    """Test RouteSegment with edge cases and boundary values."""
    start_loc = Location(address="Start", latitude=0, longitude=0)
    end_loc = Location(address="End", latitude=1, longitude=1)

    # Test minimum valid values
    min_segment = RouteSegment(
        start_location=start_loc,
        end_location=end_loc,
        distance_km=0.1,  # Minimum reasonable distance
        duration_hours=0.01,  # Minimum reasonable duration
        country="DE"
    )
    assert min_segment.distance_km == 0.1
    assert min_segment.duration_hours == 0.01

    # Test large values
    max_segment = RouteSegment(
        start_location=start_loc,
        end_location=end_loc,
        distance_km=9999.99,
        duration_hours=168.0,  # 1 week
        country="US"
    )
    assert max_segment.distance_km == 9999.99
    assert max_segment.duration_hours == 168.0

    # Test timeline events
    event_segment = RouteSegment(
        start_location=start_loc,
        end_location=end_loc,
        distance_km=100,
        duration_hours=2.5,
        country="FR",
        timeline_event="pickup",
        is_empty_driving=True
    )
    assert event_segment.timeline_event == "pickup"
    assert event_segment.is_empty_driving is True


def test_route_segment_validation():
    """Test RouteSegment validation."""
    start = Location(address="Start", latitude=40.0, longitude=-74.0)
    end = Location(address="End", latitude=41.0, longitude=-75.0)
    
    with pytest.raises(ValidationError):
        RouteSegment(
            start_location=start,
            end_location=end,
            distance_km=-100.5,  # Negative distance
            duration_hours=2.0,
            country="US",
            _validation_mode="all",
        )

    with pytest.raises(ValidationError):
        RouteSegment(
            start_location=start,
            end_location=end,
            distance_km=100.5,
            duration_hours=0.0,  # Zero duration
            country="US",
            _validation_mode="all",
        )


def test_empty_driving_creation():
    """Test creating EmptyDriving."""
    start = Location(address="Start", latitude=40.0, longitude=-74.0)
    end = Location(address="End", latitude=41.0, longitude=-75.0)
    
    segment = CountrySegment(
        country_code="US",
        distance=Decimal("150.5"),
        duration_hours=Decimal("2.5"),
    )
    
    empty_driving = EmptyDriving(
        distance_km=150.5,
        duration_hours=2.5,
        origin=start,
        destination=end,
        segments=[segment],
    )
    assert empty_driving.distance_km == 150.5
    assert empty_driving.duration_hours == 2.5
    assert empty_driving.origin == start
    assert empty_driving.destination == end
    assert len(empty_driving.segments) == 1


def test_empty_driving_validation():
    """Test EmptyDriving validation and edge cases."""
    # Test valid creation
    empty_drive = EmptyDriving(
        distance_km=150.5,
        duration_hours=3.0,
        fuel_consumption=30.5,
        toll_costs={"DE": 25.0, "FR": 15.0}
    )
    assert empty_drive.distance_km == 150.5
    assert empty_drive.duration_hours == 3.0

    # Test invalid distance
    with pytest.raises(ValidationError):
        EmptyDriving(
            distance_km=-1.0,
            duration_hours=1.0
        )

    # Test invalid duration
    with pytest.raises(ValidationError):
        EmptyDriving(
            distance_km=100.0,
            duration_hours=0
        )

    # Test edge cases
    edge_case = EmptyDriving(
        distance_km=9999.99,
        duration_hours=168.0,  # 1 week
        fuel_consumption=999.9,
        toll_costs={"ALL": 1000.0}
    )
    assert edge_case.distance_km == 9999.99
    assert edge_case.duration_hours == 168.0


def test_route_optimization_result_creation():
    """Test creating RouteOptimizationResult."""
    locations = [
        Location(address="Start", latitude=40.0, longitude=-74.0),
        Location(address="Mid", latitude=41.0, longitude=-75.0),
        Location(address="End", latitude=42.0, longitude=-76.0),
    ]
    
    segments = [
        RouteSegment(
            start_location=locations[0],
            end_location=locations[1],
            distance_km=100.5,
            duration_hours=2.0,
            country="US",
        ),
        RouteSegment(
            start_location=locations[1],
            end_location=locations[2],
            distance_km=150.5,
            duration_hours=3.0,
            country="US",
        ),
    ]
    
    result = RouteOptimizationResult(
        optimized_route=locations,
        total_distance_km=251.0,
        total_duration_hours=5.0,
        segments=segments,
    )
    assert len(result.optimized_route) == 3
    assert result.total_distance_km == 251.0
    assert result.total_duration_hours == 5.0
    assert len(result.segments) == 2


def test_route_optimization_result_validation():
    """Test RouteOptimizationResult validation and edge cases."""
    loc1 = Location(address="Start", latitude=0, longitude=0)
    loc2 = Location(address="Mid", latitude=1, longitude=1)
    loc3 = Location(address="End", latitude=2, longitude=2)

    segment1 = RouteSegment(
        start_location=loc1,
        end_location=loc2,
        distance_km=100,
        duration_hours=2.0,
        country="DE"
    )
    segment2 = RouteSegment(
        start_location=loc2,
        end_location=loc3,
        distance_km=150,
        duration_hours=3.0,
        country="FR"
    )

    # Test with valid segments
    result = RouteOptimizationResult(
        optimized_route=[loc1, loc2, loc3],
        total_distance_km=250.0,
        total_duration_hours=5.0,
        segments=[segment1, segment2]
    )
    assert len(result.optimized_route) == 3
    assert len(result.segments) == 2
    assert result.total_distance_km == 250.0
    assert result.total_duration_hours == 5.0

    # Test with empty driving
    empty_driving = EmptyDriving(
        distance_km=50.0,
        duration_hours=1.0
    )
    result_with_empty = RouteOptimizationResult(
        optimized_route=[loc1, loc2, loc3],
        total_distance_km=300.0,
        total_duration_hours=6.0,
        segments=[segment1, segment2],
        empty_driving=empty_driving
    )
    assert result_with_empty.empty_driving.distance_km == 50.0

    # Test validation errors for negative values
    with pytest.raises(ValidationError):
        RouteOptimizationResult(
            optimized_route=[loc1, loc2],
            total_distance_km=-100,  # Negative distance
            total_duration_hours=2.0,
            segments=[segment1]
        )

    with pytest.raises(ValidationError):
        RouteOptimizationResult(
            optimized_route=[loc1, loc2],
            total_distance_km=100,
            total_duration_hours=-2.0,  # Negative duration
            segments=[segment1]
        )
