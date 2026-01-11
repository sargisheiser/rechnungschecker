"""Custom exceptions for the application."""

from typing import Any


class RechnungsCheckerError(Exception):
    """Base exception for all application errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(RechnungsCheckerError):
    """Error during invoice validation."""

    pass


class FileProcessingError(RechnungsCheckerError):
    """Error during file processing."""

    pass


class KoSITError(RechnungsCheckerError):
    """Error from KoSIT validator."""

    pass


class AuthenticationError(RechnungsCheckerError):
    """Authentication related errors."""

    pass


class AuthorizationError(RechnungsCheckerError):
    """Authorization related errors."""

    pass


class RateLimitError(RechnungsCheckerError):
    """Rate limit exceeded."""

    pass


class UsageLimitError(RechnungsCheckerError):
    """Usage limit exceeded (e.g., monthly validations)."""

    pass


class PaymentError(RechnungsCheckerError):
    """Payment processing error."""

    pass
