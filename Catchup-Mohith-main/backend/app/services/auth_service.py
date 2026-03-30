# /home/mohith/Catchup-Mohith/backend/app/services/auth_service.py
import logging
from uuid import UUID

from backend.app.cache.service import CacheService
from backend.app.core.config import settings
from backend.app.core.exceptions import (
    AccountInactiveException,
    AuthenticationRequiredException,
    AuthRateLimitedException,
    InvalidCredentialsException,
    SessionInvalidatedException,
    TokenExpiredException,
    TokenRevokedException,
)
from backend.app.core.security import (
    blacklist_token,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_user_version,
    is_blacklisted,
    set_user_version,
    verify_password,
)
from backend.app.repositories.user_repository import UserRepository
from backend.app.schemas.auth import TokenResponse
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, session: AsyncSession, cache: CacheService):
        self.session = session
        self.cache = cache
        self.user_repo = UserRepository(session)

    async def login(self, email: str, password: str, ip_address: str) -> TokenResponse:
        rate_key = f"stockbridge:ratelimit:auth:{ip_address}"
        count_str = await self.cache.get(rate_key, db=settings.redis_auth_db)
        if count_str and int(count_str) >= settings.auth_rate_limit_attempts:
            raise AuthRateLimitedException(details={"ip": ip_address})

        user = await self.user_repo.get_by_email(email)
        if user is None:
            count = await self.cache.increment(rate_key, db=settings.redis_auth_db)
            if count == 1:
                await self.cache.set(
                    rate_key,
                    str(count),
                    ttl=settings.auth_rate_limit_window_seconds,
                    db=settings.redis_auth_db,
                )
            raise InvalidCredentialsException()

        if not verify_password(password, user.hashed_password):
            count = await self.cache.increment(rate_key, db=settings.redis_auth_db)
            if count == 1:
                await self.cache.set(
                    rate_key,
                    str(count),
                    ttl=settings.auth_rate_limit_window_seconds,
                    db=settings.redis_auth_db,
                )
            raise InvalidCredentialsException()

        if not user.is_active:
            raise AccountInactiveException()

        cached_version = await get_user_version(str(user.id))
        if cached_version is None:
            await set_user_version(str(user.id), user.token_version)

        access_token = create_access_token(
            str(user.id),
            user.token_version,
            user.role.value,
        )
        refresh_token = create_refresh_token(str(user.id), user.token_version)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def refresh(self, refresh_token: str) -> TokenResponse:
        payload = decode_token(refresh_token)

        if payload.type != "refresh":
            raise AuthenticationRequiredException(
                details={"reason": "not a refresh token"}
            )

        if await is_blacklisted(payload.jti):
            raise TokenRevokedException()

        user = await self.user_repo.get_active_by_id(UUID(payload.sub))
        if user is None:
            raise AccountInactiveException()

        cached_version = await get_user_version(str(user.id))
        if cached_version is not None and cached_version != payload.version:
            raise SessionInvalidatedException()

        if user.token_version != payload.version:
            raise SessionInvalidatedException()

        new_access = create_access_token(
            str(user.id),
            user.token_version,
            user.role.value,
        )
        return TokenResponse(
            access_token=new_access,
            refresh_token=refresh_token,
        )

    async def logout(self, access_token_str: str, refresh_token_str: str) -> None:
        for token_str in (access_token_str, refresh_token_str):
            try:
                payload = decode_token(token_str)
                await blacklist_token(payload.jti, payload.exp)
            except (
                AuthenticationRequiredException,
                TokenExpiredException,
                TokenRevokedException,
            ):
                logger.warning(
                    "Could not decode token during logout. "
                    "Token may already be expired or invalid."
                )
