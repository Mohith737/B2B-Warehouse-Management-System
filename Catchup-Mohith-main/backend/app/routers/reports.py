# backend/app/routers/reports.py
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.dependencies import get_current_user
from backend.app.core.exceptions import PermissionDeniedException
from backend.app.db.session import get_db
from backend.app.models.user import User, UserRole
from backend.app.services.report_service import ReportService

router = APIRouter()

_REPORT_ROLES = {UserRole.PROCUREMENT_MANAGER, UserRole.ADMIN}


def get_report_service() -> ReportService:
    return ReportService()


def _require_report_access(current_user: User) -> None:
    """Raise PermissionDeniedException if user is warehouse_staff."""
    if current_user.role not in _REPORT_ROLES:
        raise PermissionDeniedException(
            message="Staff cannot access report endpoints",
            details={"role": current_user.role.value},
        )


@router.get(
    "/suppliers/{supplier_id}",
    summary="Download supplier performance report as CSV",
    response_class=StreamingResponse,
)
async def get_supplier_report(
    supplier_id: UUID,
    months: int = Query(
        default=12,
        description="Number of months of history to include (1-36)",
    ),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    service: ReportService = Depends(get_report_service),
) -> StreamingResponse:
    _require_report_access(current_user)

    filename, buffer = await service.generate_supplier_report(
        supplier_id=supplier_id,
        months=months,
        session=session,
    )
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/monthly-tier-summary",
    summary="Download monthly tier summary report as CSV",
    response_class=StreamingResponse,
)
async def get_monthly_tier_summary(
    month: str = Query(
        description="Month to report on in YYYY-MM format",
    ),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    service: ReportService = Depends(get_report_service),
) -> StreamingResponse:
    _require_report_access(current_user)

    filename, buffer = await service.generate_monthly_summary(
        month_str=month,
        session=session,
    )
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
