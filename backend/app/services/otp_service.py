"""
OTP service — 6-digit one-time password lifecycle.
Supports: email verification, password reset.
Brute-force protected with per-email attempt counters.
"""

import random
import string

from loguru import logger
from redis.asyncio import Redis

from app.core.config import settings
from app.core.exceptions import InvalidOTPError, OTPExpiredError, OTPTooManyAttemptsError

# ── Redis key prefixes ─────────────────────────────────────────────────────────
_PREFIX_OTP = "session:otp"
_PREFIX_ATTEMPTS = "session:otp_attempts"

# OTP purpose namespaces — prevents a password-reset OTP from verifying an email
_PURPOSE_VERIFY = "verify"
_PURPOSE_RESET = "reset"


class OTPService:

    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    # ── Generate & Store ───────────────────────────────────────────────────────

    async def generate_email_verification_otp(self, email: str) -> str:
        """Generate and store an OTP for new account email verification."""
        return await self._create(email=email.lower(), purpose=_PURPOSE_VERIFY)

    async def generate_password_reset_otp(self, email: str) -> str:
        """Generate and store an OTP for password reset."""
        return await self._create(email=email.lower(), purpose=_PURPOSE_RESET)

    async def generate_phone_verification_otp(self, phone: str) -> str:
        """Generate and store an OTP for phone verification."""
        phone = phone.strip()
        otp = await self._create(email=phone, purpose="phone_verify")
        await self._send_sms_twilio(phone, otp)
        return otp

    async def verify_phone_verification_otp(self, phone: str, otp: str) -> None:
        """Verify phone OTP."""
        await self._verify(email=phone.strip(), otp=otp, purpose="phone_verify")

    async def _send_sms_twilio(self, phone: str, otp: str) -> None:
        """Send SMS via Twilio API if configured. OTPs are never logged in production."""
        if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN or not settings.TWILIO_PHONE_NUMBER:
            # Never log the OTP in production; local-dev only echo, gated behind a flag.
            if settings.ECHO_DEV_OTP and not settings.is_production:
                logger.info(f"[DEV SMS] To: {phone} | SMS OTP: {otp}")
            else:
                logger.info(f"[SMS unavailable] Would send verification code to {phone} (no SMS gateway).")
            return
        import asyncio
        def _send_sync():
            try:
                from twilio.rest import Client
                client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                client.messages.create(
                    body=f"Your OneGov AI verification code is: {otp}. Valid for {settings.OTP_EXPIRE_MINUTES} minutes.",
                    from_=settings.TWILIO_PHONE_NUMBER,
                    to=phone,
                )
                logger.info(f"SMS OTP sent to {phone} via Twilio.")
            except Exception as exc:  # noqa: BLE001
                logger.error(f"Failed to send SMS to {phone}: {exc}")
        await asyncio.to_thread(_send_sync)

    # ── Verify ─────────────────────────────────────────────────────────────────

    async def verify_email_verification_otp(self, email: str, otp: str) -> None:
        """
        Verify an email-verification OTP.
        Raises on failure, returns None on success and consumes the OTP.
        """
        await self._verify(email=email.lower(), otp=otp, purpose=_PURPOSE_VERIFY)

    async def verify_password_reset_otp(self, email: str, otp: str) -> None:
        """
        Verify a password-reset OTP.
        Does NOT consume it — the caller must call consume_password_reset_otp
        after the password has been successfully changed.
        """
        await self._verify(email=email.lower(), otp=otp, purpose=_PURPOSE_RESET)

    async def consume_password_reset_otp(self, email: str) -> None:
        """Explicitly delete a password-reset OTP after successful reset."""
        await self._delete(email=email.lower(), purpose=_PURPOSE_RESET)

    # ── Private helpers ────────────────────────────────────────────────────────

    async def _create(self, email: str, purpose: str) -> str:
        otp = self._generate_code()
        key = self._otp_key(email, purpose)
        attempts_key = self._attempts_key(email, purpose)

        ttl_seconds = settings.OTP_EXPIRE_MINUTES * 60
        await self._redis.setex(key, ttl_seconds, otp)
        # Reset attempt counter whenever a fresh OTP is issued
        await self._redis.delete(attempts_key)

        logger.debug(f"OTP issued for {email} [{purpose}]")
        return otp

    async def _verify(self, email: str, otp: str, purpose: str) -> None:
        attempts_key = self._attempts_key(email, purpose)

        # Increment attempt counter BEFORE checking the OTP
        # so a correct guess still counts against the limit on the next attempt
        attempts: int = await self._redis.incr(attempts_key)
        if attempts == 1:
            # Set expiry on attempts key slightly longer than OTP lifetime
            await self._redis.expire(
                attempts_key, settings.OTP_EXPIRE_MINUTES * 60 + 300
            )

        if attempts > settings.OTP_MAX_ATTEMPTS:
            raise OTPTooManyAttemptsError(
                f"Too many OTP attempts. Please request a new code."
            )

        stored_key = self._otp_key(email, purpose)
        stored_otp = await self._redis.get(stored_key)

        if stored_otp is None:
            raise OTPExpiredError("OTP has expired. Please request a new one.")

        if stored_otp != otp:
            raise InvalidOTPError("Invalid OTP. Please check and try again.")

        # Valid — consume immediately (one-time use)
        await self._delete(email, purpose)
        await self._redis.delete(attempts_key)
        logger.debug(f"OTP verified for {email} [{purpose}]")

    async def _delete(self, email: str, purpose: str) -> None:
        await self._redis.delete(self._otp_key(email, purpose))

    @staticmethod
    def _generate_code() -> str:
        return "".join(
            random.SystemRandom().choices(string.digits, k=settings.OTP_LENGTH)
        )

    @staticmethod
    def _otp_key(email: str, purpose: str) -> str:
        return f"{_PREFIX_OTP}:{purpose}:{email}"

    @staticmethod
    def _attempts_key(email: str, purpose: str) -> str:
        return f"{_PREFIX_ATTEMPTS}:{purpose}:{email}"
