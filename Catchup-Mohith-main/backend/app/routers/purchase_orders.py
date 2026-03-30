# /home/mohith/Catchup-Mohith/backend/app/routers/purchase_orders.py
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.dependencies import get_current_user, require_role
from backend.app.core.exceptions import PageLimitExceededException
from backend.app.db.session import get_db
from backend.app.models.user import User, UserRole
from backend.app.schemas.common import ListResponse, SingleResponse
from backend.app.schemas.purchase_order import POCreate, POListParams, PORead, POUpdate
from backend.app.services.purchase_order_service import PurchaseOrderService

router = APIRouter()

POStatus = Literal[
    "draft",
    "submitted",
    "acknowledged",
    "shipped",
    "received",
    "closed",
    "cancelled",
]


@router.get(
    "/",
    response_model=ListResponse[PORead],
    summary="List purchase orders",
)
async def list_purchase_orders(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1),
    status: POStatus | None = Query(default=None),
    supplier_id: UUID | None = Query(default=None),
    created_by_me: bool = Query(default=False),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ListResponse[PORead]:
    if page_size > 50:
        raise PageLimitExceededException(details={"max": 50, "requested": page_size})

    params = POListParams(
        page=page,
        page_size=page_size,
        status=status,
        supplier_id=supplier_id,
        created_by_me=created_by_me,
    )
    service = PurchaseOrderService(session)
    return await service.list_purchase_orders(
        params=params,
        current_user_id=current_user.id,
        current_user_role=current_user.role,
    )


@router.get(
    "/{id}",
    response_model=SingleResponse[PORead],
    summary="Get purchase order by ID",
)
async def get_purchase_order(
    id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SingleResponse[PORead]:
    service = PurchaseOrderService(session)
    po = await service.get_purchase_order(id)
    return SingleResponse(data=po)


@router.post(
    "/",
    response_model=SingleResponse[PORead],
    status_code=201,
    summary="Create purchase order",
)
async def create_purchase_order(
    body: POCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.PROCUREMENT_MANAGER, UserRole.ADMIN)
    ),
) -> SingleResponse[PORead]:
    service = PurchaseOrderService(session)
    po = await service.create_purchase_order(body, created_by=current_user.id)
    return SingleResponse(data=po)


@router.put(
    "/{id}",
    response_model=SingleResponse[PORead],
    summary="Update draft purchase order",
)
async def update_purchase_order(
    id: UUID,
    body: POUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.PROCUREMENT_MANAGER, UserRole.ADMIN)
    ),
) -> SingleResponse[PORead]:
    service = PurchaseOrderService(session)
    po = await service.update_purchase_order(id, body)
    return SingleResponse(data=po)


@router.post(
    "/{id}/submit",
    response_model=SingleResponse[PORead],
    summary="Submit draft purchase order",
)
async def submit_purchase_order(
    id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.PROCUREMENT_MANAGER, UserRole.ADMIN)
    ),
) -> SingleResponse[PORead]:
    service = PurchaseOrderService(session)
    po = await service.submit_purchase_order(id)
    return SingleResponse(data=po)


@router.post(
    "/{id}/acknowledge",
    response_model=SingleResponse[PORead],
    summary="Acknowledge submitted purchase order",
)
async def acknowledge_purchase_order(
    id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.PROCUREMENT_MANAGER, UserRole.ADMIN)
    ),
) -> SingleResponse[PORead]:
    service = PurchaseOrderService(session)
    po = await service.acknowledge_purchase_order(id)
    return SingleResponse(data=po)


@router.post(
    "/{id}/mark-shipped",
    response_model=SingleResponse[PORead],
    summary="Mark acknowledged purchase order as shipped",
)
async def mark_shipped_purchase_order(
    id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.PROCUREMENT_MANAGER, UserRole.ADMIN)
    ),
) -> SingleResponse[PORead]:
    service = PurchaseOrderService(session)
    po = await service.mark_shipped_purchase_order(id)
    return SingleResponse(data=po)


@router.post(
    "/{id}/cancel",
    response_model=SingleResponse[PORead],
    summary="Cancel purchase order",
)
async def cancel_purchase_order(
    id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.PROCUREMENT_MANAGER, UserRole.ADMIN)
    ),
) -> SingleResponse[PORead]:
    service = PurchaseOrderService(session)
    po = await service.cancel_purchase_order(id)
    return SingleResponse(data=po)


@router.delete(
    "/{id}",
    response_model=SingleResponse[dict],
    summary="Soft-delete draft purchase order",
)
async def delete_purchase_order(
    id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
) -> SingleResponse[dict]:
    service = PurchaseOrderService(session)
    await service.delete_purchase_order(id)
    return SingleResponse(data={"message": "Purchase order deleted successfully"})
