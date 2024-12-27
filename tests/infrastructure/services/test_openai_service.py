"""Test OpenAI service implementation."""
import os
import time
import pytest
from unittest.mock import Mock, patch, MagicMock
from openai import OpenAI
from openai._exceptions import OpenAIError
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice
from dotenv import load_dotenv
import logging

from src.domain.interfaces import AIServiceError
from src.domain.value_objects import Location
from src.infrastructure.services.openai_service import OpenAIService
from src.settings import Settings, get_settings, APISettings

logger = logging.getLogger(__name__)

# Load environment variables
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
env_path = os.path.join(project_root, '.env')

logger.info(f"Current directory: {project_root}")
logger.info(f".env file exists: {os.path.exists(env_path)}")

# Log environment before loading
logger.info("Environment before loading .env:")
logger.info(f"OPENAI_API_KEY before: {os.getenv('OPENAI_API_KEY', 'test-key')}")

# Load environment variables
load_dotenv(env_path)

# Log environment after loading
logger.info("Environment after loading .env:")
logger.info(f"OPENAI_API_KEY after: {os.getenv('OPENAI_API_KEY')}")

# Get API key from environment
api_key = os.getenv('OPENAI_API_KEY')
logger.info(f"API Key: {api_key[:10]}... (length: {len(api_key)})")

@pytest.fixture
def mock_settings():
    """Create mock settings."""
    api_settings = APISettings(
        openai_api_key="test-key",
        openai_model="gpt-4o-mini",  # Match the default from settings.py
        openai_max_retries=3,
        openai_retry_delay=1.0,
        openai_timeout=60.0
    )
    settings = Mock()
    settings.api = api_settings
    return settings

@pytest.fixture
def mock_settings_without_api():
    """Create mock settings without API key."""
    api_settings = APISettings(
        openai_api_key=None,
        openai_model="gpt-4o-mini",
        openai_max_retries=3,
        openai_retry_delay=1.0,
        openai_timeout=60.0
    )
    settings = Mock()
    settings.api = api_settings
    return settings

@pytest.fixture
def mock_openai_client(mocker):
    """Create mock OpenAI client with proper response structure."""
    # Create mock response with proper structure
    mock_choice = mocker.Mock()
    mock_choice.message.content = "Test response"
    mock_choice.message.role = "assistant"
    
    mock_response = mocker.Mock()
    mock_response.choices = [mock_choice]
    mock_response.model = "gpt-3.5-turbo"
    mock_response.id = "chatcmpl-123"
    mock_response.created = int(time.time())
    mock_response.usage = {"total_tokens": 20, "prompt_tokens": 10, "completion_tokens": 10}
    
    # Set up mock client structure
    mock_completions = mocker.Mock()
    mock_completions.create.return_value = mock_response
    
    mock_chat = mocker.Mock()
    mock_chat.completions = mock_completions
    
    mock_client = mocker.Mock()
    mock_client.chat = mock_chat
    
    # Mock OpenAI class
    mocker.patch('src.infrastructure.services.openai_service.OpenAI', return_value=mock_client)
    
    # Mock httpx client
    mock_http_client = mocker.Mock()
    mock_http_client.headers = {"content-type": "application/json"}
    mocker.patch('httpx.Client', return_value=mock_http_client)
    
    return mock_client

def create_test_location(address: str = "Test Street 1, 12345 Berlin, Germany", latitude: float = 52.52, longitude: float = 13.405, country: str = "Germany") -> Location:
    """Create a test location."""
    return Location(
        address=address,
        latitude=latitude,
        longitude=longitude,
        country=country
    )

def create_mock_chat_completion(content: str) -> ChatCompletion:
    """Create a mock chat completion response."""
    message = ChatCompletionMessage(role="assistant", content=content)
    choice = Choice(
        index=0,
        message=message,
        finish_reason="stop",
        logprobs=None
    )
    return ChatCompletion(
        id="mock-id",
        choices=[choice],
        created=int(time.time()),
        model="gpt-4o-mini",
        object="chat.completion",
        usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
    )

def test_init_without_api_key(mock_settings_without_api, mock_openai_client):
    """Test initialization without API key."""
    with patch('src.infrastructure.services.openai_service.get_settings', return_value=mock_settings_without_api), \
         patch.dict(os.environ, {}, clear=True):
        with pytest.raises(AIServiceError) as exc_info:
            OpenAIService()
        assert "OpenAI API key not found in settings or environment" in str(exc_info.value)

def test_init_with_api_key(mock_openai_client):
    """Test initialization with API key."""
    service = OpenAIService(api_key="test-key")
    assert service.api_key == "test-key"

def test_init_with_settings(mock_settings, mock_openai_client):
    """Test initialization with settings."""
    with patch('src.infrastructure.services.openai_service.get_settings', return_value=mock_settings):
        service = OpenAIService()
        assert service.api_key == "test-key"
        assert service.model == "gpt-4o-mini"  # Match the default from settings.py

def test_generate_response_success(mock_openai_client):
    """Test successful response generation."""
    service = OpenAIService(api_key="test-key")
    response = service.generate_response("Test prompt")
    assert response == "Test response"

def test_generate_route_fact_success(mock_openai_client):
    """Test successful route fact generation."""
    service = OpenAIService(api_key="test-key")
    origin = create_test_location()
    destination = create_test_location(
        address="Test Street 1, 12345 Paris, France",
        country="France"
    )
    fact = service.generate_route_fact(origin, destination)
    assert fact == "Test response"

def test_enhance_route_description_success(mock_openai_client):
    """Test successful route description enhancement."""
    service = OpenAIService(api_key="test-key")
    origin = create_test_location()
    destination = create_test_location(
        address="Test Street 1, 12345 Paris, France",
        country="France"
    )
    description = service.enhance_route_description(origin, destination, 1000.0, 12.5)
    assert description == "Test response"

def test_enhance_route_description_success_with_context(mock_openai_client):
    """Test successful route description enhancement with context."""
    service = OpenAIService(api_key="test-key")
    origin = create_test_location()
    destination = create_test_location(
        address="Test Street 1, 12345 Paris, France",
        country="France"
    )
    context = {
        "transport_type": "refrigerated truck",
        "cargo_type": "perishable goods",
        "special_requirements": "temperature control"
    }
    description = service.enhance_route_description(origin, destination, 1000.0, 12.5, context)
    assert description == "Test response"

def test_enhance_route_description_with_empty_context(mock_openai_client):
    """Test route description enhancement with empty context."""
    service = OpenAIService(api_key="test-key")
    origin = create_test_location()
    destination = create_test_location(
        address="Test Street 1, 12345 Paris, France",
        country="France"
    )
    description = service.enhance_route_description(origin, destination, 1000.0, 12.5, {})
    assert description == "Test response"

def test_generate_fun_fact_success(mock_openai_client):
    """Test successful fun fact generation."""
    service = OpenAIService(api_key="test-key")
    origin = create_test_location()
    destination = create_test_location(
        address="Test Street 1, 12345 Paris, France",
        country="France"
    )
    route = Mock(
        origin=origin,
        destination=destination,
        id="test-id",
        vehicle_type="truck",
        has_cargo=True,
        empty_drive=False
    )
    fact = service.generate_fun_fact(route)
    assert fact == "Test response"

def test_generate_route_description_success(mock_openai_client):
    """Test successful route description generation."""
    service = OpenAIService(api_key="test-key")
    origin = create_test_location()
    destination = create_test_location(
        address="Test Street 1, 12345 Paris, France",
        country="France"
    )
    route = Mock(
        origin=origin,
        destination=destination,
        id="test-id",
        vehicle_type="truck",
        has_cargo=True,
        empty_drive=False,
        distance_km=500.0,
        duration_hours=6.0
    )
    description = service.generate_route_description(route)
    assert description == "Test response"

def test_enhance_route_description_error_handling(mock_openai_client):
    """Test error handling in route description enhancement."""
    mock_openai_client.chat.completions.create.side_effect = OpenAIError("API error")

    service = OpenAIService(api_key="test-key")
    origin = create_test_location()
    destination = create_test_location(
        address="Test Street 1, 12345 Paris, France",
        country="France"
    )

    with pytest.raises(AIServiceError) as exc_info:
        service.enhance_route_description(origin, destination, 1000.0, 12.5)
    assert "Failed to generate route description" in str(exc_info.value)

def test_generate_fun_fact_api_error(mock_openai_client):
    """Test API error handling in fun fact generation."""
    mock_openai_client.chat.completions.create.side_effect = OpenAIError("API error")

    service = OpenAIService(api_key="test-key")
    origin = create_test_location()
    destination = create_test_location(
        address="Test Street 1, 12345 Paris, France",
        country="France"
    )
    route = Mock(
        origin=origin,
        destination=destination,
        id="test-id",
        vehicle_type="truck",
        has_cargo=True,
        empty_drive=False
    )

    with pytest.raises(AIServiceError) as exc_info:
        service.generate_fun_fact(route)
    assert "Failed to generate fun fact" in str(exc_info.value)

def test_generate_route_description_error(mock_openai_client):
    """Test error handling in route description generation."""
    mock_openai_client.chat.completions.create.side_effect = OpenAIError("API error")

    service = OpenAIService(api_key="test-key")
    origin = create_test_location()
    destination = create_test_location(
        address="Test Street 1, 12345 Paris, France",
        country="France"
    )
    route = Mock(
        origin=origin,
        destination=destination,
        id="test-id",
        vehicle_type="truck",
        has_cargo=True,
        empty_drive=False,
        distance_km=500.0,
        duration_hours=6.0
    )

    with pytest.raises(AIServiceError) as exc_info:
        service.generate_route_description(route)
    assert "Failed to generate route description" in str(exc_info.value)

class TestOpenAIServiceIntegration:
    """Integration tests for OpenAIService."""

    def setup_method(self):
        """Setup for each test method."""
        # Skip integration tests if no API key is available
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key or api_key == "test-key":
            pytest.skip("Valid OpenAI API key not found in environment")
        self.service = OpenAIService(api_key=api_key)

    def test_generate_route_fact_integration(self):
        """Integration test for route fact generation."""
        origin = create_test_location()
        destination = create_test_location(
            address="Test Street 1, 12345 Paris, France",
            country="France"
        )
        fact = self.service.generate_route_fact(origin, destination)
        assert fact and isinstance(fact, str)
        assert len(fact) > 0

    def test_enhance_route_description_integration(self):
        """Integration test for route description enhancement."""
        origin = create_test_location()
        destination = create_test_location(
            address="Test Street 1, 12345 Paris, France",
            country="France"
        )
        description = self.service.enhance_route_description(
            origin=origin,
            destination=destination,
            distance_km=1050.5,
            duration_hours=10.5,
            context={
                "vehicle_type": "truck",
                "has_cargo": True,
                "empty_drive": False
            }
        )
        assert description and isinstance(description, str)
        assert len(description) > 0
