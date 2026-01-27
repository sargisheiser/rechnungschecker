"""Security utilities for authentication and authorization."""

import random
import string
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import bcrypt
from jose import JWTError, jwt

from app.config import get_settings

settings = get_settings()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash.

    Note: bcrypt has a max password length of 72 bytes.
    Passwords longer than 72 bytes are truncated before verification.
    """
    # Truncate to 72 bytes (bcrypt limitation)
    password_bytes = plain_password.encode('utf-8')[:72]
    return bcrypt.checkpw(password_bytes, hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt.

    Note: bcrypt has a max password length of 72 bytes.
    Passwords longer than 72 bytes are truncated.
    """
    # Truncate to 72 bytes (bcrypt limitation)
    password_bytes = password.encode('utf-8')[:72]
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode('utf-8')


def create_access_token(
    subject: str | UUID,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Create a JWT access token.

    Args:
        subject: The subject (usually user ID) to encode
        expires_delta: Optional custom expiration time
        extra_claims: Optional additional claims to include

    Returns:
        Encoded JWT token string
    """
    if expires_delta:
        expire = datetime.now(UTC).replace(tzinfo=None) + expires_delta
    else:
        expire = datetime.now(UTC).replace(tzinfo=None) + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode: dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "type": "access",
        "iat": datetime.now(UTC).replace(tzinfo=None),
    }

    if extra_claims:
        to_encode.update(extra_claims)

    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(
    subject: str | UUID,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT refresh token.

    Args:
        subject: The subject (usually user ID) to encode
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT refresh token string
    """
    if expires_delta:
        expire = datetime.now(UTC).replace(tzinfo=None) + expires_delta
    else:
        expire = datetime.now(UTC).replace(tzinfo=None) + timedelta(days=settings.refresh_token_expire_days)

    to_encode: dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "type": "refresh",
        "iat": datetime.now(UTC).replace(tzinfo=None),
    }

    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT token.

    Args:
        token: The JWT token to decode

    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        return None


def verify_access_token(token: str) -> dict[str, Any] | None:
    """Verify an access token and return its payload.

    Args:
        token: The access token to verify

    Returns:
        Token payload if valid, None otherwise
    """
    payload = decode_token(token)
    if payload is None:
        return None

    # Check token type
    if payload.get("type") != "access":
        return None

    return payload


def verify_refresh_token(token: str) -> dict[str, Any] | None:
    """Verify a refresh token and return its payload.

    Args:
        token: The refresh token to verify

    Returns:
        Token payload if valid, None otherwise
    """
    payload = decode_token(token)
    if payload is None:
        return None

    # Check token type
    if payload.get("type") != "refresh":
        return None

    return payload


def create_email_verification_token(email: str) -> str:
    """Create a token for email verification.

    Args:
        email: The email address to verify

    Returns:
        Encoded verification token
    """
    expire = datetime.now(UTC).replace(tzinfo=None) + timedelta(hours=24)
    to_encode = {
        "sub": email,
        "exp": expire,
        "type": "email_verification",
    }
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def verify_email_verification_token(token: str) -> str | None:
    """Verify an email verification token.

    Args:
        token: The verification token

    Returns:
        Email address if valid, None otherwise
    """
    payload = decode_token(token)
    if payload is None:
        return None

    if payload.get("type") != "email_verification":
        return None

    return payload.get("sub")


def create_password_reset_token(email: str) -> str:
    """Create a token for password reset.

    Args:
        email: The email address for password reset

    Returns:
        Encoded password reset token
    """
    expire = datetime.now(UTC).replace(tzinfo=None) + timedelta(hours=1)  # 1 hour validity
    to_encode = {
        "sub": email,
        "exp": expire,
        "type": "password_reset",
    }
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def verify_password_reset_token(token: str) -> str | None:
    """Verify a password reset token.

    Args:
        token: The password reset token

    Returns:
        Email address if valid, None otherwise
    """
    payload = decode_token(token)
    if payload is None:
        return None

    if payload.get("type") != "password_reset":
        return None

    return payload.get("sub")


def generate_verification_code(length: int = 6) -> str:
    """Generate a random numeric verification code.

    Args:
        length: Length of the code (default 6)

    Returns:
        Random numeric code string
    """
    return ''.join(random.choices(string.digits, k=length))
