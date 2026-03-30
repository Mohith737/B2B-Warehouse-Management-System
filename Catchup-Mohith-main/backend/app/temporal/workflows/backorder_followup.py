# backend/app/temporal/workflows/backorder_followup.py
import logging
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from backend.app.temporal.activities.backorder_activities import (
        get_backorder_summary,
        send_backorder_notification,
    )

logger = logging.getLogger(__name__)

_RETRY_POLICY = RetryPolicy(
    maximum_attempts=3,
    initial_interval=timedelta(seconds=1),
    backoff_coefficient=2.0,
)

_ACTIVITY_TIMEOUT = timedelta(minutes=5)


@workflow.defn
class BackorderFollowupWorkflow:
    """
    Event-driven workflow — triggered by GRNService.complete_grn()
    after a partial receipt creates backorder records.

    Workflow ID: "backorder-followup-{grn_id}"

    Fetches all backorders for the GRN, then sends a notification
    email to all procurement_manager users listing outstanding
    quantities.

    The workflow is idempotent: get_backorder_summary returns the
    same data on repeated runs; send_backorder_notification is
    wrapped in try/except so email failures never fail the workflow.
    """

    @workflow.run
    async def run(self, grn_id: str) -> None:
        logger.info("BackorderFollowupWorkflow starting for GRN %s", grn_id)

        backorders: list[dict] = await workflow.execute_activity(
            get_backorder_summary,
            grn_id,
            schedule_to_close_timeout=_ACTIVITY_TIMEOUT,
            retry_policy=_RETRY_POLICY,
        )

        if not backorders:
            logger.info(
                "BackorderFollowupWorkflow: no backorders for GRN %s — nothing to do",
                grn_id,
            )
            return

        logger.info(
            "BackorderFollowupWorkflow: %d backorders found for GRN %s — "
            "sending notification",
            len(backorders),
            grn_id,
        )

        await workflow.execute_activity(
            send_backorder_notification,
            grn_id,
            backorders,
            schedule_to_close_timeout=_ACTIVITY_TIMEOUT,
            retry_policy=_RETRY_POLICY,
        )

        logger.info("BackorderFollowupWorkflow complete for GRN %s", grn_id)
