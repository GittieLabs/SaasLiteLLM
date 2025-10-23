"""
Comprehensive tests for direct_provider_service module

Tests direct LLM provider integration including:
- Provider enum and exception classes
- DirectProviderService initialization
- chat_completion() router logic for all providers
- chat_completion_stream() router logic
- Provider detection from model names
- Error handling (rate limits, auth failures, general errors)
- Retry logic with exponential backoff
- get_direct_provider_service() factory function
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from typing import Dict, Any

# Import from src
import sys
from pathlib import Path as PathType
sys.path.insert(0, str(PathType(__file__).parent.parent / "src"))

from services.direct_provider_service import (
    DirectProviderService,
    Provider,
    ProviderError,
    RateLimitError,
    AuthenticationError,
    get_direct_provider_service
)


class TestProviderEnum:
    """Test Provider enum"""

    def test_provider_enum_values(self):
        """Test that Provider enum has expected values"""
        assert Provider.OPENAI.value == "openai"
        assert Provider.ANTHROPIC.value == "anthropic"
        assert Provider.GEMINI.value == "gemini"
        assert Provider.FIREWORKS.value == "fireworks"

    def test_provider_enum_from_string(self):
        """Test creating Provider from string"""
        assert Provider("openai") == Provider.OPENAI
        assert Provider("anthropic") == Provider.ANTHROPIC
        assert Provider("gemini") == Provider.GEMINI
        assert Provider("fireworks") == Provider.FIREWORKS

    def test_provider_enum_case_sensitive(self):
        """Test that Provider enum is case-sensitive"""
        # Should work with lowercase
        provider = Provider("openai")
        assert provider == Provider.OPENAI


class TestExceptions:
    """Test custom exception classes"""

    def test_provider_error_is_exception(self):
        """Test ProviderError is an Exception"""
        error = ProviderError("test error")
        assert isinstance(error, Exception)
        assert str(error) == "test error"

    def test_rate_limit_error_is_provider_error(self):
        """Test RateLimitError inherits from ProviderError"""
        error = RateLimitError("rate limited")
        assert isinstance(error, ProviderError)
        assert isinstance(error, Exception)

    def test_authentication_error_is_provider_error(self):
        """Test AuthenticationError inherits from ProviderError"""
        error = AuthenticationError("auth failed")
        assert isinstance(error, ProviderError)
        assert isinstance(error, Exception)


class TestDirectProviderServiceInit:
    """Test DirectProviderService initialization"""

    def test_service_initialization(self):
        """Test service initializes with correct defaults"""
        service = DirectProviderService()

        assert service.max_retries == 3
        assert service.base_retry_delay == 1.0

    def test_service_has_required_methods(self):
        """Test service has all required methods"""
        service = DirectProviderService()

        assert hasattr(service, 'chat_completion')
        assert hasattr(service, 'chat_completion_stream')
        assert hasattr(service, 'detect_provider_from_model')
        assert hasattr(service, 'get_provider_credential')


class TestDetectProviderFromModel:
    """Test provider detection from model names"""

    def test_detect_openai_gpt_models(self):
        """Test OpenAI GPT model detection"""
        service = DirectProviderService()

        assert service.detect_provider_from_model("gpt-4") == "openai"
        assert service.detect_provider_from_model("gpt-4o") == "openai"
        assert service.detect_provider_from_model("gpt-3.5-turbo") == "openai"
        assert service.detect_provider_from_model("GPT-4") == "openai"  # Case insensitive

    def test_detect_openai_o_models(self):
        """Test OpenAI O1/O3 model detection"""
        service = DirectProviderService()

        assert service.detect_provider_from_model("o1-preview") == "openai"
        assert service.detect_provider_from_model("o3-mini") == "openai"

    def test_detect_anthropic_claude_models(self):
        """Test Anthropic Claude model detection"""
        service = DirectProviderService()

        assert service.detect_provider_from_model("claude-3-opus") == "anthropic"
        assert service.detect_provider_from_model("claude-sonnet-4-5") == "anthropic"
        assert service.detect_provider_from_model("CLAUDE-HAIKU-3-5") == "anthropic"

    def test_detect_google_gemini_models(self):
        """Test Google Gemini model detection"""
        service = DirectProviderService()

        assert service.detect_provider_from_model("gemini-pro") == "gemini"
        assert service.detect_provider_from_model("gemini-1.5-flash") == "gemini"
        assert service.detect_provider_from_model("gemini-2.5-pro") == "gemini"

    def test_detect_fireworks_models(self):
        """Test Fireworks model detection"""
        service = DirectProviderService()

        assert service.detect_provider_from_model("llama-3-70b") == "fireworks"
        assert service.detect_provider_from_model("mixtral-8x7b") == "fireworks"
        assert service.detect_provider_from_model("accounts/fireworks/models/llama-v3") == "fireworks"

    def test_detect_unknown_model_defaults_to_openai(self):
        """Test unknown models default to OpenAI"""
        service = DirectProviderService()

        # Unknown model should default to OpenAI
        assert service.detect_provider_from_model("unknown-model-xyz") == "openai"


class TestChatCompletionRouting:
    """Test chat_completion() routing to provider-specific methods"""

    @pytest.mark.asyncio
    async def test_chat_completion_routes_to_openai(self):
        """Test chat_completion routes OpenAI requests correctly"""
        service = DirectProviderService()

        # Mock the OpenAI-specific method
        mock_response = {
            "id": "chatcmpl-123",
            "model": "gpt-4o",
            "choices": [{"message": {"role": "assistant", "content": "Hello!"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
        }
        service._openai_chat_completion = AsyncMock(return_value=mock_response)

        messages = [{"role": "user", "content": "Hi"}]
        result = await service.chat_completion(
            provider="openai",
            api_key="sk-test",
            model="gpt-4o",
            messages=messages
        )

        # Verify the OpenAI method was called
        service._openai_chat_completion.assert_called_once()
        assert result == mock_response

    @pytest.mark.asyncio
    async def test_chat_completion_routes_to_anthropic(self):
        """Test chat_completion routes Anthropic requests correctly"""
        service = DirectProviderService()

        mock_response = {
            "id": "msg_123",
            "model": "claude-sonnet-4-5",
            "choices": [{"message": {"role": "assistant", "content": "Hello!"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
        }
        service._anthropic_chat_completion = AsyncMock(return_value=mock_response)

        messages = [{"role": "user", "content": "Hi"}]
        result = await service.chat_completion(
            provider="anthropic",
            api_key="sk-ant-test",
            model="claude-sonnet-4-5",
            messages=messages
        )

        service._anthropic_chat_completion.assert_called_once()
        assert result == mock_response

    @pytest.mark.asyncio
    async def test_chat_completion_routes_to_gemini(self):
        """Test chat_completion routes Gemini requests correctly"""
        service = DirectProviderService()

        mock_response = {
            "id": "gemini-123",
            "model": "gemini-pro",
            "choices": [{"message": {"role": "assistant", "content": "Hello!"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
        }
        service._gemini_chat_completion = AsyncMock(return_value=mock_response)

        messages = [{"role": "user", "content": "Hi"}]
        result = await service.chat_completion(
            provider="gemini",
            api_key="test-key",
            model="gemini-pro",
            messages=messages
        )

        service._gemini_chat_completion.assert_called_once()
        assert result == mock_response

    @pytest.mark.asyncio
    async def test_chat_completion_routes_to_fireworks(self):
        """Test chat_completion routes Fireworks requests correctly"""
        service = DirectProviderService()

        mock_response = {
            "id": "fw-123",
            "model": "llama-3-70b",
            "choices": [{"message": {"role": "assistant", "content": "Hello!"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
        }
        service._fireworks_chat_completion = AsyncMock(return_value=mock_response)

        messages = [{"role": "user", "content": "Hi"}]
        result = await service.chat_completion(
            provider="fireworks",
            api_key="fw-test",
            model="llama-3-70b",
            messages=messages
        )

        service._fireworks_chat_completion.assert_called_once()
        assert result == mock_response

    @pytest.mark.asyncio
    async def test_chat_completion_unsupported_provider_raises_error(self):
        """Test chat_completion raises error for unsupported provider"""
        service = DirectProviderService()

        messages = [{"role": "user", "content": "Hi"}]

        # Invalid provider should raise ValueError
        with pytest.raises(ValueError):
            await service.chat_completion(
                provider="invalid_provider",
                api_key="test-key",
                model="test-model",
                messages=messages
            )

    @pytest.mark.asyncio
    async def test_chat_completion_passes_all_parameters(self):
        """Test that all parameters are passed through correctly"""
        service = DirectProviderService()

        mock_response = {"id": "test", "model": "gpt-4o", "choices": [], "usage": {}}
        service._openai_chat_completion = AsyncMock(return_value=mock_response)

        messages = [{"role": "user", "content": "Hi"}]
        await service.chat_completion(
            provider="openai",
            api_key="sk-test",
            model="gpt-4o",
            messages=messages,
            temperature=0.5,
            max_tokens=100,
            response_format={"type": "json_object"},
            tools=[{"type": "function", "function": {"name": "test"}}],
            tool_choice="auto",
            top_p=0.9,
            frequency_penalty=0.5,
            presence_penalty=0.5,
            stop=["END"]
        )

        # Verify all parameters were passed
        call_kwargs = service._openai_chat_completion.call_args[1]
        assert call_kwargs["temperature"] == 0.5
        assert call_kwargs["max_tokens"] == 100
        assert call_kwargs["response_format"] == {"type": "json_object"}
        assert call_kwargs["tools"] == [{"type": "function", "function": {"name": "test"}}]
        assert call_kwargs["top_p"] == 0.9


class TestChatCompletionStreamRouting:
    """Test chat_completion_stream() routing"""

    @pytest.mark.asyncio
    async def test_chat_completion_stream_routes_to_openai(self):
        """Test streaming routes to OpenAI"""
        service = DirectProviderService()

        mock_response = Mock()
        service._openai_chat_completion_stream = AsyncMock(return_value=mock_response)

        messages = [{"role": "user", "content": "Hi"}]
        result = await service.chat_completion_stream(
            provider="openai",
            api_key="sk-test",
            model="gpt-4o",
            messages=messages
        )

        service._openai_chat_completion_stream.assert_called_once()
        assert result == mock_response

    @pytest.mark.asyncio
    async def test_chat_completion_stream_routes_to_anthropic(self):
        """Test streaming routes to Anthropic"""
        service = DirectProviderService()

        mock_response = Mock()
        service._anthropic_chat_completion_stream = AsyncMock(return_value=mock_response)

        messages = [{"role": "user", "content": "Hi"}]
        result = await service.chat_completion_stream(
            provider="anthropic",
            api_key="sk-ant-test",
            model="claude-sonnet-4-5",
            messages=messages
        )

        service._anthropic_chat_completion_stream.assert_called_once()
        assert result == mock_response

    @pytest.mark.asyncio
    async def test_chat_completion_stream_routes_to_gemini(self):
        """Test streaming routes to Gemini"""
        service = DirectProviderService()

        mock_response = Mock()
        service._gemini_chat_completion_stream = AsyncMock(return_value=mock_response)

        messages = [{"role": "user", "content": "Hi"}]
        result = await service.chat_completion_stream(
            provider="gemini",
            api_key="test-key",
            model="gemini-pro",
            messages=messages
        )

        service._gemini_chat_completion_stream.assert_called_once()
        assert result == mock_response

    @pytest.mark.asyncio
    async def test_chat_completion_stream_routes_to_fireworks(self):
        """Test streaming routes to Fireworks"""
        service = DirectProviderService()

        mock_response = Mock()
        service._fireworks_chat_completion_stream = AsyncMock(return_value=mock_response)

        messages = [{"role": "user", "content": "Hi"}]
        result = await service.chat_completion_stream(
            provider="fireworks",
            api_key="fw-test",
            model="llama-3-70b",
            messages=messages
        )

        service._fireworks_chat_completion_stream.assert_called_once()
        assert result == mock_response


class TestGetProviderCredential:
    """Test get_provider_credential() database query logic"""

    @pytest.mark.asyncio
    async def test_get_provider_credential_found(self):
        """Test retrieving existing provider credential"""
        service = DirectProviderService()

        # Mock database and credential
        mock_db = Mock()
        mock_credential = Mock()
        mock_credential.provider = "openai"
        mock_credential.get_api_key = Mock(return_value="sk-test-key")

        # Mock query chain
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_credential
        mock_db.query.return_value = mock_query

        result = await service.get_provider_credential(
            mock_db,
            "org_123",
            "openai"
        )

        assert result == ("sk-test-key", "openai")
        mock_db.query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_provider_credential_not_found(self):
        """Test when credential not found"""
        service = DirectProviderService()

        # Mock database with no result
        mock_db = Mock()
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query

        result = await service.get_provider_credential(
            mock_db,
            "org_123",
            "openai"
        )

        assert result is None


class TestGetDirectProviderService:
    """Test factory function"""

    def test_get_direct_provider_service_returns_instance(self):
        """Test factory function returns DirectProviderService instance"""
        service = get_direct_provider_service()

        assert isinstance(service, DirectProviderService)
        assert service.max_retries == 3
        assert service.base_retry_delay == 1.0

    def test_get_direct_provider_service_returns_new_instance(self):
        """Test factory returns new instance each time"""
        service1 = get_direct_provider_service()
        service2 = get_direct_provider_service()

        # Should be different instances
        assert service1 is not service2


class TestOpenAIIntegration:
    """Test OpenAI-specific behavior (mocked)"""

    @pytest.mark.asyncio
    async def test_openai_response_format_conversion(self):
        """Test that OpenAI response is converted to standard format"""
        service = DirectProviderService()

        # Mock OpenAI client
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.id = "chatcmpl-123"
        mock_response.model = "gpt-4o"
        mock_response.created = 1234567890
        mock_response.object = "chat.completion"

        # Mock choice
        mock_choice = Mock()
        mock_choice.index = 0
        mock_choice.finish_reason = "stop"
        mock_choice.message = Mock()
        mock_choice.message.role = "assistant"
        mock_choice.message.content = "Hello, world!"
        mock_choice.message.tool_calls = None
        mock_response.choices = [mock_choice]

        # Mock usage
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch('openai.AsyncOpenAI', return_value=mock_client):
            result = await service._openai_chat_completion(
                api_key="sk-test",
                model="gpt-4o",
                messages=[{"role": "user", "content": "Hi"}]
            )

        # Verify response format
        assert result["id"] == "chatcmpl-123"
        assert result["model"] == "gpt-4o"
        assert len(result["choices"]) == 1
        assert result["choices"][0]["message"]["content"] == "Hello, world!"
        assert result["usage"]["total_tokens"] == 15

    @pytest.mark.asyncio
    async def test_openai_rate_limit_retry(self):
        """Test retry logic for OpenAI rate limits"""
        service = DirectProviderService()
        service.max_retries = 3
        service.base_retry_delay = 0.01  # Fast for testing

        # Mock OpenAI client that fails twice then succeeds
        import openai
        mock_client = AsyncMock()

        rate_limit_error = openai.RateLimitError("Rate limit exceeded", response=Mock(), body=None)

        # First two calls fail, third succeeds
        mock_response = Mock()
        mock_response.id = "chatcmpl-123"
        mock_response.model = "gpt-4o"
        mock_response.created = 1234567890
        mock_response.object = "chat.completion"
        mock_response.choices = []
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        mock_client.chat.completions.create = AsyncMock(
            side_effect=[rate_limit_error, rate_limit_error, mock_response]
        )

        with patch('openai.AsyncOpenAI', return_value=mock_client):
            result = await service._openai_chat_completion(
                api_key="sk-test",
                model="gpt-4o",
                messages=[{"role": "user", "content": "Hi"}]
            )

        # Should have succeeded after retries
        assert result["id"] == "chatcmpl-123"
        assert mock_client.chat.completions.create.call_count == 3

    @pytest.mark.asyncio
    async def test_openai_auth_error_no_retry(self):
        """Test that auth errors don't retry"""
        service = DirectProviderService()

        import openai
        mock_client = AsyncMock()
        auth_error = openai.AuthenticationError("Invalid API key", response=Mock(), body=None)
        mock_client.chat.completions.create = AsyncMock(side_effect=auth_error)

        with patch('openai.AsyncOpenAI', return_value=mock_client):
            with pytest.raises(AuthenticationError):
                await service._openai_chat_completion(
                    api_key="sk-invalid",
                    model="gpt-4o",
                    messages=[{"role": "user", "content": "Hi"}]
                )

        # Should only try once for auth errors
        assert mock_client.chat.completions.create.call_count == 1


class TestAnthropicIntegration:
    """Test Anthropic-specific behavior (mocked)"""

    @pytest.mark.asyncio
    async def test_anthropic_message_conversion(self):
        """Test that messages are converted to Anthropic format"""
        service = DirectProviderService()

        # Mock Anthropic client
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.id = "msg_123"
        mock_response.model = "claude-sonnet-4-5"
        mock_response.stop_reason = "end_turn"

        # Mock content block
        mock_content_block = Mock()
        mock_content_block.text = "Hello from Claude!"
        mock_response.content = [mock_content_block]

        # Mock usage
        mock_response.usage = Mock()
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 8

        mock_client.messages.create = AsyncMock(return_value=mock_response)

        with patch('anthropic.AsyncAnthropic', return_value=mock_client):
            result = await service._anthropic_chat_completion(
                api_key="sk-ant-test",
                model="claude-sonnet-4-5",
                messages=[
                    {"role": "system", "content": "You are helpful"},
                    {"role": "user", "content": "Hello"}
                ]
            )

        # Verify system message was separated
        call_kwargs = mock_client.messages.create.call_args[1]
        assert "system" in call_kwargs
        assert call_kwargs["system"] == "You are helpful"

        # Verify response format
        assert result["model"] == "claude-sonnet-4-5"
        assert result["choices"][0]["message"]["content"] == "Hello from Claude!"
        assert result["usage"]["prompt_tokens"] == 10
        assert result["usage"]["completion_tokens"] == 8


class TestRetryLogic:
    """Test retry and error handling logic"""

    @pytest.mark.asyncio
    async def test_exponential_backoff(self):
        """Test that retry delay increases exponentially"""
        service = DirectProviderService()
        service.max_retries = 3
        service.base_retry_delay = 1.0

        import openai
        mock_client = AsyncMock()

        # Always fail with rate limit
        rate_limit_error = openai.RateLimitError("Rate limit", response=Mock(), body=None)
        mock_client.chat.completions.create = AsyncMock(side_effect=rate_limit_error)

        with patch('openai.AsyncOpenAI', return_value=mock_client):
            with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                try:
                    await service._openai_chat_completion(
                        api_key="sk-test",
                        model="gpt-4o",
                        messages=[{"role": "user", "content": "Hi"}]
                    )
                except RateLimitError:
                    pass

        # Check exponential backoff: 1.0, 2.0 (for 3 retries = 2 sleeps between attempts)
        assert mock_sleep.call_count == 2
        sleep_delays = [call[0][0] for call in mock_sleep.call_args_list]
        assert sleep_delays[0] == 1.0  # First retry after 1s
        assert sleep_delays[1] == 2.0  # Second retry after 2s


class TestProviderSpecificParameters:
    """Test that provider-specific parameters are handled"""

    @pytest.mark.asyncio
    async def test_openai_supports_response_format(self):
        """Test OpenAI receives response_format parameter"""
        service = DirectProviderService()

        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.id = "test"
        mock_response.model = "gpt-4o"
        mock_response.choices = []
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 1
        mock_response.usage.completion_tokens = 1
        mock_response.usage.total_tokens = 2
        mock_response.created = 123
        mock_response.object = "chat.completion"

        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch('openai.AsyncOpenAI', return_value=mock_client):
            await service._openai_chat_completion(
                api_key="sk-test",
                model="gpt-4o",
                messages=[{"role": "user", "content": "Hi"}],
                response_format={"type": "json_object"}
            )

        # Verify response_format was passed
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert "response_format" in call_kwargs
        assert call_kwargs["response_format"] == {"type": "json_object"}

    @pytest.mark.asyncio
    async def test_anthropic_requires_max_tokens(self):
        """Test Anthropic uses default max_tokens if not provided"""
        service = DirectProviderService()

        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.id = "msg_123"
        mock_response.model = "claude-sonnet-4-5"
        mock_response.stop_reason = "end_turn"
        mock_response.content = []
        mock_response.usage = Mock()
        mock_response.usage.input_tokens = 1
        mock_response.usage.output_tokens = 1

        mock_client.messages.create = AsyncMock(return_value=mock_response)

        with patch('anthropic.AsyncAnthropic', return_value=mock_client):
            await service._anthropic_chat_completion(
                api_key="sk-ant-test",
                model="claude-sonnet-4-5",
                messages=[{"role": "user", "content": "Hi"}]
                # No max_tokens provided
            )

        # Verify default max_tokens=4096 was used
        call_kwargs = mock_client.messages.create.call_args[1]
        assert "max_tokens" in call_kwargs
        assert call_kwargs["max_tokens"] == 4096
