"""API dependencies for dependency injection."""

import logging
from datetime import UTC, date, datetime
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import verify_access_token
from app.models.api_key import APIKey, generate_key_hash
from app.models.user import User

logger = logging.getLogger(__name__)

# HTTP Bearer security scheme
security = HTTPBearer(auto_error=False)


async def _authenticate_with_api_key(
    token: str,
    db: AsyncSession,
) -> User | None:
    """Authenticate using an API key.

    Args:
        token: The API key (rc_live_xxx format)
        db: Database session

    Returns:
        The authenticated User or None if invalid
    """
    # Hash the key to look it up
    key_hash = generate_key_hash(token)

    # Find the API key
    result = await db.execute(
        select(APIKey)
        .options(selectinload(APIKey.user))
        .where(APIKey.key_hash == key_hash)
    )
    api_key = result.scalar_one_or_none()

    if api_key is None:
        return None

    # Check if key is valid
    if not api_key.is_valid():
        logger.warning(f"Invalid API key used: {api_key.key_prefix}")
        return None

    # Check if user is active and can use API
    user = api_key.user
    if not user.is_active:
        return None

    if not user.can_use_api():
        logger.warning(f"API key used by user without API access: {user.email}")
        return None

    # Check monthly API call limits
    today = date.today()
    reset_month = api_key.requests_reset_date.month
    reset_year = api_key.requests_reset_date.year
    if reset_month != today.month or reset_year != today.year:
        api_key.requests_this_month = 0
        api_key.requests_reset_date = datetime.now(UTC).replace(tzinfo=None)

    # Check if user has reached API call limit
    api_limit = user.get_api_calls_limit()
    if api_key.requests_this_month >= api_limit:
        logger.warning(f"API call limit reached for user: {user.email}")
        return None

    # Record usage
    api_key.record_usage()
    await db.commit()

    logger.debug(f"API key authenticated: user={user.email}, key={api_key.key_prefix}")

    return user


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Get the current authenticated user.

    Supports both JWT tokens and API keys (rc_live_xxx format).

    Args:
        credentials: Bearer token credentials
        db: Database session

    Returns:
        The authenticated User

    Raises:
        HTTPException: If authentication fails
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nicht authentifiziert",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Check if it's an API key (starts with rc_live_)
    if token.startswith("rc_live_"):
        user = await _authenticate_with_api_key(token, db)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Ungueltiger oder abgelaufener API-Schluessel",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user

    # Otherwise treat as JWT token
    payload = verify_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ungültiger oder abgelaufener Token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ungültiger Token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Benutzer nicht gefunden",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Benutzerkonto deaktiviert",
        )

    return user


async def get_current_user_optional(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User | None:
    """Get the current user if authenticated, otherwise None.

    Supports both JWT tokens and API keys (rc_live_xxx format).
    This is useful for endpoints that work differently for
    authenticated vs guest users.

    Args:
        credentials: Bearer token credentials
        db: Database session

    Returns:
        The authenticated User or None for guests
    """
    if credentials is None:
        return None

    token = credentials.credentials

    # Check if it's an API key
    if token.startswith("rc_live_"):
        return await _authenticate_with_api_key(token, db)

    # Otherwise treat as JWT token
    payload = verify_access_token(token)

    if payload is None:
        return None

    user_id = payload.get("sub")
    if user_id is None:
        return None

    # Get user from database
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        return None

    return user


async def get_verified_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Get the current user and verify email is confirmed.

    Args:
        current_user: The authenticated user

    Returns:
        The verified User

    Raises:
        HTTPException: If email is not verified
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="E-Mail-Adresse nicht verifiziert",
        )
    return current_user


async def get_current_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Get the current user and verify admin access.

    Args:
        current_user: The authenticated user

    Returns:
        The admin User

    Raises:
        HTTPException: If user is not an admin
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administratorzugriff erforderlich",
        )
    return current_user


# Type aliases for cleaner dependency injection
CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_current_user_optional)]
VerifiedUser = Annotated[User, Depends(get_verified_user)]
CurrentAdmin = Annotated[User, Depends(get_current_admin)]
DbSession = Annotated[AsyncSession, Depends(get_db)]
