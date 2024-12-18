"""Test OpenAI service implementation."""
import os
import time
import pytest
from unittest.mock import Mock, patch
import openai
from openai._exceptions import OpenAIError
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice
from dotenv import load_dotenv
import logging

from src.domain.interfaces import AIServiceError
from src.domain.value_objects import Location
from src.infrastructure.services.openai_service import OpenAIService
from src.config import Settings, get_settings

logger = logging.getLogger(__name__)

@pytest.fixture
def mock_settings():
    """Create mock settings."""
    settings = Settings(
        _env_file=None,  # Disable .env file loading
        OPENAI_API_KEY="sk-test-dummy-key",  # Use a properly formatted dummy key
        OPENAI_MODEL="gpt-4o-mini",  # Keep the original model name
        OPENAI_MAX_RETRIES=3,
        OPENAI_RETRY_DELAY=1.0
    )
    return settings


@pytest.fixture
def mock_openai_client():
    """Create mock OpenAI client."""
    mock_client = Mock(spec=openai.OpenAI)
    mock_chat = Mock()
    mock_completions = Mock()
    mock_client.chat = mock_chat
    mock_chat.completions = mock_completions
    mock_completions.create = Mock()
    return mock_client


def create_mock_chat_completion(content: str) -> ChatCompletion:
    """Create a mock ChatCompletion object."""
    return ChatCompletion(
        id="test-id",
        choices=[
            Choice(
                finish_reason="stop",
                index=0,
                message=ChatCompletionMessage(
                    content=content,
                    role="assistant"
                )
            )
        ],
        created=int(time.time()),
        model="gpt-3.5-turbo",
        object="chat.completion",
        usage={"completion_tokens": 10, "prompt_tokens": 20, "total_tokens": 30}
    )


def test_init_without_api_key():
    """Test initialization without API key."""
    settings = Settings(_env_file=None)  # Disable .env file loading
    settings.OPENAI_API_KEY = None
    with patch.dict(os.environ, {'OPENAI_API_KEY': ''}, clear=True), \
         patch('src.infrastructure.services.openai_service.get_settings', return_value=settings):
        with pytest.raises(AIServiceError):
            OpenAIService()


def test_init_with_api_key():
    """Test initialization with explicit API key."""
    test_key = 'test-key-1234'
    settings = Settings(_env_file=None)
    settings.OPENAI_API_KEY = None
    settings.OPENAI_MODEL = "gpt-4o-mini"
    settings.OPENAI_MAX_RETRIES = 3
    settings.OPENAI_RETRY_DELAY = 1.0
    
    mock_client = Mock()
    with patch.dict(os.environ, {'OPENAI_API_KEY': ''}, clear=True), \
         patch('src.infrastructure.services.openai_service.get_settings', return_value=settings), \
         patch('src.infrastructure.services.openai_service.OpenAI', return_value=mock_client):
        service = OpenAIService(api_key=test_key)
        assert service.api_key == test_key
        assert service.model == "gpt-4o-mini"
        assert service.max_retries == 3
        assert service.retry_delay == 1.0
        assert service.client == mock_client  # Verify we got our mock


def test_init_with_settings(mock_settings):
    """Test initialization with settings."""
    mock_client = Mock()
    with patch.dict(os.environ, {'OPENAI_API_KEY': ''}, clear=True), \
         patch('src.infrastructure.services.openai_service.get_settings', return_value=mock_settings), \
         patch('src.infrastructure.services.openai_service.OpenAI', return_value=mock_client):
        service = OpenAIService()
        assert service.api_key == mock_settings.OPENAI_API_KEY
        assert service.model == mock_settings.OPENAI_MODEL
        assert service.max_retries == mock_settings.OPENAI_MAX_RETRIES
        assert service.retry_delay == mock_settings.OPENAI_RETRY_DELAY
        assert service.client == mock_client  # Verify we got our mock


def test_generate_response_success(mock_settings, mock_openai_client):
    """Test successful response generation."""
    expected_response = "A helpful response about transportation."
    mock_completion = create_mock_chat_completion(expected_response)
    mock_openai_client.chat.completions.create.return_value = mock_completion

    with patch('src.infrastructure.services.openai_service.get_settings', return_value=mock_settings), \
         patch('src.infrastructure.services.openai_service.OpenAI', return_value=mock_openai_client):
        service = OpenAIService()
        response = service.generate_response("Test prompt")
        assert response == expected_response


def test_generate_route_fact_success(mock_settings, mock_openai_client):
    """Test successful route fact generation."""
    expected_fact = "An interesting fact about the route."
    mock_completion = create_mock_chat_completion(expected_fact)
    mock_openai_client.chat.completions.create.return_value = mock_completion

    with patch('src.infrastructure.services.openai_service.get_settings', return_value=mock_settings), \
         patch('src.infrastructure.services.openai_service.OpenAI', return_value=mock_openai_client):
        service = OpenAIService()
        origin = Location(address="New York", latitude=40.7128, longitude=-74.0060)
        destination = Location(address="Boston", latitude=42.3601, longitude=-71.0589)
        fact = service.generate_route_fact(origin, destination)
        assert fact == expected_fact


def test_enhance_route_description_success(mock_settings, mock_openai_client):
    """Test successful route description enhancement."""
    expected_description = "A scenic route through historic landmarks."
    mock_completion = create_mock_chat_completion(expected_description)
    mock_openai_client.chat.completions.create.return_value = mock_completion

    with patch('src.infrastructure.services.openai_service.get_settings', return_value=mock_settings), \
         patch('src.infrastructure.services.openai_service.OpenAI', return_value=mock_openai_client):
        service = OpenAIService()
        origin = Location(address="New York", latitude=40.7128, longitude=-74.0060)
        destination = Location(address="Boston", latitude=42.3601, longitude=-71.0589)
        description = service.enhance_route_description(origin, destination, 350.5, 4.5)
        assert description == expected_description


def test_enhance_route_description_success_with_context(mock_settings, mock_openai_client):
    """Test successful route description enhancement with context."""
    origin = Location(address="Berlin, Germany", latitude=52.5200, longitude=13.4050)
    destination = Location(address="Munich, Germany", latitude=48.1351, longitude=11.5820)
    distance_km = 584.0
    duration_hours = 5.5
    context = {
        "transport_type": "Heavy truck",
        "cargo_type": "Refrigerated goods",
        "special_requirements": "Temperature controlled"
    }
    
    expected_content = (
        "The route from Berlin to Munich primarily follows the A9 motorway. "
        "Key considerations for refrigerated transport include:"
        "\n- Multiple truck stops with refrigeration services"
        "\n- Heavy traffic around Nuremberg during peak hours"
        "\n- Gradual elevation changes through Thuringia"
    )
    
    mock_completion = create_mock_chat_completion(expected_content)
    mock_openai_client.chat.completions.create.return_value = mock_completion
    
    with patch('src.infrastructure.services.openai_service.get_settings', return_value=mock_settings), \
         patch('src.infrastructure.services.openai_service.OpenAI', return_value=mock_openai_client):
        service = OpenAIService()
        result = service.enhance_route_description(origin, destination, distance_km, duration_hours, context)
        
        assert result == expected_content
        
        call_args = mock_openai_client.chat.completions.create.call_args
        messages = call_args[1]['messages']
        
        assert messages[0]['role'] == 'system'
        assert 'logistics route analyst' in messages[0]['content']
        assert 'highways' in messages[0]['content']
        assert 'traffic patterns' in messages[0]['content']
        
        assert messages[1]['role'] == 'user'
        assert 'Berlin, Germany' in messages[1]['content']
        assert 'Munich, Germany' in messages[1]['content']
        assert '584.0 km' in messages[1]['content']
        assert '5.5 hours' in messages[1]['content']
        assert 'Heavy truck' in messages[1]['content']
        assert 'Refrigerated goods' in messages[1]['content']


def test_enhance_route_description_error_handling(mock_settings, mock_openai_client):
    """Test error handling in route description enhancement."""
    origin = Location(address="Berlin, Germany", latitude=52.5200, longitude=13.4050)
    destination = Location(address="Munich, Germany", latitude=48.1351, longitude=11.5820)
    
    mock_openai_client.chat.completions.create.side_effect = OpenAIError("API Error")
    
    with patch('src.infrastructure.services.openai_service.get_settings', return_value=mock_settings), \
         patch('src.infrastructure.services.openai_service.OpenAI', return_value=mock_openai_client):
        service = OpenAIService()
        
        with pytest.raises(AIServiceError) as exc_info:
            service.enhance_route_description(origin, destination, 584.0, 5.5)
        
        assert "Failed to enhance route description" in str(exc_info.value)


def test_enhance_route_description_with_empty_context(mock_settings, mock_openai_client):
    """Test route description enhancement with empty context."""
    origin = Location(address="Berlin, Germany", latitude=52.5200, longitude=13.4050)
    destination = Location(address="Munich, Germany", latitude=48.1351, longitude=11.5820)
    
    expected_content = "Basic route description without context"
    mock_completion = create_mock_chat_completion(expected_content)
    mock_openai_client.chat.completions.create.return_value = mock_completion
    
    with patch('src.infrastructure.services.openai_service.get_settings', return_value=mock_settings), \
         patch('src.infrastructure.services.openai_service.OpenAI', return_value=mock_openai_client):
        service = OpenAIService()
        result = service.enhance_route_description(origin, destination, 584.0, 5.5)
        
        assert result == expected_content
        call_args = mock_openai_client.chat.completions.create.call_args
        messages = call_args[1]['messages']
        
        assert "Additional context" not in messages[1]['content']


def test_generate_fun_fact_success(mock_settings, mock_openai_client):
    """Test successful fun fact generation."""
    with patch.dict(os.environ, {'OPENAI_API_KEY': ''}, clear=True), \
         patch('src.infrastructure.services.openai_service.get_settings', return_value=mock_settings), \
         patch('src.infrastructure.services.openai_service.OpenAI', return_value=mock_openai_client):  
        
        # Create mock response
        mock_message = ChatCompletionMessage(
            role="assistant",
            content="Fun fact about the route from Berlin to Warsaw"
        )
        mock_choice = Choice(
            finish_reason="stop",
            index=0,
            message=mock_message,
            logprobs=None
        )
        mock_completion = ChatCompletion(
            id="mock-completion",
            choices=[mock_choice],
            model="gpt-4o-mini",
            object="chat.completion",
            created=int(time.time())
        )
        
        # Set up the mock to return our prepared response
        mock_openai_client.chat.completions.create.return_value = mock_completion

        service = OpenAIService()  
        origin = Location(address="Berlin, Germany", latitude=52.5200, longitude=13.4050)
        destination = Location(address="Warsaw, Poland", latitude=52.2297, longitude=21.0122)
        result = service.generate_route_fact(origin, destination)
        
        # Assertions
        assert isinstance(result, str)
        assert len(result) > 0
        mock_openai_client.chat.completions.create.assert_called_once()


def test_generate_fun_fact_api_error(mock_settings, mock_openai_client):
    """Test API error handling in fun fact generation."""
    with patch.dict(os.environ, {'OPENAI_API_KEY': ''}, clear=True), \
         patch('src.infrastructure.services.openai_service.get_settings', return_value=mock_settings), \
         patch('src.infrastructure.services.openai_service.OpenAI', return_value=mock_openai_client):  
        # Create a mock error response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "API error"
        mock_error = OpenAIError("API error")
        mock_error.response = mock_response
        mock_error.body = {"error": {"message": "API error"}}
        
        mock_openai_client.chat.completions.create.side_effect = [mock_error] * 3  

        service = OpenAIService()  
        origin = Location(address="Berlin, Germany", latitude=52.5200, longitude=13.4050)
        destination = Location(address="Warsaw, Poland", latitude=52.2297, longitude=21.0122)
        with pytest.raises(AIServiceError) as exc_info:
            service.generate_route_fact(origin, destination)
        assert "OpenAI API error after 3 retries" in str(exc_info.value)


def test_generate_fun_fact_rate_limit(mock_settings, mock_openai_client):
    """Test rate limit error handling in fun fact generation."""
    with patch.dict(os.environ, {'OPENAI_API_KEY': ''}, clear=True), \
         patch('src.infrastructure.services.openai_service.get_settings', return_value=mock_settings), \
         patch('src.infrastructure.services.openai_service.OpenAI', return_value=mock_openai_client):  
        # Create a mock rate limit error response
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        mock_error = OpenAIError("Rate limit exceeded")
        mock_error.response = mock_response
        mock_error.body = {"error": {"message": "Rate limit exceeded"}}
        
        mock_openai_client.chat.completions.create.side_effect = [mock_error] * 3  

        service = OpenAIService()  
        origin = Location(address="Berlin, Germany", latitude=52.5200, longitude=13.4050)
        destination = Location(address="Warsaw, Poland", latitude=52.2297, longitude=21.0122)
        with pytest.raises(AIServiceError) as exc_info:
            service.generate_route_fact(origin, destination)
        assert "OpenAI API error after 3 retries" in str(exc_info.value)


def test_generate_route_description_success(mock_settings, mock_openai_client):
    """Test successful route description generation."""
    with patch.dict(os.environ, {'OPENAI_API_KEY': ''}, clear=True), \
         patch('src.infrastructure.services.openai_service.get_settings', return_value=mock_settings), \
         patch('src.infrastructure.services.openai_service.OpenAI', return_value=mock_openai_client):  
        
        # Create mock response
        mock_message = ChatCompletionMessage(
            role="assistant",
            content="Detailed route description from Berlin to Warsaw"
        )
        mock_choice = Choice(
            finish_reason="stop",
            index=0,
            message=mock_message,
            logprobs=None
        )
        mock_completion = ChatCompletion(
            id="mock-completion",
            choices=[mock_choice],
            model="gpt-4o-mini",
            object="chat.completion",
            created=int(time.time())
        )
        
        # Set up the mock to return our prepared response
        mock_openai_client.chat.completions.create.return_value = mock_completion

        service = OpenAIService()  
        origin = Location(address="Berlin, Germany", latitude=52.5200, longitude=13.4050)
        destination = Location(address="Warsaw, Poland", latitude=52.2297, longitude=21.0122)
        result = service.enhance_route_description(origin, destination, 500.0, 6.5)
        
        # Assertions
        assert isinstance(result, str)
        assert len(result) > 0
        mock_openai_client.chat.completions.create.assert_called_once()


def test_generate_route_description_error(mock_settings, mock_openai_client):
    """Test error handling in route description generation."""
    with patch.dict(os.environ, {'OPENAI_API_KEY': ''}, clear=True), \
         patch('src.infrastructure.services.openai_service.get_settings', return_value=mock_settings), \
         patch('src.infrastructure.services.openai_service.OpenAI', return_value=mock_openai_client):  
        # Create a mock error response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "API error"
        mock_error = OpenAIError("API error")
        mock_error.response = mock_response
        mock_error.body = {"error": {"message": "API error"}}
        
        mock_openai_client.chat.completions.create.side_effect = [mock_error] * 3  

        service = OpenAIService()  
        origin = Location(address="Berlin, Germany", latitude=52.5200, longitude=13.4050)
        destination = Location(address="Warsaw, Poland", latitude=52.2297, longitude=21.0122)
        with pytest.raises(AIServiceError) as exc_info:
            service.enhance_route_description(origin, destination, 500.0, 6.5)
        assert "OpenAI API error after 3 retries" in str(exc_info.value)


@pytest.mark.integration
class TestOpenAIServiceIntegration:
    """Integration tests for OpenAIService."""
    
    @pytest.fixture(autouse=True)
    def setup(self, caplog):
        """Setup for each test method."""
        caplog.set_level(logging.INFO)
        
        # Get current directory and .env file path
        current_dir = os.getcwd()
        env_file_path = os.path.join(current_dir, '.env')
        logger.info(f"Current directory: {current_dir}")
        logger.info(f".env file exists: {os.path.exists(env_file_path)}")
        
        # Debug: Print environment variables before loading
        logger.info("Environment before loading .env:")
        logger.info(f"OPENAI_API_KEY before: {os.getenv('OPENAI_API_KEY')}")
        
        # Load environment variables with explicit path
        load_dotenv(dotenv_path=env_file_path, override=True)
        
        # Debug: Print environment variables after loading
        logger.info("Environment after loading .env:")
        logger.info(f"OPENAI_API_KEY after: {os.getenv('OPENAI_API_KEY')}")
        
        # Get API key and print debug info
        self.api_key = os.getenv('OPENAI_API_KEY')
        logger.info(f"API Key: {self.api_key[:10] if self.api_key else 'None'}... (length: {len(self.api_key) if self.api_key else 0})")
        
        # Check if API key is set
        if not self.api_key:
            pytest.skip("OPENAI_API_KEY not set in environment")
            
        # Verify API key format
        if not self.api_key.startswith(('sk-', 'sk-proj-')):
            logger.info(f"Invalid key format. Key starts with: {self.api_key[:10] if self.api_key else 'None'}...")
            pytest.skip("Invalid OPENAI_API_KEY format")
            
        # Initialize settings with explicit env file path
        self.settings = Settings(_env_file=env_file_path)
        logger.info(f"Settings API Key: {self.settings.OPENAI_API_KEY[:10] if self.settings.OPENAI_API_KEY else 'None'}... (length: {len(self.settings.OPENAI_API_KEY) if self.settings.OPENAI_API_KEY else 0})")

    def test_generate_route_fact_integration(self):
        """Integration test for route fact generation."""
        try:
            service = OpenAIService(api_key=self.api_key)  # Pass API key directly
            origin = Location(address="Berlin, Germany", latitude=52.5200, longitude=13.4050)
            destination = Location(address="Warsaw, Poland", latitude=52.2297, longitude=21.0122)
            result = service.generate_route_fact(origin, destination)
            assert isinstance(result, str)
            assert len(result) > 0
        except AIServiceError as e:
            pytest.fail(f"Integration test failed: {str(e)}")

    def test_enhance_route_description_integration(self):
        """Integration test for route description enhancement."""
        try:
            service = OpenAIService(api_key=self.api_key)  # Pass API key directly
            origin = Location(address="Berlin, Germany", latitude=52.5200, longitude=13.4050)
            destination = Location(address="Warsaw, Poland", latitude=52.2297, longitude=21.0122)
            result = service.enhance_route_description(origin, destination, 500.0, 6.5)
            assert isinstance(result, str)
            assert len(result) > 0
        except AIServiceError as e:
            pytest.fail(f"Integration test failed: {str(e)}")
