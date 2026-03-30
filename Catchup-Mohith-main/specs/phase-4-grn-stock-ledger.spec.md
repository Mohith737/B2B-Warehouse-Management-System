# specs/phase-4-grn-stock-ledger.spec.md
# Phase 4 — GRN and Stock Ledger Spec

## Purpose
This phase makes inventory numbers real. Every stock movement
in StockBridge traces back to a ledger entry created here.
GRN (Goods Receipt Note) is the process of receiving physical
goods against a Purchase Order. When goods arrive, a GRN is
created, lines are received, stock increases via ledger entries,
and the PO transitions toward closed. This phase enforces the
most critical invariant in the system: current_stock is never
written directly — it is always the sum of ledger entries.

## Scope

### In Scope
backend/app/models/grn.py
backend/app/models/grn_line.py
backend/app/models/stock_ledger.py
backend/app/models/backorder.py
backend/app/schemas/grn.py
backend/app/schemas/stock_ledger.py
backend/app/repositories/grn_repository.py
backend/app/repositories/grn_line_repository.py
backend/app/repositories/stock_ledger_repository.py
backend/app/repositories/backorder_repository.py
backend/app/services/stock_ledger_service.py
backend/app/services/grn_service.py
backend/app/routers/grns.py
backend/alembic/versions/014_create_grns.py
backend/alembic/versions/015_create_grn_lines.py
backend/alembic/versions/016_create_stock_ledger.py
backend/alembic/versions/017_create_backorders.py
backend/tests/unit/test_grn_service.py
backend/tests/unit/test_stock_ledger_service.py
backend/tests/integration/test_grn_endpoints.py
backend/tests/integration/test_stock_ledger.py

### Out of Scope
Temporal auto-reorder workflow — Phase 5 reads auto_reorder
  trigger set by GRN completion but does not implement here.
Frontend GRN wizard — Phase 8.
Email notifications — Phase 5.
SendGrid integration — Phase 5.

## Acceptance Criteria

1.  POST /grns creates GRN against a shipped PO only —
    non-shipped PO returns HTTP 400 INVALID_STATE_TRANSITION
2.  POST /grns with invalid PO ID returns HTTP 404
3.  POST /grns/{id}/lines adds a receipt line to a GRN
4.  POST /grns/{id}/lines with quantity exceeding
    remaining_quantity returns HTTP 400 OVER_RECEIPT
5.  POST /grns/{id}/lines with barcode that does not match
    the product on the PO line returns HTTP 400 BARCODE_MISMATCH
6.  POST /grns/{id}/complete completes the GRN — transitions
    PO to received if all lines fully received
7.  POST /grns/{id}/complete with partial receipt automatically
    creates a Backorder for unreceived quantities
8.  POST /grns/{id}/complete sets auto_reorder_triggered=true
    on the GRN if any product falls below reorder threshold
9.  GET /grns returns paginated list default 20 max 50
10. GET /grns/{id} returns GRN with all lines
11. GET /stock-ledger returns cursor-paginated ledger entries
    — never offset pagination
12. GET /stock-ledger?product_id={id} filters by product
13. GET /stock-ledger returns next_cursor in meta when more
    results exist, null when on last page
14. current_stock on Product is updated via ledger entry only
    — never via direct assignment
15. Each GRN line receipt creates exactly one StockLedger entry
    with change_type grn_receipt
16. Stock ledger entry quantity_change is always positive for
    receipts — negative for reservations
17. Completing a GRN with all lines fully received transitions
    PO status from shipped to received
18. Warehouse staff can create GRNs and add lines
19. All unit tests pass
20. All integration tests pass
21. ruff check backend/ passes
22. black --check backend/ passes

## GRN Lifecycle

States: open → completed

A GRN is created in open state against a shipped PO.
Lines are added one at a time via POST /grns/{id}/lines.
When POST /grns/{id}/complete is called:
  - Each PO line is checked: received_qty vs ordered_qty
  - If all lines fully received: PO transitions to received
  - If any line partially received: backorder created for gap
  - auto_reorder_triggered set if any product below threshold
  - GRN status set to completed
  - completed_at set to utcnow

A completed GRN cannot have lines added to it.
A GRN can only be created against a PO in shipped status.

## Stock Ledger Rules — Critical

These rules are absolute and must never be violated:

Rule 1: current_stock is NEVER written directly on the Product
model. It is always computed as the running balance from ledger
entries. StockLedgerService.add_entry() is the ONLY place that
updates current_stock.

Rule 2: add_entry() fetches the product with SELECT FOR UPDATE
before updating current_stock. This prevents concurrent GRN
receipts from creating race conditions.

Rule 3: quantity_change in ledger entries:
  grn_receipt: always positive (stock increases)
  po_reservation: always negative (stock decreases)
  manual_adjustment: positive or negative
  reorder_auto: always positive
  backorder_fulfillment: always positive

Rule 4: current_stock must never go below zero from a ledger
entry. If an entry would make current_stock negative raise
InsufficientStockException.

Rule 5: The ledger is append-only. Entries are never deleted
or updated. Corrections are made via new entries.

Rule 6: Cursor pagination on stock ledger uses the entry ID
(UUID) as cursor. Client passes ?cursor={last_id} to get
the next page. Response includes next_cursor in meta.

## Barcode Verification Rules

When a GRN line is added with a barcode:
1. Look up the product by barcode
2. Verify the product matches the product_id on the PO line
   being received
3. If barcode not found: raise NotFoundException
4. If barcode found but product does not match PO line:
   raise BarcodeMismatchException HTTP 400 BARCODE_MISMATCH
5. If barcode matches: proceed with receipt

Barcode is optional on GRN lines. If no barcode provided,
product_id must be provided directly and must match a PO line.

## Backorder Logic

When GRN is completed with partial receipt:
For each PO line where received_qty < ordered_qty:
  Create a Backorder record with:
    original_po_id: the PO being received against
    product_id: the product that was under-received
    quantity_ordered: the original PO line quantity
    quantity_received: what was actually received
    quantity_outstanding: ordered - received
    status: open
    grn_id: the completing GRN

Backorder is informational in this phase. Phase 5 Temporal
workflow handles auto-reorder from backorders.

## Edge Cases

- Over-receipt: quantity_received on a GRN line cannot exceed
  the remaining quantity on the PO line (ordered minus already
  received from prior GRNs against same PO line). Raise
  OverReceiptException HTTP 400 OVER_RECEIPT.

- Multiple GRNs against one PO: a PO can have multiple GRNs
  if partial receipts are done over time. Each GRN adds to
  the running received total on each PO line.

- Duplicate GRN line for same product: a single GRN cannot
  have two lines for the same product. Raise ConflictException.

- Completing already completed GRN: raise
  InvalidStateTransitionException.

- GRN against non-shipped PO: raise
  InvalidStateTransitionException with current PO status in
  details.

- Auto-reorder threshold check: after completing GRN, for each
  product received check if current_stock <= reorder_point
  (or low_stock_threshold_override if set). If yes set
  auto_reorder_triggered=true on the GRN. This is a flag only
  in Phase 4 — Phase 5 Temporal workflow acts on it.

- SessionStorage note: the GRN wizard in Phase 8 frontend
  persists wizard state in sessionStorage. GRN service must
  complete atomically — partial completion is not allowed.
  Either all stock entries and backorders are created or none.

- Zero quantity GRN line: quantity_received must be > 0.
  Pydantic validator enforces this.

## Error Scenarios

| Scenario                          | HTTP | Error Code                |
|-----------------------------------|------|---------------------------|
| PO not found                      | 404  | NOT_FOUND                 |
| GRN not found                     | 404  | NOT_FOUND                 |
| Product not found                 | 404  | NOT_FOUND                 |
| Barcode not found                 | 404  | NOT_FOUND                 |
| PO not in shipped status          | 400  | INVALID_STATE_TRANSITION  |
| GRN already completed             | 400  | INVALID_STATE_TRANSITION  |
| Over-receipt                      | 400  | OVER_RECEIPT              |
| Barcode does not match PO line    | 400  | BARCODE_MISMATCH          |
| Insufficient stock                | 400  | INSUFFICIENT_STOCK        |
| Duplicate product in GRN          | 409  | CONFLICT                  |
| Staff creates GRN                 | 200  | allowed                   |
| cursor pagination invalid cursor  | 400  | INVALID_CURSOR            |

Add to exceptions.py:
  OverReceiptException — OVER_RECEIPT → 400
  BarcodeMismatchException — BARCODE_MISMATCH → 400
  InsufficientStockException — INSUFFICIENT_STOCK → 400
  InvalidCursorException — INVALID_CURSOR → 400

## Test Cases

### Unit Tests — test_stock_ledger_service.py
  test_add_entry_increases_current_stock
  test_add_entry_uses_select_for_update
  test_add_entry_negative_change_decreases_stock
  test_add_entry_would_make_stock_negative_raises_insufficient
  test_add_entry_creates_ledger_record
  test_get_page_returns_cursor_meta_when_more_exist
  test_get_page_returns_null_cursor_on_last_page

### Unit Tests — test_grn_service.py
  test_create_grn_against_shipped_po_succeeds
  test_create_grn_against_non_shipped_raises_invalid_transition
  test_add_line_over_receipt_raises_over_receipt
  test_add_line_barcode_mismatch_raises_barcode_mismatch
  test_add_line_duplicate_product_raises_conflict
  test_complete_grn_all_lines_full_transitions_po_to_received
  test_complete_grn_partial_creates_backorder
  test_complete_grn_sets_auto_reorder_flag_when_below_threshold
  test_complete_already_completed_raises_invalid_transition
  test_complete_grn_is_atomic

### Integration Tests — test_grn_endpoints.py
  test_create_grn_returns_201
  test_create_grn_against_draft_po_returns_400
  test_add_grn_line_returns_201
  test_add_grn_line_over_receipt_returns_400
  test_add_grn_line_barcode_mismatch_returns_400
  test_complete_grn_returns_200
  test_complete_grn_partial_creates_backorder
  test_complete_grn_updates_po_status_to_received
  test_complete_already_completed_returns_400
  test_get_grn_returns_200_with_lines
  test_list_grns_pagination_default_20

### Integration Tests — test_stock_ledger.py
  test_grn_receipt_creates_ledger_entry
  test_ledger_entry_updates_current_stock
  test_cursor_pagination_first_page
  test_cursor_pagination_second_page_with_cursor
  test_cursor_pagination_last_page_has_null_cursor
  test_filter_by_product_id
  test_concurrent_receipt_no_negative_stock

## Implementation Notes

- StockLedgerService.add_entry(session, product_id,
  quantity_change, change_type, reference_id, notes):
  Step 1: SELECT product FOR UPDATE
  Step 2: Compute new_stock = current_stock + quantity_change
  Step 3: If new_stock < 0 raise InsufficientStockException
  Step 4: product.current_stock = new_stock
  Step 5: Create StockLedger entry
  Step 6: Flush (do not commit — caller owns transaction)

- GRNService.complete_grn() is fully atomic:
  All stock entries and backorder creation happen in one
  transaction. If any step fails everything rolls back.

- Cursor pagination implementation:
  GET /stock-ledger?cursor={uuid}&limit=20
  Query: WHERE id > cursor ORDER BY id ASC LIMIT limit+1
  If len(results) > limit: next_cursor = results[limit].id
  Return results[:limit] and next_cursor in meta.
  If cursor is not a valid UUID raise InvalidCursorException.

- GRN model fields: id, po_id, status, completed_at,
  auto_reorder_triggered, created_by, created_at, updated_at.
  No soft delete on GRN — receipts are permanent records.

- GRNLine model fields: id, grn_id, product_id,
  quantity_received, unit_cost, barcode_scanned,
  created_at, updated_at.
  UniqueConstraint on (grn_id, product_id).

- StockLedger model fields: id, product_id, quantity_change,
  change_type, reference_id, notes, balance_after,
  created_at. No updated_at — ledger is append-only.
  balance_after stores current_stock value after this entry.

- Backorder model fields: id, original_po_id, product_id,
  quantity_ordered, quantity_received, quantity_outstanding,
  status, grn_id, created_at, updated_at.

- Register grns router in main.py with prefix /grns.
  Register stock_ledger router with prefix /stock-ledger.
  Add all 4 new exceptions to EXCEPTION_STATUS_MAP.

- RBAC:
  GRN create and add lines: all authenticated users
  GRN complete: PROCUREMENT_MANAGER and ADMIN
  GRN read: all authenticated users
  Stock ledger read: all authenticated users
