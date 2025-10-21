"""
Provider Credentials Model
Stores API keys and configuration for AI model providers (OpenAI, Anthropic, Gemini, Fireworks)
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Boolean, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from ..models.job_tracking import Base
from ..utils.encryption import encrypt_api_key, decrypt_api_key
import enum


class ProviderType(str, enum.Enum):
    """Supported AI model providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    FIREWORKS = "fireworks"


class ProviderCredential(Base):
    """
    Provider API credentials and configuration

    This table stores encrypted API keys for different AI providers.
    Each organization can have credentials for multiple providers.
    """
    __tablename__ = "provider_credentials"

    credential_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(String, nullable=False, index=True)
    provider = Column(SQLEnum(ProviderType), nullable=False)

    # Encrypted API key (will be encrypted at application layer)
    api_key = Column(Text, nullable=False)

    # Optional custom API base URL (for proxies or custom endpoints)
    api_base = Column(String, nullable=True)

    # Credential label for admin identification
    credential_name = Column(String, nullable=False)

    # Whether this credential is active
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Who created/updated (admin user ID)
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)

    def to_dict(self):
        """Convert to dictionary (excluding sensitive data by default)"""
        return {
            "credential_id": str(self.credential_id),
            "organization_id": self.organization_id,
            "provider": self.provider.value,
            "credential_name": self.credential_name,
            "api_base": self.api_base,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "has_api_key": bool(self.api_key),  # Indicate presence without exposing
        }

    def to_dict_with_key(self):
        """
        Convert to dictionary including decrypted API key (use carefully)

        WARNING: This exposes the decrypted API key. Only use when necessary
        and ensure the response is not logged or exposed to untrusted parties.
        """
        data = self.to_dict()
        try:
            data["api_key"] = decrypt_api_key(self.api_key)
        except Exception as e:
            # If decryption fails, indicate the issue
            data["api_key"] = None
            data["decryption_error"] = str(e)
        return data

    def set_api_key(self, plain_api_key: str):
        """
        Set the API key with encryption.

        Args:
            plain_api_key: Plain text API key to encrypt and store
        """
        self.api_key = encrypt_api_key(plain_api_key)

    def get_api_key(self) -> str:
        """
        Get the decrypted API key for use.

        Returns:
            str: Decrypted API key

        Raises:
            InvalidToken: If decryption fails
        """
        return decrypt_api_key(self.api_key)

    def __repr__(self):
        return f"<ProviderCredential {self.credential_name} ({self.provider.value}) for org {self.organization_id}>"
