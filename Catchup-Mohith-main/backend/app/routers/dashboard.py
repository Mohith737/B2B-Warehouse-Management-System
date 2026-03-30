# backend/app/routers/dashboard.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.dependencies import get_current_user
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.schemas.common import (
    ListResponse,
    SingleResponse,
    make_pagination_meta,
)
from backend.app.schemas.dashboard import (
    DashboardAdminRead,
    DashboardManagerRead,
    DashboardStaffRead,
    LowStockProductRead,
    StockMovementSummary,
)
from backend.app.services.dashboard_service import DashboardService

router = APIRouter()


def get_dashboard_service() -> DashboardService:
    return DashboardService()


@router.get(
    "/",
    response_model=SingleResponse[
        DashboardStaffRead | DashboardManagerRead | DashboardAdminRead
    ],
    summary="Get role-specific dashboard metrics",
)
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    service: DashboardService = Depends(get_dashboard_service),
) -> SingleResponse[DashboardStaffRead | DashboardManagerRead | DashboardAdminRead]:
    data = await service.get_dashboard(
        user_id=current_user.id,
        role=current_user.role,
        session=session,
    )
    return SingleResponse(data=data)


@router.get(
    "/low-stock",
    response_model=ListResponse[LowStockProductRead],
    summary="Get products below reorder threshold (paginated)",
)
async def get_low_stock(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(
        default=20,
        ge=1,
        le=50,
        description="Number of results per page (max 50)",
    ),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    service: DashboardService = Depends(get_dashboard_service),
) -> ListResponse[LowStockProductRead]:
    return await service.get_low_stock(
        page=page,
        page_size=page_size,
        session=session,
    )


@router.get(
    "/recent-activity",
    response_model=ListResponse[StockMovementSummary],
    summary="Get recent stock ledger activity",
)
async def get_recent_activity(
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of entries to return (max 100)",
    ),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    service: DashboardService = Depends(get_dashboard_service),
) -> ListResponse[StockMovementSummary]:
    items = await service.get_recent_activity(
        user_id=current_user.id,
        role=current_user.role,
        limit=limit,
        session=session,
    )
    return ListResponse(
        data=items,
        meta=make_pagination_meta(
            total=len(items),
            page=1,
            page_size=limit,
        ),
    )
