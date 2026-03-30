# /home/mohith/Catchup-Mohith/backend/app/core/dependencies.py
from uuid import UUID

from backend.app.cache.service import CacheService, cache_service
from backend.app.core.exceptions import (
    AccountInactiveException,
    AuthenticationRequiredException,
    PermissionDeniedException,
    SessionInvalidatedException,
    TokenRevokedException,
)
from backend.app.core.security import decode_token, get_user_version, is_blacklisted
from backend.app.db.session import get_db
from backend.app.models.user import User, UserRole
from backend.app.repositories.user_repository import UserRepository
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_cache() -> CacheService:
    return cache_service


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache),
) -> User:
    payload = decode_token(token)

    if payload.type != "access":
        raise AuthenticationRequiredException(details={"reason": "not an access token"})

    if await is_blacklisted(payload.jti):
        raise TokenRevokedException()

    cached_version = await get_user_version(payload.sub)
    if cached_version is not None and cached_version != payload.version:
        raise SessionInvalidatedException()

    user_repo = UserRepository(session)
    user = await user_repo.get_active_by_id(UUID(payload.sub))
    if user is None:
        raise AccountInactiveException()

    if user.token_version != payload.version:
        raise SessionInvalidatedException()

    return user


def require_role(*roles: UserRole):
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise PermissionDeniedException(
                details={
                    "required_roles": [r.value for r in roles],
                    "user_role": current_user.role.value,
                }
            )
        return current_user

    return role_checker
