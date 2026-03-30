# /home/mohith/Catchup-Mohith/backend/app/core/security.py
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from backend.app.cache.service import cache_service
from backend.app.core.config import settings
from backend.app.core.exceptions import (
    AuthenticationRequiredException,
    TokenExpiredException,
)
from backend.app.schemas.auth import TokenPayload
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(
    user_id: str,
    token_version: int,
    role: str | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": user_id,
        "jti": str(uuid4()),
        "type": "access",
        "version": token_version,
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
    }
    if role is not None:
        payload["role"] = role
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(user_id: str, token_version: int) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.refresh_token_expire_days)
    payload = {
        "sub": user_id,
        "jti": str(uuid4()),
        "type": "refresh",
        "version": token_version,
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> TokenPayload:
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        return TokenPayload(**payload)
    except ExpiredSignatureError as exc:
        raise TokenExpiredException() from exc
    except JWTError as exc:
        raise AuthenticationRequiredException() from exc


async def blacklist_token(jti: str, exp: int) -> None:
    now = int(datetime.now(timezone.utc).timestamp())
    ttl = max(1, exp - now)
    await cache_service.set(
        f"stockbridge:blacklist:{jti}",
        "1",
        ttl=ttl,
        db=settings.redis_auth_db,
    )


async def is_blacklisted(jti: str) -> bool:
    result = await cache_service.get(
        f"stockbridge:blacklist:{jti}",
        db=settings.redis_auth_db,
    )
    return result is not None


async def get_user_version(user_id: str) -> int | None:
    result = await cache_service.get(
        f"stockbridge:user_version:{user_id}",
        db=settings.redis_auth_db,
    )
    return int(result) if result is not None else None


async def set_user_version(user_id: str, version: int) -> None:
    await cache_service.set(
        f"stockbridge:user_version:{user_id}",
        str(version),
        ttl=86400 * 30,
        db=settings.redis_auth_db,
    )


async def increment_user_version(user_id: str) -> None:
    result = await cache_service.increment(
        f"stockbridge:user_version:{user_id}",
        db=settings.redis_auth_db,
    )
    if result is None:
        import logging

        logging.getLogger(__name__).warning(
            "Could not increment user_version for "
            f"user_id={user_id}. Redis may be unavailable."
        )
