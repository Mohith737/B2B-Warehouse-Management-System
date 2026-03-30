# /home/mohith/Catchup-Mohith/specs/phase-2-product-catalog.spec.md
# Phase 2 — Product Catalog Spec

## Purpose
What this phase establishes, why it builds directly on Phase 1,
and what business capability it delivers. Explain that the product
catalog is the foundation for GRN, PO, and stock ledger features
in later phases — nothing can be received, ordered, or tracked
without a product existing first.

## Scope

### In Scope — Implemented in this phase
List every file implemented in Phase 2 product catalog:
  backend/app/models/product.py
  backend/app/schemas/product.py
  backend/app/repositories/product_repository.py
  backend/app/services/product_service.py
  backend/app/routers/products.py
  backend/tests/unit/test_product_service.py
  backend/tests/integration/test_product_endpoints.py

### Out of Scope — Stubbed only, implemented in later phases
Be explicit. Include:
  StockLedgerService — referenced but not implemented here.
    ProductService calls a stub that raises NotImplementedError.
    Full implementation in Phase 4.
  GRN, PO, Backorder models — not referenced in this phase.
  Supplier model — not referenced in this phase.
  Frontend product pages — Phase 8.
  All Temporal workflows — Phase 5.

## Acceptance Criteria
Numbered list. Every item is binary — pass or fail.

1.  GET /products returns paginated list with default page_size 20
2.  GET /products?page_size=101 returns HTTP 400 PAGE_LIMIT_EXCEEDED
3.  GET /products?badge=low_stock returns only low_stock products
4.  GET /products?search=widget returns products matching name
    or SKU (case-insensitive, partial match)
5.  GET /products/{id} returns single product with stock_badge
6.  GET /products/{id} for soft-deleted product returns HTTP 404
7.  GET /products/barcode-lookup?barcode={code} returns product
    or HTTP 404 BARCODE_NOT_FOUND
8.  POST /products creates product — procurement_manager and
    admin only — warehouse_staff receives HTTP 403
9.  PUT /products/{id} updates product — procurement_manager and
    admin only — warehouse_staff receives HTTP 403
10. DELETE /products/{id} soft-deletes product — admin only —
    manager and staff receive HTTP 403
11. PUT /products/{id} with stale version number returns
    HTTP 409 CONFLICT (optimistic locking)
12. PUT /products/{id} with correct version succeeds and
    returns incremented version in response
13. stock_badge is computed server-side on every read:
    out_of_stock when current_stock == 0
    low_stock when current_stock > 0 and current_stock <=
    threshold (low_stock_threshold_override if set,
    otherwise reorder_point)
    in_stock when current_stock > threshold
14. current_stock field is never accepted in POST or PUT
    request body — it is rejected with HTTP 422
15. POST /products with duplicate SKU returns HTTP 409 CONFLICT
16. POST /products with duplicate barcode returns HTTP 409 CONFLICT
17. All unit tests pass with pytest backend/tests/unit/
18. All integration tests pass with pytest backend/tests/integration/
19. product_service.py has minimum 85% test coverage
20. ruff check backend/ passes with zero errors
21. black --check backend/ passes with zero errors

## Edge Cases
Every edge case implementation must handle:

- stock_badge threshold: when low_stock_threshold_override is
  set and greater than 0, it replaces reorder_point entirely
  for badge computation. When it is null or 0, reorder_point
  is used. Never average the two.
- current_stock boundary: a product with current_stock exactly
  equal to reorder_point is low_stock, not in_stock. The
  threshold is inclusive on the low_stock side.
- Zero reorder_point: if reorder_point is 0 and
  low_stock_threshold_override is null, then any product with
  current_stock > 0 is in_stock. Only current_stock == 0 is
  out_of_stock.
- Optimistic locking: version is read from the DB at query
  time. If the version in the PUT request body does not match
  the DB version at update time, raise ConflictException.
  The service must re-fetch the product inside the transaction
  to get the locked version before writing.
- Soft delete visibility: GET /products never returns
  soft-deleted products. GET /products/{id} returns 404 for
  soft-deleted products. The barcode lookup also excludes
  soft-deleted products.
- SKU uniqueness: SKU unique constraint is at the DB level.
  The service must check before insert and raise
  ConflictException with details showing the conflicting SKU,
  not let the DB raise an IntegrityError.
- Barcode uniqueness: same as SKU — check before insert, raise
  ConflictException, never expose raw DB errors.
- Barcode field is optional: a product may have no barcode.
  Barcode lookup on a product with no barcode must not be
  possible. Two products with no barcode is allowed (null is
  not unique-constrained against null in PostgreSQL partial
  index).
- Search is across both name and SKU simultaneously. A search
  term matching either field returns the product. Use ILIKE
  for case-insensitive matching.
- Pagination max enforcement: page_size above 100 is rejected
  at the router layer before hitting the service. The error
  response must use the PAGE_LIMIT_EXCEEDED code.
- current_stock write prevention: the ProductCreate and
  ProductUpdate schemas must not include current_stock as a
  field. If a client sends current_stock in the request body
  it is silently ignored by Pydantic (extra="ignore").
- version field in response: every ProductRead response must
  include the current version integer. This is required by
  the frontend to send correct optimistic lock values on PUT.

## Error Scenarios

| Scenario                        | HTTP | Error Code            |
|---------------------------------|------|-----------------------|
| Product not found               | 404  | NOT_FOUND             |
| Soft-deleted product lookup     | 404  | NOT_FOUND             |
| Barcode not found               | 404  | BARCODE_NOT_FOUND     |
| Duplicate SKU                   | 409  | CONFLICT              |
| Duplicate barcode               | 409  | CONFLICT              |
| Optimistic lock mismatch        | 409  | CONFLICT              |
| page_size exceeds 100           | 400  | PAGE_LIMIT_EXCEEDED   |
| warehouse_staff creates product | 403  | PERMISSION_DENIED     |
| warehouse_staff updates product | 403  | PERMISSION_DENIED     |
| staff or manager deletes product| 403  | PERMISSION_DENIED     |

All error responses use the standard envelope:
{
  "error": {
    "code": "ERROR_CODE_STRING",
    "message": "Human readable description",
    "details": {}
  }
}

Add a NotFoundException to exceptions.py:
  class NotFoundException(StockBridgeException):
      code = "NOT_FOUND"
      message = "Resource not found"
      HTTP mapping: 404

## Test Cases

### Unit Tests (no infrastructure, all dependencies mocked)
  test_compute_stock_badge_out_of_stock_when_zero
  test_compute_stock_badge_low_stock_at_reorder_point
  test_compute_stock_badge_low_stock_uses_override_when_set
  test_compute_stock_badge_in_stock_above_threshold
  test_compute_stock_badge_zero_reorder_point_only_out_of_stock
  test_create_product_raises_conflict_on_duplicate_sku
  test_create_product_raises_conflict_on_duplicate_barcode
  test_update_product_raises_conflict_on_version_mismatch
  test_update_product_succeeds_and_increments_version
  test_get_product_raises_not_found_for_missing_id
  test_get_product_raises_not_found_for_soft_deleted
  test_list_products_filters_by_badge_status
  test_list_products_search_matches_name_and_sku
  test_delete_product_sets_deleted_at
  test_barcode_lookup_raises_barcode_not_found

### Integration Tests (real PostgreSQL)
  test_create_product_returns_201_with_stock_badge
  test_create_product_duplicate_sku_returns_409
  test_create_product_warehouse_staff_returns_403
  test_get_product_returns_200_with_badge
  test_get_soft_deleted_product_returns_404
  test_update_product_returns_200_incremented_version
  test_update_product_stale_version_returns_409
  test_delete_product_admin_only_returns_200
  test_delete_product_manager_returns_403
  test_list_products_pagination_default_20
  test_list_products_page_size_over_100_returns_400
  test_list_products_filter_by_badge
  test_list_products_search_by_name
  test_list_products_search_by_sku
  test_barcode_lookup_returns_product
  test_barcode_lookup_not_found_returns_404

## Implementation Notes
Key decisions that govern how this phase must be built:

- stock_badge is a computed property. It is NOT stored in the
  database. It is computed in ProductService (or a standalone
  pure function) every time a product is read. Never store
  badge in the DB column.

- low_stock_threshold_override is a nullable Numeric column on
  the Product model. When null or zero, reorder_point is the
  threshold. When positive, it fully replaces reorder_point.

- Optimistic locking pattern:
    Step 1: Read product by ID (fails fast if not found).
    Step 2: Open transaction.
    Step 3: SELECT ... FOR UPDATE the product row inside tx.
    Step 4: Compare request.version to locked row version.
    Step 5: If mismatch, raise ConflictException immediately.
    Step 6: Apply updates, increment version by 1, flush.
    Step 7: Commit.

- ProductRepository.get_by_id_for_update uses
  with_for_update() to acquire a row lock. This is the ONLY
  place in the codebase that uses SELECT FOR UPDATE on products.

- current_stock is owned exclusively by StockLedgerService.
  ProductService never sets current_stock directly. In this
  phase, StockLedgerService is a stub that raises
  NotImplementedError. ProductService does not call it in
  Phase 2 — the constraint is enforced by not having
  current_stock in any input schema.

- Version increment: on every successful PUT, the service
  sets product.version = product.version + 1 inside the
  transaction before flush. This is done manually, not via
  SQLAlchemy's built-in optimistic locking, to keep the
  logic explicit and testable.

- Search implementation: ProductRepository.list uses ILIKE
  on both name and SKU columns joined with OR.
    filter = or_(
        Product.name.ilike(f"%{search}%"),
        Product.sku.ilike(f"%{search}%"),
    )
  Applied before pagination.

- Badge filtering: when badge parameter is provided,
  filter in Python after fetching from DB — do not try to
  filter badge in SQL since badge is computed. This means
  the count returned in PaginationMeta may differ from the
  unfiltered total when badge filter is active. Document
  this clearly in the API response: filtered_total is
  included in meta alongside the full total.

  Alternative — preferred if performant enough:
  Pre-compute badge filter bounds in SQL:
    out_of_stock: WHERE current_stock = 0
    low_stock:    WHERE current_stock > 0
                  AND current_stock <= COALESCE(
                    low_stock_threshold_override, reorder_point)
    in_stock:     WHERE current_stock > COALESCE(
                    low_stock_threshold_override, reorder_point)
  Use SQL approach — it is more accurate for pagination counts.

- Barcode lookup endpoint is GET /products/barcode-lookup
  with query parameter ?barcode=VALUE. It is NOT
  GET /products/{barcode}. The path must be defined before
  the GET /products/{id} route in the router to avoid FastAPI
  treating "barcode-lookup" as a UUID and routing incorrectly.

- NotFoundException must be added to exceptions.py and mapped
  to HTTP 404 in main.py global exception handler. Add it now
  and update the EXCEPTION_STATUS_MAP in main.py.

- RBAC enforcement uses the require_role dependency from
  Phase 1 dependencies.py:
    Read: all authenticated users
    Create/Update: PROCUREMENT_MANAGER, ADMIN
    Delete: ADMIN only
