"""Unit tests for app.core.security."""

import time
import uuid

import pytest

from app.core.exceptions import InvalidTokenError, TokenExpiredError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_token_remaining_seconds,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_is_not_plain_text(self):
        assert hash_password("MySecret@1") != "MySecret@1"

    def test_verify_correct_password(self):
        h = hash_password("Correct@1")
        assert verify_password("Correct@1", h) is True

    def test_reject_wrong_password(self):
        h = hash_password("Correct@1")
        assert verify_password("Wrong@1", h) is False

    def test_two_hashes_differ(self):
        # bcrypt uses a random salt — same plaintext → different hashes
        h1 = hash_password("Same@1234")
        h2 = hash_password("Same@1234")
        assert h1 != h2


class TestJWT:
    def test_access_token_returns_string_and_jti(self):
        token, jti = create_access_token(subject="user-1", role="user")
        assert isinstance(token, str) and len(token) > 20
        assert isinstance(jti, str) and len(jti) == 36  # UUID4

    def test_decode_valid_access_token(self):
        uid = str(uuid.uuid4())
        token, jti = create_access_token(subject=uid, role="admin")
        payload = decode_token(token, expected_type="access")
        assert payload["sub"] == uid
        assert payload["role"] == "admin"
        assert payload["jti"] == jti
        assert payload["type"] == "access"

    def test_refresh_token_type(self):
        token, _ = create_refresh_token(subject="user-1")
        payload = decode_token(token, expected_type="refresh")
        assert payload["type"] == "refresh"

    def test_wrong_type_raises_invalid_token(self):
        # Try to decode an access token as if it were a refresh token
        token, _ = create_access_token(subject="user-1", role="user")
        with pytest.raises(InvalidTokenError):
            decode_token(token, expected_type="refresh")

    def test_tampered_token_raises_invalid_token(self):
        token, _ = create_access_token(subject="user-1", role="user")
        tampered = token[:-10] + "TAMPERED!!"
        with pytest.raises(InvalidTokenError):
            decode_token(tampered)

    def test_get_remaining_seconds_positive(self):
        token, _ = create_access_token(subject="user-1", role="user")
        remaining = get_token_remaining_seconds(token)
        assert remaining > 0

    def test_extra_claims_are_included(self):
        token, _ = create_access_token(
            subject="user-1", role="user", extra_claims={"custom": "value"}
        )
        payload = decode_token(token)
        assert payload["custom"] == "value"
