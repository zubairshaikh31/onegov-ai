"""
Custom exception hierarchy.
All application exceptions inherit from OneGovError so we can catch them
uniformly in the global exception handler in main.py.
"""

from fastapi import status


class OneGovError(Exception):
    """Base exception for all application errors."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: str = "internal_error"
    message: str = "An unexpected error occurred"

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.__class__.message
        super().__init__(self.message)


# ── Authentication & Authorization ────────────────────────────────────────────

class AuthenticationError(OneGovError):
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = "authentication_failed"
    message = "Authentication failed"


class InvalidCredentialsError(AuthenticationError):
    error_code = "invalid_credentials"
    message = "Invalid email or password"


class InvalidTokenError(AuthenticationError):
    error_code = "invalid_token"
    message = "Invalid or malformed token"


class TokenExpiredError(AuthenticationError):
    error_code = "token_expired"
    message = "Token has expired"


class TokenBlacklistedError(AuthenticationError):
    error_code = "token_revoked"
    message = "Token has been revoked"


class PermissionDeniedError(OneGovError):
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "permission_denied"
    message = "You do not have permission to perform this action"


ForbiddenError = PermissionDeniedError



# ── Account State ─────────────────────────────────────────────────────────────

class AccountNotFoundError(OneGovError):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "account_not_found"
    message = "Account not found"


class AccountInactiveError(AuthenticationError):
    error_code = "account_inactive"
    message = "Your account has been deactivated. Please contact support"


class AccountLockedError(AuthenticationError):
    error_code = "account_locked"
    message = "Account temporarily locked due to too many failed attempts"


class EmailNotVerifiedError(AuthenticationError):
    error_code = "email_not_verified"
    message = "Please verify your email address before logging in"


# ── OTP ───────────────────────────────────────────────────────────────────────

class OTPError(OneGovError):
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = "otp_error"
    message = "OTP error"


class InvalidOTPError(OTPError):
    error_code = "invalid_otp"
    message = "Invalid OTP code"


class OTPExpiredError(OTPError):
    error_code = "otp_expired"
    message = "OTP has expired. Please request a new one"


class OTPTooManyAttemptsError(OTPError):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    error_code = "otp_too_many_attempts"
    message = "Too many OTP attempts. Please request a new code"


# ── Resource ──────────────────────────────────────────────────────────────────

class NotFoundError(OneGovError):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "not_found"
    message = "Resource not found"


class AlreadyExistsError(OneGovError):
    status_code = status.HTTP_409_CONFLICT
    error_code = "already_exists"
    message = "Resource already exists"


class ValidationError(OneGovError):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    error_code = "validation_error"
    message = "Validation failed"


# ── External Services ─────────────────────────────────────────────────────────

class ServiceUnavailableError(OneGovError):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    error_code = "service_unavailable"
    message = "Service temporarily unavailable"


class ExternalServiceError(OneGovError):
    status_code = status.HTTP_502_BAD_GATEWAY
    error_code = "external_service_error"
    message = "External service error"
