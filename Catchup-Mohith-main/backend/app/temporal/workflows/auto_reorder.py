# backend/app/temporal/workflows/auto_reorder.py
import logging
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from backend.app.temporal.activities.reorder_activities import (
        create_auto_reorder_po,
        get_reorder_eligible_products,
        send_reorder_email,
    )

logger = logging.getLogger(__name__)

_RETRY_POLICY = RetryPolicy(
    maximum_attempts=3,
    initial_interval=timedelta(seconds=1),
    backoff_coefficient=2.0,
)

_ACTIVITY_TIMEOUT = timedelta(minutes=5)


@workflow.defn
class AutoReorderWorkflow:
    """
    Cron workflow — runs every 2 hours.
    Schedule: "0 */2 * * *"
    Workflow ID: "auto-reorder-{YYYY-MM-DD-HH}"

    For each product eligible for auto-reorder, creates a submitted
    PO and sends an email notification to all procurement_manager
    users. Products are processed in parallel — one product failure
    does not block others.

    The workflow is idempotent: if a submitted auto-generated PO
    already exists for a product, that product is skipped.
    """

    @workflow.run
    async def run(self) -> None:
        logger.info("AutoReorderWorkflow starting")

        eligible_product_ids: list[str] = await workflow.execute_activity(
            get_reorder_eligible_products,
            schedule_to_close_timeout=_ACTIVITY_TIMEOUT,
            retry_policy=_RETRY_POLICY,
        )

        if not eligible_product_ids:
            logger.info("AutoReorderWorkflow: no eligible products — nothing to do")
            return

        logger.info(
            "AutoReorderWorkflow: %d eligible products found, processing in parallel",
            len(eligible_product_ids),
        )

        import asyncio

        tasks = [
            self._process_one_product(product_id) for product_id in eligible_product_ids
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

        logger.info("AutoReorderWorkflow complete")

    async def _process_one_product(self, product_id: str) -> None:
        """
        Create PO for one product and send notification email.
        Errors are caught and logged so parallel siblings are not affected.
        """
        try:
            result: dict = await workflow.execute_activity(
                create_auto_reorder_po,
                product_id,
                schedule_to_close_timeout=_ACTIVITY_TIMEOUT,
                retry_policy=_RETRY_POLICY,
            )

            if result.get("skipped"):
                logger.info(
                    "AutoReorderWorkflow: product %s skipped (po_id=%s)",
                    product_id,
                    result.get("po_id"),
                )
                return

            po_id = result["po_id"]
            logger.info(
                "AutoReorderWorkflow: PO %s created for product %s — sending email",
                po_id,
                product_id,
            )

            await workflow.execute_activity(
                send_reorder_email,
                po_id,
                product_id,
                schedule_to_close_timeout=_ACTIVITY_TIMEOUT,
                retry_policy=_RETRY_POLICY,
            )

        except Exception as exc:
            logger.error(
                "AutoReorderWorkflow: error processing product %s: %s",
                product_id,
                exc,
                exc_info=True,
            )
