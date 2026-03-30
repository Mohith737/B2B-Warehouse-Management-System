# backend/app/temporal/workflows/tier_recalculation.py
import logging
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from backend.app.services.tier_scoring import TIER_ORDER
    from backend.app.temporal.activities.tier_activities import (
        calculate_supplier_tier,
        get_all_active_suppliers,
        send_monthly_summary_email,
        send_tier_change_email,
    )

logger = logging.getLogger(__name__)

_RETRY_POLICY = RetryPolicy(
    maximum_attempts=3,
    initial_interval=timedelta(seconds=1),
    backoff_coefficient=2.0,
)

_ACTIVITY_TIMEOUT = timedelta(minutes=10)
_EMAIL_TIMEOUT = timedelta(minutes=5)


@workflow.defn
class TierRecalculationWorkflow:
    """
    Cron workflow — runs on the last day of each month at 23:00 UTC.
    Schedule: "0 23 L * *"
    Workflow ID: "tier-recalc-{YYYY-MM}"

    Processes each active supplier sequentially — one supplier
    failure does not block others. After all suppliers are processed,
    sends a monthly summary email to all admin users.

    The workflow is idempotent: SupplierMetricsHistory rows are
    upserted, so re-running for the same month is safe.
    """

    @workflow.run
    async def run(self, year: int, month: int) -> None:
        logger.info("TierRecalculationWorkflow starting for %d-%02d", year, month)

        supplier_ids: list[str] = await workflow.execute_activity(
            get_all_active_suppliers,
            schedule_to_close_timeout=_ACTIVITY_TIMEOUT,
            retry_policy=_RETRY_POLICY,
        )

        if not supplier_ids:
            logger.info(
                "TierRecalculationWorkflow: no active suppliers — nothing to do"
            )
            return

        logger.info(
            "TierRecalculationWorkflow: processing %d suppliers sequentially",
            len(supplier_ids),
        )

        promoted_count = 0
        demoted_count = 0
        unchanged_count = 0
        insufficient_count = 0

        for supplier_id in supplier_ids:
            try:
                result: dict = await workflow.execute_activity(
                    calculate_supplier_tier,
                    supplier_id,
                    year,
                    month,
                    schedule_to_close_timeout=_ACTIVITY_TIMEOUT,
                    retry_policy=_RETRY_POLICY,
                )

                if result.get("insufficient_data"):
                    insufficient_count += 1
                    logger.info(
                        "TierRecalculationWorkflow: supplier %s insufficient data "
                        "for %d-%02d",
                        supplier_id,
                        year,
                        month,
                    )
                    continue

                old_tier = result.get("old_tier")
                new_tier = result.get("new_tier")
                tier_changed = result.get("tier_changed", False)

                if not tier_changed:
                    unchanged_count += 1
                elif old_tier and new_tier:
                    if TIER_ORDER.get(new_tier, 0) > TIER_ORDER.get(old_tier, 0):
                        promoted_count += 1
                    else:
                        demoted_count += 1
                    await workflow.execute_activity(
                        send_tier_change_email,
                        supplier_id,
                        old_tier,
                        new_tier,
                        year,
                        month,
                        schedule_to_close_timeout=_EMAIL_TIMEOUT,
                        retry_policy=_RETRY_POLICY,
                    )

            except Exception as exc:
                logger.error(
                    "TierRecalculationWorkflow: error processing supplier %s: %s",
                    supplier_id,
                    exc,
                    exc_info=True,
                )
                unchanged_count += 1

        stats = {
            "promoted_count": promoted_count,
            "demoted_count": demoted_count,
            "unchanged_count": unchanged_count,
            "insufficient_count": insufficient_count,
        }
        await workflow.execute_activity(
            send_monthly_summary_email,
            year,
            month,
            stats,
            schedule_to_close_timeout=_EMAIL_TIMEOUT,
            retry_policy=_RETRY_POLICY,
        )

        logger.info(
            "TierRecalculationWorkflow complete for %d-%02d: "
            "promoted=%d demoted=%d unchanged=%d insufficient=%d",
            year,
            month,
            promoted_count,
            demoted_count,
            unchanged_count,
            insufficient_count,
        )
