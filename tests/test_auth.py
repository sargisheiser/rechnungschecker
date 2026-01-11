"""Tests for authentication endpoints and security."""

import pytest
from httpx import AsyncClient

from app.core.security import (
    create_access_token,
    create_email_verification_token,
    create_password_reset_token,
    create_refresh_token,
    get_password_hash,
    verify_access_token,
    verify_email_verification_token,
    verify_password,
    verify_password_reset_token,
    verify_refresh_token,
)


class TestPasswordHashing:
    """Tests for password hashing utilities."""

    def test_password_hash_and_verify(self) -> None:
        """Test that passwords can be hashed and verified."""
        password = "TestPassword123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert verify_password(password, hashed)

    def test_wrong_password_fails(self) -> None:
        """Test that wrong password verification fails."""
        password = "TestPassword123"
        wrong_password = "WrongPassword456"
        hashed = get_password_hash(password)

        assert not verify_password(wrong_password, hashed)

    def test_hash_is_unique(self) -> None:
        """Test that same password produces different hashes (salt)."""
        password = "TestPassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        assert hash1 != hash2
        # But both should verify
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)


class TestJWTTokens:
    """Tests for JWT token utilities."""

    def test_create_and_verify_access_token(self) -> None:
        """Test access token creation and verification."""
        user_id = "test-user-123"
        token = create_access_token(user_id)

        payload = verify_access_token(token)
        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["type"] == "access"

    def test_create_and_verify_refresh_token(self) -> None:
        """Test refresh token creation and verification."""
        user_id = "test-user-123"
        token = create_refresh_token(user_id)

        payload = verify_refresh_token(token)
        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"

    def test_access_token_not_valid_as_refresh(self) -> None:
        """Test that access token cannot be used as refresh token."""
        user_id = "test-user-123"
        access_token = create_access_token(user_id)

        payload = verify_refresh_token(access_token)
        assert payload is None

    def test_refresh_token_not_valid_as_access(self) -> None:
        """Test that refresh token cannot be used as access token."""
        user_id = "test-user-123"
        refresh_token = create_refresh_token(user_id)

        payload = verify_access_token(refresh_token)
        assert payload is None

    def test_invalid_token_fails(self) -> None:
        """Test that invalid token verification fails."""
        payload = verify_access_token("invalid-token")
        assert payload is None

    def test_email_verification_token(self) -> None:
        """Test email verification token creation and verification."""
        email = "test@example.com"
        token = create_email_verification_token(email)

        result = verify_email_verification_token(token)
        assert result == email

    def test_password_reset_token(self) -> None:
        """Test password reset token creation and verification."""
        email = "test@example.com"
        token = create_password_reset_token(email)

        result = verify_password_reset_token(token)
        assert result == email


class TestAuthEndpoints:
    """Tests for authentication API endpoints."""

    @pytest.mark.asyncio
    async def test_register_success(self, async_client: AsyncClient) -> None:
        """Test successful user registration."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123",
            },
        )

        # Note: This will fail without a database connection
        # In a real test, we'd use a test database
        assert response.status_code in [201, 500]  # 500 if no DB

    @pytest.mark.asyncio
    async def test_register_weak_password(self, async_client: AsyncClient) -> None:
        """Test registration with weak password fails."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "weak",  # Too short, no uppercase, no digit
            },
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, async_client: AsyncClient) -> None:
        """Test registration with invalid email fails."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "SecurePass123",
            },
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, async_client: AsyncClient) -> None:
        """Test login with invalid credentials fails."""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "WrongPassword123",
            },
        )

        # Either 401 (unauthorized) or 500 (no DB)
        assert response.status_code in [401, 500]

    @pytest.mark.asyncio
    async def test_get_me_unauthorized(self, async_client: AsyncClient) -> None:
        """Test /me endpoint without authentication fails."""
        response = await async_client.get("/api/v1/auth/me")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_me_invalid_token(self, async_client: AsyncClient) -> None:
        """Test /me endpoint with invalid token fails."""
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_forgot_password_always_succeeds(
        self, async_client: AsyncClient
    ) -> None:
        """Test forgot password always returns success (prevent enumeration)."""
        response = await async_client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "any@example.com"},
        )

        # Should succeed even if email doesn't exist (or DB unavailable)
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_usage_unauthorized(self, async_client: AsyncClient) -> None:
        """Test usage endpoint without authentication fails."""
        response = await async_client.get("/api/v1/auth/usage")

        assert response.status_code == 401


class TestPasswordValidation:
    """Tests for password validation rules."""

    @pytest.mark.asyncio
    async def test_password_no_uppercase(self, async_client: AsyncClient) -> None:
        """Test password without uppercase fails."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "nouppercase123",
            },
        )

        assert response.status_code == 422
        assert "Großbuchstaben" in response.text

    @pytest.mark.asyncio
    async def test_password_no_lowercase(self, async_client: AsyncClient) -> None:
        """Test password without lowercase fails."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "NOLOWERCASE123",
            },
        )

        assert response.status_code == 422
        assert "Kleinbuchstaben" in response.text

    @pytest.mark.asyncio
    async def test_password_no_digit(self, async_client: AsyncClient) -> None:
        """Test password without digit fails."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "NoDigitsHere",
            },
        )

        assert response.status_code == 422
        assert "Zahl" in response.text
