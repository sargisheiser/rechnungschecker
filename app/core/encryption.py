"""Encryption service for securing sensitive data at rest."""

import base64
import hashlib
import logging

from cryptography.fernet import Fernet

from app.config import get_settings

logger = logging.getLogger(__name__)


class EncryptionService:
    """Service for encrypting and decrypting sensitive data.

    Uses Fernet symmetric encryption with a key derived from the
    application's secret key.
    """

    def __init__(self):
        """Initialize encryption service with derived key."""
        settings = get_settings()
        self._fernet = Fernet(self._derive_key(settings.secret_key))

    @staticmethod
    def _derive_key(secret: str) -> bytes:
        """Derive a Fernet-compatible key from the application secret.

        Args:
            secret: The application secret key

        Returns:
            A 32-byte URL-safe base64-encoded key
        """
        # Use SHA256 to get a consistent 32-byte key
        key = hashlib.sha256(secret.encode()).digest()
        return base64.urlsafe_b64encode(key)

    def encrypt(self, data: str) -> str:
        """Encrypt a string.

        Args:
            data: The plaintext string to encrypt

        Returns:
            The encrypted string (base64-encoded)
        """
        return self._fernet.encrypt(data.encode()).decode()

    def decrypt(self, encrypted: str) -> str:
        """Decrypt a string.

        Args:
            encrypted: The encrypted string (base64-encoded)

        Returns:
            The decrypted plaintext string

        Raises:
            cryptography.fernet.InvalidToken: If decryption fails
        """
        return self._fernet.decrypt(encrypted.encode()).decode()


# Singleton instance
encryption_service = EncryptionService()
