"""
FastAPI dependency functions.
Centralised here so auth logic is never duplicated across endpoints.
"""
import uuid
from typing import Annotated
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import (
    InvalidTokenError, PermissionDeniedError, TokenBlacklistedError,
)
from app.core.redis import get_redis
from app.core.security import decode_token
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.email_service import EmailService
from app.services.otp_service import OTPService
from app.services.token_service import TokenService

_bearer_scheme = HTTPBearer(auto_error=False)

DbDep = Annotated[AsyncSession, Depends(get_db)]
RedisDep = Annotated[Redis, Depends(get_redis)]

def get_token_service(redis: RedisDep) -> TokenService:
    return TokenService(redis=redis)

def get_otp_service(redis: RedisDep) -> OTPService:
    return OTPService(redis=redis)

def get_email_service() -> EmailService:
    return EmailService()

def get_auth_service(
    db: DbDep,
    token_service: Annotated[TokenService, Depends(get_token_service)],
    otp_service: Annotated[OTPService, Depends(get_otp_service)],
    email_service: Annotated[EmailService, Depends(get_email_service)],
) -> AuthService:
    return AuthService(db=db, token_service=token_service,
                       otp_service=otp_service, email_service=email_service)

TokenServiceDep = Annotated[TokenService, Depends(get_token_service)]
OTPServiceDep = Annotated[OTPService, Depends(get_otp_service)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]

async def get_current_user(
    request: Request,
    db: DbDep,
    redis: RedisDep,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)
    ] = None,
) -> User:
    if credentials is None:
        raise InvalidTokenError("Missing authorization header.")
    token = credentials.credentials
    payload = decode_token(token, expected_type="access")
    jti: str = payload.get("jti", "")
    token_service = TokenService(redis=redis)
    if await token_service.is_access_token_blacklisted(jti):
        raise TokenBlacklistedError()
    user_id_str: str = payload.get("sub", "")
    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError as exc:
        raise InvalidTokenError("Invalid user identifier in token.") from exc
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id_with_roles(user_id)
    if user is None or user.deleted_at is not None:
        raise InvalidTokenError("User account not found.")
    if not user.is_active:
        from app.core.exceptions import AccountInactiveError
        raise AccountInactiveError()
    return user

async def get_optional_current_user(
    request: Request,
    db: DbDep,
    redis: RedisDep,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)
    ] = None,
) -> User | None:
    if credentials is None:
        return None
    try:
        token = credentials.credentials
        payload = decode_token(token, expected_type="access")
        jti: str = payload.get("jti", "")
        token_service = TokenService(redis=redis)
        if await token_service.is_access_token_blacklisted(jti):
            return None
        user_id_str: str = payload.get("sub", "")
        user_id = uuid.UUID(user_id_str)
        user_repo = UserRepository(db)
        user = await user_repo.get_by_id_with_roles(user_id)
        if user is None or user.deleted_at is not None or not user.is_active:
            return None
        return user
    except Exception:
        return None

async def get_current_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not current_user.is_admin:
        raise PermissionDeniedError()
    return current_user

CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentAdmin = Annotated[User, Depends(get_current_admin)]
OptionalCurrentUser = Annotated[User | None, Depends(get_optional_current_user)]



def get_client_ip(request: Request) -> str | None:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else None

def get_user_agent(request: Request) -> str | None:
    return request.headers.get("User-Agent")
