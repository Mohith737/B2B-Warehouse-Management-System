# /home/mohith/Catchup-Mohith/backend/app/repositories/purchase_order_repository.py
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.purchase_order import PurchaseOrder
from backend.app.models.user import UserRole
from backend.app.repositories.base_repository import BaseRepository


class PurchaseOrderRepository(BaseRepository[PurchaseOrder]):
    def __init__(self, session: AsyncSession):
        super().__init__(PurchaseOrder, session)

    async def get_by_po_number(self, po_number: str) -> PurchaseOrder | None:
        result = await self.session.execute(
            select(PurchaseOrder)
            .where(PurchaseOrder.po_number == po_number)
            .where(PurchaseOrder.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_lines(self, id: UUID) -> PurchaseOrder | None:
        result = await self.session.execute(
            select(PurchaseOrder)
            .options(selectinload(PurchaseOrder.lines))
            .where(PurchaseOrder.id == id)
            .where(PurchaseOrder.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_by_id_for_update(self, id: UUID) -> PurchaseOrder | None:
        result = await self.session.execute(
            select(PurchaseOrder)
            .where(PurchaseOrder.id == id)
            .where(PurchaseOrder.deleted_at.is_(None))
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def list_with_filters(
        self,
        current_user_id: UUID,
        current_user_role: UserRole,
        status: str | None = None,
        supplier_id: UUID | None = None,
        created_by_me: bool = False,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[PurchaseOrder], int]:
        base_query = (
            select(PurchaseOrder)
            .options(selectinload(PurchaseOrder.lines))
            .where(PurchaseOrder.deleted_at.is_(None))
        )

        if current_user_role == UserRole.WAREHOUSE_STAFF:
            base_query = base_query.where(PurchaseOrder.created_by == current_user_id)
        elif created_by_me:
            base_query = base_query.where(PurchaseOrder.created_by == current_user_id)

        if status is not None:
            base_query = base_query.where(PurchaseOrder.status == status)

        if supplier_id is not None:
            base_query = base_query.where(PurchaseOrder.supplier_id == supplier_id)

        count_query = select(func.count()).select_from(base_query.subquery())
        total = (await self.session.execute(count_query)).scalar_one()

        data_query = (
            base_query.order_by(PurchaseOrder.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        items = list((await self.session.execute(data_query)).scalars().all())
        return items, total

    async def get_open_exposure_for_supplier_for_update(
        self,
        supplier_id: UUID,
        exclude_po_id: UUID,
    ) -> Decimal:
        result = await self.session.execute(
            select(func.coalesce(func.sum(PurchaseOrder.total_amount), 0))
            .where(PurchaseOrder.supplier_id == supplier_id)
            .where(PurchaseOrder.id != exclude_po_id)
            .where(PurchaseOrder.deleted_at.is_(None))
            .where(PurchaseOrder.status.in_(["submitted", "acknowledged", "shipped"]))
            .with_for_update()
        )
        value = result.scalar_one()
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value))
