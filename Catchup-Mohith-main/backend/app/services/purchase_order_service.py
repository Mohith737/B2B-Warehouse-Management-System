# /home/mohith/Catchup-Mohith/backend/app/services/purchase_order_service.py
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.exceptions import (
    ConflictException,
    CreditLimitExceededException,
    InvalidStateTransitionException,
    NotFoundException,
    PageLimitExceededException,
    SupplierInactiveException,
)
from backend.app.models.po_line import POLine
from backend.app.models.purchase_order import POStatus, PurchaseOrder
from backend.app.models.user import UserRole
from backend.app.repositories.po_line_repository import POLineRepository
from backend.app.repositories.product_repository import ProductRepository
from backend.app.repositories.purchase_order_repository import PurchaseOrderRepository
from backend.app.repositories.supplier_repository import SupplierRepository
from backend.app.schemas.common import ListResponse, make_pagination_meta
from backend.app.schemas.purchase_order import (
    POCreate,
    POListParams,
    PORead,
    POUpdate,
    POLineRead,
)
from backend.app.services.po_number_service import PONumberService
from backend.app.services.po_state_machine import validate_transition


class PurchaseOrderService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.po_repo = PurchaseOrderRepository(session)
        self.po_line_repo = POLineRepository(session)
        self.supplier_repo = SupplierRepository(session)
        self.product_repo = ProductRepository(session)
        self.po_number_service = PONumberService(session)

    async def get_purchase_order(self, id: UUID) -> PORead:
        po = await self.po_repo.get_by_id_with_lines(id)
        if po is None:
            raise NotFoundException(message=f"Purchase order with id={id} not found")
        return self._to_read(po)

    async def list_purchase_orders(
        self,
        params: POListParams,
        current_user_id: UUID,
        current_user_role: UserRole,
    ) -> ListResponse[PORead]:
        if params.page_size > 50:
            raise PageLimitExceededException(
                details={"max": 50, "requested": params.page_size}
            )

        items, total = await self.po_repo.list_with_filters(
            current_user_id=current_user_id,
            current_user_role=current_user_role,
            status=params.status,
            supplier_id=params.supplier_id,
            created_by_me=params.created_by_me,
            skip=(params.page - 1) * params.page_size,
            limit=params.page_size,
        )
        return ListResponse(
            data=[self._to_read(item) for item in items],
            meta=make_pagination_meta(
                total=total,
                page=params.page,
                page_size=params.page_size,
            ),
        )

    async def create_purchase_order(self, data: POCreate, created_by: UUID) -> PORead:
        self._validate_distinct_products([line.product_id for line in data.lines])

        supplier = await self.supplier_repo.get_by_id(data.supplier_id)
        if supplier is None:
            raise NotFoundException(
                message=f"Supplier with id={data.supplier_id} not found"
            )
        if not supplier.is_active:
            raise SupplierInactiveException(
                details={"supplier_id": str(data.supplier_id)}
            )

        created_po_id: UUID | None = None
        for attempt in range(2):
            try:
                tx = (
                    self.session.begin_nested()
                    if self.session.in_transaction()
                    else self.session.begin()
                )
                async with tx:
                    po_number = await self.po_number_service.generate_next_po_number()
                    po = PurchaseOrder(
                        po_number=po_number,
                        supplier_id=data.supplier_id,
                        created_by=created_by,
                        status=POStatus.DRAFT.value,
                        notes=data.notes,
                        expected_delivery_date=data.expected_delivery_date,
                        total_amount=Decimal("0"),
                    )
                    created = await self.po_repo.create(po)
                    created_po_id = created.id

                    for line in data.lines:
                        await self._ensure_product_exists(line.product_id)
                        po_line = POLine(
                            po_id=created.id,
                            product_id=line.product_id,
                            quantity_ordered=line.quantity_ordered,
                            quantity_received=Decimal("0"),
                            unit_price=line.unit_price,
                            line_total=line.quantity_ordered * line.unit_price,
                        )
                        await self.po_line_repo.create(po_line)

                    await self._recalculate_total(created.id)
                break
            except IntegrityError as exc:
                if attempt == 0 and "po_number" in str(exc.orig).lower():
                    continue
                if "po_number" in str(exc.orig).lower():
                    raise ConflictException(
                        details={
                            "field": "po_number",
                            "message": "Failed to allocate unique PO number",
                        }
                    ) from exc
                raise ConflictException(
                    details={"message": "PO creation failed due to a conflict"}
                ) from exc

        assert created_po_id is not None
        created_po = await self.po_repo.get_by_id_with_lines(created_po_id)
        assert created_po is not None
        return self._to_read(created_po)

    async def update_purchase_order(self, id: UUID, data: POUpdate) -> PORead:
        self._validate_distinct_products([line.product_id for line in data.lines])

        async with self.session.begin():
            po = await self.po_repo.get_by_id_for_update(id)
            if po is None:
                raise NotFoundException(
                    message=f"Purchase order with id={id} not found"
                )

            if po.status != POStatus.DRAFT.value:
                raise InvalidStateTransitionException(
                    details={
                        "current_state": po.status,
                        "target_action": "update",
                        "message": "Only draft purchase orders can be updated",
                    }
                )

            po.notes = data.notes
            po.expected_delivery_date = data.expected_delivery_date
            await self.session.flush()

            await self.po_line_repo.delete_by_po_id(po.id)
            for line in data.lines:
                await self._ensure_product_exists(line.product_id)
                po_line = POLine(
                    po_id=po.id,
                    product_id=line.product_id,
                    quantity_ordered=line.quantity_ordered,
                    quantity_received=Decimal("0"),
                    unit_price=line.unit_price,
                    line_total=line.quantity_ordered * line.unit_price,
                )
                await self.po_line_repo.create(po_line)

            await self._recalculate_total(po.id)

        updated_po = await self.po_repo.get_by_id_with_lines(id)
        assert updated_po is not None
        return self._to_read(updated_po)

    async def submit_purchase_order(self, id: UUID) -> PORead:
        async with self.session.begin():
            po = await self.po_repo.get_by_id_for_update(id)
            if po is None:
                raise NotFoundException(
                    message=f"Purchase order with id={id} not found"
                )

            validate_transition(po.status, POStatus.SUBMITTED.value)

            supplier = await self.supplier_repo.get_by_id(po.supplier_id)
            if supplier is None:
                raise NotFoundException(
                    message=f"Supplier with id={po.supplier_id} not found"
                )
            if not supplier.is_active:
                raise SupplierInactiveException(
                    details={"supplier_id": str(po.supplier_id)}
                )

            current_exposure = (
                await self.po_repo.get_open_exposure_for_supplier_for_update(
                    supplier_id=po.supplier_id,
                    exclude_po_id=po.id,
                )
            )
            this_po_amount = Decimal(str(po.total_amount))
            total_exposure = current_exposure + this_po_amount
            credit_limit = Decimal(str(supplier.credit_limit))

            if total_exposure > credit_limit:
                gap = total_exposure - credit_limit
                raise CreditLimitExceededException(
                    details={
                        "credit_limit": str(credit_limit),
                        "current_exposure": str(current_exposure),
                        "this_po_amount": str(this_po_amount),
                        "gap": str(gap),
                    }
                )

            po.status = POStatus.SUBMITTED.value
            self._set_transition_timestamp(po, POStatus.SUBMITTED.value)
            await self.session.flush()

        submitted_po = await self.po_repo.get_by_id_with_lines(id)
        assert submitted_po is not None
        return self._to_read(submitted_po)

    async def acknowledge_purchase_order(self, id: UUID) -> PORead:
        return await self._transition(id, POStatus.ACKNOWLEDGED.value)

    async def mark_shipped_purchase_order(self, id: UUID) -> PORead:
        return await self._transition(id, POStatus.SHIPPED.value)

    async def cancel_purchase_order(self, id: UUID) -> PORead:
        return await self._transition(id, POStatus.CANCELLED.value)

    async def delete_purchase_order(self, id: UUID) -> None:
        async with self.session.begin():
            po = await self.po_repo.get_by_id_for_update(id)
            if po is None:
                raise NotFoundException(
                    message=f"Purchase order with id={id} not found"
                )
            if po.status != POStatus.DRAFT.value:
                raise InvalidStateTransitionException(
                    details={
                        "current_state": po.status,
                        "target_action": "delete",
                        "message": "Only draft purchase orders can be deleted",
                    }
                )
            await self.po_repo.soft_delete(po)

    async def _transition(self, id: UUID, target_status: str) -> PORead:
        async with self.session.begin():
            po = await self.po_repo.get_by_id_for_update(id)
            if po is None:
                raise NotFoundException(
                    message=f"Purchase order with id={id} not found"
                )
            validate_transition(po.status, target_status)
            po.status = target_status
            self._set_transition_timestamp(po, target_status)
            await self.session.flush()

        transitioned_po = await self.po_repo.get_by_id_with_lines(id)
        assert transitioned_po is not None
        return self._to_read(transitioned_po)

    async def _recalculate_total(self, po_id: UUID) -> None:
        lines = await self.po_line_repo.list_by_po_id(po_id)
        total = sum((Decimal(str(line.line_total)) for line in lines), Decimal("0"))
        po = await self.po_repo.get_by_id_for_update(po_id)
        if po is None:
            raise NotFoundException(message=f"Purchase order with id={po_id} not found")
        po.total_amount = total
        await self.session.flush()

    async def _ensure_product_exists(self, product_id: UUID) -> None:
        product = await self.product_repo.get_by_id(product_id)
        if product is None:
            raise NotFoundException(message=f"Product with id={product_id} not found")

    def _validate_distinct_products(self, product_ids: list[UUID]) -> None:
        if len(product_ids) != len(set(product_ids)):
            raise ConflictException(
                details={"field": "lines", "message": "Duplicate product in lines"}
            )

    def _set_transition_timestamp(self, po: PurchaseOrder, target_status: str) -> None:
        now = datetime.now(timezone.utc)
        if target_status == POStatus.SUBMITTED.value:
            po.submitted_at = now
        elif target_status == POStatus.ACKNOWLEDGED.value:
            po.acknowledged_at = now
        elif target_status == POStatus.SHIPPED.value:
            po.shipped_at = now
        elif target_status == POStatus.RECEIVED.value:
            po.received_at = now
        elif target_status == POStatus.CLOSED.value:
            po.closed_at = now
        elif target_status == POStatus.CANCELLED.value:
            po.cancelled_at = now

    def _to_read(self, po: PurchaseOrder) -> PORead:
        lines = [POLineRead.model_validate(line) for line in po.lines]
        return PORead(
            id=po.id,
            po_number=po.po_number,
            supplier_id=po.supplier_id,
            created_by=po.created_by,
            status=po.status,
            total_amount=po.total_amount,
            notes=po.notes,
            expected_delivery_date=po.expected_delivery_date,
            submitted_at=po.submitted_at,
            acknowledged_at=po.acknowledged_at,
            shipped_at=po.shipped_at,
            received_at=po.received_at,
            closed_at=po.closed_at,
            cancelled_at=po.cancelled_at,
            created_at=po.created_at,
            updated_at=po.updated_at,
            lines=lines,
        )
