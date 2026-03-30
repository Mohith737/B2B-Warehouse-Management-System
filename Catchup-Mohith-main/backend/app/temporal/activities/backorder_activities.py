# backend/app/temporal/activities/backorder_activities.py
import logging
from uuid import UUID

from sqlalchemy import and_, select
from temporalio import activity

from backend.app.db.session import AsyncSessionLocal
from backend.app.models.backorder import Backorder
from backend.app.models.product import Product
from backend.app.models.purchase_order import PurchaseOrder
from backend.app.models.user import User, UserRole
from backend.app.temporal.activities.email_activities import send_email

logger = logging.getLogger(__name__)


@activity.defn
async def get_backorder_summary(grn_id: str) -> list[dict]:
    """
    Return all backorder records for the given GRN enriched with
    product name and PO number.

    Idempotent — safe to run twice; returns the same data.
    """
    gid = UUID(grn_id)

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Backorder).where(Backorder.grn_id == gid))
        backorders = list(result.scalars().all())

        if not backorders:
            logger.info("get_backorder_summary: no backorders found for GRN %s", grn_id)
            return []

        product_ids = {b.product_id for b in backorders}
        po_ids = {b.original_po_id for b in backorders}

        products_result = await session.execute(
            select(Product).where(Product.id.in_(product_ids))
        )
        products_by_id = {p.id: p for p in products_result.scalars().all()}

        pos_result = await session.execute(
            select(PurchaseOrder).where(PurchaseOrder.id.in_(po_ids))
        )
        pos_by_id = {po.id: po for po in pos_result.scalars().all()}

        summary = []
        for b in backorders:
            product = products_by_id.get(b.product_id)
            po = pos_by_id.get(b.original_po_id)
            summary.append(
                {
                    "backorder_id": str(b.id),
                    "product_id": str(b.product_id),
                    "product_name": product.name if product else "Unknown Product",
                    "po_number": po.po_number if po else "Unknown PO",
                    "quantity_ordered": str(b.quantity_ordered),
                    "quantity_received": str(b.quantity_received),
                    "quantity_outstanding": str(b.quantity_outstanding),
                    "status": b.status,
                }
            )

        logger.info(
            "get_backorder_summary: found %d backorders for GRN %s",
            len(summary),
            grn_id,
        )
        return summary


@activity.defn
async def send_backorder_notification(
    grn_id: str,
    backorders: list[dict],
) -> None:
    """
    Send backorder_notification email to all procurement_manager users.

    All errors are caught and logged — this activity never raises.
    """
    info = activity.info()
    workflow_id = info.workflow_id
    activity_id = info.activity_id

    try:
        if not backorders:
            logger.info(
                "send_backorder_notification: no backorders for GRN %s, "
                "nothing to send",
                grn_id,
            )
            return

        async with AsyncSessionLocal() as session:
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
                "send_backorder_notification: no active procurement_manager users "
                "found for GRN %s",
                grn_id,
            )
            return

        po_number = backorders[0].get("po_number", "Unknown PO")
        subject = f"Backorder Created — {po_number}"

        lines = "\n".join(
            f"  - {b['product_name']}: "
            f"ordered {b['quantity_ordered']}, "
            f"received {b['quantity_received']}, "
            f"outstanding {b['quantity_outstanding']}"
            for b in backorders
        )
        body = (
            f"A partial goods receipt has created the following backorders.\n\n"
            f"PO Number: {po_number}\n"
            f"GRN ID:    {grn_id}\n\n"
            f"Outstanding Items:\n"
            f"{lines}\n\n"
            f"Log in to StockBridge to review and manage these backorders."
        )

        for manager in managers:
            await send_email(
                to_emails=[manager.email],
                subject=subject,
                body=body,
                email_type="backorder_notification",
                workflow_id=workflow_id,
                activity_id=activity_id,
            )

    except Exception as exc:
        logger.error(
            "send_backorder_notification: unexpected error for GRN %s: %s",
            grn_id,
            exc,
            exc_info=True,
        )
