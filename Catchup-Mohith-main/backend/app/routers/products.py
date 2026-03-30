# /home/mohith/Catchup-Mohith/backend/app/routers/products.py
from uuid import UUID

from backend.app.core.dependencies import get_current_user, require_role
from backend.app.core.exceptions import PageLimitExceededException
from backend.app.db.session import get_db
from backend.app.models.user import User, UserRole
from backend.app.schemas.common import ListResponse, SingleResponse
from backend.app.schemas.product import (
    ProductCreate,
    ProductListParams,
    ProductRead,
    ProductUpdate,
    StockBadge,
)
from backend.app.services.product_service import ProductService
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get(
    "/barcode-lookup",
    response_model=SingleResponse[ProductRead],
    summary="Look up product by barcode",
)
async def barcode_lookup(
    barcode: str = Query(..., min_length=1),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SingleResponse[ProductRead]:
    service = ProductService(session)
    product = await service.barcode_lookup(barcode)
    return SingleResponse(data=product)


@router.get(
    "/",
    response_model=ListResponse[ProductRead],
    summary="List products with optional filters",
)
async def list_products(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1),
    search: str | None = Query(default=None),
    badge: StockBadge | None = Query(default=None),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ListResponse[ProductRead]:
    if page_size > 100:
        raise PageLimitExceededException(details={"max": 100, "requested": page_size})
    params = ProductListParams(
        page=page,
        page_size=page_size,
        search=search,
        badge=badge,
    )
    service = ProductService(session)
    return await service.list_products(params)


@router.get(
    "/{id}",
    response_model=SingleResponse[ProductRead],
    summary="Get product by ID",
)
async def get_product(
    id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SingleResponse[ProductRead]:
    service = ProductService(session)
    product = await service.get_product(id)
    return SingleResponse(data=product)


@router.post(
    "/",
    response_model=SingleResponse[ProductRead],
    status_code=201,
    summary="Create a new product",
)
async def create_product(
    body: ProductCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.PROCUREMENT_MANAGER, UserRole.ADMIN)
    ),
) -> SingleResponse[ProductRead]:
    service = ProductService(session)
    product = await service.create_product(body)
    return SingleResponse(data=product)


@router.put(
    "/{id}",
    response_model=SingleResponse[ProductRead],
    summary="Update product — requires current version for optimistic locking",
)
async def update_product(
    id: UUID,
    body: ProductUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.PROCUREMENT_MANAGER, UserRole.ADMIN)
    ),
) -> SingleResponse[ProductRead]:
    service = ProductService(session)
    product = await service.update_product(id, body)
    return SingleResponse(data=product)


@router.delete(
    "/{id}",
    response_model=SingleResponse[dict],
    summary="Soft-delete a product — admin only",
)
async def delete_product(
    id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
) -> SingleResponse[dict]:
    service = ProductService(session)
    await service.delete_product(id)
    return SingleResponse(data={"message": "Product deleted successfully"})
