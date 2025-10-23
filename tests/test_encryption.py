"""
Comprehensive tests for encryption utilities

Tests API key encryption/decryption, key generation, and error handling.
"""
import pytest
import os
from unittest.mock import patch, MagicMock
from cryptography.fernet import Fernet, InvalidToken

# Import from src
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.encryption import (
    get_encryption_key,
    encrypt_api_key,
    decrypt_api_key,
    generate_encryption_key
)


class TestEncryptionKeyGeneration:
    """Test encryption key generation"""

    def test_generate_encryption_key_format(self):
        """Test that generated key is valid Fernet key"""
        key = generate_encryption_key()

        # Should be a string
        assert isinstance(key, str)

        # Should be valid base64 and correct length
        assert len(key) == 44  # Fernet keys are 44 chars when base64 encoded

        # Should be usable to create Fernet instance
        fernet = Fernet(key.encode())
        assert fernet is not None

    def test_generate_encryption_key_uniqueness(self):
        """Test that each generated key is unique"""
        key1 = generate_encryption_key()
        key2 = generate_encryption_key()

        assert key1 != key2

    def test_generate_encryption_key_can_encrypt_decrypt(self):
        """Test that generated key can encrypt and decrypt"""
        key = generate_encryption_key()
        test_data = "test-api-key-12345"

        fernet = Fernet(key.encode())
        encrypted = fernet.encrypt(test_data.encode())
        decrypted = fernet.decrypt(encrypted).decode()

        assert decrypted == test_data


class TestGetEncryptionKey:
    """Test getting encryption key from environment"""

    def test_get_encryption_key_from_env(self):
        """Test getting key from ENCRYPTION_KEY env var"""
        test_key = Fernet.generate_key().decode()

        with patch.dict(os.environ, {'ENCRYPTION_KEY': test_key}):
            key = get_encryption_key()
            assert key == test_key

    def test_get_encryption_key_production_requires_env_var(self):
        """Test that production mode requires ENCRYPTION_KEY"""
        with patch.dict(os.environ, {}, clear=True):
            # Remove ENCRYPTION_KEY if it exists
            os.environ.pop('ENCRYPTION_KEY', None)
            os.environ['ENV'] = 'production'

            with pytest.raises(ValueError, match="ENCRYPTION_KEY environment variable must be set in production"):
                get_encryption_key()

    def test_get_encryption_key_development_generates_default(self):
        """Test that development mode generates a default key"""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop('ENCRYPTION_KEY', None)
            os.environ['ENV'] = 'development'

            key = get_encryption_key()

            # Should return a valid key
            assert isinstance(key, str)
            assert len(key) == 44

            # Should be usable
            fernet = Fernet(key.encode())
            assert fernet is not None

    def test_get_encryption_key_no_env_assumes_development(self):
        """Test that missing ENV defaults to development"""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop('ENCRYPTION_KEY', None)
            os.environ.pop('ENV', None)

            # Should not raise error (assumes development)
            key = get_encryption_key()
            assert isinstance(key, str)


class TestEncryptApiKey:
    """Test API key encryption"""

    def setup_method(self):
        """Set up test encryption key"""
        self.test_key = Fernet.generate_key().decode()
        self.test_api_key = "sk-test-1234567890abcdef"

    def test_encrypt_api_key_basic(self):
        """Test basic encryption"""
        with patch('utils.encryption.get_encryption_key', return_value=self.test_key):
            encrypted = encrypt_api_key(self.test_api_key)

            # Should return a string
            assert isinstance(encrypted, str)

            # Should be different from original
            assert encrypted != self.test_api_key

            # Should be longer than original (encryption overhead)
            assert len(encrypted) > len(self.test_api_key)

    def test_encrypt_api_key_deterministic_with_same_key(self):
        """Test that same key produces consistent encryption"""
        with patch('utils.encryption.get_encryption_key', return_value=self.test_key):
            # Note: Fernet encryption includes a timestamp, so it won't be identical
            # But it should decrypt to the same value
            encrypted1 = encrypt_api_key(self.test_api_key)
            encrypted2 = encrypt_api_key(self.test_api_key)

            # Encrypted values will be different (includes nonce)
            # But both should decrypt to same value
            fernet = Fernet(self.test_key.encode())
            decrypted1 = fernet.decrypt(encrypted1.encode()).decode()
            decrypted2 = fernet.decrypt(encrypted2.encode()).decode()

            assert decrypted1 == self.test_api_key
            assert decrypted2 == self.test_api_key

    def test_encrypt_api_key_empty_string(self):
        """Test encrypting empty string"""
        with patch('utils.encryption.get_encryption_key', return_value=self.test_key):
            encrypted = encrypt_api_key("")

            # Should still encrypt
            assert isinstance(encrypted, str)
            assert len(encrypted) > 0

            # Should decrypt back to empty string
            fernet = Fernet(self.test_key.encode())
            decrypted = fernet.decrypt(encrypted.encode()).decode()
            assert decrypted == ""

    def test_encrypt_api_key_with_special_characters(self):
        """Test encrypting API key with special characters"""
        special_key = "sk-test_KEY.with/special+chars=123"

        with patch('utils.encryption.get_encryption_key', return_value=self.test_key):
            encrypted = encrypt_api_key(special_key)

            fernet = Fernet(self.test_key.encode())
            decrypted = fernet.decrypt(encrypted.encode()).decode()
            assert decrypted == special_key


class TestDecryptApiKey:
    """Test API key decryption"""

    def setup_method(self):
        """Set up test encryption key and encrypted data"""
        self.test_key = Fernet.generate_key().decode()
        self.test_api_key = "sk-test-1234567890abcdef"

        # Pre-encrypt the test key
        fernet = Fernet(self.test_key.encode())
        self.encrypted_api_key = fernet.encrypt(self.test_api_key.encode()).decode()

    def test_decrypt_api_key_basic(self):
        """Test basic decryption"""
        with patch('utils.encryption.get_encryption_key', return_value=self.test_key):
            decrypted = decrypt_api_key(self.encrypted_api_key)
            assert decrypted == self.test_api_key

    def test_decrypt_api_key_wrong_key_raises_error(self):
        """Test that wrong key raises InvalidToken error"""
        wrong_key = Fernet.generate_key().decode()

        with patch('utils.encryption.get_encryption_key', return_value=wrong_key):
            with pytest.raises(Exception):  # Will raise InvalidToken or similar
                decrypt_api_key(self.encrypted_api_key)

    def test_decrypt_api_key_invalid_token_format(self):
        """Test that invalid token format raises error"""
        invalid_token = "not-a-valid-encrypted-token"

        with patch('utils.encryption.get_encryption_key', return_value=self.test_key):
            with pytest.raises(Exception):
                decrypt_api_key(invalid_token)

    def test_decrypt_api_key_empty_string(self):
        """Test decrypting empty encrypted string"""
        fernet = Fernet(self.test_key.encode())
        encrypted_empty = fernet.encrypt("".encode()).decode()

        with patch('utils.encryption.get_encryption_key', return_value=self.test_key):
            decrypted = decrypt_api_key(encrypted_empty)
            assert decrypted == ""


class TestEncryptionRoundTrip:
    """Test complete encryption/decryption round trips"""

    def test_round_trip_basic(self):
        """Test encrypt then decrypt returns original"""
        test_key = Fernet.generate_key().decode()
        original_api_key = "sk-test-round-trip-12345"

        with patch('utils.encryption.get_encryption_key', return_value=test_key):
            encrypted = encrypt_api_key(original_api_key)
            decrypted = decrypt_api_key(encrypted)

            assert decrypted == original_api_key

    def test_round_trip_multiple_keys(self):
        """Test encrypting/decrypting multiple API keys"""
        test_key = Fernet.generate_key().decode()
        api_keys = [
            "sk-openai-key-12345",
            "sk-anthropic-key-67890",
            "gemini-api-key-abcdef",
            "fw-fireworks-key-xyz123"
        ]

        with patch('utils.encryption.get_encryption_key', return_value=test_key):
            for original_key in api_keys:
                encrypted = encrypt_api_key(original_key)
                decrypted = decrypt_api_key(encrypted)
                assert decrypted == original_key

    def test_round_trip_with_unicode(self):
        """Test encrypting/decrypting keys with Unicode characters"""
        test_key = Fernet.generate_key().decode()
        unicode_key = "sk-test-key-with-émojis-🔑-and-spéçîål-chars"

        with patch('utils.encryption.get_encryption_key', return_value=test_key):
            encrypted = encrypt_api_key(unicode_key)
            decrypted = decrypt_api_key(encrypted)

            assert decrypted == unicode_key

    def test_round_trip_long_key(self):
        """Test encrypting/decrypting very long API key"""
        test_key = Fernet.generate_key().decode()
        long_key = "sk-" + "a" * 1000  # Very long key

        with patch('utils.encryption.get_encryption_key', return_value=test_key):
            encrypted = encrypt_api_key(long_key)
            decrypted = decrypt_api_key(encrypted)

            assert decrypted == long_key


class TestEncryptionSecurity:
    """Test encryption security properties"""

    def test_different_keys_produce_different_encrypted_values(self):
        """Test that different encryption keys produce different encrypted values"""
        api_key = "sk-test-12345"
        key1 = Fernet.generate_key().decode()
        key2 = Fernet.generate_key().decode()

        with patch('utils.encryption.get_encryption_key', return_value=key1):
            encrypted1 = encrypt_api_key(api_key)

        with patch('utils.encryption.get_encryption_key', return_value=key2):
            encrypted2 = encrypt_api_key(api_key)

        # Different keys should produce different encrypted values
        assert encrypted1 != encrypted2

    def test_encrypted_value_does_not_contain_original(self):
        """Test that encrypted value doesn't obviously contain the original"""
        test_key = Fernet.generate_key().decode()
        api_key = "sk-very-secret-key-12345"

        with patch('utils.encryption.get_encryption_key', return_value=test_key):
            encrypted = encrypt_api_key(api_key)

            # Encrypted value should not contain the original key
            assert api_key not in encrypted
            assert "secret" not in encrypted.lower()

    def test_key_rotation_scenario(self):
        """Test key rotation scenario - decrypt with old key, re-encrypt with new key"""
        old_key = Fernet.generate_key().decode()
        new_key = Fernet.generate_key().decode()
        api_key = "sk-test-rotation-12345"

        # Encrypt with old key
        with patch('utils.encryption.get_encryption_key', return_value=old_key):
            encrypted_old = encrypt_api_key(api_key)

        # Decrypt with old key
        with patch('utils.encryption.get_encryption_key', return_value=old_key):
            decrypted = decrypt_api_key(encrypted_old)
            assert decrypted == api_key

        # Re-encrypt with new key
        with patch('utils.encryption.get_encryption_key', return_value=new_key):
            encrypted_new = encrypt_api_key(decrypted)

        # Verify with new key
        with patch('utils.encryption.get_encryption_key', return_value=new_key):
            final_decrypted = decrypt_api_key(encrypted_new)
            assert final_decrypted == api_key
