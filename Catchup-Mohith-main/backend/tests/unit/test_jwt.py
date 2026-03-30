# /home/mohith/Catchup-Mohith/backend/tests/unit/test_jwt.py
from uuid import uuid4

import pytest
from backend.app.core.config import settings
from backend.app.core.exceptions import (
    AuthenticationRequiredException,
    TokenExpiredException,
)
from backend.app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from jose import jwt


@pytest.mark.asyncio
async def test_create_access_token_contains_correct_claims():
    user_id = str(uuid4())
    token = create_access_token(user_id, token_version=0)
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    assert payload["sub"] == user_id
    assert payload["type"] == "access"
    assert payload["version"] == 0
    assert "jti" in payload
    assert "exp" in payload
    assert "iat" in payload


@pytest.mark.asyncio
async def test_create_refresh_token_has_7_day_expiry():
    user_id = str(uuid4())
    token = create_refresh_token(user_id, token_version=0)
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    assert payload["type"] == "refresh"
    duration = payload["exp"] - payload["iat"]
    assert abs(duration - 7 * 24 * 3600) < 60


@pytest.mark.asyncio
async def test_decode_token_returns_payload():
    user_id = str(uuid4())
    token = create_access_token(user_id, token_version=1)
    payload = decode_token(token)
    assert payload.sub == user_id
    assert payload.type == "access"
    assert payload.version == 1
    assert payload.jti is not None


@pytest.mark.asyncio
async def test_decode_expired_token_raises_token_expired():
    from datetime import datetime, timedelta, timezone
    from uuid import uuid4 as _uuid4

    now = datetime.now(timezone.utc)
    expired_payload = {
        "sub": str(_uuid4()),
        "jti": str(_uuid4()),
        "type": "access",
        "version": 0,
        "exp": int((now - timedelta(minutes=1)).timestamp()),
        "iat": int(now.timestamp()),
    }
    expired_token = jwt.encode(
        expired_payload,
        settings.secret_key,
        algorithm=settings.algorithm,
    )
    with pytest.raises(TokenExpiredException):
        decode_token(expired_token)


@pytest.mark.asyncio
async def test_decode_invalid_token_raises_authentication_required():
    with pytest.raises(AuthenticationRequiredException):
        decode_token("not.a.valid.token")


@pytest.mark.asyncio
async def test_token_contains_unique_jti_per_token():
    user_id = str(uuid4())
    token1 = create_access_token(user_id, 0)
    token2 = create_access_token(user_id, 0)
    p1 = decode_token(token1)
    p2 = decode_token(token2)
    assert p1.jti != p2.jti


def test_hash_password_produces_bcrypt_hash():
    from backend.app.core import security

    class _PwdContext:
        @staticmethod
        def hash(_plain):
            return "$2b$stub-hash"

    original = security.pwd_context
    security.pwd_context = _PwdContext()
    try:
        hashed = hash_password("mysecretpassword")
        assert hashed.startswith("$2b$")
    finally:
        security.pwd_context = original


def test_verify_password_returns_true_for_correct_password():
    from backend.app.core import security

    class _PwdContext:
        @staticmethod
        def verify(plain, hashed):
            return plain == "correctpassword" and hashed == "stub-hash"

    original = security.pwd_context
    security.pwd_context = _PwdContext()
    try:
        assert verify_password("correctpassword", "stub-hash") is True
    finally:
        security.pwd_context = original


def test_verify_password_returns_false_for_wrong_password():
    from backend.app.core import security

    class _PwdContext:
        @staticmethod
        def verify(plain, hashed):
            return plain == "correctpassword" and hashed == "stub-hash"

    original = security.pwd_context
    security.pwd_context = _PwdContext()
    try:
        assert verify_password("wrongpassword", "stub-hash") is False
    finally:
        security.pwd_context = original
