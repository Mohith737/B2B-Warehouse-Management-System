# /home/mohith/Catchup-Mohith/backend/app/routers/grns.py
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.dependencies import get_current_user, require_role
from backend.app.core.exceptions import PageLimitExceededException
from backend.app.db.session import get_db
from backend.app.models.user import User, UserRole
from backend.app.schemas.common import (
    ListResponse,
    SingleResponse,
    make_pagination_meta,
)
from backend.app.schemas.grn import GRNCreate, GRNLineCreate, GRNListParams, GRNRead
from backend.app.services.grn_service import GRNService

router = APIRouter()


@router.post(
    "/",
    response_model=SingleResponse[GRNRead],
    status_code=201,
    summary="Create GRN for a shipped purchase order",
)
async def create_grn(
    body: GRNCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SingleResponse[GRNRead]:
    service = GRNService()
    created = await service.create_grn(
        po_id=body.po_id,
        created_by=current_user.id,
        session=session,
    )
    return SingleResponse(data=created)


@router.post(
    "/{id}/lines",
    response_model=SingleResponse[GRNRead],
    status_code=201,
    summary="Add receipt line to GRN",
)
async def add_grn_line(
    id: UUID,
    body: GRNLineCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SingleResponse[GRNRead]:
    service = GRNService()
    updated = await service.add_line(grn_id=id, data=body, session=session)
    return SingleResponse(data=updated)


@router.post(
    "/{id}/complete",
    response_model=SingleResponse[GRNRead],
    summary="Complete GRN and apply stock ledger updates",
)
async def complete_grn(
    id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_role(
            UserRole.WAREHOUSE_STAFF,
            UserRole.PROCUREMENT_MANAGER,
            UserRole.ADMIN,
        )
    ),
) -> SingleResponse[GRNRead]:
    service = GRNService()
    completed = await service.complete_grn(grn_id=id, session=session)
    return SingleResponse(data=completed)


@router.get(
    "/",
    response_model=ListResponse[GRNRead],
    summary="List GRNs",
)
async def list_grns(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1),
    po_id: UUID | None = Query(default=None),
    status: str | None = Query(default=None),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ListResponse[GRNRead]:
    if page_size > 50:
        raise PageLimitExceededException(details={"max": 50, "requested": page_size})

    params = GRNListParams(
        page=page,
        page_size=page_size,
        po_id=po_id,
        status=status,
    )
    service = GRNService()
    items, total = await service.list_grns(params=params, session=session)
    return ListResponse(
        data=items,
        meta=make_pagination_meta(total=total, page=page, page_size=page_size),
    )


@router.get(
    "/{id}",
    response_model=SingleResponse[GRNRead],
    summary="Get GRN by ID",
)
async def get_grn(
    id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SingleResponse[GRNRead]:
    service = GRNService()
    grn = await service.get_grn(grn_id=id, session=session)
    return SingleResponse(data=grn)
