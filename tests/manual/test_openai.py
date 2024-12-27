"""Script to test OpenAI service with real API calls."""
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent.parent)
sys.path.append(project_root)

from src.infrastructure.services.openai_service import OpenAIService
from src.domain.value_objects import Location
from tests.manual.test_utils import load_env, get_required_env

def main():
    """Test OpenAI service functionality."""
    try:
        # Load environment variables
        load_env()
        api_key = get_required_env("OPENAI_API_KEY")
        
        # Initialize the service
        service = OpenAIService(api_key=api_key)
        print("Service initialized successfully")
        
        # Test settings
        print("\nService settings:")
        print(f"API Key: {'*' * 8}{service.api_key[-4:]}")  # Only show last 4 chars
        print(f"Model: {service.model}")
        print(f"Max retries: {service.max_retries}")
        print(f"Retry delay: {service.retry_delay}")
        
        # Test locations
        berlin = Location(address="Berlin, Germany", latitude=52.5200, longitude=13.4050)
        warsaw = Location(address="Warsaw, Poland", latitude=52.2297, longitude=21.0122)
        
        # Test route fact generation
        print("\nTesting route fact generation...")
        try:
            fact = service.generate_route_fact(berlin, warsaw)
            print("✓ Generated fact successfully:")
            print(fact)
        except Exception as e:
            print(f"✗ Failed to generate fact: {e}")
        
        # Test route description enhancement
        print("\nTesting route description enhancement...")
        try:
            description = service.enhance_route_description(berlin, warsaw, 500.0, 6.5)
            print("✓ Generated description successfully:")
            print(description)
        except Exception as e:
            print(f"✗ Failed to generate description: {e}")
    
    except Exception as e:
        print(f"✗ Failed to initialize service: {e}")
        return

if __name__ == "__main__":
    main()
