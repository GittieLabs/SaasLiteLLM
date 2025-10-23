"""
Unit tests for DirectProviderService (Phase 1: LiteLLM Proxy Removal)

Tests the direct provider integration service that calls LLM provider APIs directly
without going through the LiteLLM proxy.
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import httpx

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from services.direct_provider_service import (
    DirectProviderService,
    get_direct_provider_service,
    Provider
)


@pytest.fixture
def direct_service():
    """Fixture to create a DirectProviderService instance"""
    return DirectProviderService()


@pytest.fixture
def mock_db():
    """Fixture to create a mock database session"""
    return Mock()


class TestProviderDetection:
    """Test provider detection from model names"""

    def test_detect_openai_gpt4(self, direct_service):
        """Test detection of OpenAI GPT-4 models"""
        assert direct_service.detect_provider_from_model("gpt-4") == "openai"
        assert direct_service.detect_provider_from_model("gpt-4-turbo") == "openai"
        assert direct_service.detect_provider_from_model("gpt-4o") == "openai"

    def test_detect_openai_gpt35(self, direct_service):
        """Test detection of OpenAI GPT-3.5 models"""
        assert direct_service.detect_provider_from_model("gpt-3.5-turbo") == "openai"

    def test_detect_openai_o1(self, direct_service):
        """Test detection of OpenAI O1 models"""
        assert direct_service.detect_provider_from_model("o1-preview") == "openai"
        assert direct_service.detect_provider_from_model("o1-mini") == "openai"

    def test_detect_anthropic_claude(self, direct_service):
        """Test detection of Anthropic Claude models"""
        assert direct_service.detect_provider_from_model("claude-3-opus") == "anthropic"
        assert direct_service.detect_provider_from_model("claude-3-sonnet") == "anthropic"
        assert direct_service.detect_provider_from_model("claude-2") == "anthropic"

    def test_detect_gemini(self, direct_service):
        """Test detection of Google Gemini models"""
        assert direct_service.detect_provider_from_model("gemini-pro") == "gemini"
        assert direct_service.detect_provider_from_model("gemini-1.5-pro") == "gemini"

    def test_detect_fireworks_llama(self, direct_service):
        """Test detection of Fireworks models"""
        assert direct_service.detect_provider_from_model("llama-v3-70b") == "fireworks"
        assert direct_service.detect_provider_from_model("mixtral-8x7b") == "fireworks"
        assert direct_service.detect_provider_from_model("fireworks/llama") == "fireworks"

    def test_detect_default_to_openai(self, direct_service):
        """Test that unknown models default to OpenAI"""
        assert direct_service.detect_provider_from_model("unknown-model") == "openai"


class TestProviderCredentialRetrieval:
    """Test retrieval of provider credentials from database"""

    def test_provider_credential_method_exists(self, direct_service):
        """Test that get_provider_credential method exists"""
        assert hasattr(direct_service, 'get_provider_credential')
        assert callable(getattr(direct_service, 'get_provider_credential'))


class TestOpenAIChatCompletion:
    """Test OpenAI chat completion calls"""

    def test_openai_chat_completion_method_exists(self, direct_service):
        """Test that OpenAI chat completion method exists"""
        assert hasattr(direct_service, '_openai_chat_completion')
        assert hasattr(direct_service, 'chat_completion')


class TestAnthropicChatCompletion:
    """Test Anthropic chat completion calls"""

    def test_anthropic_chat_completion_method_exists(self, direct_service):
        """Test that Anthropic chat completion method exists"""
        assert hasattr(direct_service, '_anthropic_chat_completion')
        assert hasattr(direct_service, 'chat_completion')


class TestGeminiChatCompletion:
    """Test Google Gemini chat completion calls"""

    @pytest.mark.asyncio
    async def test_gemini_message_conversion(self, direct_service):
        """Test conversion of OpenAI format to Gemini format"""
        mock_response = {
            "candidates": [{
                "content": {
                    "parts": [{"text": "Hello from Gemini!"}]
                },
                "finishReason": "STOP"
            }],
            "usageMetadata": {
                "promptTokenCount": 8,
                "candidatesTokenCount": 12,
                "totalTokenCount": 20
            }
        }

        with patch('httpx.AsyncClient') as mock_client:
            mock_post = AsyncMock(return_value=Mock(
                status_code=200,
                json=Mock(return_value=mock_response)
            ))
            mock_client.return_value.__aenter__.return_value.post = mock_post

            result = await direct_service.chat_completion(
                provider="gemini",
                api_key="test-gemini-key",
                model="gemini-pro",
                messages=[{"role": "user", "content": "Hello"}]
            )

            # Verify conversion to OpenAI format
            assert "choices" in result
            assert result["choices"][0]["message"]["content"] == "Hello from Gemini!"
            assert result["usage"]["total_tokens"] == 20


class TestFireworksChatCompletion:
    """Test Fireworks AI chat completion calls"""

    @pytest.mark.asyncio
    async def test_fireworks_chat_completion(self, direct_service):
        """Test Fireworks chat completion (uses OpenAI-compatible API)"""
        mock_response = {
            "id": "fw-123",
            "choices": [{
                "message": {"content": "Response from Llama"},
                "finish_reason": "stop"
            }],
            "usage": {"total_tokens": 30}
        }

        with patch('httpx.AsyncClient') as mock_client:
            mock_post = AsyncMock(return_value=Mock(
                status_code=200,
                json=Mock(return_value=mock_response)
            ))
            mock_client.return_value.__aenter__.return_value.post = mock_post

            result = await direct_service.chat_completion(
                provider="fireworks",
                api_key="fw-test",
                model="llama-v3-70b",
                messages=[{"role": "user", "content": "Test"}]
            )

            assert result["choices"][0]["message"]["content"] == "Response from Llama"


class TestStreamingChatCompletion:
    """Test streaming chat completions"""

    def test_streaming_method_exists(self, direct_service):
        """Test that streaming methods exist"""
        assert hasattr(direct_service, 'chat_completion_stream')
        assert callable(getattr(direct_service, 'chat_completion_stream'))


class TestServiceSingleton:
    """Test the singleton pattern for DirectProviderService"""

    def test_get_direct_provider_service_returns_instance(self):
        """Test that get_direct_provider_service returns a DirectProviderService instance"""
        service = get_direct_provider_service()
        assert isinstance(service, DirectProviderService)


class TestErrorHandling:
    """Test error handling in DirectProviderService"""

    @pytest.mark.asyncio
    async def test_invalid_provider(self, direct_service):
        """Test handling of invalid provider"""
        with pytest.raises(ValueError, match="is not a valid Provider"):
            await direct_service.chat_completion(
                provider="invalid_provider",
                api_key="test",
                model="test-model",
                messages=[{"role": "user", "content": "Test"}]
            )

    def test_provider_enum_has_all_providers(self):
        """Test that Provider enum has all supported providers"""
        from services.direct_provider_service import Provider
        assert hasattr(Provider, 'OPENAI')
        assert hasattr(Provider, 'ANTHROPIC')
        assert hasattr(Provider, 'GEMINI')
        assert hasattr(Provider, 'FIREWORKS')
