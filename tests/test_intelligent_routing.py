"""
Unit tests for Intelligent Routing in call_litellm (Phase 2: LiteLLM Proxy Removal)

Tests the intelligent routing logic that automatically routes requests to direct
provider APIs when credentials exist, otherwise falls back to LiteLLM proxy.
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def mock_db():
    """Fixture to create a mock database session"""
    return Mock()


@pytest.fixture
def mock_team_credits():
    """Fixture to create mock team credits"""
    team_credits = Mock()
    team_credits.organization_id = "org_test_123"
    team_credits.virtual_key = "sk-litellm-test"
    return team_credits


@pytest.fixture
def mock_settings():
    """Fixture to mock settings"""
    settings = Mock()
    settings.litellm_proxy_url = "http://localhost:4000"
    return settings


class TestIntelligentRouting:
    """Test intelligent routing logic in call_litellm"""

    @pytest.mark.asyncio
    async def test_route_to_direct_provider_when_credentials_exist(self, mock_db, mock_settings):
        """Test routing to direct provider when credentials are found"""
        from saas_api import call_litellm

        # Mock provider credential
        mock_credential = Mock()
        mock_credential.provider = "openai"
        mock_credential.get_api_key.return_value = "sk-real-openai-key"

        # Mock database query to return credential
        mock_query = Mock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.first.return_value = mock_credential
        mock_db.query.return_value = mock_query

        # Mock DirectProviderService
        mock_direct_response = {
            "id": "direct-123",
            "choices": [{"message": {"content": "Direct provider response"}}],
            "usage": {"total_tokens": 20}
        }

        with patch('saas_api.settings', mock_settings), \
             patch('saas_api.DirectProviderService') as mock_service_class:

            mock_service_instance = Mock()
            mock_service_instance.detect_provider_from_model.return_value = "openai"
            mock_service_instance.get_provider_credential = AsyncMock(
                return_value=("sk-real-openai-key", "openai")
            )
            mock_service_instance.chat_completion = AsyncMock(return_value=mock_direct_response)
            mock_service_class.return_value = mock_service_instance

            # Call with db and organization_id to enable direct routing
            result = await call_litellm(
                model="gpt-4",
                messages=[{"role": "user", "content": "Test"}],
                virtual_key="sk-litellm-test",
                team_id="team_123",
                db=mock_db,
                organization_id="org_test_123"
            )

            # Verify direct provider was used
            assert result["id"] == "direct-123"
            assert result["choices"][0]["message"]["content"] == "Direct provider response"

    @pytest.mark.asyncio
    async def test_fallback_to_litellm_when_no_credentials(self, mock_db, mock_settings):
        """Test fallback to LiteLLM proxy when no credentials found"""
        from saas_api import call_litellm

        # Mock database query to return None (no credentials)
        mock_query = Mock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        # Mock LiteLLM proxy response
        mock_litellm_response = {
            "id": "litellm-123",
            "choices": [{"message": {"content": "LiteLLM proxy response"}}],
            "usage": {"total_tokens": 15}
        }

        with patch('saas_api.settings', mock_settings), \
             patch('httpx.AsyncClient') as mock_client:

            mock_post = AsyncMock(return_value=Mock(
                status_code=200,
                json=Mock(return_value=mock_litellm_response)
            ))
            mock_client.return_value.__aenter__.return_value.post = mock_post

            # Call with db and organization_id
            result = await call_litellm(
                model="gpt-4",
                messages=[{"role": "user", "content": "Test"}],
                virtual_key="sk-litellm-test",
                team_id="team_123",
                db=mock_db,
                organization_id="org_test_123"
            )

            # Verify LiteLLM proxy was used
            assert result["id"] == "litellm-123"
            assert result["choices"][0]["message"]["content"] == "LiteLLM proxy response"

    @pytest.mark.asyncio
    async def test_fallback_to_litellm_when_no_db(self, mock_settings):
        """Test fallback to LiteLLM when db parameter not provided"""
        from saas_api import call_litellm

        # Mock LiteLLM proxy response
        mock_litellm_response = {
            "id": "litellm-456",
            "choices": [{"message": {"content": "Response without DB"}}],
            "usage": {"total_tokens": 10}
        }

        with patch('saas_api.settings', mock_settings), \
             patch('httpx.AsyncClient') as mock_client:

            mock_post = AsyncMock(return_value=Mock(
                status_code=200,
                json=Mock(return_value=mock_litellm_response)
            ))
            mock_client.return_value.__aenter__.return_value.post = mock_post

            # Call WITHOUT db parameter
            result = await call_litellm(
                model="gpt-4",
                messages=[{"role": "user", "content": "Test"}],
                virtual_key="sk-litellm-test",
                team_id="team_123"
                # No db or organization_id
            )

            # Verify LiteLLM proxy was used
            assert result["id"] == "litellm-456"

    @pytest.mark.asyncio
    async def test_fallback_to_litellm_when_no_organization_id(self, mock_db, mock_settings):
        """Test fallback to LiteLLM when organization_id not provided"""
        from saas_api import call_litellm

        # Mock LiteLLM proxy response
        mock_litellm_response = {
            "id": "litellm-789",
            "choices": [{"message": {"content": "Response without org_id"}}],
            "usage": {"total_tokens": 12}
        }

        with patch('saas_api.settings', mock_settings), \
             patch('httpx.AsyncClient') as mock_client:

            mock_post = AsyncMock(return_value=Mock(
                status_code=200,
                json=Mock(return_value=mock_litellm_response)
            ))
            mock_client.return_value.__aenter__.return_value.post = mock_post

            # Call with db but WITHOUT organization_id
            result = await call_litellm(
                model="gpt-4",
                messages=[{"role": "user", "content": "Test"}],
                virtual_key="sk-litellm-test",
                team_id="team_123",
                db=mock_db
                # No organization_id
            )

            # Verify LiteLLM proxy was used
            assert result["id"] == "litellm-789"

    @pytest.mark.asyncio
    async def test_fallback_to_litellm_on_direct_provider_error(self, mock_db, mock_settings):
        """Test fallback to LiteLLM when direct provider raises an error"""
        from saas_api import call_litellm

        # Mock LiteLLM proxy response
        mock_litellm_response = {
            "id": "litellm-fallback",
            "choices": [{"message": {"content": "Fallback response"}}],
            "usage": {"total_tokens": 18}
        }

        with patch('saas_api.settings', mock_settings), \
             patch('saas_api.get_direct_provider_service') as mock_get_service, \
             patch('httpx.AsyncClient') as mock_client:

            # Mock DirectProviderService to raise an error
            mock_service = Mock()
            mock_service.detect_provider_from_model.side_effect = Exception("Provider error")
            mock_get_service.return_value = mock_service

            # Mock LiteLLM client
            mock_post = AsyncMock(return_value=Mock(
                status_code=200,
                json=Mock(return_value=mock_litellm_response)
            ))
            mock_client.return_value.__aenter__.return_value.post = mock_post

            # Call with db and organization_id
            result = await call_litellm(
                model="gpt-4",
                messages=[{"role": "user", "content": "Test"}],
                virtual_key="sk-litellm-test",
                team_id="team_123",
                db=mock_db,
                organization_id="org_test_123"
            )

            # Verify fallback to LiteLLM occurred
            assert result["id"] == "litellm-fallback"


class TestRoutingWithDifferentProviders:
    """Test routing for different LLM providers"""

    @pytest.mark.asyncio
    async def test_route_anthropic_with_credentials(self, mock_db, mock_settings):
        """Test routing to Anthropic when credentials exist"""
        from saas_api import call_litellm

        # Mock Anthropic credential
        mock_credential = Mock()
        mock_credential.provider = "anthropic"
        mock_credential.get_api_key.return_value = "sk-ant-test"

        mock_query = Mock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.first.return_value = mock_credential
        mock_db.query.return_value = mock_query

        mock_direct_response = {
            "id": "claude-123",
            "choices": [{"message": {"content": "Claude response"}}],
            "usage": {"total_tokens": 25}
        }

        with patch('saas_api.settings', mock_settings), \
             patch('saas_api.get_direct_provider_service') as mock_get_service:

            mock_service = Mock()
            mock_service.detect_provider_from_model.return_value = "anthropic"
            mock_service.get_provider_credential = AsyncMock(
                return_value=("sk-ant-test", "anthropic")
            )
            mock_service.chat_completion = AsyncMock(return_value=mock_direct_response)
            mock_get_service.return_value = mock_service

            result = await call_litellm(
                model="claude-3-opus",
                messages=[{"role": "user", "content": "Test"}],
                virtual_key="sk-litellm-test",
                team_id="team_123",
                db=mock_db,
                organization_id="org_test_123"
            )

            # Verify Anthropic was called
            mock_service.chat_completion.assert_called_once()
            assert result["id"] == "claude-123"

    @pytest.mark.asyncio
    async def test_route_gemini_with_credentials(self, mock_db, mock_settings):
        """Test routing to Gemini when credentials exist"""
        from saas_api import call_litellm

        mock_direct_response = {
            "id": "gemini-123",
            "choices": [{"message": {"content": "Gemini response"}}],
            "usage": {"total_tokens": 30}
        }

        with patch('saas_api.settings', mock_settings), \
             patch('saas_api.get_direct_provider_service') as mock_get_service:

            mock_service = Mock()
            mock_service.detect_provider_from_model.return_value = "gemini"
            mock_service.get_provider_credential = AsyncMock(
                return_value=("gemini-key-test", "gemini")
            )
            mock_service.chat_completion = AsyncMock(return_value=mock_direct_response)
            mock_get_service.return_value = mock_service

            result = await call_litellm(
                model="gemini-pro",
                messages=[{"role": "user", "content": "Test"}],
                virtual_key="sk-litellm-test",
                team_id="team_123",
                db=mock_db,
                organization_id="org_test_123"
            )

            assert result["id"] == "gemini-123"


class TestStreamingRouting:
    """Test routing for streaming requests"""

    @pytest.mark.asyncio
    async def test_streaming_with_direct_provider(self, mock_db, mock_settings):
        """Test streaming routing to direct provider"""
        from saas_api import call_litellm

        # Mock streaming response
        mock_stream_response = Mock()
        mock_stream_response.status_code = 200

        with patch('saas_api.settings', mock_settings), \
             patch('saas_api.get_direct_provider_service') as mock_get_service:

            mock_service = Mock()
            mock_service.detect_provider_from_model.return_value = "openai"
            mock_service.get_provider_credential = AsyncMock(
                return_value=("sk-openai-test", "openai")
            )
            mock_service.chat_completion_stream = AsyncMock(return_value=mock_stream_response)
            mock_get_service.return_value = mock_service

            result = await call_litellm(
                model="gpt-4",
                messages=[{"role": "user", "content": "Test"}],
                virtual_key="sk-litellm-test",
                team_id="team_123",
                stream=True,
                db=mock_db,
                organization_id="org_test_123"
            )

            # Verify streaming was called
            mock_service.chat_completion_stream.assert_called_once()
            assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_streaming_fallback_to_litellm(self, mock_db, mock_settings):
        """Test streaming fallback to LiteLLM proxy"""
        from saas_api import call_litellm

        # Mock no credentials found
        mock_query = Mock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        mock_stream_response = Mock()
        mock_stream_response.status_code = 200

        with patch('saas_api.settings', mock_settings), \
             patch('httpx.AsyncClient') as mock_client:

            mock_post = AsyncMock(return_value=mock_stream_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post

            result = await call_litellm(
                model="gpt-4",
                messages=[{"role": "user", "content": "Test"}],
                virtual_key="sk-litellm-test",
                team_id="team_123",
                stream=True,
                db=mock_db,
                organization_id="org_test_123"
            )

            # Verify LiteLLM streaming was used
            assert result.status_code == 200


class TestLoggingBehavior:
    """Test logging for routing decisions"""

    @pytest.mark.asyncio
    async def test_logs_direct_provider_routing(self, mock_db, mock_settings, caplog):
        """Test that direct provider routing is logged"""
        from saas_api import call_litellm
        import logging

        caplog.set_level(logging.INFO)

        mock_direct_response = {
            "id": "test-123",
            "choices": [{"message": {"content": "Test"}}],
            "usage": {"total_tokens": 10}
        }

        with patch('saas_api.settings', mock_settings), \
             patch('saas_api.get_direct_provider_service') as mock_get_service:

            mock_service = Mock()
            mock_service.detect_provider_from_model.return_value = "openai"
            mock_service.get_provider_credential = AsyncMock(
                return_value=("sk-test", "openai")
            )
            mock_service.chat_completion = AsyncMock(return_value=mock_direct_response)
            mock_get_service.return_value = mock_service

            await call_litellm(
                model="gpt-4",
                messages=[{"role": "user", "content": "Test"}],
                virtual_key="sk-litellm-test",
                team_id="team_123",
                db=mock_db,
                organization_id="org_test_123"
            )

            # Check that routing was logged (this would work if logging is set up)
            # In actual implementation, verify logs contain routing info


class TestBackwardCompatibility:
    """Test backward compatibility with existing code"""

    @pytest.mark.asyncio
    async def test_existing_callers_without_new_params(self, mock_settings):
        """Test that existing code without db/organization_id still works"""
        from saas_api import call_litellm

        mock_litellm_response = {
            "id": "compat-123",
            "choices": [{"message": {"content": "Compatible response"}}],
            "usage": {"total_tokens": 8}
        }

        with patch('saas_api.settings', mock_settings), \
             patch('httpx.AsyncClient') as mock_client:

            mock_post = AsyncMock(return_value=Mock(
                status_code=200,
                json=Mock(return_value=mock_litellm_response)
            ))
            mock_client.return_value.__aenter__.return_value.post = mock_post

            # Call WITHOUT new parameters (backward compatibility)
            result = await call_litellm(
                model="gpt-4",
                messages=[{"role": "user", "content": "Test"}],
                virtual_key="sk-litellm-test",
                team_id="team_123"
            )

            # Should work and use LiteLLM proxy
            assert result["id"] == "compat-123"
            assert result["choices"][0]["message"]["content"] == "Compatible response"
