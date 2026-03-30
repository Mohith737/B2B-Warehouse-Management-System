# backend/app/services/grn_service.py
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.exceptions import (
    BarcodeMismatchException,
    ConflictException,
    InvalidStateTransitionException,
    NotFoundException,
    OverReceiptException,
)
from backend.app.models.backorder import Backorder
from backend.app.models.grn import GRN, GRNStatus
from backend.app.models.grn_line import GRNLine
from backend.app.models.purchase_order import POStatus
from backend.app.repositories.backorder_repository import BackorderRepository
from backend.app.repositories.grn_line_repository import GRNLineRepository
from backend.app.repositories.grn_repository import GRNRepository
from backend.app.repositories.po_line_repository import POLineRepository
from backend.app.repositories.product_repository import ProductRepository
from backend.app.repositories.purchase_order_repository import PurchaseOrderRepository
from backend.app.schemas.grn import GRNLineCreate, GRNListParams, GRNRead
from backend.app.services.stock_ledger_service import StockLedgerService


class GRNService:
    def __init__(self):
        self.stock_ledger_service = StockLedgerService()

    async def create_grn(
        self,
        po_id: UUID,
        created_by: UUID,
        session: AsyncSession,
    ) -> GRNRead:
        po_repo = PurchaseOrderRepository(session)
        grn_repo = GRNRepository(session)

        po = await po_repo.get_by_id_for_update(po_id)
        if po is None:
            raise NotFoundException(message=f"Purchase order with id={po_id} not found")

        if po.status != POStatus.SHIPPED.value:
            raise InvalidStateTransitionException(
                details={
                    "current_state": po.status,
                    "required_state": POStatus.SHIPPED.value,
                }
            )

        tx = session.begin_nested() if session.in_transaction() else session.begin()
        async with tx:
            created = await grn_repo.create(
                GRN(
                    po_id=po_id,
                    status=GRNStatus.OPEN.value,
                    auto_reorder_triggered=False,
                    created_by=created_by,
                )
            )

        setattr(created, "lines", [])
        return GRNRead.model_validate(created)

    async def add_line(
        self,
        grn_id: UUID,
        data: GRNLineCreate,
        session: AsyncSession,
    ) -> GRNRead:
        grn_repo = GRNRepository(session)
        grn_line_repo = GRNLineRepository(session)
        po_line_repo = POLineRepository(session)
        product_repo = ProductRepository(session)

        grn = await grn_repo.get_by_id_with_lines(grn_id)
        if grn is None:
            raise NotFoundException(message=f"GRN with id={grn_id} not found")

        if grn.status != GRNStatus.OPEN.value:
            raise InvalidStateTransitionException(
                details={
                    "current_state": grn.status,
                    "required_state": GRNStatus.OPEN.value,
                }
            )

        duplicate = await grn_line_repo.get_by_grn_and_product(grn_id, data.product_id)
        if duplicate is not None:
            raise ConflictException(
                details={
                    "field": "product_id",
                    "value": str(data.product_id),
                    "message": "Duplicate product in GRN",
                }
            )

        po_line = await po_line_repo.get_by_po_id_product_id(grn.po_id, data.product_id)
        if po_line is None:
            raise NotFoundException(
                message=(
                    f"Product id={data.product_id} not found on "
                    f"purchase order id={grn.po_id}"
                )
            )

        if data.barcode_scanned:
            scanned_product = await product_repo.get_by_barcode(data.barcode_scanned)
            if scanned_product is None:
                raise NotFoundException(
                    message=f"Barcode {data.barcode_scanned} not found"
                )
            if scanned_product.id != po_line.product_id:
                raise BarcodeMismatchException(
                    details={
                        "barcode": data.barcode_scanned,
                        "expected_product_id": str(po_line.product_id),
                        "scanned_product_id": str(scanned_product.id),
                    }
                )

        already_received = await grn_line_repo.get_total_received_for_po_line(
            po_line.id
        )
        remaining_quantity = Decimal(str(po_line.quantity_ordered)) - Decimal(
            str(already_received)
        )
        requested_quantity = Decimal(str(data.quantity_received))

        if requested_quantity > remaining_quantity:
            raise OverReceiptException(
                details={
                    "po_line_id": str(po_line.id),
                    "remaining_quantity": str(remaining_quantity),
                    "requested_quantity": str(requested_quantity),
                }
            )

        tx = session.begin_nested() if session.in_transaction() else session.begin()
        async with tx:
            await grn_line_repo.create(
                GRNLine(
                    grn_id=grn_id,
                    product_id=data.product_id,
                    quantity_received=requested_quantity,
                    unit_cost=Decimal(str(data.unit_cost)),
                    barcode_scanned=data.barcode_scanned,
                )
            )

        updated = await grn_repo.get_by_id_with_lines(grn_id)
        if updated is None:
            raise NotFoundException(message=f"GRN with id={grn_id} not found")
        return GRNRead.model_validate(updated)

    async def complete_grn(self, grn_id: UUID, session: AsyncSession) -> GRNRead:
        grn_repo = GRNRepository(session)
        grn_line_repo = GRNLineRepository(session)
        po_repo = PurchaseOrderRepository(session)
        po_line_repo = POLineRepository(session)
        product_repo = ProductRepository(session)
        backorder_repo = BackorderRepository(session)

        tx = session.begin_nested() if session.in_transaction() else session.begin()
        async with tx:
            grn = await grn_repo.get_by_id_with_lines(grn_id)
            if grn is None:
                raise NotFoundException(message=f"GRN with id={grn_id} not found")

            if grn.status != GRNStatus.OPEN.value:
                raise InvalidStateTransitionException(
                    details={
                        "current_state": grn.status,
                        "required_state": GRNStatus.OPEN.value,
                    }
                )

            po = await po_repo.get_by_id_for_update(grn.po_id)
            if po is None:
                raise NotFoundException(
                    message=f"Purchase order with id={grn.po_id} not found"
                )

            grn_lines = await grn_line_repo.get_lines_for_grn(grn_id)
            if not grn_lines:
                raise ConflictException(
                    details={"message": "Cannot complete GRN with no lines"}
                )

            for line in grn_lines:
                await self.stock_ledger_service.add_entry(
                    session=session,
                    product_id=line.product_id,
                    quantity_change=Decimal(str(line.quantity_received)),
                    change_type="grn_receipt",
                    reference_id=grn.id,
                    notes=f"GRN {grn.id} receipt",
                )

            po_lines = await po_line_repo.list_by_po_id(po.id)
            all_fully_received = True

            for po_line in po_lines:
                total_received = await grn_line_repo.get_total_received_for_po_line(
                    po_line.id
                )
                ordered = Decimal(str(po_line.quantity_ordered))
                received = Decimal(str(total_received))

                if received < ordered:
                    all_fully_received = False
                    outstanding = ordered - received
                    await backorder_repo.create_backorder(
                        Backorder(
                            original_po_id=po.id,
                            product_id=po_line.product_id,
                            quantity_ordered=ordered,
                            quantity_received=received,
                            quantity_outstanding=outstanding,
                            status="open",
                            grn_id=grn.id,
                        )
                    )

            if all_fully_received:
                po.status = POStatus.RECEIVED.value
                po.received_at = datetime.now(timezone.utc)

            auto_reorder = False
            for line in grn_lines:
                product = await product_repo.get_by_id(line.product_id)
                if product is None:
                    raise NotFoundException(
                        message=f"Product with id={line.product_id} not found"
                    )

                threshold = (
                    Decimal(str(product.low_stock_threshold_override))
                    if product.low_stock_threshold_override is not None
                    and Decimal(str(product.low_stock_threshold_override)) > 0
                    else Decimal(str(product.reorder_point))
                )
                if Decimal(str(product.current_stock)) <= threshold:
                    auto_reorder = True
                    break

            grn.auto_reorder_triggered = auto_reorder
            grn.status = GRNStatus.COMPLETED.value
            grn.completed_at = datetime.now(timezone.utc)
            await session.flush()

        completed = await grn_repo.get_by_id_with_lines(grn_id)
        if completed is None:
            raise NotFoundException(message=f"GRN with id={grn_id} not found")
        return GRNRead.model_validate(completed)

    async def get_grn(self, grn_id: UUID, session: AsyncSession) -> GRNRead:
        grn_repo = GRNRepository(session)
        grn = await grn_repo.get_by_id_with_lines(grn_id)
        if grn is None:
            raise NotFoundException(message=f"GRN with id={grn_id} not found")
        return GRNRead.model_validate(grn)

    async def list_grns(
        self,
        params: GRNListParams,
        session: AsyncSession,
    ) -> tuple[list[GRNRead], int]:
        grn_repo = GRNRepository(session)
        skip = (params.page - 1) * params.page_size
        grns, total = await grn_repo.list_with_filters(
            po_id=params.po_id,
            status=params.status,
            skip=skip,
            limit=params.page_size,
        )

        items: list[GRNRead] = []
        for grn in grns:
            grn_with_lines = await grn_repo.get_by_id_with_lines(grn.id)
            if grn_with_lines is None:
                raise NotFoundException(message=f"GRN with id={grn.id} not found")
            items.append(GRNRead.model_validate(grn_with_lines))

        return items, total
