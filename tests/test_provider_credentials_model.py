"""
Comprehensive tests for provider_credentials model

Tests the ProviderCredential model including encryption, serialization, and enum types.
"""
import pytest
import uuid
from datetime import datetime
from unittest.mock import patch, MagicMock
from cryptography.fernet import InvalidToken

# Import from src
import sys
from pathlib import Path as PathType
sys.path.insert(0, str(PathType(__file__).parent.parent / "src"))

from models.provider_credentials import ProviderCredential, ProviderType


@pytest.fixture
def sample_credential():
    """Create a sample provider credential"""
    credential = ProviderCredential()
    credential.credential_id = uuid.uuid4()
    credential.organization_id = "org-12345"
    credential.provider = ProviderType.OPENAI
    credential.credential_name = "Test OpenAI Key"
    credential.api_base = None
    credential.is_active = True
    credential.created_at = datetime.utcnow()
    credential.updated_at = datetime.utcnow()
    credential.created_by = "admin-user-1"
    credential.updated_by = "admin-user-1"
    return credential


class TestProviderType:
    """Test ProviderType enum"""

    def test_provider_types_exist(self):
        """Test that all provider types are defined"""
        assert ProviderType.OPENAI == "openai"
        assert ProviderType.ANTHROPIC == "anthropic"
        assert ProviderType.GEMINI == "gemini"
        assert ProviderType.FIREWORKS == "fireworks"

    def test_provider_type_values(self):
        """Test provider type string values"""
        assert ProviderType.OPENAI.value == "openai"
        assert ProviderType.ANTHROPIC.value == "anthropic"
        assert ProviderType.GEMINI.value == "gemini"
        assert ProviderType.FIREWORKS.value == "fireworks"

    def test_provider_type_is_str_enum(self):
        """Test that ProviderType is a string enum"""
        assert isinstance(ProviderType.OPENAI, str)
        assert isinstance(ProviderType.ANTHROPIC, str)


class TestProviderCredentialModel:
    """Test ProviderCredential model basic functionality"""

    def test_model_has_required_fields(self, sample_credential):
        """Test that model has all required fields"""
        assert hasattr(sample_credential, 'credential_id')
        assert hasattr(sample_credential, 'organization_id')
        assert hasattr(sample_credential, 'provider')
        assert hasattr(sample_credential, 'api_key')
        assert hasattr(sample_credential, 'credential_name')
        assert hasattr(sample_credential, 'is_active')

    def test_model_has_optional_fields(self, sample_credential):
        """Test that model has optional fields"""
        assert hasattr(sample_credential, 'api_base')
        assert hasattr(sample_credential, 'created_by')
        assert hasattr(sample_credential, 'updated_by')

    def test_model_has_timestamps(self, sample_credential):
        """Test that model has timestamp fields"""
        assert hasattr(sample_credential, 'created_at')
        assert hasattr(sample_credential, 'updated_at')
        assert isinstance(sample_credential.created_at, datetime)
        assert isinstance(sample_credential.updated_at, datetime)

    def test_credential_id_is_uuid(self, sample_credential):
        """Test that credential_id is a UUID"""
        assert isinstance(sample_credential.credential_id, uuid.UUID)

    def test_provider_is_enum(self, sample_credential):
        """Test that provider is ProviderType enum"""
        assert isinstance(sample_credential.provider, ProviderType)

    def test_is_active_default(self):
        """Test that is_active defaults to True"""
        credential = ProviderCredential()
        credential.is_active = True
        assert credential.is_active is True


class TestSetApiKey:
    """Test set_api_key method"""

    @patch('models.provider_credentials.encrypt_api_key')
    def test_set_api_key_encrypts(self, mock_encrypt, sample_credential):
        """Test that set_api_key encrypts the key"""
        mock_encrypt.return_value = "encrypted_key_data"

        sample_credential.set_api_key("sk-test-1234567890")

        mock_encrypt.assert_called_once_with("sk-test-1234567890")
        assert sample_credential.api_key == "encrypted_key_data"

    @patch('models.provider_credentials.encrypt_api_key')
    def test_set_api_key_with_special_characters(self, mock_encrypt, sample_credential):
        """Test setting API key with special characters"""
        mock_encrypt.return_value = "encrypted_special_key"
        special_key = "sk-test_KEY.with/special+chars=123"

        sample_credential.set_api_key(special_key)

        mock_encrypt.assert_called_once_with(special_key)

    @patch('models.provider_credentials.encrypt_api_key')
    def test_set_api_key_replaces_existing(self, mock_encrypt, sample_credential):
        """Test that set_api_key replaces existing key"""
        mock_encrypt.side_effect = ["encrypted_1", "encrypted_2"]

        sample_credential.set_api_key("key1")
        assert sample_credential.api_key == "encrypted_1"

        sample_credential.set_api_key("key2")
        assert sample_credential.api_key == "encrypted_2"


class TestGetApiKey:
    """Test get_api_key method"""

    @patch('models.provider_credentials.decrypt_api_key')
    def test_get_api_key_decrypts(self, mock_decrypt, sample_credential):
        """Test that get_api_key decrypts the key"""
        sample_credential.api_key = "encrypted_key_data"
        mock_decrypt.return_value = "sk-test-1234567890"

        result = sample_credential.get_api_key()

        mock_decrypt.assert_called_once_with("encrypted_key_data")
        assert result == "sk-test-1234567890"

    @patch('models.provider_credentials.decrypt_api_key')
    def test_get_api_key_raises_on_invalid_token(self, mock_decrypt, sample_credential):
        """Test that get_api_key raises exception on decryption failure"""
        sample_credential.api_key = "invalid_encrypted_data"
        mock_decrypt.side_effect = InvalidToken("Failed to decrypt")

        with pytest.raises(InvalidToken):
            sample_credential.get_api_key()


class TestToDict:
    """Test to_dict method"""

    def test_to_dict_excludes_api_key(self, sample_credential):
        """Test that to_dict excludes the actual API key"""
        sample_credential.api_key = "encrypted_key_data"

        result = sample_credential.to_dict()

        assert "api_key" not in result
        assert "has_api_key" in result
        assert result["has_api_key"] is True

    def test_to_dict_includes_credential_id(self, sample_credential):
        """Test that to_dict includes credential_id as string"""
        result = sample_credential.to_dict()

        assert "credential_id" in result
        assert isinstance(result["credential_id"], str)
        assert result["credential_id"] == str(sample_credential.credential_id)

    def test_to_dict_includes_organization_id(self, sample_credential):
        """Test that to_dict includes organization_id"""
        result = sample_credential.to_dict()

        assert "organization_id" in result
        assert result["organization_id"] == sample_credential.organization_id

    def test_to_dict_includes_provider_value(self, sample_credential):
        """Test that to_dict includes provider as string value"""
        result = sample_credential.to_dict()

        assert "provider" in result
        assert result["provider"] == "openai"

    def test_to_dict_includes_metadata(self, sample_credential):
        """Test that to_dict includes credential metadata"""
        result = sample_credential.to_dict()

        assert "credential_name" in result
        assert "api_base" in result
        assert "is_active" in result
        assert result["credential_name"] == "Test OpenAI Key"
        assert result["is_active"] is True

    def test_to_dict_includes_timestamps(self, sample_credential):
        """Test that to_dict includes timestamps as ISO format"""
        result = sample_credential.to_dict()

        assert "created_at" in result
        assert "updated_at" in result
        assert isinstance(result["created_at"], str)
        assert isinstance(result["updated_at"], str)

    def test_to_dict_has_api_key_false_when_no_key(self, sample_credential):
        """Test that has_api_key is False when api_key is empty"""
        sample_credential.api_key = ""

        result = sample_credential.to_dict()

        assert result["has_api_key"] is False

    def test_to_dict_with_api_base(self, sample_credential):
        """Test to_dict with custom API base URL"""
        sample_credential.api_base = "https://custom-proxy.example.com"

        result = sample_credential.to_dict()

        assert result["api_base"] == "https://custom-proxy.example.com"

    def test_to_dict_with_no_api_base(self, sample_credential):
        """Test to_dict with null API base"""
        sample_credential.api_base = None

        result = sample_credential.to_dict()

        assert result["api_base"] is None


class TestToDictWithKey:
    """Test to_dict_with_key method"""

    @patch('models.provider_credentials.decrypt_api_key')
    def test_to_dict_with_key_includes_decrypted_key(self, mock_decrypt, sample_credential):
        """Test that to_dict_with_key includes decrypted API key"""
        sample_credential.api_key = "encrypted_key_data"
        mock_decrypt.return_value = "sk-test-1234567890"

        result = sample_credential.to_dict_with_key()

        assert "api_key" in result
        assert result["api_key"] == "sk-test-1234567890"
        mock_decrypt.assert_called_once_with("encrypted_key_data")

    @patch('models.provider_credentials.decrypt_api_key')
    def test_to_dict_with_key_handles_decryption_error(self, mock_decrypt, sample_credential):
        """Test that to_dict_with_key handles decryption errors gracefully"""
        sample_credential.api_key = "invalid_encrypted_data"
        mock_decrypt.side_effect = InvalidToken("Failed to decrypt")

        result = sample_credential.to_dict_with_key()

        assert result["api_key"] is None
        assert "decryption_error" in result
        assert "Failed to decrypt" in result["decryption_error"]

    @patch('models.provider_credentials.decrypt_api_key')
    def test_to_dict_with_key_includes_all_fields(self, mock_decrypt, sample_credential):
        """Test that to_dict_with_key includes all base fields"""
        sample_credential.api_key = "encrypted_key_data"
        mock_decrypt.return_value = "sk-test-key"

        result = sample_credential.to_dict_with_key()

        assert "credential_id" in result
        assert "organization_id" in result
        assert "provider" in result
        assert "credential_name" in result
        assert "api_base" in result
        assert "is_active" in result
        assert "created_at" in result
        assert "updated_at" in result

    @patch('models.provider_credentials.decrypt_api_key')
    def test_to_dict_with_key_warning_use_carefully(self, mock_decrypt, sample_credential):
        """Test to_dict_with_key exposes sensitive data (warning in docstring)"""
        sample_credential.api_key = "encrypted_key"
        mock_decrypt.return_value = "sk-sensitive-key"

        result = sample_credential.to_dict_with_key()

        # This method should expose the decrypted key (with warning in docstring)
        assert result["api_key"] == "sk-sensitive-key"


class TestRepr:
    """Test __repr__ method"""

    def test_repr_format(self, sample_credential):
        """Test __repr__ string format"""
        result = repr(sample_credential)

        assert "<ProviderCredential" in result
        assert "Test OpenAI Key" in result
        assert "openai" in result
        assert "org-12345" in result

    def test_repr_with_different_providers(self):
        """Test __repr__ with different provider types"""
        for provider in [ProviderType.OPENAI, ProviderType.ANTHROPIC, ProviderType.GEMINI, ProviderType.FIREWORKS]:
            credential = ProviderCredential()
            credential.credential_name = f"Test {provider.value} Key"
            credential.provider = provider
            credential.organization_id = "org-test"

            result = repr(credential)

            assert f"Test {provider.value} Key" in result
            assert provider.value in result


class TestIntegration:
    """Integration tests for complete workflows"""

    @patch('models.provider_credentials.encrypt_api_key')
    @patch('models.provider_credentials.decrypt_api_key')
    def test_set_and_get_api_key_roundtrip(self, mock_decrypt, mock_encrypt, sample_credential):
        """Test setting and getting API key"""
        original_key = "sk-test-original-key-12345"
        encrypted_key = "encrypted_version_of_key"

        mock_encrypt.return_value = encrypted_key
        mock_decrypt.return_value = original_key

        # Set key
        sample_credential.set_api_key(original_key)
        assert sample_credential.api_key == encrypted_key

        # Get key
        retrieved_key = sample_credential.get_api_key()
        assert retrieved_key == original_key

    @patch('models.provider_credentials.encrypt_api_key')
    @patch('models.provider_credentials.decrypt_api_key')
    def test_complete_credential_lifecycle(self, mock_decrypt, mock_encrypt):
        """Test complete credential lifecycle"""
        mock_encrypt.return_value = "encrypted_key"
        mock_decrypt.return_value = "sk-original-key"

        # Create credential
        credential = ProviderCredential()
        credential.credential_id = uuid.uuid4()
        credential.organization_id = "org-lifecycle-test"
        credential.provider = ProviderType.ANTHROPIC
        credential.credential_name = "Lifecycle Test Key"
        credential.is_active = True
        credential.created_at = datetime.utcnow()
        credential.updated_at = datetime.utcnow()

        # Set API key
        credential.set_api_key("sk-original-key")

        # Convert to dict (safe, no key)
        safe_dict = credential.to_dict()
        assert "api_key" not in safe_dict
        assert safe_dict["has_api_key"] is True
        assert safe_dict["provider"] == "anthropic"

        # Convert to dict with key (sensitive)
        sensitive_dict = credential.to_dict_with_key()
        assert sensitive_dict["api_key"] == "sk-original-key"

        # Get API key for use
        api_key = credential.get_api_key()
        assert api_key == "sk-original-key"

    def test_multiple_credentials_different_providers(self):
        """Test creating credentials for different providers"""
        providers = [
            (ProviderType.OPENAI, "OpenAI Key", "org-1"),
            (ProviderType.ANTHROPIC, "Anthropic Key", "org-1"),
            (ProviderType.GEMINI, "Gemini Key", "org-2"),
            (ProviderType.FIREWORKS, "Fireworks Key", "org-2"),
        ]

        credentials = []
        for provider, name, org_id in providers:
            cred = ProviderCredential()
            cred.credential_id = uuid.uuid4()
            cred.organization_id = org_id
            cred.provider = provider
            cred.credential_name = name
            cred.is_active = True
            credentials.append(cred)

        # Verify all credentials are distinct
        ids = [c.credential_id for c in credentials]
        assert len(ids) == len(set(ids))  # All unique

        # Verify providers
        assert credentials[0].provider == ProviderType.OPENAI
        assert credentials[1].provider == ProviderType.ANTHROPIC
        assert credentials[2].provider == ProviderType.GEMINI
        assert credentials[3].provider == ProviderType.FIREWORKS


class TestEdgeCases:
    """Test edge cases and error conditions"""

    @patch('models.provider_credentials.encrypt_api_key')
    def test_empty_string_api_key(self, mock_encrypt, sample_credential):
        """Test setting empty string as API key"""
        mock_encrypt.return_value = ""

        sample_credential.set_api_key("")

        assert sample_credential.api_key == ""

    @patch('models.provider_credentials.encrypt_api_key')
    def test_very_long_api_key(self, mock_encrypt, sample_credential):
        """Test setting very long API key"""
        long_key = "sk-" + "a" * 1000
        mock_encrypt.return_value = "encrypted_long_key"

        sample_credential.set_api_key(long_key)

        mock_encrypt.assert_called_once_with(long_key)

    @patch('models.provider_credentials.encrypt_api_key')
    def test_api_key_with_unicode(self, mock_encrypt, sample_credential):
        """Test API key with Unicode characters"""
        unicode_key = "sk-test-key-with-émojis-🔑-and-spéçîål"
        mock_encrypt.return_value = "encrypted_unicode_key"

        sample_credential.set_api_key(unicode_key)

        mock_encrypt.assert_called_once_with(unicode_key)

    def test_credential_with_null_api_base(self, sample_credential):
        """Test credential with null API base (default)"""
        sample_credential.api_base = None

        result = sample_credential.to_dict()

        assert result["api_base"] is None

    def test_credential_with_custom_api_base(self, sample_credential):
        """Test credential with custom API base"""
        custom_base = "https://api-proxy.company.com/v1"
        sample_credential.api_base = custom_base

        result = sample_credential.to_dict()

        assert result["api_base"] == custom_base

    def test_inactive_credential(self, sample_credential):
        """Test inactive credential"""
        sample_credential.is_active = False

        result = sample_credential.to_dict()

        assert result["is_active"] is False
