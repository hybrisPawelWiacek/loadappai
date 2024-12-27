"""Tests for route service interface."""
import pytest
from uuid import UUID
from typing import Dict, List, Optional

from src.domain.entities.route import Route
from src.domain.value_objects import Location
from src.domain.interfaces.services.route_service import RouteService, RouteServiceError

class TestRouteService(RouteService):
    """Test implementation of RouteService interface."""
    
    def create_route(self, 
        origin: Location, 
        destination: Location,
        via_points: Optional[List[Location]] = None
    ) -> Route:
        raise NotImplementedError()
    
    def optimize_empty_driving(self, route: Route) -> Route:
        raise NotImplementedError()
    
    def validate_route(self, route: Route) -> bool:
        raise NotImplementedError()
    
    def get_route_details(self, route_id: UUID) -> Dict:
        raise NotImplementedError()
    
    def update_route(self, route_id: UUID, updates: Dict) -> Route:
        raise NotImplementedError()

def test_route_service_interface():
    """Test that RouteService interface can be implemented."""
    service = TestRouteService()
    assert isinstance(service, RouteService)
    
    # Create test data
    origin = Location(lat=52.5200, lon=13.4050)
    destination = Location(lat=51.5074, lon=-0.1278)
    route_id = UUID('00000000-0000-0000-0000-000000000000')
    
    # Verify that all abstract methods are required
    with pytest.raises(NotImplementedError):
        service.create_route(origin, destination)
    
    with pytest.raises(NotImplementedError):
        service.optimize_empty_driving(Route(id=route_id, origin=origin, destination=destination))
    
    with pytest.raises(NotImplementedError):
        service.validate_route(Route(id=route_id, origin=origin, destination=destination))
    
    with pytest.raises(NotImplementedError):
        service.get_route_details(route_id)
    
    with pytest.raises(NotImplementedError):
        service.update_route(route_id, {"status": "active"})
