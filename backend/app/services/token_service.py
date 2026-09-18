"""
Token service — manages JWT lifecycle using Redis.
Handles access token blacklisting and refresh token rotation.
"""

from loguru import logger
from redis.asyncio import Redis

from app.core.config import settings
from app.core.exceptions import ServiceUnavailableError, TokenBlacklistedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_token_remaining_seconds,
)

# ── Redis key prefixes ─────────────────────────────────────────────────────────
_PREFIX_REFRESH = "session:refresh"
_PREFIX_BLACKLIST = "session:blacklist"


class TokenService:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    # ── Issue ──────────────────────────────────────────────────────────────────

    async def issue_token_pair(
        self, user_id: str, role: str
    ) -> tuple[str, str, str, str]:
        """
        Create and persist a new access + refresh token pair.

        Returns:
            (access_token, refresh_token, access_jti, refresh_jti)
        """
        access_token, access_jti = create_access_token(subject=user_id, role=role)
        refresh_token, refresh_jti = create_refresh_token(subject=user_id)

        await self._store_refresh_token(user_id=user_id, jti=refresh_jti)

        return access_token, refresh_token, access_jti, refresh_jti

    # ── Refresh ────────────────────────────────────────────────────────────────

    async def rotate_refresh_token(
        self, refresh_token: str, role: str
    ) -> tuple[str, str]:
        """
        Validate a refresh token, revoke it, and issue a new pair.
        Implements refresh token rotation for improved security.

        Returns:
            (new_access_token, new_refresh_token)
        """
        payload = decode_token(refresh_token, expected_type="refresh")
        user_id: str = payload["sub"]
        old_jti: str = payload["jti"]

        if not await self._is_refresh_token_valid(user_id=user_id, jti=old_jti):
            # Token was already used or was explicitly revoked — possible replay attack
            logger.warning(
                f"Refresh token replay attempt detected for user {user_id}, jti={old_jti}"
            )
            # Revoke ALL user sessions as a security measure
            await self.revoke_all_user_tokens(user_id)
            raise TokenBlacklistedError(
                "Refresh token has been revoked. Please log in again."
            )

        # Revoke the old refresh token (one-time use)
        await self._revoke_refresh_token(user_id=user_id, jti=old_jti)

        # Issue new pair
        new_access, _, _, new_refresh_jti = await self.issue_token_pair(
            user_id=user_id, role=role
        )
        new_refresh, _ = create_refresh_token(subject=user_id)
        await self._store_refresh_token(user_id=user_id, jti=new_refresh_jti)

        return new_access, new_refresh

    # ── Revoke ─────────────────────────────────────────────────────────────────

    async def revoke_access_token(self, access_token: str) -> None:
        """
        Add an access token to the blacklist.
        TTL is set to the token's remaining lifetime so Redis auto-expires it.
        """
        remaining = get_token_remaining_seconds(access_token)
        if remaining <= 0:
            return  # already expired — nothing to blacklist

        try:
            payload = decode_token(access_token, expected_type="access")
            jti = payload["jti"]
            await self._redis.setex(
                f"{_PREFIX_BLACKLIST}:{jti}", remaining, "revoked"
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Could not blacklist access token: {exc}")

    async def revoke_refresh_token_by_token(self, refresh_token: str) -> None:
        """Decode a refresh token and delete it from Redis (logout)."""
        try:
            payload = decode_token(refresh_token, expected_type="refresh")
            await self._revoke_refresh_token(
                user_id=payload["sub"], jti=payload["jti"]
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Could not revoke refresh token: {exc}")

    async def revoke_all_user_tokens(self, user_id: str) -> int:
        """
        Revoke all active refresh tokens for a user.
        Used on password change, account suspension, and security incidents.
        Returns the number of tokens revoked.
        """
        count = 0
        try:
            pattern = f"{_PREFIX_REFRESH}:{user_id}:*"
            async for key in self._redis.scan_iter(pattern):
                await self._redis.delete(key)
                count += 1
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Failed to revoke all tokens for user {user_id}: {exc}")
        return count

    # ── Validation ─────────────────────────────────────────────────────────────

    async def is_access_token_blacklisted(self, jti: str) -> bool:
        """Return True if the access token has been explicitly revoked."""
        try:
            return await self._redis.exists(f"{_PREFIX_BLACKLIST}:{jti}") == 1
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Redis unavailable during blacklist check: {exc}")
            # Fail safe: reject the token if we can't verify it's valid
            raise ServiceUnavailableError(
                "Session store unavailable. Please try again."
            ) from exc

    # ── Private helpers ────────────────────────────────────────────────────────

    async def _store_refresh_token(self, user_id: str, jti: str) -> None:
        key = f"{_PREFIX_REFRESH}:{user_id}:{jti}"
        await self._redis.setex(
            key, settings.refresh_token_expire_seconds, "valid"
        )

    async def _is_refresh_token_valid(self, user_id: str, jti: str) -> bool:
        key = f"{_PREFIX_REFRESH}:{user_id}:{jti}"
        return await self._redis.exists(key) == 1

    async def _revoke_refresh_token(self, user_id: str, jti: str) -> None:
        key = f"{_PREFIX_REFRESH}:{user_id}:{jti}"
        await self._redis.delete(key)
