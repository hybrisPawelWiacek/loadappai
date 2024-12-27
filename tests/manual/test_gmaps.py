"""Script to test Google Maps service with real API calls."""
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent.parent)
sys.path.append(project_root)

from src.infrastructure.services.google_maps_service import GoogleMapsService
from src.domain.value_objects import Location
from tests.manual.test_utils import load_env, get_required_env

def main():
    """Test Google Maps service functionality."""
    try:
        # Load environment variables
        load_env()
        api_key = get_required_env("GOOGLE_MAPS_API_KEY")
        
        # Initialize the service
        service = GoogleMapsService(api_key=api_key)
        print("Service initialized successfully")

        # Test locations
        warsaw = Location(
            address="Warsaw, Poland",
            latitude=52.2297,
            longitude=21.0122
        )
        berlin = Location(
            address="Berlin, Germany",
            latitude=52.5200,
            longitude=13.4050
        )
        
        print("\nTesting route from Warsaw to Berlin...")
        
        # Test distance calculation
        distance = service.calculate_distance(warsaw, berlin)
        print(f"\nDriving distance: {distance:.2f} km")
        
        # Test duration calculation
        duration = service.calculate_duration(warsaw, berlin)
        print(f"Estimated duration: {duration:.2f} hours")
        
        # Test route segmentation
        print("\nRoute segments:")
        segments = service.get_route_segments(warsaw, berlin, include_tolls=True)
        for segment in segments:
            print(f"Country: {segment.country_code}, Distance: {segment.distance:.2f} km")
            if segment.toll_rates:
                print("Toll rates:")
                for vehicle_type, rate in segment.toll_rates.items():
                    print(f"  {vehicle_type}: {rate:.2f}")

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
