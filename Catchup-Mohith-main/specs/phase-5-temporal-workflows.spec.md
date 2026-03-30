# specs/phase-5-temporal-workflows.spec.md
# Phase 5 — Temporal Workflows Spec

## Purpose
This phase implements the three Temporal workflows that drive
StockBridge's automated business processes. Phase 4 set the
auto_reorder_triggered flag on GRNs and created Backorder records
— this phase acts on them. The tier scoring pure function from
Phase 2 gets its monthly execution engine here. SendGrid email
activities are implemented here for the first time.

Without this phase, stock replenishment is manual, supplier tiers
never update automatically, and no email notifications are sent.
This phase makes the system self-managing within the rules locked
in planning.

## Scope

### In Scope
backend/app/temporal/workflows/auto_reorder_workflow.py
backend/app/temporal/workflows/tier_recalculation_workflow.py
backend/app/temporal/workflows/backorder_followup_workflow.py
backend/app/temporal/activities/reorder_activities.py
backend/app/temporal/activities/tier_activities.py
backend/app/temporal/activities/email_activities.py
backend/app/temporal/activities/backorder_activities.py
backend/app/temporal/worker.py
backend/app/services/email_service.py
backend/app/repositories/email_failure_log_repository.py
backend/alembic/versions/018_create_email_failure_log.py
backend/tests/unit/test_auto_reorder_workflow.py
backend/tests/unit/test_tier_recalculation_workflow.py
backend/tests/unit/test_email_activities.py

### Out of Scope
Frontend notification UI — Phase 9.
Email template design — plain text emails only in this phase.
Temporal UI dashboard configuration — operational concern.
SendGrid webhook handling — not planned for this project.

## Acceptance Criteria

1.  Auto-reorder workflow runs every 2 hours via cron schedule
2.  Auto-reorder workflow processes each eligible product as a
    separate parallel activity — one product failure does not
    block others
3.  Auto-reorder skips inactive suppliers — logs warning and
    continues without failing the workflow
4.  Auto-reorder creates PO in submitted status directly —
    not draft — with po_number in SB-AUTO-YYYY-NNNNNN format
5.  Auto-reorder is idempotent — if a submitted auto-reorder PO
    already exists for a product, does not create a duplicate
6.  Auto-reorder sends email to procurement_manager users after
    creating each PO
7.  Tier recalculation workflow runs on last day of each month
    at 23:00 UTC via cron schedule
8.  Tier recalculation processes each supplier sequentially —
    one supplier failure does not block others
9.  Tier recalculation calls tier_scoring.compute_tier_decision
    with the month's aggregated metrics
10. Tier recalculation updates supplier.current_tier,
    consecutive_on_time, and consecutive_late fields
11. Tier recalculation writes one SupplierMetricsHistory record
    per supplier per month
12. Tier recalculation sends monthly summary email to all
    admin users after completing all suppliers
13. Backorder follow-up workflow is triggered by GRN completion
    when partial receipt creates backorders
14. Backorder follow-up sends email notification to
    procurement_manager users listing outstanding quantities
15. All email sends are wrapped in try/except — email failure
    never fails a workflow
16. Failed email attempts are logged to email_failure_log table
    with retry_count, last_error, and resolved flag
17. SendGrid sandbox mode is used in all non-production
    environments (ENVIRONMENT != production)
18. All Temporal activities have retry policies — max 3 attempts
    with exponential backoff starting at 1 second
19. All workflow IDs use idempotency keys to prevent duplicate
    execution
20. All unit tests pass
21. ruff check backend/ passes
22. black --check backend/ passes

## Workflow Definitions

### Workflow 1 — Auto-Reorder
Schedule: every 2 hours (cron: "0 */2 * * *")
Workflow ID: "auto-reorder-{YYYY-MM-DD-HH}" (hourly uniqueness)

Execution steps:
1. Activity: get_reorder_eligible_products()
   Returns list of products where:
   - auto_reorder_enabled = true
   - current_stock <= reorder_point (or low_stock_threshold_override)
   - No open auto-reorder PO already exists for this product
   - preferred_supplier is set and is active

2. For each eligible product (parallel execution):
   Activity: create_auto_reorder_po(product_id)
   - Fetch product and preferred_supplier
   - If supplier inactive: log warning, return without error
   - Check idempotency: if submitted auto-PO exists for this
     product skip and return existing PO id
   - Create PO in submitted status (not draft)
   - PO number format: SB-AUTO-{YYYY}-{NNNNNN}
   - quantity = product.reorder_quantity
   - unit_price = product.unit_price (last known price)
   - created_by = system user (id of the admin seed user)
   - Activity: send_reorder_email(po_id, product_id)
     Send to all procurement_manager role users

3. Workflow completes — no overall result needed

### Workflow 2 — Monthly Tier Recalculation
Schedule: last day of month at 23:00 UTC
Cron: "0 23 L * *" (Temporal supports L for last day)
Workflow ID: "tier-recalc-{YYYY-MM}" (monthly uniqueness)

Execution steps:
1. Activity: get_all_active_suppliers()
   Returns list of supplier IDs

2. For each supplier (sequential, not parallel):
   Activity: calculate_supplier_tier(supplier_id, year, month)
   - Fetch supplier record
   - Aggregate metrics for the month:
     total_po_lines: count of POLine records for supplier
       in this month where PO status in received/closed
     backorder_rate: backorders / total_po_lines
     on_time_rate: on-time deliveries / total_po_lines
   - If total_po_lines < 20: mark as insufficient_data=true,
     keep current tier, still write SupplierMetricsHistory row
   - Call tier_scoring.compute_tier_decision() with metrics
   - Update supplier fields:
     current_tier = result.new_tier
     consecutive_on_time = result.consecutive_qualifying_months
     consecutive_late = result.consecutive_underperforming_months
   - Write SupplierMetricsHistory record with all metrics
     and decision_reason from TierDecisionResult
   - Activity: send_tier_change_email(supplier_id)
     Only if tier actually changed (new_tier != old_tier)
     Send to all admin users

3. Activity: send_monthly_summary_email(year, month)
   Send to all admin users after all suppliers processed
   Email contains: count of promotions, demotions, no-changes,
   insufficient data count

### Workflow 3 — Backorder Follow-Up
Trigger: signal from GRNService.complete_grn() after partial
receipt creates backorder records
Workflow ID: "backorder-followup-{grn_id}"

Execution steps:
1. Activity: get_backorder_summary(grn_id)
   Returns list of backorder records for this GRN

2. Activity: send_backorder_notification(grn_id, backorder_list)
   Send to all procurement_manager role users
   Email contains: PO number, product names,
   quantities ordered vs received vs outstanding

3. Workflow completes

## Email Types (9 Total — All Locked in Planning)

1. auto_reorder_created — trigger: auto-reorder PO created
   To: all procurement_manager users
   Subject: "Auto-Reorder PO Created — {product_name}"
   Body: PO number, supplier name, product, quantity, total

2. po_submitted — trigger: PO manually submitted
   To: all admin users
   Subject: "New PO Submitted — {po_number}"
   Body: PO details, submitter name, supplier, total amount

3. po_acknowledged — trigger: PO acknowledged by supplier
   To: PO creator
   Subject: "PO Acknowledged — {po_number}"
   Body: PO number, supplier name, acknowledged timestamp

4. tier_change — trigger: supplier tier changes
   To: all admin users
   Subject: "Supplier Tier Change — {supplier_name}"
   Body: supplier name, old tier, new tier, decision reason

5. monthly_summary — trigger: monthly recalculation complete
   To: all admin users
   Subject: "Monthly Supplier Tier Summary — {YYYY-MM}"
   Body: counts of promotions/demotions/no-changes/insufficient

6. backorder_notification — trigger: partial GRN completion
   To: all procurement_manager users
   Subject: "Backorder Created — {po_number}"
   Body: list of products with outstanding quantities

7. low_stock_alert — trigger: auto-reorder flag set on GRN
   To: all procurement_manager users
   Subject: "Low Stock Alert — {product_name}"
   Body: product name, current stock, reorder point

8. po_cancelled — trigger: PO cancelled
   To: PO creator
   Subject: "PO Cancelled — {po_number}"
   Body: PO number, cancellation timestamp, cancelled by

9. system_health_alert — trigger: health check degraded
   To: all admin users
   Subject: "StockBridge System Alert"
   Body: which service is degraded and since when

## Edge Cases

- Auto-reorder duplicate guard: check for existing PO with
  status submitted and auto_generated=true and product matches
  BEFORE creating. Use SELECT FOR UPDATE to prevent race.
  If duplicate exists return existing PO id, log info, no email.

- Inactive supplier during auto-reorder: log WARNING with
  product_id and supplier_id. Do not raise exception. Continue
  to next product. The activity returns a skip result.

- Insufficient tier data: fewer than 20 PO lines is not an error.
  SupplierMetricsHistory row is still written with
  insufficient_data=true. Current tier is preserved unchanged.

- Email failure: NEVER fails the workflow. Wrap all SendGrid
  calls in try/except. On failure write to email_failure_log
  with all context needed to retry manually. Log ERROR.

- SendGrid sandbox: when ENVIRONMENT is not "production",
  use SendGrid's sandbox mode (mail_settings.sandbox_mode=True).
  Emails appear in SendGrid activity but are not delivered.
  This prevents test emails reaching real addresses.

- Temporal worker crash mid-workflow: Temporal's durable
  execution guarantees activities are retried automatically.
  All activities must be idempotent — safe to run twice.

- Missing preferred_supplier on product: skip the product
  during auto-reorder. Log WARNING. This is a data quality
  issue to fix via admin, not an error condition.

- Tier recalculation for new supplier with no history:
  total_po_lines = 0 → insufficient_data = true.
  Current tier stays Silver (default). No email sent.

- System user for auto-generated POs: the PO created_by field
  must reference a real user UUID. Use the admin user created
  by migration 011. Cache this UUID in the worker at startup.

## Error Scenarios

| Scenario                           | Behavior                      |
|------------------------------------|-------------------------------|
| SendGrid API error                 | Log to email_failure_log, continue |
| SendGrid invalid API key           | Log ERROR, mark all pending emails as failed |
| Database unavailable in activity   | Temporal retries up to 3 times |
| Supplier not found in tier calc    | Log ERROR, skip supplier, continue |
| Product not found in auto-reorder  | Log ERROR, skip product, continue |
| Workflow already running same ID   | Temporal deduplicates — no action |
| Worker crashes mid-workflow        | Temporal resumes from last completed activity |

## Test Cases

### Unit Tests — test_auto_reorder_workflow.py
  test_get_reorder_eligible_products_returns_correct_products
  test_get_reorder_eligible_excludes_inactive_supplier
  test_get_reorder_eligible_excludes_no_preferred_supplier
  test_get_reorder_eligible_excludes_existing_open_po
  test_create_auto_reorder_po_creates_in_submitted_status
  test_create_auto_reorder_po_uses_auto_format_number
  test_create_auto_reorder_po_idempotent_returns_existing
  test_create_auto_reorder_po_inactive_supplier_skips
  test_auto_reorder_po_number_format_is_SB_AUTO_YYYY_NNNNNN

### Unit Tests — test_tier_recalculation_workflow.py
  test_calculate_supplier_tier_calls_compute_tier_decision
  test_calculate_supplier_tier_writes_metrics_history
  test_calculate_supplier_tier_updates_supplier_fields
  test_calculate_supplier_tier_insufficient_data_preserved
  test_calculate_supplier_tier_no_email_if_tier_unchanged
  test_calculate_supplier_tier_sends_email_if_tier_changed
  test_monthly_summary_sent_after_all_suppliers_processed

### Unit Tests — test_email_activities.py
  test_send_email_uses_sandbox_in_non_production
  test_send_email_uses_real_sendgrid_in_production
  test_send_email_failure_logs_to_email_failure_log
  test_send_email_failure_does_not_raise
  test_send_email_failure_sets_retry_count
  test_email_failure_log_resolved_flag_defaults_false

## Implementation Notes

- worker.py starts the Temporal worker process. It registers
  all workflows and activities. It is the entry point for the
  temporal-worker Docker service. On startup it fetches and
  caches the system admin user UUID for auto-generated POs.

- All activities use @activity.defn decorator from temporalio.
  All workflows use @workflow.defn decorator. Never mix
  activity and workflow code in the same function.

- Workflow schedules are registered at worker startup using
  Temporal's schedule API not hardcoded cron in Docker.

- email_service.py wraps the SendGrid Python SDK. Single
  method: send(to_emails, subject, body, email_type).
  Reads SENDGRID_API_KEY from settings. Reads ENVIRONMENT
  from settings to determine sandbox mode. Never called
  directly from services — only from email_activities.py.

- email_failure_log table fields:
  id (UUID PK), email_type, to_emails (JSON array),
  subject, body, error_message, retry_count (default 0),
  resolved (default false), workflow_id, activity_id,
  created_at, updated_at.

- Auto-reorder PO number uses a separate sequence from manual
  POs. Format: SB-AUTO-{YYYY}-{NNNNNN}. po_number_service.py
  gets a new method: generate_auto_po_number(session, year).

- add auto_generated boolean column to purchase_orders table
  via migration 019. Default false. Auto-reorder workflow sets
  true. This column is what the duplicate guard queries.

- Metrics aggregation for tier recalculation:
  total_po_lines: COUNT of POLine records where PO supplier_id
    matches and PO status in (received, closed) and
    PO received_at is within the target month
  backorder_count: COUNT of Backorder records where
    original_po_id matches those POs
  backorder_rate: backorder_count / total_po_lines (Decimal)
  on_time_rate: placeholder 0.90 in Phase 5 — actual
    delivery tracking is a future enhancement. Document
    this clearly in the code with a TODO comment that is
    the ONLY permitted TODO in the codebase.

- Temporal connection settings from config:
  TEMPORAL_HOST (default: temporal)
  TEMPORAL_PORT (default: 7233)
  TEMPORAL_NAMESPACE (default: default)
  TEMPORAL_TASK_QUEUE (default: stockbridge-main)

- Register grns router signal endpoint in Phase 5:
  POST /grns/{id}/signal-backorder-followup is called
  internally by grn_service.complete_grn() after commit
  to trigger the backorder workflow. This is not a user-
  facing endpoint — it is an internal service call.
  Alternatively use Temporal client directly from grn_service
  post-commit to start the workflow. Use direct client call —
  cleaner than an HTTP endpoint.

- RBAC for any new endpoints: none in this phase —
  all triggers are internal (cron or service calls).
