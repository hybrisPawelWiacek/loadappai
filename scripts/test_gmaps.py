"""Script to test Google Maps service with real API calls."""
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from src.infrastructure.services.google_maps_service import GoogleMapsService
from src.domain.value_objects import Location

def main():
    """Test Google Maps service functionality."""
    try:
        # Initialize the service
        service = GoogleMapsService()
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
        segments = service.get_country_segments(warsaw, berlin, transport_type="truck")
        
        print("\nRoute segments:")
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
