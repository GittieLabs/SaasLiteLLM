"""
Comprehensive tests for encryption utilities

Tests API key encryption/decryption, key generation, and error handling.
"""
import pytest
import os
from unittest.mock import patch
from cryptography.fernet import Fernet

# Import from src
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.encryption import (
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


class TestEncryptApiKey:
    """Test API key encryption"""

    def test_encrypt_api_key_basic(self):
        """Test basic encryption"""
        test_key = Fernet.generate_key().decode()
        test_api_key = "sk-test-1234567890abcdef"

        with patch.dict(os.environ, {'ENCRYPTION_KEY': test_key}):
            # Reset the global fernet instance
            import utils.encryption
            utils.encryption._fernet = None

            encrypted = encrypt_api_key(test_api_key)

            # Should return a string
            assert isinstance(encrypted, str)

            # Should be different from original
            assert encrypted != test_api_key

            # Should be longer than original (encryption overhead)
            assert len(encrypted) > len(test_api_key)

    def test_encrypt_api_key_empty_string_raises_error(self):
        """Test that empty string raises error"""
        test_key = Fernet.generate_key().decode()

        with patch.dict(os.environ, {'ENCRYPTION_KEY': test_key}):
            import utils.encryption
            utils.encryption._fernet = None

            with pytest.raises(ValueError, match="API key cannot be empty"):
                encrypt_api_key("")

    def test_encrypt_api_key_with_special_characters(self):
        """Test encrypting API key with special characters"""
        test_key = Fernet.generate_key().decode()
        special_key = "sk-test_KEY.with/special+chars=123"

        with patch.dict(os.environ, {'ENCRYPTION_KEY': test_key}):
            import utils.encryption
            utils.encryption._fernet = None

            encrypted = encrypt_api_key(special_key)

            # Should encrypt successfully
            assert isinstance(encrypted, str)
            assert len(encrypted) > 0


class TestDecryptApiKey:
    """Test API key decryption"""

    def test_decrypt_api_key_basic(self):
        """Test basic decryption"""
        test_key = Fernet.generate_key().decode()
        test_api_key = "sk-test-1234567890abcdef"

        with patch.dict(os.environ, {'ENCRYPTION_KEY': test_key}):
            import utils.encryption
            utils.encryption._fernet = None

            # Encrypt first
            encrypted = encrypt_api_key(test_api_key)

            # Reset fernet to ensure we're using the same key
            utils.encryption._fernet = None

            # Then decrypt
            decrypted = decrypt_api_key(encrypted)
            assert decrypted == test_api_key

    def test_decrypt_api_key_empty_string_raises_error(self):
        """Test that empty encrypted string raises error"""
        test_key = Fernet.generate_key().decode()

        with patch.dict(os.environ, {'ENCRYPTION_KEY': test_key}):
            import utils.encryption
            utils.encryption._fernet = None

            with pytest.raises(ValueError, match="Encrypted API key cannot be empty"):
                decrypt_api_key("")

    def test_decrypt_api_key_invalid_token_format(self):
        """Test that invalid token format raises error"""
        test_key = Fernet.generate_key().decode()
        invalid_token = "not-a-valid-encrypted-token"

        with patch.dict(os.environ, {'ENCRYPTION_KEY': test_key}):
            import utils.encryption
            utils.encryption._fernet = None

            with pytest.raises(Exception):  # Will raise InvalidToken
                decrypt_api_key(invalid_token)


class TestEncryptionRoundTrip:
    """Test complete encryption/decryption round trips"""

    def test_round_trip_basic(self):
        """Test encrypt then decrypt returns original"""
        test_key = Fernet.generate_key().decode()
        original_api_key = "sk-test-round-trip-12345"

        with patch.dict(os.environ, {'ENCRYPTION_KEY': test_key}):
            import utils.encryption
            utils.encryption._fernet = None

            encrypted = encrypt_api_key(original_api_key)

            utils.encryption._fernet = None

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

        with patch.dict(os.environ, {'ENCRYPTION_KEY': test_key}):
            for original_key in api_keys:
                import utils.encryption
                utils.encryption._fernet = None

                encrypted = encrypt_api_key(original_key)

                utils.encryption._fernet = None

                decrypted = decrypt_api_key(encrypted)
                assert decrypted == original_key

    def test_round_trip_with_unicode(self):
        """Test encrypting/decrypting keys with Unicode characters"""
        test_key = Fernet.generate_key().decode()
        unicode_key = "sk-test-key-with-émojis-🔑-and-spéçîål-chars"

        with patch.dict(os.environ, {'ENCRYPTION_KEY': test_key}):
            import utils.encryption
            utils.encryption._fernet = None

            encrypted = encrypt_api_key(unicode_key)

            utils.encryption._fernet = None

            decrypted = decrypt_api_key(encrypted)

            assert decrypted == unicode_key

    def test_round_trip_long_key(self):
        """Test encrypting/decrypting very long API key"""
        test_key = Fernet.generate_key().decode()
        long_key = "sk-" + "a" * 1000  # Very long key

        with patch.dict(os.environ, {'ENCRYPTION_KEY': test_key}):
            import utils.encryption
            utils.encryption._fernet = None

            encrypted = encrypt_api_key(long_key)

            utils.encryption._fernet = None

            decrypted = decrypt_api_key(encrypted)

            assert decrypted == long_key


class TestEncryptionSecurity:
    """Test encryption security properties"""

    def test_different_keys_produce_different_encrypted_values(self):
        """Test that different encryption keys produce different encrypted values"""
        api_key = "sk-test-12345"
        key1 = Fernet.generate_key().decode()
        key2 = Fernet.generate_key().decode()

        with patch.dict(os.environ, {'ENCRYPTION_KEY': key1}):
            import utils.encryption
            utils.encryption._fernet = None
            encrypted1 = encrypt_api_key(api_key)

        with patch.dict(os.environ, {'ENCRYPTION_KEY': key2}):
            utils.encryption._fernet = None
            encrypted2 = encrypt_api_key(api_key)

        # Different keys should produce different encrypted values
        assert encrypted1 != encrypted2

    def test_encrypted_value_does_not_contain_original(self):
        """Test that encrypted value doesn't obviously contain the original"""
        test_key = Fernet.generate_key().decode()
        api_key = "sk-very-secret-key-12345"

        with patch.dict(os.environ, {'ENCRYPTION_KEY': test_key}):
            import utils.encryption
            utils.encryption._fernet = None

            encrypted = encrypt_api_key(api_key)

            # Encrypted value should not contain the original key
            assert api_key not in encrypted
            assert "secret" not in encrypted.lower()

    def test_same_plaintext_produces_different_ciphertext(self):
        """Test that encrypting same plaintext twice produces different ciphertext (due to nonce)"""
        test_key = Fernet.generate_key().decode()
        api_key = "sk-test-12345"

        with patch.dict(os.environ, {'ENCRYPTION_KEY': test_key}):
            import utils.encryption
            utils.encryption._fernet = None
            encrypted1 = encrypt_api_key(api_key)

            utils.encryption._fernet = None
            encrypted2 = encrypt_api_key(api_key)

            # Different encryptions of same plaintext should differ (due to nonce)
            assert encrypted1 != encrypted2

            # But both should decrypt to same value
            utils.encryption._fernet = None
            assert decrypt_api_key(encrypted1) == api_key

            utils.encryption._fernet = None
            assert decrypt_api_key(encrypted2) == api_key


class TestEnvironmentConfiguration:
    """Test environment-based key configuration"""

    def test_uses_encryption_key_from_environment(self):
        """Test that ENCRYPTION_KEY environment variable is used"""
        test_key = Fernet.generate_key().decode()
        api_key = "sk-test-env-key"

        with patch.dict(os.environ, {'ENCRYPTION_KEY': test_key}):
            import utils.encryption
            utils.encryption._fernet = None

            encrypted = encrypt_api_key(api_key)

            utils.encryption._fernet = None

            decrypted = decrypt_api_key(encrypted)
            assert decrypted == api_key

    def test_development_fallback_key(self):
        """Test that development environment uses fallback key"""
        api_key = "sk-test-dev-key"

        # Remove ENCRYPTION_KEY and set ENV to development
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop('ENCRYPTION_KEY', None)
            os.environ['ENV'] = 'development'

            import utils.encryption
            utils.encryption._fernet = None

            # Should not raise error
            encrypted = encrypt_api_key(api_key)

            utils.encryption._fernet = None

            decrypted = decrypt_api_key(encrypted)
            assert decrypted == api_key

    def test_production_requires_encryption_key(self):
        """Test that production mode requires ENCRYPTION_KEY"""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop('ENCRYPTION_KEY', None)
            os.environ['ENVIRONMENT'] = 'production'

            import utils.encryption
            utils.encryption._fernet = None

            with pytest.raises(ValueError, match="ENCRYPTION_KEY environment variable must be set in production"):
                encrypt_api_key("sk-test")


class TestKeyRotation:
    """Test encryption key rotation"""

    def test_rotate_encryption_key_basic(self):
        """Test basic key rotation"""
        from utils.encryption import rotate_encryption_key

        old_key = Fernet.generate_key().decode()
        new_key = "new-encryption-key-for-rotation"
        api_key = "sk-test-rotation-12345"

        # Encrypt with old key
        with patch.dict(os.environ, {'ENCRYPTION_KEY': old_key}):
            import utils.encryption
            utils.encryption._fernet = None
            encrypted_with_old = encrypt_api_key(api_key)

        # Rotate to new key
        with patch.dict(os.environ, {'ENCRYPTION_KEY': old_key}):
            utils.encryption._fernet = None
            encrypted_with_new = rotate_encryption_key(encrypted_with_old, new_key)

        # Verify we can decrypt with new key
        with patch.dict(os.environ, {'ENCRYPTION_KEY': new_key}):
            utils.encryption._fernet = None
            decrypted = decrypt_api_key(encrypted_with_new)
            assert decrypted == api_key

    def test_rotate_encryption_key_preserves_data(self):
        """Test that key rotation preserves the original data"""
        from utils.encryption import rotate_encryption_key

        old_key = Fernet.generate_key().decode()
        new_key = "another-new-key-for-testing"
        original_data = "sk-very-important-api-key-xyz"

        # Encrypt with old key
        with patch.dict(os.environ, {'ENCRYPTION_KEY': old_key}):
            import utils.encryption
            utils.encryption._fernet = None
            encrypted_old = encrypt_api_key(original_data)

        # Rotate key
        with patch.dict(os.environ, {'ENCRYPTION_KEY': old_key}):
            utils.encryption._fernet = None
            encrypted_new = rotate_encryption_key(encrypted_old, new_key)

        # Encrypted values should be different
        assert encrypted_old != encrypted_new

        # But decrypted values should be the same
        with patch.dict(os.environ, {'ENCRYPTION_KEY': new_key}):
            utils.encryption._fernet = None
            decrypted = decrypt_api_key(encrypted_new)
            assert decrypted == original_data
