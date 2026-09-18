"""Integration tests for /api/v1/auth/* endpoints."""

import pytest
from httpx import AsyncClient

BASE = "/api/v1/auth"

# ── Registration ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestRegister:
    async def test_register_returns_201(self, client: AsyncClient):
        resp = await client.post(f"{BASE}/register", json={
            "full_name": "Priya Patel",
            "email": "priya@example.com",
            "password": "Priya@1234!",
        })
        assert resp.status_code == 201
        body = resp.json()
        assert body["success"] is True
        assert "user_id" in body["data"]
        assert body["data"]["email"] == "priya@example.com"

    async def test_duplicate_email_returns_409(self, client: AsyncClient):
        payload = {"full_name": "Dup User", "email": "dup@example.com", "password": "Dup@1234!"}
        await client.post(f"{BASE}/register", json=payload)
        resp = await client.post(f"{BASE}/register", json=payload)
        assert resp.status_code == 409

    async def test_weak_password_returns_422(self, client: AsyncClient):
        resp = await client.post(f"{BASE}/register", json={
            "full_name": "Weak Pass",
            "email": "weak@example.com",
            "password": "password",   # no uppercase, no special char
        })
        assert resp.status_code == 422

    async def test_invalid_email_returns_422(self, client: AsyncClient):
        resp = await client.post(f"{BASE}/register", json={
            "full_name": "Bad Email",
            "email": "not-an-email",
            "password": "Test@1234!",
        })
        assert resp.status_code == 422


# ── Login ──────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestLogin:
    async def test_login_verified_user_returns_200(
        self, client: AsyncClient, test_user, auth_headers
    ):
        resp = await client.post(f"{BASE}/login", json={
            "email": "test@example.com",
            "password": "Test@1234!",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert "access_token" in body["data"]
        assert "refresh_token" in body["data"]
        assert body["data"]["token_type"] == "bearer"

    async def test_wrong_password_returns_401(self, client: AsyncClient, test_user):
        resp = await client.post(f"{BASE}/login", json={
            "email": "test@example.com",
            "password": "Wrong@1234!",
        })
        assert resp.status_code == 401
        assert resp.json()["success"] is False

    async def test_nonexistent_email_returns_401(self, client: AsyncClient):
        resp = await client.post(f"{BASE}/login", json={
            "email": "ghost@example.com",
            "password": "Test@1234!",
        })
        assert resp.status_code == 401

    async def test_unverified_user_returns_401(self, client: AsyncClient, db_session):
        from app.models.user import User
        from app.core.security import hash_password

        unverified = User(
            email="unverified@example.com",
            full_name="Unverified User",
            password_hash=hash_password("Test@1234!"),
            is_active=True,
            is_email_verified=False,
        )
        db_session.add(unverified)
        await db_session.flush()

        resp = await client.post(f"{BASE}/login", json={
            "email": "unverified@example.com",
            "password": "Test@1234!",
        })
        assert resp.status_code == 401
        assert "verify" in resp.json()["message"].lower()


# ── OTP Verification ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestOTP:
    async def test_resend_otp_always_returns_200(self, client: AsyncClient):
        # Even for unknown email (prevents enumeration)
        resp = await client.post(f"{BASE}/resend-otp", json={"email": "nobody@example.com"})
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    async def test_invalid_otp_format_returns_422(self, client: AsyncClient):
        resp = await client.post(f"{BASE}/verify-otp", json={
            "email": "test@example.com",
            "otp": "abc",   # must be 6 digits
        })
        assert resp.status_code == 422


# ── Forgot / Reset Password ────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestPasswordReset:
    async def test_forgot_password_always_returns_200(self, client: AsyncClient):
        # Never reveals whether account exists
        resp = await client.post(f"{BASE}/forgot-password", json={
            "email": "anyone@example.com"
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is True


# ── Protected endpoints ────────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestProtectedEndpoints:
    async def test_get_me_without_token_returns_401(self, client: AsyncClient):
        resp = await client.get("/api/v1/users/me")
        assert resp.status_code == 401

    async def test_get_me_with_token_returns_profile(
        self, client: AsyncClient, test_user, auth_headers
    ):
        resp = await client.get("/api/v1/users/me", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["email"] == "test@example.com"
        assert body["data"]["full_name"] == "Test User"


# ── Health check ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestHealth:
    async def test_ping(self, client: AsyncClient):
        resp = await client.get("/api/v1/health/ping")
        assert resp.status_code == 200
        assert resp.json() == {"ping": "pong"}


# ── Google OAuth Login ─────────────────────────────────────────────────────────

from unittest.mock import patch

@pytest.mark.asyncio
class TestGoogleLogin:
    @patch("app.services.auth_service._verify_google_token_sync")
    async def test_google_login_new_user(self, mock_verify, client: AsyncClient, db_session):
        mock_verify.return_value = {
            "sub": "google-oauth-sub-12345",
            "email": "google-user@example.com",
            "email_verified": True,
            "name": "Google User",
            "picture": "http://example.com/avatar.jpg",
        }
        from app.core.config import settings
        original_client_id = settings.GOOGLE_CLIENT_ID
        settings.GOOGLE_CLIENT_ID = "mock-client-id"
        try:
            resp = await client.post("/api/v1/auth/google", json={"id_token": "valid-token"})
            assert resp.status_code == 200
            data = resp.json()["data"]
            assert data["email"] == "google-user@example.com"
            assert data["full_name"] == "Google User"
            assert "access_token" in data
        finally:
            settings.GOOGLE_CLIENT_ID = original_client_id

    @patch("app.services.auth_service._verify_google_token_sync")
    async def test_google_login_existing_user(self, mock_verify, client: AsyncClient, db_session):
        from app.models.user import User
        from app.models.role import Role
        
        role = Role(name="user", description="User", is_system=True)
        db_session.add(role)
        await db_session.flush()
        user = User(
            email="google-user@example.com",
            full_name="Google User",
            google_id="google-oauth-sub-12345",
            is_active=True,
            is_email_verified=True,
        )
        user.roles.append(role)
        db_session.add(user)
        await db_session.flush()

        mock_verify.return_value = {
            "sub": "google-oauth-sub-12345",
            "email": "google-user@example.com",
            "email_verified": True,
            "name": "Google User",
            "picture": "http://example.com/avatar.jpg",
        }
        from app.core.config import settings
        original_client_id = settings.GOOGLE_CLIENT_ID
        settings.GOOGLE_CLIENT_ID = "mock-client-id"
        try:
            resp = await client.post("/api/v1/auth/google", json={"id_token": "valid-token"})
            assert resp.status_code == 200
            data = resp.json()["data"]
            assert data["email"] == "google-user@example.com"
            assert "access_token" in data
        finally:
            settings.GOOGLE_CLIENT_ID = original_client_id

