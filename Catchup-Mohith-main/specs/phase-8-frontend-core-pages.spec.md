# specs/phase-8-frontend-core-pages.spec.md
# Phase 8 — Frontend Core Pages Spec

## Purpose
Builds the four core operational pages: product list, supplier
list, PO wizard, and GRN form. Every role uses these daily.
All builds on atoms, stores, and API client from Phase 7.

## Acceptance Criteria

1.  ProductsPage renders with Carbon DataTable, search, pagination
2.  Empty products → EmptyState atom with role-aware message
3.  Loading products → LoadingSkeleton atom
4.  API error → Carbon InlineNotification with retry button
5.  SuppliersPage renders with StatusBadge tier per supplier
6.  Supplier tier filter works (Silver / Gold / Diamond / All)
7.  PO wizard has 4 steps: Select Supplier → Add Lines → Review → Confirm
8.  PO wizard state persists in wizardStore (sessionStorage)
9.  ConfirmationBanner shown on wizard mount if session exists
10. GRN form shows open POs for selection
11. GRN barcode input accepts scan and Enter key
12. GRN over-receipt prevention — qty cannot exceed remaining
13. GRNSummaryPanel shown before final submission
14. Staff cannot access /suppliers or /purchase-orders → /unauthorized
15. All pages handle 4 states: loading, empty, error, success
16. Carbon components only — no raw HTML equivalents
17. No hardcoded colors or spacing — tokens only
18. `pnpm build` passes with zero TypeScript errors
19. `pnpm lint` passes
20. `pnpm test:e2e` passes

## API Endpoints Used

### Products
GET /products?page=1&page_size=20&search=&is_active=true
Response: ListResponse[ProductRead]
Fields used: id, name, sku, current_stock, reorder_point,
  low_stock_threshold_override, is_active

### Suppliers
GET /suppliers?page=1&page_size=20&current_tier=&is_active=true
Response: ListResponse[SupplierRead]
Fields used: id, name, contact_email, current_tier, credit_limit,
  tier_locked, is_active

### Purchase Orders
GET /purchase-orders?page=1&page_size=20&status=
POST /purchase-orders
GET /purchase-orders/:id
GET /purchase-orders/:id/credit-check

POST payload:
```typescript
{
  supplier_id: string
  lines: { product_id: string; quantity: number; unit_price: number }[]
  notes?: string
}
```

### GRNs
GET /grns?status=open (for PO selection — use acknowledged POs)
POST /grns — create GRN from PO
POST /grns/:id/lines/:line_id/receive — receive a line

POST /grns payload: { po_id: string }
Receive line payload: { received_quantity: number; barcode?: string }

## Feature Structure

All 4 features follow locked layer order from AGENTS.md:
```
client/src/features/<feature>/
  types/        — TypeScript types first
  constants/    — static config, labels, steps
  hooks/        — data fetching (.ts not .tsx)
  components/   — dumb presentational
  containers/   — orchestration, wires hooks to components
  styles/       — feature SCSS only
```

## Design System — Molecules (New in Phase 8)

### SearchBar
Props: value, onChange, placeholder, isLoading
Uses Carbon Search. Debounces 300ms via useEffect.

### PaginationBar
Props: page, pageSize, totalItems, onPageChange, onPageSizeChange
Uses Carbon Pagination. pageSizes: [10, 20, 50].

### FilterBar
Props: filters: FilterOption[], activeFilter, onFilterChange
Uses Carbon ContentSwitcher.

### DataTableToolbar
Props: title, totalCount, searchProps, actions?
Composes SearchBar + optional action buttons.
Uses Carbon TableToolbar pattern.

### WizardStepper
Props: steps: string[], currentStep: number
Uses Carbon ProgressIndicator.
Steps: ['Select Supplier', 'Add Lines', 'Review', 'Confirm']

### FormFieldError
Props: message: string | undefined
Renders Carbon inline error text. Only renders when message defined.

### CreditWarning
Props: creditLimit, estimatedTotal, onProceed, onCancel
Full molecule — uses Carbon Modal with warning.
Triggers when estimatedTotal > creditLimit * 0.9.
Manager can acknowledge and proceed or cancel.

## Design System — Organisms (New in Phase 8)

### ProductTable
Props: products, isLoading, isEmpty, error, onRetry
Carbon DataTable columns: SKU, Name, Stock, Reorder Point,
Status badge (low/ok), Actions
All 4 states handled: LoadingSkeleton, EmptyState,
InlineNotification error, DataTable success.

### SupplierTable
Props: suppliers, isLoading, isEmpty, error, onRetry
Carbon DataTable columns: Name, Tier (StatusBadge), Credit Limit,
Contact, Status, Actions
Same 4-state pattern.

### POLineEditor
Props: lines, products, onAddLine, onRemoveLine,
       onUpdateQuantity, onUpdateUnitPrice
Carbon NumberInput for quantity and unit price.
Running line total displayed per row.
Validates quantity > 0 and unit_price > 0.

### GRNLineScanner
Props: poLines, scannedLines, onScan, onUpdateQty, onRemove
Carbon TextInput barcode field per line.
On Enter key: call onScan(barcode, poLineId), clear input.
Remaining qty = ordered - already_received.
If entered qty > remaining: show Carbon InlineNotification
kind="warning" inline, disable confirm.

### GRNSummaryPanel
Props: poNumber, lines, onConfirm, onBack
Pre-submission summary using Carbon StructuredList.
Final step before POST /grns receive calls.

## Pages

### ProductsPage
Route: /products — all authenticated roles
AppShell: pageTitle="Products" activeView="products"
Staff: read-only table, no create button
Manager/Admin: table + "Create Product" button (disabled Phase 8,
  active Phase 9)

Layout: PageTitle → DataTableToolbar → ProductTable → PaginationBar

### SuppliersPage
Route: /suppliers — procurement_manager and admin only
Staff → /unauthorized on mount check in container
Layout: PageTitle → FilterBar (tier) → DataTableToolbar →
  SupplierTable → PaginationBar

### PurchaseOrdersPage
Route: /purchase-orders — procurement_manager and admin only
Layout: PageTitle → FilterBar (status) → DataTableToolbar with
  "Create PO" button → PO DataTable with StatusBadge → PaginationBar
"Create PO" navigates to /purchase-orders/new

### CreatePOPage (PO Wizard)
Route: /purchase-orders/new — procurement_manager and admin only

On mount: check wizardStore — if state exists show
ConfirmationBanner (Continue or Start Fresh).

Step 1 — Select Supplier:
  SearchBar → supplier list with RadioButtonGroup
  Show tier badge and credit limit per supplier
  Next disabled until supplier selected
  On select: wizardStore.updateSupplier()

Step 2 — Add Lines:
  SearchBar for products → POLineEditor organism
  Running estimated total
  CreditWarning if total > 90% credit limit
  Back and Next (disabled if no lines)

Step 3 — Review:
  WizardStepper at step 3
  Read-only supplier + lines summary
  Carbon TextArea for notes
  Back and Submit PO buttons
  On submit: POST /purchase-orders with wizardStore state
  On success: wizardStore.setStep(4), save PO number

Step 4 — Confirm:
  Success state with PO number
  "View PO" → /purchase-orders/:id
  "Create Another" → wizardStore.resetWizard()
  useEffect cleanup: resetWizard() only if step === 4

### GRNPage
Route: /grns — all authenticated roles

On mount: check grnSessionStore — if session exists show
ConfirmationBanner (Continue or Start Fresh).

Phase A — Select PO:
  List of acknowledged POs (useOpenPOsQuery)
  On select: POST /grns → store grnId in grnSessionStore

Phase B — Scan Lines:
  GRNLineScanner organism for each PO line

Phase C — Review:
  GRNSummaryPanel

Phase D — Complete:
  On confirm: POST receive for each scanned line
  On success: grnSessionStore.resetSession()
  Invalidate ['grns'] and ['products'] query keys

## Hook Specifications

All .ts extension. All in features/<feature>/hooks/.

### useProductsQuery.ts
queryKey: ['products', params]
staleTime: 60000

### useSuppliersQuery.ts
queryKey: ['suppliers', params]
staleTime: 60000

### usePurchaseOrdersQuery.ts
queryKey: ['purchase-orders', params]
staleTime: 30000

### useCreatePOMutation.ts
POST /purchase-orders
retry: 0
onSuccess: invalidate ['purchase-orders']

### useOpenPOsQuery.ts
GET /purchase-orders?status=acknowledged&page_size=50
queryKey: ['purchase-orders', { status: 'acknowledged' }]

### useCreateGRNMutation.ts
POST /grns
retry: 0

### useReceiveLineMutation.ts
POST /grns/:grnId/lines/:lineId/receive
retry: 0
onSuccess: invalidate ['grns'] and ['products']

## Role Access Table

| Route                   | staff | manager | admin |
|-------------------------|-------|---------|-------|
| /products               | ✓ RO  | ✓       | ✓     |
| /suppliers              | ✗     | ✓       | ✓     |
| /purchase-orders        | ✗     | ✓       | ✓     |
| /purchase-orders/new    | ✗     | ✓       | ✓     |
| /grns                   | ✓     | ✓       | ✓     |

Role guard: check in container on mount, navigate to /unauthorized
if access denied. Never scattered if-else in components.

## Four State Rule — Enforced on Every Component

loading → LoadingSkeleton atom
empty → EmptyState atom (message from props — never hardcoded)
error → Carbon InlineNotification + retry button
success → actual data

No blank screens in any state. Every container passes the correct
state down to the organism.

## E2E Tests

### products.spec.ts
  test_products_page_loads_for_staff
  test_products_page_loads_for_manager
  test_products_search_filters_results
  test_products_pagination_works
  test_products_empty_state_shown_when_no_results

### suppliers.spec.ts
  test_suppliers_page_loads_for_manager
  test_suppliers_staff_redirects_to_unauthorized
  test_suppliers_tier_filter_silver
  test_suppliers_tier_filter_gold
  test_suppliers_search_filters_results

### po-wizard.spec.ts
  test_po_wizard_renders_step_1_on_load
  test_po_wizard_next_disabled_without_supplier
  test_po_wizard_select_supplier_enables_next
  test_po_wizard_step_2_add_line_updates_total
  test_po_wizard_step_3_review_shows_all_lines
  test_po_wizard_credit_warning_shown_near_limit
  test_po_wizard_submit_creates_po_shows_confirm
  test_po_wizard_sessionstorage_persists_on_refresh
  test_po_wizard_confirmation_banner_on_resume
  test_po_wizard_start_fresh_clears_session

### grn.spec.ts
  test_grn_page_shows_acknowledged_pos
  test_grn_select_po_shows_line_scanner
  test_grn_barcode_enter_key_triggers_scan
  test_grn_over_receipt_shows_warning
  test_grn_summary_panel_shown_before_confirm
  test_grn_confirmation_banner_on_resume
  test_grn_completion_clears_session

## Implementation Notes

- Debounce: SearchBar uses useEffect + setTimeout 300ms.
  No external debounce library.
- WizardStepper: display only. Container owns step via wizardStore.
- Barcode input: Carbon TextInput onKeyDown. Enter key calls
  onScan(value, poLineId) then clears field value.
- Over-receipt: remaining = line.quantity - line.already_received.
  Compute in GRNLineScanner, show warning inline.
- wizardStore.resetWizard() in useEffect cleanup only when
  step === 4. Back navigation must NOT clear store.
- After GRN completion invalidate both ['grns'] and ['products']
  because current_stock changes on receipt.
- Query keys pattern: [resource, params] for easy invalidation.
- FilterBar 'All' option sends no filter param to API.
- PaginationBar default page_size: 20.
- CreditWarning is a Carbon Modal — not a disabled button.
