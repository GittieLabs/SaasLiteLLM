"""
Authentication Utilities

Provides password hashing/verification and JWT token generation/validation
for admin user management system.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import hashlib

from passlib.context import CryptContext
from jose import JWTError, jwt

from src.config.settings import settings

# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
# In production, this should be a secure random string stored in environment variables
# For now, we'll derive it from MASTER_KEY for consistency
SECRET_KEY = hashlib.sha256(settings.master_key.encode()).hexdigest()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24  # 24 hours default session


# Password Hashing Functions

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password to hash

    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to check against

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


# JWT Token Functions

def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.

    Args:
        data: Dictionary of claims to encode in the token
              (should include user_id, email, role)
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),  # Issued at
    })

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate a JWT access token.

    Args:
        token: JWT token string to decode

    Returns:
        Dictionary of token claims if valid, None if invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def create_token_hash(token: str) -> str:
    """
    Create a SHA-256 hash of a JWT token for storage.

    We store hashed tokens in the database instead of plain tokens
    for security (similar to password hashing).

    Args:
        token: JWT token to hash

    Returns:
        SHA-256 hex digest of the token
    """
    return hashlib.sha256(token.encode()).hexdigest()


def verify_token_hash(token: str, token_hash: str) -> bool:
    """
    Verify a token against its stored hash.

    Args:
        token: JWT token to verify
        token_hash: Stored hash to check against

    Returns:
        True if token matches hash, False otherwise
    """
    computed_hash = create_token_hash(token)
    return computed_hash == token_hash


# Token Extraction

def extract_bearer_token(authorization: Optional[str]) -> Optional[str]:
    """
    Extract JWT token from Authorization header.

    Args:
        authorization: Authorization header value (e.g., "Bearer <token>")

    Returns:
        Token string if valid format, None otherwise
    """
    if not authorization:
        return None

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    return parts[1]
