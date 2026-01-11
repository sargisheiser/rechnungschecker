"""Pydantic schemas for authentication endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRegister(BaseModel):
    """Schema for user registration."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=100)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        """Validate password has minimum complexity."""
        if not any(c.isupper() for c in v):
            raise ValueError("Passwort muss mindestens einen Großbuchstaben enthalten")
        if not any(c.islower() for c in v):
            raise ValueError("Passwort muss mindestens einen Kleinbuchstaben enthalten")
        if not any(c.isdigit() for c in v):
            raise ValueError("Passwort muss mindestens eine Zahl enthalten")
        return v


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Schema for token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Access token expiration in seconds")


class TokenRefresh(BaseModel):
    """Schema for token refresh request."""

    refresh_token: str


class PasswordReset(BaseModel):
    """Schema for password reset request."""

    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""

    token: str
    new_password: str = Field(min_length=8, max_length=100)

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        """Validate password has minimum complexity."""
        if not any(c.isupper() for c in v):
            raise ValueError("Passwort muss mindestens einen Großbuchstaben enthalten")
        if not any(c.islower() for c in v):
            raise ValueError("Passwort muss mindestens einen Kleinbuchstaben enthalten")
        if not any(c.isdigit() for c in v):
            raise ValueError("Passwort muss mindestens eine Zahl enthalten")
        return v


class EmailVerification(BaseModel):
    """Schema for email verification."""

    token: str


class UserResponse(BaseModel):
    """Schema for user response."""

    id: UUID
    email: str
    is_active: bool
    is_verified: bool
    plan: str
    validations_this_month: int
    conversions_this_month: int
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Schema for user profile update."""

    email: EmailStr | None = None


class PasswordChange(BaseModel):
    """Schema for password change."""

    current_password: str
    new_password: str = Field(min_length=8, max_length=100)

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        """Validate password has minimum complexity."""
        if not any(c.isupper() for c in v):
            raise ValueError("Passwort muss mindestens einen Großbuchstaben enthalten")
        if not any(c.islower() for c in v):
            raise ValueError("Passwort muss mindestens einen Kleinbuchstaben enthalten")
        if not any(c.isdigit() for c in v):
            raise ValueError("Passwort muss mindestens eine Zahl enthalten")
        return v


class UsageResponse(BaseModel):
    """Schema for usage statistics response."""

    plan: str
    validations_used: int
    validations_limit: int | None = Field(description="None means unlimited")
    conversions_used: int
    conversions_limit: int
    usage_reset_date: datetime
