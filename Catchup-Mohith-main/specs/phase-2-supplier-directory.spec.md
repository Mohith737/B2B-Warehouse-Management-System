# Phase 2 — Supplier Directory Spec

## Purpose
This phase delivers the supplier directory — the second core
domain entity required before any purchase order can be created.
Suppliers must exist before POs reference them, making this phase
a direct prerequisite for Phase 3 PO lifecycle. The tier scoring
pure function lives here because it is tightly coupled to supplier
state: tier_locked, consecutive streak counters, and current_tier
are all supplier fields that the scoring function reads and
updates. The tier scoring function itself has zero database calls
and is 100% unit testable — a CI gate enforces this. Supplier
credit limits, which the PO service checks during submission in
Phase 3, are also defined here.

## Scope

### In Scope — Implemented in this phase
  backend/app/models/supplier.py
  backend/app/models/supplier_metrics_history.py
  backend/app/schemas/supplier.py
  backend/app/repositories/supplier_repository.py
  backend/app/repositories/supplier_metrics_history_repository.py
  backend/app/services/supplier_service.py
  backend/app/services/tier_scoring.py
  backend/app/routers/suppliers.py
  backend/tests/unit/test_supplier_service.py
  backend/tests/unit/test_tier_scoring.py
  backend/tests/integration/test_supplier_endpoints.py

### Out of Scope — Stubbed only, implemented in later phases
  PO credit check — supplier credit_limit is defined here but
    the enforcement logic lives in Phase 3 PO service.
  Temporal tier recalculation workflow — Phase 5. The
    SupplierMetricsHistory write path is not called from the
    supplier service in this phase. Repository read methods
    are implemented; write methods are stubs.
  Frontend supplier pages — Phase 8.
  Email notifications for tier changes — Phase 5 via Temporal
    email activities.

## Acceptance Criteria
Numbered list. Every item is binary — pass or fail.

1.  GET /suppliers returns paginated list with default
    page_size 20 and maximum 50
2.  GET /suppliers?page_size=51 returns HTTP 400
    PAGE_LIMIT_EXCEEDED
3.  GET /suppliers?search=acme returns suppliers matching
    name case-insensitively (partial match)
4.  GET /suppliers?tier=Gold returns Gold tier suppliers only
5.  GET /suppliers?is_active=false returns inactive suppliers
6.  GET /suppliers/{id} returns supplier with current_tier
    and credit_limit
7.  GET /suppliers/{id}/metrics returns last 12 months of
    SupplierMetricsHistory ordered by period descending
8.  POST /suppliers creates supplier — procurement_manager
    and admin only — warehouse_staff receives HTTP 403
9.  PUT /suppliers/{id} updates supplier — procurement_manager
    and admin only — warehouse_staff receives HTTP 403
10. DELETE /suppliers/{id} soft-deletes supplier — admin
    only — manager and staff receive HTTP 403
11. POST /suppliers/{id}/deactivate sets is_active=false —
    admin only — returns HTTP 403 for non-admin
12. POST /suppliers/{id}/activate sets is_active=true —
    admin only — returns HTTP 403 for non-admin
13. PUT /suppliers/{id}/tier-lock sets tier_locked=true or
    false — admin only — returns HTTP 403 for non-admin
14. tier_scoring.compute_tier_decision returns the correct
    tier for all valid inputs
15. tier_scoring.compute_tier_decision raises
    InsufficientDataException when total_po_lines < 20
16. tier_scoring.compute_tier_decision returns current tier
    unchanged when tier_locked=true
17. tier_scoring.compute_tier_decision uses worst-metric-wins
    — the lowest qualifying metric determines the result
18. test_tier_scoring.py achieves 100% coverage — CI gate
    fails the build if coverage drops below 100%
19. All unit tests pass with pytest backend/tests/unit/
20. All integration tests pass with
    pytest backend/tests/integration/
21. ruff check backend/ passes with zero errors
22. black --check backend/ passes with zero errors

## Edge Cases

- tier_locked=true: compute_tier_decision returns the current
  tier unchanged regardless of metric performance.
  Streak counters (consecutive_qualifying_months and
  consecutive_underperforming_months) still update normally.
  Only the tier assignment is frozen.

- Minimum PO lines: fewer than 20 total_po_lines in the
  evaluation period raises InsufficientDataException. Exactly
  20 is sufficient and must not raise.

- Worst-metric-wins: each metric is evaluated independently
  for the tier it would qualify for. The minimum resulting
  tier across all metrics is returned. Example: if
  backorder_rate qualifies for Gold but on_time_rate only
  qualifies for Silver, the final result is Silver.

- Streak counters: consecutive_qualifying_months increments
  when performance meets the next tier threshold.
  consecutive_underperforming_months increments when
  performance falls below the demotion threshold.
  Each resets to 0 when the direction reverses.
  Promotion requires 3 consecutive qualifying months.
  Demotion requires 2 consecutive underperforming months.

- New supplier with no metrics history: treated as
  insufficient data. Remains at default Silver tier.
  No exception is raised at supplier creation — only at
  scoring time when fewer than 20 PO lines exist.

- Inactive supplier: can still be read and have metrics
  history. Cannot be selected as preferred_supplier on a
  product. Cannot receive auto-reorder POs (Phase 5 checks
  is_active before creating reorder POs).

- Soft delete vs deactivate: soft delete (DELETE endpoint)
  sets deleted_at and removes the supplier from all listings.
  Deactivate (POST /deactivate) keeps the supplier visible
  in listings but sets is_active=false and blocks PO creation.

- Credit limit override: admin can set credit_limit directly
  on the supplier record. This is the authoritative value the
  PO service checks in Phase 3. There is no tier-based
  automatic credit limit in this system — it is always
  manually set by admin.

- Duplicate supplier name is allowed — two suppliers may
  share a trading name. Duplicate email is not allowed —
  the email column has a unique constraint.

- Metrics endpoint returns at most 12 months of history,
  ordered most recent first. Returns an empty list if no
  history exists — never returns 404.

## Error Scenarios

| Scenario                          | HTTP | Error Code          |
|-----------------------------------|------|---------------------|
| Supplier not found                | 404  | NOT_FOUND           |
| Soft-deleted supplier lookup      | 404  | NOT_FOUND           |
| Duplicate supplier email          | 409  | CONFLICT            |
| Staff creates supplier            | 403  | PERMISSION_DENIED   |
| Staff or manager deletes supplier | 403  | PERMISSION_DENIED   |
| Staff or manager deactivates      | 403  | PERMISSION_DENIED   |
| Staff or manager activates        | 403  | PERMISSION_DENIED   |
| Staff or manager tier-locks       | 403  | PERMISSION_DENIED   |
| page_size exceeds 50              | 400  | PAGE_LIMIT_EXCEEDED |
| total_po_lines fewer than 20      | 400  | INSUFFICIENT_DATA   |

All error responses use the standard envelope:
{
  "error": {
    "code": "ERROR_CODE_STRING",
    "message": "Human readable description",
    "details": {}
  }
}

## Test Cases

### Unit Tests — test_tier_scoring.py
100% coverage is a CI gate. Every branch must be tested.

  test_compute_tier_insufficient_data_below_20_lines
    total_po_lines=19 raises InsufficientDataException

  test_compute_tier_insufficient_data_zero_lines
    total_po_lines=0 raises InsufficientDataException

  test_compute_tier_exactly_20_lines_is_sufficient
    total_po_lines=20 does not raise — returns a result

  test_compute_tier_locked_supplier_tier_unchanged
    tier_locked=True returns current_tier unchanged

  test_compute_tier_locked_streaks_still_update
    tier_locked=True but streak counters still increment

  test_compute_tier_worst_metric_wins_backorder_overrides_ontime
    backorder_rate qualifies Gold, on_time_rate qualifies
    Silver → result is Silver

  test_compute_tier_worst_metric_wins_ontime_overrides_backorder
    on_time_rate qualifies Gold, backorder_rate qualifies
    Silver → result is Silver

  test_compute_tier_silver_to_gold_requires_3_consecutive
    2 consecutive qualifying months → stays Silver
    3 consecutive qualifying months → promotes to Gold

  test_compute_tier_gold_to_diamond_requires_3_consecutive
    2 consecutive qualifying months at Gold → stays Gold
    3 consecutive qualifying months at Gold → promotes Diamond

  test_compute_tier_demotion_requires_2_consecutive
    1 underperforming month → stays at current tier
    2 underperforming months → demotes

  test_compute_tier_streak_resets_on_direction_change
    2 qualifying months then 1 underperforming →
    qualifying streak resets to 0

  test_compute_tier_new_supplier_no_history_stays_silver
    total_po_lines=0 raises InsufficientDataException
    (handled gracefully by caller, not a fatal error)

  test_compute_tier_all_thresholds_silver_boundaries
    backorder_rate=10.1% at Silver → stays Silver (not Gold)
    backorder_rate=10.0% at Silver after 3 months → Gold

  test_compute_tier_all_thresholds_gold_boundaries
    backorder_rate=5.1% at Gold → stays Gold (not Diamond)
    backorder_rate=5.0% at Gold after 3 months → Diamond

  test_compute_tier_all_thresholds_diamond_boundaries
    backorder_rate=30.1% at Diamond for 2 months → demotes
    backorder_rate=30.0% at Diamond → stays Diamond

### Unit Tests — test_supplier_service.py
  test_create_supplier_success
  test_create_supplier_duplicate_email_raises_conflict
  test_get_supplier_not_found_raises_not_found
  test_deactivate_supplier_sets_is_active_false
  test_activate_supplier_sets_is_active_true
  test_tier_lock_sets_tier_locked_true
  test_list_suppliers_filters_by_tier
  test_list_suppliers_filters_by_active_status

### Integration Tests — test_supplier_endpoints.py
  test_create_supplier_returns_201
  test_create_supplier_duplicate_email_returns_409
  test_create_supplier_staff_returns_403
  test_get_supplier_returns_200
  test_get_supplier_metrics_returns_list
  test_update_supplier_returns_200
  test_deactivate_supplier_admin_only
  test_activate_supplier_admin_only
  test_tier_lock_admin_only_returns_200
  test_list_suppliers_pagination_default_20
  test_list_suppliers_filter_by_tier
  test_list_suppliers_filter_by_active
  test_list_suppliers_search_by_name
  test_delete_supplier_admin_only_returns_200
  test_delete_supplier_manager_returns_403

## Implementation Notes

- tier_scoring.py is a pure function module. Zero database
  calls. Zero imports from models, repositories, or services.
  Input: TierScoringInput dataclass.
  Output: TierDecisionResult dataclass.
  Both dataclasses defined in tier_scoring.py itself.

- TierScoringInput fields:
    total_po_lines: int
    backorder_rate: Decimal        (0.0 to 1.0 as fraction)
    on_time_rate: Decimal          (0.0 to 1.0 as fraction)
    current_tier: str              ("Silver", "Gold", "Diamond")
    tier_locked: bool
    consecutive_qualifying_months: int
    consecutive_underperforming_months: int

- TierDecisionResult fields:
    new_tier: str
    consecutive_qualifying_months: int
    consecutive_underperforming_months: int
    decision_reason: str
    insufficient_data: bool

- Tier promotion thresholds (locked — never change without
  explicit spec change):
    Silver → Gold:
      backorder_rate <= 0.10 AND on_time_rate >= 0.90
      for 3 consecutive qualifying months
    Gold → Diamond:
      backorder_rate <= 0.05 AND on_time_rate >= 0.95
      for 3 consecutive qualifying months

- Tier demotion thresholds (same for Gold and Diamond):
    Demotion trigger:
      backorder_rate > 0.30 OR on_time_rate < 0.70
      for 2 consecutive underperforming months
    Gold → Silver on demotion
    Diamond → Gold on demotion

- Worst-metric-wins algorithm:
    Step 1: For each metric, determine what tier it qualifies
            for independently.
    Step 2: Take the minimum (lowest) tier across all metrics.
    Step 3: Apply streak and locked logic to that minimum.

- SupplierMetricsHistory writes happen in Phase 5 via the
  Temporal tier recalculation workflow. In this phase,
  SupplierMetricsHistoryRepository implements:
    get_last_n_months(supplier_id, n=12) — read only
    The write method create() is inherited from BaseRepository
    but not called from SupplierService.

- IntegrityError catch on email: same pattern as Phase 2
  product SKU. Pre-check with email_exists() before insert,
  then catch IntegrityError as fallback for race conditions.

- SupplierRead schema must include: id, name, email, phone,
  address, payment_terms_days, lead_time_days, credit_limit,
  current_tier, tier_locked, consecutive_on_time,
  consecutive_late, is_active, created_at, updated_at.

- SupplierCreate must not include: current_tier, tier_locked,
  consecutive_on_time, consecutive_late — these are managed
  by the system not by the client.

- Metrics endpoint GET /suppliers/{id}/metrics returns:
  ListResponse[SupplierMetricsHistoryRead] with no pagination
  — always returns up to 12 months, ordered by period
  descending (most recent first). Empty list if no history.

- RBAC enforcement:
    Read (list, get, metrics): all authenticated users
    Create / Update: PROCUREMENT_MANAGER, ADMIN
    Deactivate / Activate / TierLock / Delete: ADMIN only

- Register the suppliers router in main.py with prefix
  /suppliers and tag suppliers after generating the router.
