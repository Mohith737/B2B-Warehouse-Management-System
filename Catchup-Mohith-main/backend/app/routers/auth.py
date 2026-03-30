# /home/mohith/Catchup-Mohith/backend/app/routers/auth.py
from backend.app.core.dependencies import get_cache, get_current_user
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse
from backend.app.schemas.common import SingleResponse
from backend.app.services.auth_service import AuthService
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


def get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


@router.post(
    "/login",
    response_model=SingleResponse[TokenResponse],
    summary="Login with email and password",
)
async def login(
    body: LoginRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
    cache=Depends(get_cache),
) -> SingleResponse[TokenResponse]:
    ip = get_client_ip(request)
    service = AuthService(session=session, cache=cache)
    tokens = await service.login(
        email=body.email, password=body.password, ip_address=ip
    )
    return SingleResponse(data=tokens)


@router.post(
    "/refresh",
    response_model=SingleResponse[TokenResponse],
    summary="Refresh access token using refresh token",
)
async def refresh(
    body: RefreshRequest,
    session: AsyncSession = Depends(get_db),
    cache=Depends(get_cache),
) -> SingleResponse[TokenResponse]:
    service = AuthService(session=session, cache=cache)
    tokens = await service.refresh(refresh_token=body.refresh_token)
    return SingleResponse(data=tokens)


@router.post(
    "/logout",
    response_model=SingleResponse[dict],
    summary="Logout and blacklist both tokens",
)
async def logout(
    body: RefreshRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
    cache=Depends(get_cache),
    current_user: User = Depends(get_current_user),
) -> SingleResponse[dict]:
    auth_header = request.headers.get("Authorization", "")
    access_token_str = auth_header.removeprefix("Bearer ").strip()

    service = AuthService(session=session, cache=cache)
    await service.logout(
        access_token_str=access_token_str,
        refresh_token_str=body.refresh_token,
    )
    return SingleResponse(data={"message": "Logged out successfully"})
