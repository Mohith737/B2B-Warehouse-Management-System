# /home/mohith/Catchup-Mohith/backend/app/temporal/worker.py
import asyncio
import logging
import signal
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, cast, String
from temporalio.client import (
    Client,
    Schedule,
    ScheduleActionStartWorkflow,
    ScheduleSpec,
)
from temporalio.service import RPCError
from temporalio.worker import Worker

from backend.app.core.config import settings
from backend.app.db.session import AsyncSessionLocal
from backend.app.models.user import User, UserRole
from backend.app.temporal.activities import reorder_activities
from backend.app.temporal.activities.backorder_activities import (
    get_backorder_summary,
    send_backorder_notification,
)
from backend.app.temporal.activities.email_activities import send_email
from backend.app.temporal.activities.reorder_activities import (
    create_auto_reorder_po,
    get_reorder_eligible_products,
    send_reorder_email,
)
from backend.app.temporal.activities.tier_activities import (
    calculate_supplier_tier,
    get_all_active_suppliers,
    send_monthly_summary_email,
    send_tier_change_email,
)
from backend.app.temporal.workflows.auto_reorder import AutoReorderWorkflow
from backend.app.temporal.workflows.backorder_followup import BackorderFollowupWorkflow
from backend.app.temporal.workflows.tier_recalculation import TierRecalculationWorkflow

logger = logging.getLogger(__name__)

SYSTEM_USER_ID: UUID | None = None


def _temporal_target() -> str:
    return f"{settings.temporal_host}:{settings.temporal_port}"


def _task_queue() -> str:
    return getattr(settings, "temporal_task_queue", "stockbridge-temporal")


async def _load_system_user_id() -> UUID | None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User.id)
            .where(cast(User.role, String) == UserRole.ADMIN.value)
            .where(User.is_active.is_(True))
            .order_by(User.created_at.asc())
            .limit(1)
        )
        return result.scalar_one_or_none()


async def _ensure_schedule(
    client: Client,
    schedule_id: str,
    workflow,
    cron_expression: str,
    task_queue: str,
    args: list | None = None,
) -> None:
    handle = client.get_schedule_handle(schedule_id)
    try:
        await handle.describe()
        logger.info("Temporal schedule exists, skipping create: %s", schedule_id)
        return
    except RPCError:
        pass

    await client.create_schedule(
        schedule_id,
        Schedule(
            action=ScheduleActionStartWorkflow(
                workflow,
                args=args or [],
                id=f"{schedule_id}-workflow",
                task_queue=task_queue,
            ),
            spec=ScheduleSpec(cron_expressions=[cron_expression]),
        ),
    )
    logger.info(
        "Created Temporal schedule %s with cron %s",
        schedule_id,
        cron_expression,
    )


async def _register_startup_schedules(client: Client, task_queue: str) -> None:
    await _ensure_schedule(
        client=client,
        schedule_id="auto-reorder-schedule",
        workflow=AutoReorderWorkflow.run,
        cron_expression="0 */2 * * *",
        task_queue=task_queue,
    )

    now = datetime.now(timezone.utc)
    await _ensure_schedule(
        client=client,
        schedule_id="tier-recalculation-schedule",
        workflow=TierRecalculationWorkflow.run,
        cron_expression="0 23 1 * *",
        task_queue=task_queue,
        args=[now.year, now.month],
    )


async def main() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO)
    )

    global SYSTEM_USER_ID
    SYSTEM_USER_ID = await _load_system_user_id()
    reorder_activities.SYSTEM_ADMIN_UUID = SYSTEM_USER_ID
    logger.info("Loaded SYSTEM_USER_ID=%s", SYSTEM_USER_ID)

    task_queue = _task_queue()
    client = await Client.connect(
        _temporal_target(),
        namespace=settings.temporal_namespace,
    )

    await _register_startup_schedules(client=client, task_queue=task_queue)

    worker = Worker(
        client,
        task_queue=task_queue,
        workflows=[
            AutoReorderWorkflow,
            TierRecalculationWorkflow,
            BackorderFollowupWorkflow,
        ],
        activities=[
            get_reorder_eligible_products,
            create_auto_reorder_po,
            send_reorder_email,
            get_all_active_suppliers,
            calculate_supplier_tier,
            send_tier_change_email,
            send_monthly_summary_email,
            send_email,
            get_backorder_summary,
            send_backorder_notification,
        ],
    )

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    def _shutdown_signal_handler() -> None:
        logger.info("Temporal worker shutdown signal received")
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _shutdown_signal_handler)
        except NotImplementedError:
            signal.signal(sig, lambda *_: _shutdown_signal_handler())

    worker_task = asyncio.create_task(worker.run())
    await stop_event.wait()
    await worker.shutdown()
    await worker_task


if __name__ == "__main__":
    asyncio.run(main())
