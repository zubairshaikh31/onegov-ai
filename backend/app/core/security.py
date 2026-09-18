"""
Security utilities: password hashing, JWT creation and validation.
All token operations go through this module — never roll your own crypto elsewhere.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.exceptions import InvalidTokenError, TokenExpiredError

# bcrypt context — work factor 12 is the production sweet spot (2^12 rounds)
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


# ── Password Utilities ────────────────────────────────────────────────────────

def hash_password(plain_password: str) -> str:
    """Return a bcrypt hash of the given password."""
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if the plain password matches the stored hash."""
    return _pwd_context.verify(plain_password, hashed_password)


# ── JWT Utilities ─────────────────────────────────────────────────────────────

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(
    subject: str,
    role: str,
    extra_claims: dict[str, Any] | None = None,
) -> tuple[str, str]:
    """
    Create a short-lived JWT access token.

    Returns:
        (token_string, jti) — the jti is used for blacklisting on logout.
    """
    jti = str(uuid.uuid4())
    now = _utcnow()
    payload: dict[str, Any] = {
        "sub": str(subject),
        "role": role,
        "jti": jti,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    if extra_claims:
        payload.update(extra_claims)

    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, jti


def create_refresh_token(subject: str) -> tuple[str, str]:
    """
    Create a long-lived refresh token.

    Returns:
        (token_string, jti)
    """
    jti = str(uuid.uuid4())
    now = _utcnow()
    payload: dict[str, Any] = {
        "sub": str(subject),
        "jti": jti,
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, jti


def decode_token(token: str, expected_type: str = "access") -> dict[str, Any]:
    """
    Decode and validate a JWT token.

    Raises:
        TokenExpiredError: if the token has expired.
        InvalidTokenError: if the token is malformed, has wrong type,
                           or fails signature verification.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_exp": True},
        )
    except JWTError as exc:
        error_msg = str(exc).lower()
        if "expired" in error_msg:
            raise TokenExpiredError("Token has expired") from exc
        raise InvalidTokenError(f"Token validation failed: {exc}") from exc

    if payload.get("type") != expected_type:
        raise InvalidTokenError(
            f"Expected token type '{expected_type}', got '{payload.get('type')}'"
        )

    return payload


def get_token_remaining_seconds(token: str) -> int:
    """
    Return the number of seconds until the token expires.
    Returns 0 if expired or invalid.
    Used for setting blacklist TTL.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_exp": False},  # we handle expiry ourselves
        )
        exp = payload.get("exp", 0)
        remaining = int(exp - _utcnow().timestamp())
        return max(remaining, 0)
    except JWTError:
        return 0
