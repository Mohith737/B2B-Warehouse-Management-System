# specs/phase-3-po-lifecycle.spec.md
# Phase 3 — Purchase Order Lifecycle Spec

## Purpose
This phase implements the complete purchase order lifecycle —
the commercial heart of StockBridge. Every stock receipt in
Phase 4 traces back to a PO. Every supplier payment obligation
traces back to a PO. The credit check that prevents over-
commitment runs inside the PO submit transaction. Getting this
phase right is what makes the entire system trustworthy.

This phase builds directly on Phase 2: suppliers and products
must exist before a PO can reference them. Phase 4 GRN
processing depends on POs being in the correct state before
receipts can be created.

## Scope

### In Scope — Implemented in this phase
backend/app/models/purchase_order.py
backend/app/models/po_line.py
backend/app/schemas/purchase_order.py
backend/app/repositories/purchase_order_repository.py
backend/app/repositories/po_line_repository.py
backend/app/services/po_number_service.py
backend/app/services/po_state_machine.py
backend/app/services/purchase_order_service.py
backend/app/routers/purchase_orders.py
backend/tests/unit/test_po_state_machine.py
backend/tests/unit/test_purchase_order_service.py
backend/tests/integration/test_po_lifecycle_api.py
backend/tests/integration/test_po_credit_limit.py

### Out of Scope — Stubbed only, implemented in later phases
GRN creation — Phase 4 depends on POs in shipped status.
Stock ledger writes — Phase 4.
Temporal auto-reorder workflow — Phase 5 creates POs in
  submitted state directly. PO model supports this.
SendGrid email on PO submit — Phase 5 Temporal activity.
Frontend PO wizard — Phase 8.

## Acceptance Criteria
Numbered list. Every item is binary — pass or fail.

1.  POST /purchase-orders creates PO in draft status with
    auto-generated PO number
2.  POST /purchase-orders with no lines returns HTTP 422
3.  POST /purchase-orders with inactive supplier returns
    HTTP 400 SUPPLIER_INACTIVE
4.  POST /purchase-orders — warehouse_staff returns HTTP 403
5.  GET /purchase-orders returns paginated list default 20
    max 50
6.  GET /purchase-orders?status=submitted returns only
    submitted POs
7.  GET /purchase-orders?supplier_id={id} filters by supplier
8.  GET /purchase-orders/{id} returns PO with all lines
9.  PUT /purchase-orders/{id} updates draft PO lines and notes
10. PUT /purchase-orders/{id} on non-draft PO returns HTTP 400
    INVALID_STATE_TRANSITION
11. POST /purchase-orders/{id}/submit transitions draft to
    submitted — checks credit limit inside transaction
12. POST /purchase-orders/{id}/submit when credit would be
    exceeded returns HTTP 400 CREDIT_LIMIT_EXCEEDED with
    exact gap amount in details
13. POST /purchase-orders/{id}/acknowledge transitions
    submitted to acknowledged — manager and admin only
14. POST /purchase-orders/{id}/mark-shipped transitions
    acknowledged to shipped — manager and admin only
15. POST /purchase-orders/{id}/cancel cancels from draft or
    submitted only — returns HTTP 400 for other states
16. POST /purchase-orders/{id}/cancel on acknowledged or
    shipped PO returns HTTP 400 INVALID_STATE_TRANSITION
17. DELETE /purchase-orders/{id} soft-deletes draft PO only —
    admin only — non-draft returns HTTP 400
18. GET /purchase-orders?created_by=me returns only POs
    created by the current user (staff sees only own POs)
19. PO number is unique, sequential-looking, and never reused
20. total_amount on PO is sum of all line totals, updated
    on every line change
21. All unit tests pass
22. All integration tests pass
23. ruff check backend/ passes
24. black --check backend/ passes

## State Machine

States: draft → submitted → acknowledged → shipped →
        received → closed

Cancellation: allowed from draft and submitted only.
              acknowledged and shipped cannot be cancelled.

Legal transitions:
  draft       → submitted    (POST /submit)
  draft       → cancelled    (POST /cancel)
  submitted   → acknowledged (POST /acknowledge)
  submitted   → cancelled    (POST /cancel)
  acknowledged → shipped     (POST /mark-shipped)
  shipped     → received     (set by GRN service in Phase 4)
  received    → closed       (set by GRN service in Phase 4)

Illegal transitions raise InvalidStateTransitionException
with details showing current state and attempted transition.

State timestamps: submitted_at, acknowledged_at, shipped_at,
received_at, closed_at — set to UTC now on each transition.

## Credit Check — Critical Rules

The credit check runs INSIDE the submit transaction.
Never run it before opening the transaction.
Never run it after the transaction has committed.

Algorithm:
1. Open transaction
2. SELECT SUM(total_amount) FROM purchase_orders
   WHERE supplier_id = {id}
   AND status IN ('submitted', 'acknowledged', 'shipped')
   AND id != {current_po_id}
   FOR UPDATE  ← locks rows to prevent concurrent race
3. Add current PO total_amount to the sum
4. Compare to supplier.credit_limit
5. If total > credit_limit:
   raise CreditLimitExceededException with details:
     credit_limit: supplier.credit_limit
     current_exposure: existing open PO total
     this_po_amount: current PO total_amount
     gap: (current_exposure + this_po_amount) - credit_limit
6. If within limit: update status to submitted, set
   submitted_at, commit

The gap amount in the error details is what the frontend
displays to the manager explaining exactly how much over
the limit this PO would push the supplier exposure.

## Edge Cases

- Empty PO: a PO must have at least one line. POST create
  with empty lines array returns 422 validation error.

- Zero quantity line: each POLine quantity_ordered must be
  > 0. Pydantic validator enforces this.

- Duplicate product in lines: two lines with the same
  product_id in one PO are not allowed. Service checks
  before insert and raises ConflictException.

- Credit check with zero credit limit: if supplier
  credit_limit is 0.00, any PO submission fails with
  CREDIT_LIMIT_EXCEEDED. Zero means no credit extended.

- Credit check excludes received and closed POs: only
  submitted, acknowledged, shipped POs count as open
  exposure. Received and closed are settled obligations.

- Soft deleted PO: GET returns 404. State transitions on
  soft deleted PO return 404.

- PO number generation: format SB-{YYYY}-{NNNNNN} where
  YYYY is current year and NNNNNN is zero-padded sequence.
  Example: SB-2025-000001. Sequence is per-year. Uses
  database sequence or MAX+1 with row lock to prevent gaps
  or duplicates under concurrency.

- Staff visibility: warehouse_staff can only see POs they
  created. procurement_manager and admin see all POs.
  Enforced at repository query level, not in router.

- Update on non-draft: only draft POs can be edited.
  Any PUT on submitted or later state raises
  InvalidStateTransitionException.

- line_total: computed as quantity_ordered * unit_price.
  Stored as a regular Numeric column, updated by service
  on every line write. Not a database generated column
  (avoids SQLAlchemy complexity with generated columns).

- total_amount on PO header: recomputed as SUM of all
  line_totals after every line add/update/remove. Service
  calls _recalculate_total() after any line change.

- Cancellation sets cancelled_at timestamp and status to
  cancelled. Cancelled POs are visible in listings with
  status filter but excluded from credit exposure calculation.

## Error Scenarios

| Scenario                         | HTTP | Error Code                    |
|----------------------------------|------|-------------------------------|
| PO not found                     | 404  | NOT_FOUND                     |
| Supplier not found               | 404  | NOT_FOUND                     |
| Product not found in line        | 404  | NOT_FOUND                     |
| Supplier inactive                | 400  | SUPPLIER_INACTIVE             |
| Illegal state transition         | 400  | INVALID_STATE_TRANSITION      |
| Credit limit exceeded            | 400  | CREDIT_LIMIT_EXCEEDED         |
| Duplicate product in lines       | 409  | CONFLICT                      |
| Staff creates PO                 | 403  | PERMISSION_DENIED             |
| Staff cancels PO                 | 403  | PERMISSION_DENIED             |
| Non-admin deletes PO             | 403  | PERMISSION_DENIED             |
| page_size exceeds 50             | 400  | PAGE_LIMIT_EXCEEDED           |
| Empty lines on create            | 422  | (Pydantic validation)         |
| Zero quantity line               | 422  | (Pydantic validation)         |

Add these to exceptions.py if not already present:
  SupplierInactiveException — code SUPPLIER_INACTIVE → 400

## Test Cases

### Unit Tests — test_po_state_machine.py
  test_draft_to_submitted_is_legal
  test_draft_to_cancelled_is_legal
  test_submitted_to_acknowledged_is_legal
  test_submitted_to_cancelled_is_legal
  test_acknowledged_to_shipped_is_legal
  test_shipped_to_received_is_legal
  test_received_to_closed_is_legal
  test_draft_to_acknowledged_is_illegal
  test_draft_to_shipped_is_illegal
  test_acknowledged_to_cancelled_is_illegal
  test_shipped_to_cancelled_is_illegal
  test_closed_to_any_is_illegal
  test_cancelled_to_any_is_illegal

### Unit Tests — test_purchase_order_service.py
  test_create_po_success_returns_po_with_number
  test_create_po_inactive_supplier_raises_supplier_inactive
  test_create_po_empty_lines_raises_validation_error
  test_create_po_duplicate_product_in_lines_raises_conflict
  test_submit_po_within_credit_limit_succeeds
  test_submit_po_exceeds_credit_limit_raises_with_gap
  test_submit_po_zero_credit_limit_always_fails
  test_submit_po_excludes_received_closed_from_exposure
  test_cancel_po_from_draft_succeeds
  test_cancel_po_from_submitted_succeeds
  test_cancel_po_from_acknowledged_raises_invalid_transition
  test_update_po_draft_succeeds
  test_update_po_non_draft_raises_invalid_transition
  test_recalculate_total_sums_all_line_totals

### Integration Tests — test_po_lifecycle_api.py
  test_create_po_returns_201_with_po_number
  test_create_po_staff_returns_403
  test_create_po_inactive_supplier_returns_400
  test_get_po_returns_200_with_lines
  test_get_po_not_found_returns_404
  test_list_pos_pagination_default_20
  test_list_pos_filter_by_status
  test_list_pos_filter_by_supplier
  test_staff_sees_only_own_pos
  test_submit_po_returns_200_submitted_status
  test_submit_po_sets_submitted_at_timestamp
  test_acknowledge_po_returns_200
  test_mark_shipped_returns_200
  test_cancel_from_draft_returns_200
  test_cancel_from_acknowledged_returns_400
  test_update_draft_po_returns_200
  test_update_submitted_po_returns_400
  test_delete_draft_po_admin_only

### Integration Tests — test_po_credit_limit.py
  test_submit_within_limit_succeeds
  test_submit_exactly_at_limit_succeeds
  test_submit_one_cent_over_limit_fails
  test_credit_check_includes_all_open_pos
  test_credit_check_excludes_received_pos
  test_credit_check_excludes_closed_pos
  test_credit_check_excludes_cancelled_pos
  test_error_details_contain_gap_amount

## Implementation Notes

- po_number_service.py generates PO numbers using format
  SB-{YYYY}-{NNNNNN}. Implementation uses a SELECT MAX
  with row-level lock inside a transaction to get the next
  sequence number for the current year. On first PO of the
  year, starts at 000001. Thread-safe under concurrency.

- po_state_machine.py defines LEGAL_TRANSITIONS as a dict:
  {
    "draft": ["submitted", "cancelled"],
    "submitted": ["acknowledged", "cancelled"],
    "acknowledged": ["shipped"],
    "shipped": ["received"],
    "received": ["closed"],
    "closed": [],
    "cancelled": [],
  }
  validate_transition(current: str, target: str) raises
  InvalidStateTransitionException if target not in
  LEGAL_TRANSITIONS[current].

- purchase_order_service.py owns the submit transaction.
  The credit check SELECT FOR UPDATE and the status update
  happen in the same transaction. Never split across two
  transactions.

- POLine.line_total is a regular Numeric column. Service
  sets line_total = quantity_ordered * unit_price on every
  line create or update. Not a database computed column.

- _recalculate_total(po, session) is a private method on
  PurchaseOrderService. It runs SELECT SUM(line_total) FROM
  po_lines WHERE po_id = {id} and sets po.total_amount.
  Called after every line change before commit.

- Staff RBAC on list: when current user role is
  warehouse_staff, repository adds WHERE created_by = user_id
  to the query automatically. Manager and admin get all POs.

- Catch IntegrityError on PO number generation as fallback.
  Retry once with a fresh sequence number if IntegrityError
  occurs on po_number unique constraint.

- Register purchase_orders router in main.py with prefix
  /purchase-orders and tag purchase-orders.

- Add SupplierInactiveException to exceptions.py with
  code=SUPPLIER_INACTIVE and map to HTTP 400 in main.py
  global exception handler.

- Add cancelled_at column: this was not in migration 005.
  Create migration 015_add_cancelled_at_to_purchase_orders.py
  that adds cancelled_at TIMESTAMP WITH TIME ZONE nullable
  to purchase_orders table.
