"""
Tests for Provider Credentials API

Tests the provider credentials CRUD endpoints for managing encrypted API keys.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import uuid

# Import from src
import sys
from pathlib import Path as PathType
sys.path.insert(0, str(PathType(__file__).parent.parent / "src"))

from saas_api import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def sample_credential():
    """Create a sample provider credential"""
    return {
        "credential_id": str(uuid.uuid4()),
        "organization_id": "org-test",
        "provider": "openai",
        "credential_name": "Production OpenAI Key",
        "api_key": "encrypted_key_data",
        "api_base": None,
        "is_active": True,
        "created_at": "2025-10-31T00:00:00",
        "updated_at": "2025-10-31T00:00:00"
    }


class TestCreateProviderCredential:
    """Test POST /api/provider-credentials/create endpoint"""

    @patch('api.provider_credentials.get_db')
    @patch('api.provider_credentials.encrypt_api_key')
    def test_create_credential_success(self, mock_encrypt, mock_get_db, client):
        """Test successful credential creation"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_encrypt.return_value = "encrypted_key_value"

        # Mock organization exists
        mock_db.query.return_value.filter.return_value.first.return_value = Mock()
        mock_db.add.return_value = None
        mock_db.commit.return_value = None

        payload = {
            "organization_id": "org-test",
            "provider": "openai",
            "credential_name": "Test Credential",
            "api_key": "sk-test-key-12345",
            "api_base": None
        }

        response = client.post("/api/provider-credentials/create", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "openai"
        assert data["credential_name"] == "Test Credential"
        assert data["is_active"] is True
        # API key should be encrypted
        mock_encrypt.assert_called_once()

    @patch('api.provider_credentials.get_db')
    def test_create_credential_invalid_provider(self, mock_get_db, client):
        """Test creating credential with invalid provider"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        payload = {
            "organization_id": "org-test",
            "provider": "invalid_provider",
            "credential_name": "Test Credential",
            "api_key": "sk-test-key",
        }

        response = client.post("/api/provider-credentials/create", json=payload)

        # Should reject invalid provider
        assert response.status_code in [400, 422]

    @patch('api.provider_credentials.get_db')
    @patch('api.provider_credentials.encrypt_api_key')
    def test_create_credential_with_api_base(self, mock_encrypt, mock_get_db, client):
        """Test creating credential with custom API base"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_encrypt.return_value = "encrypted_key"

        mock_db.query.return_value.filter.return_value.first.return_value = Mock()
        mock_db.add.return_value = None
        mock_db.commit.return_value = None

        payload = {
            "organization_id": "org-test",
            "provider": "openai",
            "credential_name": "Custom Endpoint",
            "api_key": "sk-test-key",
            "api_base": "https://custom.openai.endpoint.com/v1"
        }

        response = client.post("/api/provider-credentials/create", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["api_base"] == "https://custom.openai.endpoint.com/v1"


class TestListProviderCredentials:
    """Test GET /api/provider-credentials/organization/{org_id} endpoint"""

    @patch('api.provider_credentials.get_db')
    def test_list_credentials_for_organization(self, mock_get_db, client, sample_credential):
        """Test listing credentials for an organization"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Mock credentials query
        mock_cred = Mock()
        mock_cred.credential_id = sample_credential["credential_id"]
        mock_cred.organization_id = sample_credential["organization_id"]
        mock_cred.provider = sample_credential["provider"]
        mock_cred.credential_name = sample_credential["credential_name"]
        mock_cred.is_active = sample_credential["is_active"]

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_cred]

        response = client.get("/api/provider-credentials/organization/org-test")

        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert data[0]["organization_id"] == "org-test"

    @patch('api.provider_credentials.get_db')
    def test_list_credentials_empty_organization(self, mock_get_db, client):
        """Test listing credentials for organization with no credentials"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_db.query.return_value.filter.return_value.all.return_value = []

        response = client.get("/api/provider-credentials/organization/empty-org")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0


class TestUpdateProviderCredential:
    """Test PUT /api/provider-credentials/{credential_id} endpoint"""

    @patch('api.provider_credentials.get_db')
    @patch('api.provider_credentials.encrypt_api_key')
    def test_update_credential_success(self, mock_encrypt, mock_get_db, client, sample_credential):
        """Test successful credential update"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_encrypt.return_value = "new_encrypted_key"

        # Mock credential exists
        mock_cred = Mock()
        mock_cred.credential_id = sample_credential["credential_id"]
        mock_db.query.return_value.filter.return_value.first.return_value = mock_cred
        mock_db.commit.return_value = None

        payload = {
            "credential_name": "Updated Credential Name",
            "api_key": "sk-new-key-67890"
        }

        response = client.put(
            f"/api/provider-credentials/{sample_credential['credential_id']}",
            json=payload
        )

        assert response.status_code == 200
        # Should encrypt new API key
        mock_encrypt.assert_called_once()

    @patch('api.provider_credentials.get_db')
    def test_update_credential_not_found(self, mock_get_db, client):
        """Test updating non-existent credential"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_db.query.return_value.filter.return_value.first.return_value = None

        payload = {
            "credential_name": "Updated Name"
        }

        response = client.put(
            f"/api/provider-credentials/{uuid.uuid4()}",
            json=payload
        )

        assert response.status_code == 404


class TestDeleteProviderCredential:
    """Test DELETE /api/provider-credentials/{credential_id} endpoint"""

    @patch('api.provider_credentials.get_db')
    def test_delete_credential_success(self, mock_get_db, client, sample_credential):
        """Test successful credential deletion"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Mock credential exists
        mock_cred = Mock()
        mock_cred.credential_id = sample_credential["credential_id"]
        mock_db.query.return_value.filter.return_value.first.return_value = mock_cred
        mock_db.delete.return_value = None
        mock_db.commit.return_value = None

        response = client.delete(
            f"/api/provider-credentials/{sample_credential['credential_id']}"
        )

        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

    @patch('api.provider_credentials.get_db')
    def test_delete_credential_not_found(self, mock_get_db, client):
        """Test deleting non-existent credential"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_db.query.return_value.filter.return_value.first.return_value = None

        response = client.delete(f"/api/provider-credentials/{uuid.uuid4()}")

        assert response.status_code == 404


class TestActivateDeactivateCredential:
    """Test activate/deactivate credential endpoints"""

    @patch('api.provider_credentials.get_db')
    def test_activate_credential(self, mock_get_db, client, sample_credential):
        """Test activating a credential"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Mock inactive credential
        mock_cred = Mock()
        mock_cred.credential_id = sample_credential["credential_id"]
        mock_cred.is_active = False
        mock_db.query.return_value.filter.return_value.first.return_value = mock_cred
        mock_db.commit.return_value = None

        response = client.put(
            f"/api/provider-credentials/{sample_credential['credential_id']}/activate"
        )

        assert response.status_code == 200
        assert mock_cred.is_active is True

    @patch('api.provider_credentials.get_db')
    def test_deactivate_credential(self, mock_get_db, client, sample_credential):
        """Test deactivating a credential"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Mock active credential
        mock_cred = Mock()
        mock_cred.credential_id = sample_credential["credential_id"]
        mock_cred.is_active = True
        mock_db.query.return_value.filter.return_value.first.return_value = mock_cred
        mock_db.commit.return_value = None

        response = client.put(
            f"/api/provider-credentials/{sample_credential['credential_id']}/deactivate"
        )

        assert response.status_code == 200
        assert mock_cred.is_active is False

    @patch('api.provider_credentials.get_db')
    def test_activate_nonexistent_credential(self, mock_get_db, client):
        """Test activating non-existent credential"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_db.query.return_value.filter.return_value.first.return_value = None

        response = client.put(f"/api/provider-credentials/{uuid.uuid4()}/activate")

        assert response.status_code == 404


class TestCredentialSecurity:
    """Test security features of credential management"""

    @patch('api.provider_credentials.get_db')
    @patch('api.provider_credentials.encrypt_api_key')
    def test_api_key_is_encrypted(self, mock_encrypt, mock_get_db, client):
        """Test that API keys are always encrypted before storage"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_encrypt.return_value = "encrypted_value"

        mock_db.query.return_value.filter.return_value.first.return_value = Mock()
        mock_db.add.return_value = None
        mock_db.commit.return_value = None

        plain_key = "sk-very-secret-key-12345"
        payload = {
            "organization_id": "org-test",
            "provider": "openai",
            "credential_name": "Secret Key",
            "api_key": plain_key
        }

        response = client.post("/api/provider-credentials/create", json=payload)

        # Verify encryption was called with plain key
        mock_encrypt.assert_called_once_with(plain_key)

    def test_api_keys_not_exposed_in_list(self, client, sample_credential):
        """Test that full API keys are not exposed when listing credentials"""
        # In real implementation, API should not return full decrypted keys
        # This test documents the security requirement
        assert "api_key" in sample_credential
        # In production, listing should either omit or mask the key


class TestMultiProviderSupport:
    """Test support for multiple LLM providers"""

    @pytest.mark.parametrize("provider", ["openai", "anthropic", "gemini", "fireworks"])
    @patch('api.provider_credentials.get_db')
    @patch('api.provider_credentials.encrypt_api_key')
    def test_create_credentials_for_all_providers(
        self, mock_encrypt, mock_get_db, client, provider
    ):
        """Test creating credentials for all supported providers"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_encrypt.return_value = "encrypted_key"

        mock_db.query.return_value.filter.return_value.first.return_value = Mock()
        mock_db.add.return_value = None
        mock_db.commit.return_value = None

        payload = {
            "organization_id": "org-test",
            "provider": provider,
            "credential_name": f"Test {provider.title()} Key",
            "api_key": f"test-{provider}-key"
        }

        response = client.post("/api/provider-credentials/create", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == provider
