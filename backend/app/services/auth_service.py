"""
Authentication service — orchestrates the complete auth lifecycle.
"""
import asyncio
from datetime import datetime, timedelta, timezone

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    AccountInactiveError,
    AccountLockedError,
    AccountNotFoundError,
    AlreadyExistsError,
    EmailNotVerifiedError,
    ExternalServiceError,
    InvalidCredentialsError,
)
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginResponse, RegisterResponse
from app.services.email_service import EmailService
from app.services.otp_service import OTPService
from app.services.token_service import TokenService


class AuthService:
    def __init__(
        self,
        db: AsyncSession,
        token_service: TokenService,
        otp_service: OTPService,
        email_service: EmailService,
    ) -> None:
        self._db = db
        self._users = UserRepository(db)
        self._roles = RoleRepository(db)
        self._tokens = token_service
        self._otp = otp_service
        self._email = email_service

    async def register(
        self,
        full_name: str,
        email: str,
        password: str,
        phone: str | None = None,
    ) -> RegisterResponse:
        email = email.lower().strip()
        if await self._users.email_exists(email):
            raise AlreadyExistsError("An account with this email address already exists.")

        password_hash = hash_password(password)
        user = await self._users.create(
            full_name=full_name,
            email=email,
            password_hash=password_hash,
            phone=phone,
            is_active=True,
            is_email_verified=False,
        )
        default_role = await self._roles.get_by_name("user")
        if default_role:
            await self._roles.assign_role_to_user(user, default_role)

        otp = await self._otp.generate_email_verification_otp(email)
        self._email.send_otp_email(to_email=email, full_name=full_name, otp=otp)

        await self._log_audit(user_id=str(user.id), action="auth.register", status="success")
        logger.info(f"New user registered: {email}")
        return RegisterResponse(user_id=user.id, email=email)

    async def verify_email(self, email: str, otp: str) -> None:
        email = email.lower().strip()
        user = await self._users.get_by_email(email)
        if user is None:
            raise AccountNotFoundError()
        await self._otp.verify_email_verification_otp(email=email, otp=otp)
        await self._users.mark_email_verified(user.id)
        self._email.send_welcome_email(to_email=user.email, full_name=user.full_name)
        await self._log_audit(user_id=str(user.id), action="auth.email_verified", status="success")

    async def resend_verification_otp(self, email: str) -> None:
        email = email.lower().strip()
        user = await self._users.get_by_email(email)
        if user is None or user.is_email_verified:
            return
        otp = await self._otp.generate_email_verification_otp(email)
        self._email.send_otp_email(to_email=email, full_name=user.full_name, otp=otp)

    async def login(
        self,
        email: str,
        password: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> LoginResponse:
        email = email.lower().strip()
        user = await self._users.get_by_email(email)

        if user is None or user.deleted_at is not None:
            raise InvalidCredentialsError()
        if not user.is_active:
            raise AccountInactiveError()
        if user.is_locked:
            raise AccountLockedError(
                f"Account locked. Try again after {user.locked_until.strftime('%H:%M UTC')}."
            )
        if not user.password_hash or not verify_password(password, user.password_hash):
            new_count = await self._users.increment_failed_attempts(user.id)
            await self._log_audit(
                user_id=str(user.id), action="auth.login_failed", status="failure",
                details={"reason": "bad_password", "attempts": new_count},
                ip_address=ip_address, user_agent=user_agent,
            )
            if new_count >= settings.MAX_FAILED_LOGIN_ATTEMPTS:
                lock_until = datetime.now(timezone.utc) + timedelta(
                    minutes=settings.ACCOUNT_LOCKOUT_MINUTES
                )
                await self._users.lock_account(user.id, lock_until)
                raise AccountLockedError(
                    f"Too many failed attempts. Account locked for "
                    f"{settings.ACCOUNT_LOCKOUT_MINUTES} minutes."
                )
            raise InvalidCredentialsError()

        if not user.is_email_verified:
            raise EmailNotVerifiedError()

        await self._users.reset_failed_attempts(user.id)
        primary_role = user.role_names[0] if user.role_names else "user"
        access_token, refresh_token, _, _ = await self._tokens.issue_token_pair(
            user_id=str(user.id), role=primary_role
        )
        now_str = datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC")
        self._email.send_login_notification_email(
            to_email=user.email,
            full_name=user.full_name,
            device="Desktop / Mobile Device",
            browser=user_agent or "Web Client",
            ip_address=ip_address or "127.0.0.1",
            timestamp_str=now_str,
        )
        await self._log_audit(
            user_id=str(user.id), action="auth.login", status="success",
            ip_address=ip_address, user_agent=user_agent,
        )
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_seconds,
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=primary_role,
            is_admin=user.is_admin,
        )

    async def google_login(
        self,
        id_token: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> LoginResponse:
        google_payload = await asyncio.to_thread(_verify_google_token_sync, id_token)

        if not google_payload.get("email_verified"):
            raise InvalidCredentialsError("Google email address is not verified.")

        google_id: str = google_payload["sub"]
        email: str = google_payload["email"].lower()
        full_name: str = google_payload.get("name", email.split("@")[0])
        avatar_url: str | None = google_payload.get("picture")

        user = await self._users.get_by_google_id(google_id)
        if user is None:
            user = await self._users.get_by_email(email)
            if user is not None:
                await self._users.update(
                    user.id,
                    google_id=google_id,
                    avatar_url=avatar_url,
                    full_name=full_name,
                    last_login_at=datetime.now(timezone.utc),
                )
            else:
                user = await self._users.create(
                    full_name=full_name,
                    email=email,
                    google_id=google_id,
                    avatar_url=avatar_url,
                    is_active=True,
                    is_email_verified=True,
                )
                default_role = await self._roles.get_by_name("user")
                if default_role:
                    await self._roles.assign_role_to_user(user, default_role)
        else:
            await self._users.update(
                user.id,
                avatar_url=avatar_url,
                full_name=full_name,
                last_login_at=datetime.now(timezone.utc),
            )

        if not user.is_active:
            raise AccountInactiveError()

        await self._users.reset_failed_attempts(user.id)
        user = await self._users.get_by_id_with_roles(user.id) or user
        primary_role = user.role_names[0] if user.role_names else "user"

        access_token, refresh_token, _, _ = await self._tokens.issue_token_pair(
            user_id=str(user.id), role=primary_role
        )
        await self._log_audit(
            user_id=str(user.id),
            action="auth.google_login",
            status="success",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_seconds,
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=primary_role,
            is_admin=user.is_admin,
        )

    async def logout(self, access_token: str, refresh_token: str, user_id: str) -> None:
        await self._tokens.revoke_access_token(access_token)
        await self._tokens.revoke_refresh_token_by_token(refresh_token)
        await self._log_audit(user_id=user_id, action="auth.logout", status="success")

    async def forgot_password(self, email: str) -> None:
        email = email.lower().strip()
        user = await self._users.get_by_email(email)
        if user is None or not user.is_active:
            return
        otp = await self._otp.generate_password_reset_otp(email)
        self._email.send_password_reset_email(to_email=email, full_name=user.full_name, otp=otp)

    async def reset_password(self, email: str, otp: str, new_password: str) -> None:
        email = email.lower().strip()
        user = await self._users.get_by_email(email)
        if user is None:
            raise AccountNotFoundError()
        await self._otp.verify_password_reset_otp(email=email, otp=otp)
        new_hash = hash_password(new_password)
        await self._users.update_password(user.id, new_hash)
        await self._tokens.revoke_all_user_tokens(str(user.id))
        await self._otp.consume_password_reset_otp(email)
        await self._log_audit(user_id=str(user.id), action="auth.password_reset", status="success")

    async def change_password(self, user: User, current_password: str, new_password: str) -> None:
        if not user.password_hash or not verify_password(current_password, user.password_hash):
            raise InvalidCredentialsError("Current password is incorrect.")
        new_hash = hash_password(new_password)
        await self._users.update_password(user.id, new_hash)
        await self._tokens.revoke_all_user_tokens(str(user.id))
        await self._log_audit(user_id=str(user.id), action="auth.password_changed", status="success")

    async def _log_audit(
        self, action: str, status: str, user_id: str | None = None,
        details: dict | None = None, ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        try:
            import uuid
            from app.models.activity import AuditLog
            entry = AuditLog(
                user_id=uuid.UUID(user_id) if user_id else None,
                action=action, resource="auth",
                ip_address=ip_address, user_agent=user_agent,
                details=details, status=status,
            )
            self._db.add(entry)
            await self._db.flush()
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Audit log write failed for action={action}: {exc}")


def _verify_google_token_sync(id_token_str: str) -> dict:
    """Verify Google ID token: signature, issuer, expiry AND audience (fail closed)."""
    import google.auth.transport.requests
    import google.oauth2.id_token

    audiences = []
    if settings.GOOGLE_CLIENT_ID:
        audiences.append(settings.GOOGLE_CLIENT_ID.strip())
    extra = getattr(settings, "GOOGLE_CLIENT_IDS", None)
    if extra:
        audiences += [a.strip() for a in extra if a and a.strip()]
    audiences = [a for a in audiences if a]

    # Security: never accept tokens when no client is configured (config error, not a
    # reason to skip audience validation).
    if not audiences:
        raise InvalidCredentialsError(
            "Google sign-in is disabled: GOOGLE_CLIENT_ID is not configured on the server."
        )

    try:
        transport_request = google.auth.transport.requests.Request()
        # Verify signature first; the audience is then enforced explicitly below.
        payload = google.oauth2.id_token.verify_oauth2_token(id_token_str, transport_request)

        iss = payload.get("iss")
        if iss not in ("accounts.google.com", "https://accounts.google.com"):
            raise ValueError("Invalid token issuer.")

        aud = payload.get("aud")
        azp = payload.get("azp")
        if aud not in audiences and azp not in audiences:
            raise ValueError(
                f"Token audience ({aud or 'none'}) does not match any configured Google client ID."
            )
        return payload
    except Exception as exc:
        logger.warning(f"Google ID token verification failed: {exc}")
        raise InvalidCredentialsError(f"Invalid or expired Google token: {exc}") from exc

