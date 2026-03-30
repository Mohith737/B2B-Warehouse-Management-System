# backend/app/temporal/activities/tier_activities.py
import logging
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, extract, func, select
from temporalio import activity

from backend.app.db.session import AsyncSessionLocal
from backend.app.models.backorder import Backorder
from backend.app.models.po_line import POLine
from backend.app.models.purchase_order import POStatus, PurchaseOrder
from backend.app.models.supplier import Supplier
from backend.app.models.supplier_metrics_history import SupplierMetricsHistory
from backend.app.models.user import User, UserRole
from backend.app.services.tier_scoring import TierScoringInput, compute_tier_decision
from backend.app.temporal.activities.email_activities import send_email

logger = logging.getLogger(__name__)

_CLOSED_STATUSES = (POStatus.RECEIVED.value, POStatus.CLOSED.value)


@activity.defn
async def get_all_active_suppliers() -> list[str]:
    """
    Return UUIDs (as strings) of all active, non-deleted suppliers.

    Idempotent — safe to run twice.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Supplier.id).where(
                and_(
                    Supplier.is_active.is_(True),
                    Supplier.deleted_at.is_(None),
                )
            )
        )
        ids = [str(row) for row in result.scalars().all()]
        logger.info("get_all_active_suppliers found %d suppliers", len(ids))
        return ids


@activity.defn
async def calculate_supplier_tier(
    supplier_id: str,
    year: int,
    month: int,
) -> dict:
    """
    Aggregate monthly metrics for one supplier, call tier_scoring,
    update supplier fields, and write a SupplierMetricsHistory row.

    Idempotent: if a SupplierMetricsHistory row for this supplier /
    year / month already exists it is updated in-place.

    Returns:
        {
          "supplier_id": str,
          "old_tier": str | None,
          "new_tier": str | None,
          "tier_changed": bool,
          "insufficient_data": bool,
        }
    """
    sid = UUID(supplier_id)

    async with AsyncSessionLocal() as session:
        async with session.begin():
            sup_result = await session.execute(
                select(Supplier).where(
                    and_(Supplier.id == sid, Supplier.deleted_at.is_(None))
                )
            )
            supplier = sup_result.scalar_one_or_none()
            if supplier is None:
                logger.error(
                    "calculate_supplier_tier: supplier %s not found, skipping",
                    supplier_id,
                )
                return {
                    "supplier_id": supplier_id,
                    "old_tier": None,
                    "new_tier": None,
                    "tier_changed": False,
                    "insufficient_data": True,
                }

            old_tier = supplier.current_tier

            po_lines_result = await session.execute(
                select(func.count(POLine.id))
                .join(PurchaseOrder, PurchaseOrder.id == POLine.po_id)
                .where(
                    and_(
                        PurchaseOrder.supplier_id == sid,
                        PurchaseOrder.status.in_(_CLOSED_STATUSES),
                        PurchaseOrder.deleted_at.is_(None),
                        extract("year", PurchaseOrder.received_at) == year,
                        extract("month", PurchaseOrder.received_at) == month,
                    )
                )
            )
            total_po_lines: int = po_lines_result.scalar_one() or 0

            backorder_result = await session.execute(
                select(func.count(Backorder.id))
                .join(
                    PurchaseOrder,
                    PurchaseOrder.id == Backorder.original_po_id,
                )
                .where(
                    and_(
                        PurchaseOrder.supplier_id == sid,
                        PurchaseOrder.status.in_(_CLOSED_STATUSES),
                        PurchaseOrder.deleted_at.is_(None),
                        extract("year", PurchaseOrder.received_at) == year,
                        extract("month", PurchaseOrder.received_at) == month,
                    )
                )
            )
            backorder_count: int = backorder_result.scalar_one() or 0

            backorder_rate = (
                Decimal(backorder_count) / Decimal(total_po_lines)
                if total_po_lines > 0
                else Decimal("0")
            )

            # on_time_rate uses a fixed placeholder of 0.90 until shipment
            # timestamp tracking is implemented in a future phase.
            # Actual calculation requires comparing shipped_at to expected
            # delivery dates which are not yet recorded in the data model.
            on_time_rate = Decimal("0.90")

            if total_po_lines < 20:
                logger.info(
                    "calculate_supplier_tier: supplier %s has %d PO lines "
                    "(<20) for %d-%02d — insufficient data, preserving tier %s",
                    supplier_id,
                    total_po_lines,
                    year,
                    month,
                    old_tier,
                )
                await _upsert_metrics_history(
                    session=session,
                    supplier_id=sid,
                    year=year,
                    month=month,
                    total_po_lines=total_po_lines,
                    backorder_count=backorder_count,
                    backorder_rate=backorder_rate,
                    on_time_rate=on_time_rate,
                    tier_before=old_tier,
                    tier_after=old_tier,
                    decision_reason="Insufficient data — fewer than 20 PO lines.",
                    insufficient_data=True,
                )
                return {
                    "supplier_id": supplier_id,
                    "old_tier": old_tier,
                    "new_tier": old_tier,
                    "tier_changed": False,
                    "insufficient_data": True,
                }

            scoring_input = TierScoringInput(
                total_po_lines=total_po_lines,
                backorder_rate=backorder_rate,
                on_time_rate=on_time_rate,
                current_tier=old_tier,
                tier_locked=supplier.tier_locked,
                consecutive_qualifying_months=supplier.consecutive_on_time,
                consecutive_underperforming_months=supplier.consecutive_late,
            )
            result = compute_tier_decision(scoring_input)

            supplier.current_tier = result.new_tier
            supplier.consecutive_on_time = result.consecutive_qualifying_months
            supplier.consecutive_late = result.consecutive_underperforming_months
            await session.flush()

            await _upsert_metrics_history(
                session=session,
                supplier_id=sid,
                year=year,
                month=month,
                total_po_lines=total_po_lines,
                backorder_count=backorder_count,
                backorder_rate=backorder_rate,
                on_time_rate=on_time_rate,
                tier_before=old_tier,
                tier_after=result.new_tier,
                decision_reason=result.decision_reason,
                insufficient_data=False,
            )

            tier_changed = result.new_tier != old_tier
            logger.info(
                "calculate_supplier_tier: supplier %s %d-%02d "
                "old_tier=%s new_tier=%s changed=%s reason=%s",
                supplier_id,
                year,
                month,
                old_tier,
                result.new_tier,
                tier_changed,
                result.decision_reason,
            )
            return {
                "supplier_id": supplier_id,
                "old_tier": old_tier,
                "new_tier": result.new_tier,
                "tier_changed": tier_changed,
                "insufficient_data": False,
            }


async def _upsert_metrics_history(
    *,
    session,
    supplier_id: UUID,
    year: int,
    month: int,
    total_po_lines: int,
    backorder_count: int,
    backorder_rate: Decimal,
    on_time_rate: Decimal,
    tier_before: str,
    tier_after: str,
    decision_reason: str,
    insufficient_data: bool,
) -> None:
    """
    Insert or update a SupplierMetricsHistory row for the given
    supplier / year / month. Upsert makes calculate_supplier_tier
    idempotent.
    """
    existing_result = await session.execute(
        select(SupplierMetricsHistory).where(
            and_(
                SupplierMetricsHistory.supplier_id == supplier_id,
                SupplierMetricsHistory.year == year,
                SupplierMetricsHistory.month == month,
            )
        )
    )
    existing = existing_result.scalar_one_or_none()

    if existing is not None:
        existing.total_po_lines = total_po_lines
        existing.backorder_count = backorder_count
        existing.backorder_rate = backorder_rate
        existing.on_time_rate = on_time_rate
        existing.tier_before = tier_before
        existing.tier_after = tier_after
        existing.decision_reason = decision_reason
        existing.insufficient_data = insufficient_data
        await session.flush()
    else:
        record = SupplierMetricsHistory(
            supplier_id=supplier_id,
            year=year,
            month=month,
            total_po_lines=total_po_lines,
            backorder_count=backorder_count,
            backorder_rate=backorder_rate,
            on_time_rate=on_time_rate,
            tier_before=tier_before,
            tier_after=tier_after,
            decision_reason=decision_reason,
            insufficient_data=insufficient_data,
        )
        session.add(record)
        await session.flush()


@activity.defn
async def send_tier_change_email(
    supplier_id: str,
    old_tier: str,
    new_tier: str,
    year: int,
    month: int,
) -> None:
    """
    Send a tier change notification for one supplier.

    All errors are caught and logged — this activity never raises.
    """
    info = activity.info()
    workflow_id = info.workflow_id
    activity_id = info.activity_id

    try:
        sid = UUID(supplier_id)
    except ValueError:
        logger.error(
            "send_tier_change_email: invalid supplier_id=%s for %d-%02d",
            supplier_id,
            year,
            month,
        )
        return

    try:
        async with AsyncSessionLocal() as session:
            supplier_result = await session.execute(
                select(Supplier).where(
                    and_(
                        Supplier.id == sid,
                        Supplier.deleted_at.is_(None),
                    )
                )
            )
            supplier = supplier_result.scalar_one_or_none()

        if supplier is None or not supplier.is_active:
            logger.warning(
                "send_tier_change_email: supplier %s missing or inactive, skipping",
                supplier_id,
            )
            return

        subject = f"Supplier Tier Updated — {year}-{month:02d}"
        body = (
            f"Hello {supplier.name},\n\n"
            f"Your StockBridge performance tier was updated for {year}-{month:02d}.\n"
            f"Previous tier: {old_tier}\n"
            f"New tier: {new_tier}\n\n"
            f"Please review your supplier performance metrics in the dashboard."
        )

        await send_email(
            to_emails=[supplier.email],
            subject=subject,
            body=body,
            email_type="tier_change",
            workflow_id=workflow_id,
            activity_id=activity_id,
        )
    except Exception as exc:
        logger.error(
            "send_tier_change_email: unexpected error for supplier %s: %s",
            supplier_id,
            exc,
            exc_info=True,
        )


@activity.defn
async def send_monthly_summary_email(
    year: int,
    month: int,
    stats: dict,
) -> None:
    """
    Send monthly_summary email to all admin users after all suppliers
    have been processed.

    stats keys: promoted_count, demoted_count, unchanged_count,
                insufficient_count

    All errors are caught and logged — this activity never raises.
    """
    info = activity.info()
    workflow_id = info.workflow_id
    activity_id = info.activity_id

    try:
        async with AsyncSessionLocal() as session:
            users_result = await session.execute(
                select(User).where(
                    and_(
                        User.role == UserRole.ADMIN.value,
                        User.is_active.is_(True),
                    )
                )
            )
            admins = list(users_result.scalars().all())

        if not admins:
            logger.warning(
                "send_monthly_summary_email: no active admin users found "
                "for %d-%02d summary",
                year,
                month,
            )
            return

        promoted = stats.get("promoted_count", 0)
        demoted = stats.get("demoted_count", 0)
        unchanged = stats.get("unchanged_count", 0)
        insufficient = stats.get("insufficient_count", 0)

        subject = f"Monthly Supplier Tier Summary — {year}-{month:02d}"
        body = (
            f"Monthly tier recalculation completed for {year}-{month:02d}.\n\n"
            f"Results:\n"
            f"  Promotions:        {promoted}\n"
            f"  Demotions:         {demoted}\n"
            f"  No change:         {unchanged}\n"
            f"  Insufficient data: {insufficient}\n\n"
            f"Total suppliers processed: "
            f"{promoted + demoted + unchanged + insufficient}\n\n"
            f"Log in to StockBridge to review individual supplier details."
        )

        for admin in admins:
            await send_email(
                to_emails=[admin.email],
                subject=subject,
                body=body,
                email_type="monthly_summary",
                workflow_id=workflow_id,
                activity_id=activity_id,
            )

    except Exception as exc:
        logger.error(
            "send_monthly_summary_email: unexpected error for %d-%02d: %s",
            year,
            month,
            exc,
            exc_info=True,
        )
