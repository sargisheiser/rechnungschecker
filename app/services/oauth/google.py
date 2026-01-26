"""Google OAuth service for authentication."""

import logging
from dataclasses import dataclass

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


@dataclass
class GoogleUserInfo:
    """User info from Google OAuth."""

    id: str
    email: str
    verified_email: bool
    name: str | None = None
    picture: str | None = None


class GoogleOAuthService:
    """Service for Google OAuth authentication."""

    def __init__(self) -> None:
        """Initialize the Google OAuth service."""
        self.client_id = settings.google_oauth_client_id
        self.client_secret = settings.google_oauth_client_secret

    def is_configured(self) -> bool:
        """Check if Google OAuth is configured."""
        return bool(self.client_id and self.client_secret)

    def get_authorization_url(self, redirect_uri: str, state: str | None = None) -> str:
        """Generate the Google OAuth authorization URL.

        Args:
            redirect_uri: The URL to redirect to after authorization.
            state: Optional state parameter for CSRF protection.

        Returns:
            The authorization URL to redirect the user to.
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "consent",
        }

        if state:
            params["state"] = state

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{GOOGLE_AUTH_URL}?{query_string}"

    async def exchange_code(self, code: str, redirect_uri: str) -> dict:
        """Exchange authorization code for tokens.

        Args:
            code: The authorization code from Google.
            redirect_uri: The redirect URI used in the authorization request.

        Returns:
            The token response from Google.

        Raises:
            httpx.HTTPError: If the token exchange fails.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                },
            )
            response.raise_for_status()
            return response.json()

    async def get_user_info(self, access_token: str) -> GoogleUserInfo:
        """Get user info from Google using access token.

        Args:
            access_token: The access token from Google.

        Returns:
            The user info from Google.

        Raises:
            httpx.HTTPError: If the request fails.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            data = response.json()

            return GoogleUserInfo(
                id=data["id"],
                email=data["email"],
                verified_email=data.get("verified_email", False),
                name=data.get("name"),
                picture=data.get("picture"),
            )

    async def authenticate(self, code: str, redirect_uri: str) -> GoogleUserInfo:
        """Complete the OAuth flow and get user info.

        Args:
            code: The authorization code from Google.
            redirect_uri: The redirect URI used in the authorization request.

        Returns:
            The user info from Google.
        """
        tokens = await self.exchange_code(code, redirect_uri)
        return await self.get_user_info(tokens["access_token"])


# Singleton instance
google_oauth_service = GoogleOAuthService()
