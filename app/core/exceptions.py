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


# Standard error codes for API responses
class ErrorCode:
    """Standard error codes for API responses."""

    # Authentication errors
    AUTH_INVALID_CREDENTIALS = "AUTH_INVALID_CREDENTIALS"
    AUTH_EMAIL_NOT_VERIFIED = "AUTH_EMAIL_NOT_VERIFIED"
    AUTH_TOKEN_EXPIRED = "AUTH_TOKEN_EXPIRED"
    AUTH_TOKEN_INVALID = "AUTH_TOKEN_INVALID"
    AUTH_EMAIL_EXISTS = "AUTH_EMAIL_EXISTS"

    # Authorization errors
    AUTHZ_INSUFFICIENT_PERMISSIONS = "AUTHZ_INSUFFICIENT_PERMISSIONS"
    AUTHZ_PLAN_REQUIRED = "AUTHZ_PLAN_REQUIRED"

    # Validation/Usage limits
    VALIDATION_LIMIT_REACHED = "VALIDATION_LIMIT_REACHED"
    CONVERSION_LIMIT_REACHED = "CONVERSION_LIMIT_REACHED"
    GUEST_LIMIT_REACHED = "GUEST_LIMIT_REACHED"

    # Resource errors
    NOT_FOUND = "NOT_FOUND"
    ALREADY_EXISTS = "ALREADY_EXISTS"

    # File errors
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    INVALID_FILE_TYPE = "INVALID_FILE_TYPE"
    FILE_PROCESSING_ERROR = "FILE_PROCESSING_ERROR"

    # Rate limiting
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"

    # General errors
    BAD_REQUEST = "BAD_REQUEST"
    INTERNAL_ERROR = "INTERNAL_ERROR"


def api_error(
    code: str,
    message: str,
    **extra: Any,
) -> dict[str, Any]:
    """
    Create a standardized API error detail object.

    Use this for HTTPException detail to ensure consistent error format.

    Args:
        code: Error code from ErrorCode class
        message: Human-readable error message (German)
        **extra: Additional fields to include in the response

    Returns:
        Dict with code, message, and any extra fields

    Example:
        raise HTTPException(
            status_code=403,
            detail=api_error(
                ErrorCode.VALIDATION_LIMIT_REACHED,
                "Sie haben Ihr monatliches Limit erreicht.",
                validations_used=10,
                validations_limit=10,
            )
        )
    """
    return {"code": code, "message": message, **extra}
