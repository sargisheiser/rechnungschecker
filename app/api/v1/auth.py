"""Authentication API endpoints."""

import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.config import get_settings
from app.core.security import (
    create_access_token,
    create_password_reset_token,
    create_refresh_token,
    generate_verification_code,
    get_password_hash,
    verify_password,
    verify_password_reset_token,
    verify_refresh_token,
)
from app.models.audit import AuditAction
from app.models.user import User
from app.services.audit import AuditService
from app.services.email import email_service
from app.schemas.auth import (
    EmailVerification,
    PasswordChange,
    PasswordReset,
    PasswordResetConfirm,
    TokenRefresh,
    TokenResponse,
    UsageResponse,
    UserUpdate,
    UserLogin,
    UserRegister,
    UserResponse,
)

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new user account with email and password.",
)
async def register(
    data: UserRegister,
    db: DbSession,
) -> User:
    """Register a new user account.

    - Email must be unique
    - Password must be at least 8 characters with upper, lower, and digit
    - Verification email with 6-digit code will be sent
    """
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == data.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ein Konto mit dieser E-Mail-Adresse existiert bereits",
        )

    # Generate verification code
    verification_code = generate_verification_code()
    code_expires = datetime.utcnow() + timedelta(minutes=15)

    # Create new user
    user = User(
        email=data.email,
        password_hash=get_password_hash(data.password),
        is_active=True,
        is_verified=False,
        verification_code=verification_code,
        verification_code_expires=code_expires,
    )

    db.add(user)
    await db.flush()
    await db.refresh(user)

    # Send verification email with code
    await email_service.send_verification_code_email(data.email, verification_code)
    logger.info(f"User registered: {user.email}, verification code sent")

    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User login",
    description="Authenticate with email and password to get access tokens.",
)
async def login(
    data: UserLogin,
    db: DbSession,
    request: Request,
) -> TokenResponse:
    """Authenticate user and return access/refresh tokens."""
    audit_service = AuditService(db)

    # Find user by email
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(data.password, user.password_hash):
        # Log failed login attempt if user exists
        if user:
            await audit_service.log(
                user_id=user.id,
                action=AuditAction.LOGIN_FAILED,
                resource_type="user",
                resource_id=str(user.id),
                request=request,
                details={"reason": "invalid_password"},
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ungültige E-Mail-Adresse oder Passwort",
        )

    if not user.is_active:
        await audit_service.log(
            user_id=user.id,
            action=AuditAction.LOGIN_FAILED,
            resource_type="user",
            resource_id=str(user.id),
            request=request,
            details={"reason": "account_inactive"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Benutzerkonto deaktiviert",
        )

    # Update last login
    user.last_login_at = datetime.utcnow()
    await db.flush()

    # Log successful login
    await audit_service.log(
        user_id=user.id,
        action=AuditAction.LOGIN,
        resource_type="user",
        resource_id=str(user.id),
        request=request,
    )

    # Create tokens
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    logger.info(f"User logged in: {user.email}")

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Get a new access token using a valid refresh token.",
)
async def refresh_token(
    data: TokenRefresh,
    db: DbSession,
) -> TokenResponse:
    """Refresh access token using refresh token."""
    payload = verify_refresh_token(data.refresh_token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ungültiger oder abgelaufener Refresh-Token",
        )

    user_id = payload.get("sub")

    # Verify user still exists and is active
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Benutzer nicht gefunden oder deaktiviert",
        )

    # Create new tokens
    access_token = create_access_token(user.id)
    new_refresh_token = create_refresh_token(user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post(
    "/verify-email",
    status_code=status.HTTP_200_OK,
    summary="Verify email address",
    description="Verify email address using the 6-digit code sent via email.",
)
async def verify_email(
    data: EmailVerification,
    db: DbSession,
) -> dict[str, str]:
    """Verify user's email address using verification code."""
    # Find user by email
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Benutzer nicht gefunden",
        )

    if user.is_verified:
        return {"message": "E-Mail-Adresse bereits verifiziert"}

    # Check verification code
    if user.verification_code != data.code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ungültiger Verifizierungscode",
        )

    # Check if code has expired
    if user.verification_code_expires and datetime.utcnow() > user.verification_code_expires:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verifizierungscode abgelaufen. Bitte fordern Sie einen neuen an.",
        )

    # Mark as verified and clear code
    user.is_verified = True
    user.verification_code = None
    user.verification_code_expires = None
    await db.flush()

    logger.info(f"Email verified: {data.email}")

    return {"message": "E-Mail-Adresse erfolgreich verifiziert"}


@router.post(
    "/resend-verification",
    status_code=status.HTTP_200_OK,
    summary="Resend verification email",
    description="Resend the email verification code.",
)
async def resend_verification(
    data: PasswordReset,  # Reuse schema - just needs email
    db: DbSession,
) -> dict[str, str]:
    """Resend verification code email.

    Always returns success to prevent email enumeration.
    """
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if user and user.is_active and not user.is_verified:
        # Generate new verification code
        verification_code = generate_verification_code()
        user.verification_code = verification_code
        user.verification_code_expires = datetime.utcnow() + timedelta(minutes=15)
        await db.flush()

        await email_service.send_verification_code_email(data.email, verification_code)
        logger.info(f"Verification code resent to: {data.email}")

    return {
        "message": "Falls das Konto existiert und nicht verifiziert ist, wurde ein neuer Code gesendet"
    }


@router.post(
    "/forgot-password",
    status_code=status.HTTP_200_OK,
    summary="Request password reset",
    description="Request a password reset email.",
)
async def forgot_password(
    data: PasswordReset,
    db: DbSession,
    request: Request,
) -> dict[str, str]:
    """Request password reset email.

    Always returns success to prevent email enumeration.
    """
    audit_service = AuditService(db)

    # Find user (but don't reveal if they exist)
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if user and user.is_active:
        # Log password reset request
        await audit_service.log(
            user_id=user.id,
            action=AuditAction.PASSWORD_RESET_REQUEST,
            resource_type="user",
            resource_id=str(user.id),
            request=request,
        )

        # Create reset token and send email
        reset_token = create_password_reset_token(data.email)
        await email_service.send_password_reset_email(data.email, reset_token)
        logger.info(f"Password reset requested for: {data.email}")

    # Always return success to prevent email enumeration
    return {
        "message": "Falls ein Konto mit dieser E-Mail existiert, wurde eine Anleitung zum Zurücksetzen gesendet"
    }


@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
    summary="Reset password",
    description="Reset password using the token from email.",
)
async def reset_password(
    data: PasswordResetConfirm,
    db: DbSession,
    request: Request,
) -> dict[str, str]:
    """Reset password using reset token."""
    audit_service = AuditService(db)

    email = verify_password_reset_token(data.token)

    if email is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ungültiger oder abgelaufener Link zum Zurücksetzen",
        )

    # Find and update user
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Benutzer nicht gefunden",
        )

    user.password_hash = get_password_hash(data.new_password)
    await db.flush()

    # Log password reset completion
    await audit_service.log(
        user_id=user.id,
        action=AuditAction.PASSWORD_RESET_COMPLETE,
        resource_type="user",
        resource_id=str(user.id),
        request=request,
    )

    logger.info(f"Password reset completed for: {email}")

    return {"message": "Passwort erfolgreich zurückgesetzt"}


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get the current authenticated user's profile.",
)
async def get_me(
    current_user: CurrentUser,
) -> User:
    """Get current user profile."""
    return current_user


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update profile",
    description="Update the current user's profile information.",
)
async def update_profile(
    data: UserUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> User:
    """Update current user profile."""
    if data.company_name is not None:
        current_user.company_name = data.company_name

    await db.flush()
    await db.refresh(current_user)

    logger.info(f"Profile updated for: {current_user.email}")

    return current_user


@router.post(
    "/change-password",
    status_code=status.HTTP_200_OK,
    summary="Change password",
    description="Change the current user's password.",
)
async def change_password(
    data: PasswordChange,
    current_user: CurrentUser,
    db: DbSession,
    request: Request,
) -> dict[str, str]:
    """Change current user's password."""
    audit_service = AuditService(db)

    # Verify current password
    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Aktuelles Passwort ist falsch",
        )

    # Update password
    current_user.password_hash = get_password_hash(data.new_password)
    await db.flush()

    # Log password change
    await audit_service.log(
        user_id=current_user.id,
        action=AuditAction.PASSWORD_CHANGE,
        resource_type="user",
        resource_id=str(current_user.id),
        request=request,
    )

    logger.info(f"Password changed for: {current_user.email}")

    return {"message": "Passwort erfolgreich geändert"}


@router.get(
    "/usage",
    response_model=UsageResponse,
    summary="Get usage statistics",
    description="Get the current user's usage statistics and limits.",
)
async def get_usage(
    current_user: CurrentUser,
) -> UsageResponse:
    """Get current user's usage statistics."""
    return UsageResponse(
        plan=current_user.plan.value,
        validations_used=current_user.validations_this_month,
        validations_limit=current_user.get_validation_limit(),
        conversions_used=current_user.conversions_this_month,
        conversions_limit=current_user.get_conversion_limit(),
        usage_reset_date=datetime.combine(
            current_user.usage_reset_date,
            datetime.min.time(),
        ),
    )


@router.delete(
    "/me",
    status_code=status.HTTP_200_OK,
    summary="Delete account",
    description="Permanently delete the current user's account (DSGVO compliance).",
)
async def delete_account(
    current_user: CurrentUser,
    db: DbSession,
) -> dict[str, str]:
    """Delete current user account (DSGVO right to erasure)."""
    email = current_user.email

    # Delete user (cascade will handle related records)
    await db.delete(current_user)
    await db.flush()

    logger.info(f"Account deleted: {email}")

    return {"message": "Konto erfolgreich gelöscht"}
