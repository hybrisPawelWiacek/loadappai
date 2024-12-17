"""Test OpenAI service implementation."""
import os
import time
import pytest
from unittest.mock import Mock, patch
import openai
from openai._exceptions import OpenAIError
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice

from src.domain.interfaces import AIServiceError
from src.domain.value_objects import Location
from src.infrastructure.services.openai_service import OpenAIService
from src.config import Settings, get_settings


@pytest.fixture
def mock_settings():
    """Create mock settings."""
    settings = Settings(
        _env_file=None,  # Disable .env file loading
        OPENAI_API_KEY="test-key",
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
    settings = Settings(_env_file=None)  # Disable .env file loading
    settings.OPENAI_API_KEY = None  # Ensure settings has no key
    settings.OPENAI_MODEL = "gpt-4o-mini"  # Keep the original model name
    settings.OPENAI_MAX_RETRIES = 3
    settings.OPENAI_RETRY_DELAY = 1.0
    
    with patch.dict(os.environ, {'OPENAI_API_KEY': ''}, clear=True), \
         patch('src.infrastructure.services.openai_service.get_settings', return_value=settings):
        service = OpenAIService(api_key=test_key)
        assert service.api_key == test_key
        assert service.model == "gpt-4o-mini"  # Keep the original model name
        assert service.max_retries == 3
        assert service.retry_delay == 1.0


def test_init_with_settings(mock_settings):
    """Test initialization with settings."""
    with patch.dict(os.environ, {'OPENAI_API_KEY': ''}, clear=True), \
         patch('src.infrastructure.services.openai_service.get_settings', return_value=mock_settings):
        service = OpenAIService()
        assert service.api_key == mock_settings.OPENAI_API_KEY
        assert service.model == mock_settings.OPENAI_MODEL
        assert service.max_retries == mock_settings.OPENAI_MAX_RETRIES
        assert service.retry_delay == mock_settings.OPENAI_RETRY_DELAY


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
    """Integration tests for OpenAIService.
    
    These tests require a valid OpenAI API key in the environment.
    Skip if OPENAI_API_KEY is not set or if not running integration tests.
    """

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for integration tests."""
        if not os.getenv('OPENAI_API_KEY'):
            pytest.skip("OPENAI_API_KEY not set in environment")
        yield

    def test_generate_route_fact_integration(self):
        """Integration test for route fact generation."""
        service = OpenAIService()
        origin = Location(address="Berlin, Germany", latitude=52.5200, longitude=13.4050)
        destination = Location(address="Warsaw, Poland", latitude=52.2297, longitude=21.0122)
        result = service.generate_route_fact(origin, destination)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_enhance_route_description_integration(self):
        """Integration test for route description enhancement."""
        service = OpenAIService()
        origin = Location(address="Berlin, Germany", latitude=52.5200, longitude=13.4050)
        destination = Location(address="Warsaw, Poland", latitude=52.2297, longitude=21.0122)
        result = service.enhance_route_description(origin, destination, 500.0, 6.5)
        assert isinstance(result, str)
        assert len(result) > 0
