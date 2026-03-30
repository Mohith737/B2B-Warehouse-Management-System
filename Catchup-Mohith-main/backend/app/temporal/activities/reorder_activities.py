# backend/app/temporal/activities/reorder_activities.py
import logging
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, select
from temporalio import activity

from backend.app.db.session import AsyncSessionLocal
from backend.app.models.po_line import POLine
from backend.app.models.product import Product
from backend.app.models.purchase_order import POStatus, PurchaseOrder
from backend.app.models.supplier import Supplier
from backend.app.models.user import User, UserRole
from backend.app.services.po_number_service import generate_auto_po_number
from backend.app.temporal.activities.email_activities import send_email

logger = logging.getLogger(__name__)

# Populated by worker.py at startup — UUID of the seeded admin user.
SYSTEM_ADMIN_UUID: UUID | None = None


@activity.defn
async def get_reorder_eligible_products() -> list[str]:
    """
    Return UUIDs (as strings) of products eligible for auto-reorder.

    Eligibility criteria:
    - auto_reorder_enabled = true
    - preferred_supplier_id is not null
    - current_stock <= COALESCE(low_stock_threshold_override, reorder_point)
    - No existing submitted auto-generated PO for this product

    Idempotent: running twice returns the same set.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Product).where(
                and_(
                    Product.auto_reorder_enabled.is_(True),
                    Product.preferred_supplier_id.is_not(None),
                    Product.deleted_at.is_(None),
                )
            )
        )
        candidates = list(result.scalars().all())

        threshold_eligible = [
            p
            for p in candidates
            if p.current_stock
            <= (
                p.low_stock_threshold_override
                if p.low_stock_threshold_override
                else p.reorder_point
            )
        ]

        if not threshold_eligible:
            return []

        eligible_ids: list[str] = []
        for product in threshold_eligible:
            if product.preferred_supplier_id is None:
                continue

            supplier_result = await session.execute(
                select(Supplier.id)
                .where(
                    and_(
                        Supplier.id == product.preferred_supplier_id,
                        Supplier.is_active.is_(True),
                        Supplier.deleted_at.is_(None),
                    )
                )
                .limit(1)
            )
            supplier_exists = supplier_result.scalar_one_or_none()
            if supplier_exists is None:
                continue

            po_result = await session.execute(
                select(PurchaseOrder.id)
                .join(POLine, POLine.po_id == PurchaseOrder.id)
                .where(
                    and_(
                        PurchaseOrder.auto_generated.is_(True),
                        PurchaseOrder.status == POStatus.SUBMITTED.value,
                        POLine.product_id == product.id,
                        PurchaseOrder.deleted_at.is_(None),
                    )
                )
                .limit(1)
            )
            existing = po_result.scalar_one_or_none()
            if existing is None:
                eligible_ids.append(str(product.id))

        logger.info(
            "get_reorder_eligible_products found %d eligible products",
            len(eligible_ids),
        )
        return eligible_ids


@activity.defn
async def create_auto_reorder_po(product_id: str) -> dict:
    """
    Create an auto-generated PO in submitted status for the given product.

    Idempotent: if a submitted auto-generated PO already exists for
    this product, returns the existing PO id with skipped=True.

    Returns:
        {"po_id": str | None, "skipped": bool, "product_name": str,
         "supplier_name": str, "quantity": str, "total": str,
         "po_number": str}
    """
    pid = UUID(product_id)

    async with AsyncSessionLocal() as session:
        async with session.begin():
            prod_result = await session.execute(
                select(Product).where(
                    and_(Product.id == pid, Product.deleted_at.is_(None))
                )
            )
            product = prod_result.scalar_one_or_none()
            if product is None:
                logger.error(
                    "create_auto_reorder_po: product %s not found, skipping",
                    product_id,
                )
                return {"po_id": None, "skipped": True}

            if product.preferred_supplier_id is None:
                logger.warning(
                    "create_auto_reorder_po: product %s has no preferred_supplier_id, "
                    "skipping",
                    product_id,
                )
                return {"po_id": None, "skipped": True}

            sup_result = await session.execute(
                select(Supplier).where(Supplier.id == product.preferred_supplier_id)
            )
            supplier = sup_result.scalar_one_or_none()
            if supplier is None:
                logger.error(
                    "create_auto_reorder_po: supplier %s not found for product %s, "
                    "skipping",
                    product.preferred_supplier_id,
                    product_id,
                )
                return {"po_id": None, "skipped": True}

            if not supplier.is_active:
                logger.warning(
                    "create_auto_reorder_po: supplier %s is inactive for product %s, "
                    "skipping",
                    supplier.id,
                    product_id,
                )
                return {"po_id": None, "skipped": True}

            existing_result = await session.execute(
                select(PurchaseOrder)
                .join(POLine, POLine.po_id == PurchaseOrder.id)
                .where(
                    and_(
                        PurchaseOrder.auto_generated.is_(True),
                        PurchaseOrder.status == POStatus.SUBMITTED.value,
                        POLine.product_id == pid,
                        PurchaseOrder.deleted_at.is_(None),
                    )
                )
                .with_for_update(skip_locked=False)
                .limit(1)
            )
            existing_po = existing_result.scalar_one_or_none()
            if existing_po is not None:
                logger.info(
                    "create_auto_reorder_po: auto PO %s already exists for product %s, "
                    "skipping duplicate",
                    existing_po.id,
                    product_id,
                )
                return {
                    "po_id": str(existing_po.id),
                    "skipped": True,
                    "product_name": product.name,
                    "supplier_name": supplier.name,
                    "quantity": str(product.reorder_quantity),
                    "total": str(product.reorder_quantity * product.unit_price),
                    "po_number": existing_po.po_number,
                }

            year = datetime.now(timezone.utc).year
            po_number = await generate_auto_po_number(session, year)

            admin_uuid = SYSTEM_ADMIN_UUID
            if admin_uuid is None:
                admin_result = await session.execute(
                    select(User)
                    .where(
                        and_(
                            User.role == UserRole.ADMIN.value,
                            User.is_active.is_(True),
                        )
                    )
                    .limit(1)
                )
                admin_user = admin_result.scalar_one_or_none()
                if admin_user is None:
                    logger.error(
                        "create_auto_reorder_po: no active admin user found, "
                        "cannot create PO for product %s",
                        product_id,
                    )
                    return {"po_id": None, "skipped": True}
                admin_uuid = admin_user.id

            quantity = product.reorder_quantity
            unit_price = product.unit_price
            total_amount = quantity * unit_price
            now = datetime.now(timezone.utc)

            po = PurchaseOrder(
                po_number=po_number,
                supplier_id=supplier.id,
                created_by=admin_uuid,
                status=POStatus.SUBMITTED.value,
                total_amount=total_amount,
                auto_generated=True,
                submitted_at=now,
                notes="Auto-generated by reorder workflow",
            )
            session.add(po)
            await session.flush()
            await session.refresh(po)

            line = POLine(
                po_id=po.id,
                product_id=pid,
                quantity_ordered=quantity,
                quantity_received=Decimal("0"),
                unit_price=unit_price,
                line_total=total_amount,
            )
            session.add(line)
            await session.flush()

            logger.info(
                "create_auto_reorder_po: created PO %s (%s) for product %s "
                "supplier %s qty=%s total=%s",
                po.id,
                po_number,
                product_id,
                supplier.id,
                quantity,
                total_amount,
            )
            return {
                "po_id": str(po.id),
                "skipped": False,
                "product_name": product.name,
                "supplier_name": supplier.name,
                "quantity": str(quantity),
                "total": str(total_amount),
                "po_number": po_number,
            }


@activity.defn
async def send_reorder_email(po_id: str, product_id: str) -> None:
    """
    Send auto_reorder_created email to all procurement_manager users.

    All errors are caught and logged — this activity never raises.
    """
    info = activity.info()
    workflow_id = info.workflow_id
    activity_id = info.activity_id

    try:
        async with AsyncSessionLocal() as session:
            po_result = await session.execute(
                select(PurchaseOrder).where(
                    and_(
                        PurchaseOrder.id == UUID(po_id),
                        PurchaseOrder.deleted_at.is_(None),
                    )
                )
            )
            po = po_result.scalar_one_or_none()
            if po is None:
                logger.error(
                    "send_reorder_email: PO %s not found, cannot send email", po_id
                )
                return

            prod_result = await session.execute(
                select(Product).where(
                    and_(
                        Product.id == UUID(product_id),
                        Product.deleted_at.is_(None),
                    )
                )
            )
            product = prod_result.scalar_one_or_none()
            if product is None:
                logger.error(
                    "send_reorder_email: product %s not found, cannot send email",
                    product_id,
                )
                return

            sup_result = await session.execute(
                select(Supplier).where(Supplier.id == po.supplier_id)
            )
            supplier = sup_result.scalar_one_or_none()
            supplier_name = supplier.name if supplier else "Unknown Supplier"

            users_result = await session.execute(
                select(User).where(
                    and_(
                        User.role == UserRole.PROCUREMENT_MANAGER.value,
                        User.is_active.is_(True),
                    )
                )
            )
            managers = list(users_result.scalars().all())

        if not managers:
            logger.warning(
                "send_reorder_email: no active procurement_manager users found, "
                "no email sent for PO %s",
                po_id,
            )
            return

        subject = f"Auto-Reorder PO Created — {product.name}"
        body = (
            f"An auto-reorder purchase order has been created.\n\n"
            f"PO Number:    {po.po_number}\n"
            f"Supplier:     {supplier_name}\n"
            f"Product:      {product.name}\n"
            f"Quantity:     {product.reorder_quantity}\n"
            f"Total Amount: {po.total_amount}\n\n"
            f"This PO was generated automatically by the reorder workflow.\n"
            f"Please review and take appropriate action."
        )

        for user in managers:
            await send_email(
                to_emails=[user.email],
                subject=subject,
                body=body,
                email_type="auto_reorder_created",
                workflow_id=workflow_id,
                activity_id=activity_id,
            )

    except Exception as exc:
        logger.error(
            "send_reorder_email: unexpected error for PO %s: %s",
            po_id,
            exc,
            exc_info=True,
        )
