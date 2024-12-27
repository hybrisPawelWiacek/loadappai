"""Tests for toll rate service."""
from decimal import Decimal
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import pytest
from uuid import UUID

from src.domain.value_objects import Location
from src.domain.entities.route import Route
from src.domain.interfaces.services.toll_rate_service import TollRateServiceError
from src.infrastructure.services.toll_rate_service import GoogleMapsTollRateService
from src.infrastructure.data.toll_roads import TOLL_RATES


# Test data
FRANKFURT = Location(
    address="Frankfurt, Germany",
    latitude=50.1109,
    longitude=8.6821
)

MUNICH = Location(
    address="Munich, Germany",
    latitude=48.1351,
    longitude=11.5820
)

TEST_ROUTE = Route(
    id=UUID("12345678-1234-5678-1234-567812345678"),
    origin={
        "address": "Frankfurt, Germany",
        "latitude": 50.1109,
        "longitude": 8.6821
    },
    destination={
        "address": "Munich, Germany",
        "latitude": 48.1351,
        "longitude": 11.5820
    },
    pickup_time=datetime(2024, 1, 1, 10, 0),
    delivery_time=datetime(2024, 1, 1, 16, 0),
    distance_km=400,
    duration_hours=6
)

# Mock Google Maps response
MOCK_GMAPS_RESPONSE = {
    'legs': [{
        'steps': [
            {
                'html_instructions': 'Head east on <b>Local Road</b>',
                'distance': {'value': 1000}  # 1 km
            },
            {
                'html_instructions': 'Take the ramp onto <b>A3</b> towards Munich',
                'distance': {'value': 220160}  # 220.16 km
            },
            {
                'html_instructions': 'Continue onto <b>A9</b>',
                'distance': {'value': 155395}  # 155.395 km
            }
        ]
    }],
    'warnings': ['This route has toll roads']
}


@pytest.fixture
def mock_repository():
    """Create a mock repository."""
    repo = Mock()
    repo.get_by_id.return_value = TEST_ROUTE
    return repo


@pytest.fixture
def service(mock_repository):
    """Create a service instance with mocked dependencies."""
    with patch('googlemaps.Client') as mock_client:
        # Configure mock client
        instance = mock_client.return_value
        instance.directions.return_value = [MOCK_GMAPS_RESPONSE]
        
        # Create service
        service = GoogleMapsTollRateService(
            api_key="test_key",
            route_repository=mock_repository
        )
        return service


def test_service_initialization():
    """Test service initialization with explicit API key."""
    with patch('googlemaps.Client') as mock_client:
        service = GoogleMapsTollRateService(api_key="test_key")
        assert service.api_key == "test_key"
        mock_client.assert_called_once_with(key="test_key")


def test_clean_html(service):
    """Test HTML cleaning function."""
    html = '<b>Take</b> the <b>A3</b> towards <div>Munich</div>'
    cleaned = service._clean_html(html)
    assert cleaned == "take the a3 towards munich"


def test_extract_road_name(service):
    """Test road name extraction."""
    # Test various road formats
    assert service._extract_road_name("Take the A3 to Munich") == "A3"
    assert service._extract_road_name("Continue on E45") == "E45"
    assert service._extract_road_name("Exit onto D1") == "D1"
    assert service._extract_road_name("Merge onto S8") == "S8"
    assert service._extract_road_name("Take Autobahn 7") == "A7"
    
    # Test with no road name
    assert service._extract_road_name("Turn right") is None


def test_calculate_toll(service):
    """Test toll calculation."""
    route_id = UUID("12345678-1234-5678-1234-567812345678")
    
    # Test for different vehicle types
    truck_toll = service.calculate_toll(route_id, "truck")
    van_toll = service.calculate_toll(route_id, "van")
    trailer_toll = service.calculate_toll(route_id, "trailer")
    
    # Verify toll calculations
    # A3: 220.16 km, A9: 155.395 km
    total_distance = Decimal("375.555")  # 220.16 + 155.395
    
    # Expected tolls based on rates
    expected_truck = total_distance * Decimal(str(TOLL_RATES["DE"]["truck"]))
    expected_van = total_distance * Decimal(str(TOLL_RATES["DE"]["van"]))
    expected_trailer = total_distance * Decimal(str(TOLL_RATES["DE"]["trailer"]))
    
    assert truck_toll == expected_truck
    assert van_toll == expected_van
    assert trailer_toll == expected_trailer


def test_calculate_toll_errors(service, mock_repository):
    """Test error handling in toll calculation."""
    route_id = UUID("12345678-1234-5678-1234-567812345678")
    
    # Test missing repository
    service.route_repository = None
    with pytest.raises(TollRateServiceError, match="Route repository not configured"):
        service.calculate_toll(route_id, "truck")
    
    # Test missing route
    service.route_repository = mock_repository
    mock_repository.get_by_id.return_value = None
    with pytest.raises(TollRateServiceError, match="Route not found"):
        service.calculate_toll(route_id, "truck")


def test_has_toll_roads(service):
    """Test toll road detection by country."""
    assert service.has_toll_roads("DE") is True
    assert service.has_toll_roads("FR") is True
    assert service.has_toll_roads("XX") is False


def test_get_current_rates(service):
    """Test getting current toll rates."""
    # Test existing country
    de_rates = service.get_current_rates("DE")
    assert de_rates["truck"] == TOLL_RATES["DE"]["truck"]
    assert de_rates["van"] == TOLL_RATES["DE"]["van"]
    assert de_rates["trailer"] == TOLL_RATES["DE"]["trailer"]
    
    # Test non-existent country (should use default rates)
    xx_rates = service.get_current_rates("XX")
    assert xx_rates["truck"] == TOLL_RATES["default"]["truck"]


def test_unsupported_operations(service):
    """Test operations not supported by Google Maps service."""
    with pytest.raises(NotImplementedError):
        service.update_rates("DE", {}, datetime.now())
    
    with pytest.raises(NotImplementedError):
        service.validate_rates({})
    
    with pytest.raises(NotImplementedError):
        service.get_rate_history("DE", datetime.now(), datetime.now())
