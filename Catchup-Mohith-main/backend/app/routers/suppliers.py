# backend/app/routers/suppliers.py
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.dependencies import get_current_user, require_role
from backend.app.core.exceptions import PageLimitExceededException
from backend.app.db.session import get_db
from backend.app.models.user import User, UserRole
from backend.app.schemas.common import ListResponse, SingleResponse
from backend.app.schemas.supplier import (
    SupplierCreate,
    SupplierListParams,
    SupplierMetricsHistoryRead,
    SupplierRead,
    SupplierUpdate,
    TierLockRequest,
)
from backend.app.services.supplier_service import SupplierService

router = APIRouter()


@router.get(
    "/",
    response_model=ListResponse[SupplierRead],
    summary="List suppliers with optional filters",
)
async def list_suppliers(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1),
    search: str | None = Query(default=None),
    tier: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ListResponse[SupplierRead]:
    if page_size > 50:
        raise PageLimitExceededException(details={"max": 50, "requested": page_size})
    params = SupplierListParams(
        page=page,
        page_size=page_size,
        search=search,
        tier=tier,
        is_active=is_active,
    )
    service = SupplierService(session)
    return await service.list_suppliers(params)


@router.get(
    "/{id}",
    response_model=SingleResponse[SupplierRead],
    summary="Get supplier by ID",
)
async def get_supplier(
    id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SingleResponse[SupplierRead]:
    service = SupplierService(session)
    supplier = await service.get_supplier(id)
    return SingleResponse(data=supplier)


@router.get(
    "/{id}/metrics",
    response_model=SingleResponse[list[SupplierMetricsHistoryRead]],
    summary="Get last 12 months of metrics for supplier",
)
async def get_supplier_metrics(
    id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SingleResponse[list[SupplierMetricsHistoryRead]]:
    service = SupplierService(session)
    metrics = await service.get_metrics(id)
    return SingleResponse(data=metrics)


@router.post(
    "/",
    response_model=SingleResponse[SupplierRead],
    status_code=201,
    summary="Create a new supplier",
)
async def create_supplier(
    body: SupplierCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.PROCUREMENT_MANAGER, UserRole.ADMIN)
    ),
) -> SingleResponse[SupplierRead]:
    service = SupplierService(session)
    supplier = await service.create_supplier(body)
    return SingleResponse(data=supplier)


@router.put(
    "/{id}",
    response_model=SingleResponse[SupplierRead],
    summary="Update supplier details",
)
async def update_supplier(
    id: UUID,
    body: SupplierUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.PROCUREMENT_MANAGER, UserRole.ADMIN)
    ),
) -> SingleResponse[SupplierRead]:
    service = SupplierService(session)
    supplier = await service.update_supplier(id, body)
    return SingleResponse(data=supplier)


@router.delete(
    "/{id}",
    response_model=SingleResponse[dict],
    summary="Soft-delete a supplier — admin only",
)
async def delete_supplier(
    id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
) -> SingleResponse[dict]:
    service = SupplierService(session)
    await service.delete_supplier(id)
    return SingleResponse(data={"message": "Supplier deleted successfully"})


@router.post(
    "/{id}/deactivate",
    response_model=SingleResponse[SupplierRead],
    summary="Deactivate supplier — admin only",
)
async def deactivate_supplier(
    id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
) -> SingleResponse[SupplierRead]:
    service = SupplierService(session)
    supplier = await service.deactivate_supplier(id)
    return SingleResponse(data=supplier)


@router.post(
    "/{id}/activate",
    response_model=SingleResponse[SupplierRead],
    summary="Activate supplier — admin only",
)
async def activate_supplier(
    id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
) -> SingleResponse[SupplierRead]:
    service = SupplierService(session)
    supplier = await service.activate_supplier(id)
    return SingleResponse(data=supplier)


@router.put(
    "/{id}/tier-lock",
    response_model=SingleResponse[SupplierRead],
    summary="Set tier lock on supplier — admin only",
)
async def set_tier_lock(
    id: UUID,
    body: TierLockRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
) -> SingleResponse[SupplierRead]:
    service = SupplierService(session)
    supplier = await service.set_tier_lock(id, body.tier_locked)
    return SingleResponse(data=supplier)
