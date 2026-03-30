# /home/mohith/Catchup-Mohith/scripts/verify_temporal.py
#!/usr/bin/env python3
"""Verify Temporal worker connectivity and workflow registration."""
import asyncio
import os
import sys
from pathlib import Path

from temporalio.api.taskqueue.v1 import TaskQueue
from temporalio.api.enums.v1 import TaskQueueType
from temporalio.api.workflowservice.v1 import DescribeTaskQueueRequest
from temporalio.client import Client

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

TEMPORAL_ENDPOINT = f"{os.getenv('TEMPORAL_HOST', 'localhost')}:{os.getenv('TEMPORAL_PORT', '7233')}"
TASK_QUEUE = "stockbridge-main"
EXPECTED_WORKFLOWS = {
    "AutoReorderWorkflow",
    "TierRecalculationWorkflow",
    "BackorderFollowupWorkflow",
}
TIMEOUT_SECONDS = 10


async def verify() -> bool:
    passed = 0
    failed = 0

    print("=== Temporal Verification ===")
    print(f"Connecting to Temporal at {TEMPORAL_ENDPOINT}...")

    try:
        client = await asyncio.wait_for(Client.connect(TEMPORAL_ENDPOINT), timeout=TIMEOUT_SECONDS)
        print("  PASS: Connected to Temporal")
        passed += 1
    except Exception as exc:  # pragma: no cover - cli diagnostic
        print(f"  FAIL: Cannot connect to Temporal: {exc}")
        return False

    try:
        workflow_response = await asyncio.wait_for(
            client.workflow_service.describe_task_queue(
                DescribeTaskQueueRequest(
                    namespace="default",
                    task_queue=TaskQueue(name=TASK_QUEUE),
                    task_queue_type=TaskQueueType.TASK_QUEUE_TYPE_WORKFLOW,
                )
            ),
            timeout=TIMEOUT_SECONDS,
        )
        activity_response = await asyncio.wait_for(
            client.workflow_service.describe_task_queue(
                DescribeTaskQueueRequest(
                    namespace="default",
                    task_queue=TaskQueue(name=TASK_QUEUE),
                    task_queue_type=TaskQueueType.TASK_QUEUE_TYPE_ACTIVITY,
                )
            ),
            timeout=TIMEOUT_SECONDS,
        )
        print(f"  PASS: Task queue '{TASK_QUEUE}' is reachable")
        passed += 1
    except Exception as exc:  # pragma: no cover - cli diagnostic
        print(f"  FAIL: Task queue not reachable: {exc}")
        return False

    workflows_dir = PROJECT_ROOT / "backend/app/temporal/workflows"
    source_text = ""
    if workflows_dir.is_dir():
        for path in workflows_dir.glob("*.py"):
            source_text += path.read_text(encoding="utf-8")
    missing = {name for name in EXPECTED_WORKFLOWS if name not in source_text}
    if missing:
        print(
            "  FAIL: Expected workflow definitions missing in source: "
            + ", ".join(sorted(missing))
        )
        failed += 1
    else:
        print("  PASS: Expected workflow definitions found")
        passed += 1

    if workflow_response.pollers or activity_response.pollers:
        print("  PASS: Worker poller is registered")
        passed += 1
    else:
        print("  FAIL: No active pollers found for task queue")
        failed += 1

    print("")
    print(f"Results: {passed} passed, {failed} failed")
    if failed == 0:
        print("All Temporal checks passed.")
        return True
    return False


if __name__ == "__main__":
    ok = asyncio.run(verify())
    sys.exit(0 if ok else 1)
