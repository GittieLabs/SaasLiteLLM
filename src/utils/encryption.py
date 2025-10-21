"""
Encryption utilities for securing sensitive data like API keys.

This module provides Fernet symmetric encryption for provider credentials.
The encryption key should be stored securely in environment variables.
"""

import os
import base64
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2

# Global Fernet instance
_fernet: Optional[Fernet] = None


def _get_encryption_key() -> bytes:
    """
    Get or generate encryption key from environment.

    Returns:
        bytes: 32-byte encryption key suitable for Fernet

    Raises:
        ValueError: If ENCRYPTION_KEY is not set in production
    """
    key_str = os.environ.get("ENCRYPTION_KEY")

    if not key_str:
        # In development, use a default key (NOT FOR PRODUCTION)
        if os.environ.get("ENVIRONMENT") == "production":
            raise ValueError(
                "ENCRYPTION_KEY environment variable must be set in production. "
                "Generate one with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
            )

        # Development fallback - DO NOT USE IN PRODUCTION
        key_str = "dev-encryption-key-change-in-production-12345678"

    # Derive a proper 32-byte key using PBKDF2
    kdf = PBKDF2(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"saas-litellm-salt",  # Static salt for key derivation
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(key_str.encode()))
    return key


def _get_fernet() -> Fernet:
    """
    Get or initialize the global Fernet instance.

    Returns:
        Fernet: Initialized Fernet cipher
    """
    global _fernet
    if _fernet is None:
        key = _get_encryption_key()
        _fernet = Fernet(key)
    return _fernet


def encrypt_api_key(api_key: str) -> str:
    """
    Encrypt an API key for secure storage.

    Args:
        api_key: Plain text API key

    Returns:
        str: Base64-encoded encrypted API key

    Example:
        >>> encrypted = encrypt_api_key("sk-1234567890")
        >>> print(encrypted)
        'gAAAAABf...'
    """
    if not api_key:
        raise ValueError("API key cannot be empty")

    fernet = _get_fernet()
    encrypted_bytes = fernet.encrypt(api_key.encode())
    return encrypted_bytes.decode()


def decrypt_api_key(encrypted_api_key: str) -> str:
    """
    Decrypt an API key for use.

    Args:
        encrypted_api_key: Base64-encoded encrypted API key

    Returns:
        str: Plain text API key

    Raises:
        InvalidToken: If decryption fails (wrong key or corrupted data)

    Example:
        >>> decrypted = decrypt_api_key(encrypted)
        >>> print(decrypted)
        'sk-1234567890'
    """
    if not encrypted_api_key:
        raise ValueError("Encrypted API key cannot be empty")

    fernet = _get_fernet()
    try:
        decrypted_bytes = fernet.decrypt(encrypted_api_key.encode())
        return decrypted_bytes.decode()
    except InvalidToken:
        raise InvalidToken(
            "Failed to decrypt API key. The encryption key may have changed or the data is corrupted."
        )


def generate_encryption_key() -> str:
    """
    Generate a new Fernet encryption key.

    This should be called once during initial setup and the key stored securely.

    Returns:
        str: Base64-encoded encryption key

    Example:
        >>> key = generate_encryption_key()
        >>> print(key)
        'vQKvP9..._base64_key_...'
    """
    return Fernet.generate_key().decode()


def rotate_encryption_key(old_encrypted_value: str, new_key: str) -> str:
    """
    Re-encrypt a value with a new encryption key.

    This is used during key rotation to migrate encrypted data.

    Args:
        old_encrypted_value: Value encrypted with old key
        new_key: New encryption key (base64-encoded)

    Returns:
        str: Value encrypted with new key

    Example:
        >>> # Set new key in environment
        >>> os.environ['ENCRYPTION_KEY'] = new_key
        >>> new_encrypted = rotate_encryption_key(old_encrypted, new_key)
    """
    # Decrypt with current key
    decrypted = decrypt_api_key(old_encrypted_value)

    # Create new Fernet instance with new key
    kdf = PBKDF2(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"saas-litellm-salt",
        iterations=100000,
    )
    derived_key = base64.urlsafe_b64encode(kdf.derive(new_key.encode()))
    new_fernet = Fernet(derived_key)

    # Encrypt with new key
    encrypted_bytes = new_fernet.encrypt(decrypted.encode())
    return encrypted_bytes.decode()
