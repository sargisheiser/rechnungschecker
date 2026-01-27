"""API Key management endpoints."""

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.models.api_key import APIKey
from app.models.audit import AuditAction
from app.schemas.api_key import (
    APIKeyCreate,
    APIKeyCreated,
    APIKeyList,
    APIKeyResponse,
    APIKeyUpdate,
)
from app.services.audit import AuditService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/",
    response_model=APIKeyList,
    summary="List API keys",
    description="Get all API keys for the current user.",
)
async def list_api_keys(
    current_user: CurrentUser,
    db: DbSession,
) -> APIKeyList:
    """List all API keys for the current user."""
    # Check if user can use API
    if not current_user.can_use_api():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API-Zugang erfordert Pro- oder Steuerberater-Plan.",
        )

    # Get all keys for user
    result = await db.execute(
        select(APIKey)
        .where(APIKey.user_id == current_user.id)
        .order_by(APIKey.created_at.desc())
    )
    keys = result.scalars().all()

    # Calculate total API calls used this month
    total_calls_result = await db.execute(
        select(func.sum(APIKey.requests_this_month))
        .where(APIKey.user_id == current_user.id)
    )
    total_calls = total_calls_result.scalar() or 0

    return APIKeyList(
        items=[
            APIKeyResponse(
                id=key.id,
                name=key.name,
                description=key.description,
                key_prefix=key.key_prefix,
                is_active=key.is_active,
                created_at=key.created_at,
                expires_at=key.expires_at,
                last_used_at=key.last_used_at,
                usage_count=key.usage_count,
                requests_this_month=key.requests_this_month,
            )
            for key in keys
        ],
        total=len(keys),
        max_keys=current_user.get_max_api_keys(),
        api_calls_limit=current_user.get_api_calls_limit(),
        api_calls_used=total_calls,
    )


@router.post(
    "/",
    response_model=APIKeyCreated,
    status_code=status.HTTP_201_CREATED,
    summary="Create API key",
    description="Create a new API key. The key is only shown once!",
)
async def create_api_key(
    data: APIKeyCreate,
    current_user: CurrentUser,
    db: DbSession,
    request: Request,
) -> APIKeyCreated:
    """Create a new API key.

    The actual key value is only returned once at creation time.
    Store it securely!
    """
    audit_service = AuditService(db)

    # Check if user can use API
    if not current_user.can_use_api():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API-Zugang erfordert Pro- oder Steuerberater-Plan.",
        )

    # Check if user has reached max keys
    result = await db.execute(
        select(func.count(APIKey.id))
        .where(APIKey.user_id == current_user.id)
    )
    current_count = result.scalar() or 0
    max_keys = current_user.get_max_api_keys()

    if current_count >= max_keys:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximale Anzahl von {max_keys} API-Schluesseln erreicht.",
        )

    # Calculate expiration date
    expires_at = None
    if data.expires_in_days:
        expires_at = datetime.now(UTC).replace(tzinfo=None) + timedelta(days=data.expires_in_days)

    # Create the key
    api_key, raw_key = APIKey.create_key(
        user_id=current_user.id,
        name=data.name,
        description=data.description,
        expires_at=expires_at,
    )

    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    # Log audit event
    await audit_service.log(
        user_id=current_user.id,
        action=AuditAction.API_KEY_CREATE,
        resource_type="api_key",
        resource_id=str(api_key.id),
        request=request,
        details={"name": api_key.name},
    )

    logger.info(f"API key created: user={current_user.email}, key_id={api_key.id}")

    return APIKeyCreated(
        id=api_key.id,
        name=api_key.name,
        description=api_key.description,
        key_prefix=api_key.key_prefix,
        is_active=api_key.is_active,
        created_at=api_key.created_at,
        expires_at=api_key.expires_at,
        last_used_at=api_key.last_used_at,
        usage_count=api_key.usage_count,
        requests_this_month=api_key.requests_this_month,
        key=raw_key,
    )


@router.get(
    "/{key_id}",
    response_model=APIKeyResponse,
    summary="Get API key",
    description="Get details for a specific API key.",
)
async def get_api_key(
    key_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> APIKeyResponse:
    """Get details for a specific API key."""
    result = await db.execute(
        select(APIKey)
        .where(APIKey.id == key_id, APIKey.user_id == current_user.id)
    )
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API-Schluessel nicht gefunden.",
        )

    return APIKeyResponse(
        id=api_key.id,
        name=api_key.name,
        description=api_key.description,
        key_prefix=api_key.key_prefix,
        is_active=api_key.is_active,
        created_at=api_key.created_at,
        expires_at=api_key.expires_at,
        last_used_at=api_key.last_used_at,
        usage_count=api_key.usage_count,
        requests_this_month=api_key.requests_this_month,
    )


@router.patch(
    "/{key_id}",
    response_model=APIKeyResponse,
    summary="Update API key",
    description="Update an API key's name, description, or status.",
)
async def update_api_key(
    key_id: UUID,
    data: APIKeyUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> APIKeyResponse:
    """Update an API key."""
    result = await db.execute(
        select(APIKey)
        .where(APIKey.id == key_id, APIKey.user_id == current_user.id)
    )
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API-Schluessel nicht gefunden.",
        )

    # Update fields
    if data.name is not None:
        api_key.name = data.name
    if data.description is not None:
        api_key.description = data.description
    if data.is_active is not None:
        api_key.is_active = data.is_active

    await db.commit()
    await db.refresh(api_key)

    logger.info(f"API key updated: user={current_user.email}, key_id={api_key.id}")

    return APIKeyResponse(
        id=api_key.id,
        name=api_key.name,
        description=api_key.description,
        key_prefix=api_key.key_prefix,
        is_active=api_key.is_active,
        created_at=api_key.created_at,
        expires_at=api_key.expires_at,
        last_used_at=api_key.last_used_at,
        usage_count=api_key.usage_count,
        requests_this_month=api_key.requests_this_month,
    )


@router.delete(
    "/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete API key",
    description="Permanently delete an API key.",
)
async def delete_api_key(
    key_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
    request: Request,
) -> None:
    """Delete an API key."""
    audit_service = AuditService(db)

    result = await db.execute(
        select(APIKey)
        .where(APIKey.id == key_id, APIKey.user_id == current_user.id)
    )
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API-Schluessel nicht gefunden.",
        )

    key_name = api_key.name

    await db.delete(api_key)
    await db.commit()

    # Log audit event
    await audit_service.log(
        user_id=current_user.id,
        action=AuditAction.API_KEY_REVOKE,
        resource_type="api_key",
        resource_id=str(key_id),
        request=request,
        details={"name": key_name},
    )

    logger.info(f"API key deleted: user={current_user.email}, key_id={key_id}")
