"""Script to test Google Maps toll rate service with real API calls."""
import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent.parent)
sys.path.append(project_root)

from src.domain.entities.route import Route
from src.domain.value_objects import Location
from src.infrastructure.services.toll_rate_service import GoogleMapsTollRateService
from tests.manual.test_utils import load_env, get_required_env

class MockRouteRepository:
    """Mock repository for testing."""
    
    def get_by_id(self, route_id):
        """Return a mock route for testing."""
        # Get current time for pickup
        pickup_time = datetime.now()
        # Set delivery time 6 hours after pickup
        delivery_time = pickup_time + timedelta(hours=6)
        
        # Test routes
        routes = {
            # Frankfurt to Munich (known toll route via A3/A9)
            "de_route": Route(
                id=route_id,
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
                pickup_time=pickup_time,
                delivery_time=delivery_time,
                distance_km=400,
                duration_hours=4
            ),
            # Paris to Lyon (known toll route)
            "fr_route": Route(
                id=route_id,
                origin={
                    "address": "Paris, France",
                    "latitude": 48.8566,
                    "longitude": 2.3522
                },
                destination={
                    "address": "Lyon, France",
                    "latitude": 45.7640,
                    "longitude": 4.8357
                },
                pickup_time=pickup_time,
                delivery_time=delivery_time,
                distance_km=470,
                duration_hours=4.5
            ),
            # Warsaw to Krakow (mixed toll/non-toll)
            "pl_route": Route(
                id=route_id,
                origin={
                    "address": "Warsaw, Poland",
                    "latitude": 52.2297,
                    "longitude": 21.0122
                },
                destination={
                    "address": "Krakow, Poland",
                    "latitude": 50.0647,
                    "longitude": 19.9450
                },
                pickup_time=pickup_time,
                delivery_time=delivery_time,
                distance_km=290,
                duration_hours=3
            )
        }
        return routes.get("de_route")  # Default to German route

def main():
    """Test toll rate service functionality."""
    try:
        # Load environment variables
        load_env()
        api_key = get_required_env("GOOGLE_MAPS_API_KEY")
            
        # Initialize the service with mock repository
        service = GoogleMapsTollRateService(
            api_key=api_key,
            route_repository=MockRouteRepository()
        )
        print("Service initialized successfully")
        
        # Test route ID
        route_id = uuid4()
        
        print("\nTesting toll calculation for different vehicle types...")
        vehicle_types = ["truck", "van", "trailer"]
        
        for vehicle_type in vehicle_types:
            try:
                toll = service.calculate_toll(route_id, vehicle_type)
                print(f"\nVehicle type: {vehicle_type}")
                print(f"Estimated toll: {toll} EUR")
            except Exception as e:
                print(f"Error calculating toll for {vehicle_type}: {str(e)}")
        
        print("\nTesting toll road detection...")
        countries = ["DE", "FR", "PL", "CZ", "AT"]
        for country in countries:
            has_tolls = service.has_toll_roads(country)
            print(f"{country}: {'Has toll roads' if has_tolls else 'No toll roads'}")

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
