# specs/phase-9-frontend-dashboard-admin.spec.md
# Phase 9 — Frontend Dashboard and Admin Spec

## Purpose
Builds the read-heavy analytics and admin pages. Dashboard gives
each role a real-time view of system state. Stock ledger,
backorder list, and admin pages complete the full page inventory.
After this phase every route in NAV_CONFIG has a real page.

## Acceptance Criteria

1.  DashboardPage renders role-specific metrics from GET /dashboard
2.  Staff sees: total_products, low_stock_count, pending_grns,
    recent_stock_movements
3.  Manager sees staff fields plus: open_pos, overdue_backorders,
    total_suppliers, recent_activity
4.  Admin sees all manager fields plus: total_users,
    email_failures_unresolved, system_health block
5.  Dashboard polls every 30 seconds when tab focused — no full
    skeleton flash on background refetch
6.  Low stock count card links to /products
7.  StockLedgerPage uses cursor pagination with Load More button
8.  Load More appends rows — never replaces existing rows
9.  BackordersPage shows open backorders with age per row
10. Overdue backorders (> 7 days) show red warning badge
11. AdminUsersPage accessible to admin only → others /unauthorized
12. ReportsPage accessible to manager and admin
13. CSV download works via blob response and anchor click
14. All pages handle 4 states: loading, empty, error, success
15. Carbon components only — no raw HTML equivalents
16. No hardcoded colors or spacing — tokens only
17. `pnpm build` passes with zero TypeScript errors
18. `pnpm lint` passes
19. `pnpm test:e2e` passes

## API Endpoints Used

### Dashboard
GET /dashboard → role-specific DashboardRead
GET /dashboard/low-stock?page=1&page_size=20
GET /dashboard/recent-activity?limit=20

### Stock Ledger
GET /stock-ledger?page_size=20&cursor=
Response includes: items[], next_cursor (null when no more pages)
Cursor pagination — not offset. Load More pattern.

StockLedgerRead fields used:
id, product_name, product_sku, quantity_change, change_type,
reference_id, reference_type, balance_after, created_at

### Backorders
GET /purchase-orders?has_backorders=true&page=1&page_size=20
BackorderRead fields: id, po_number, product_name, product_sku,
ordered_quantity, received_quantity, backorder_quantity,
created_at, supplier_name

### Admin Users
GET /users?page=1&page_size=20
POST /users
PATCH /users/:id

### Reports
GET /reports/suppliers/:id?months=12 → StreamingResponse CSV
GET /reports/monthly-tier-summary?month=YYYY-MM → StreamingResponse CSV

## Feature Structure

All 4 features follow locked layer order:
```
client/src/features/<feature>/
  types/
  constants/
  hooks/      (.ts not .tsx)
  components/
  containers/
  styles/
```

## New Molecules (Phase 9)

### MetricCard
Props: label, value, trend?, linkTo?, isLoading
Carbon Tile. Large value display.
linkTo: clicking navigates to route via useNavigate.
isLoading: shows LoadingSkeleton instead of value.
Never hardcodes routes — always from props.

### SystemHealthIndicator
Props: databaseOk, redisOk, temporalOk, lastTierRecalc
Three Carbon Tag components (green=ok, red=down) per service.
lastTierRecalc: formatted datetime or "Never".
Admin-only molecule.

### BackorderAgeIndicator
Props: createdAt: string, overdueThresholdDays?: number (default 7)
Computes age in days client-side.
age > threshold → StatusBadge "Overdue" red
age <= threshold → StatusBadge "{n} days" blue

### CursorLoadMore
Props: hasNextCursor, isLoading, onLoadMore
Carbon Button "Load More" when hasNextCursor true.
Carbon InlineLoading when isLoading.
Hidden when hasNextCursor false.

## New Organisms (Phase 9)

### DashboardStaffSection
Props: data: DashboardStaffData, isLoading
MetricCard row: Total Products, Low Stock (linkTo=/products),
Pending GRNs. Carbon DataTable for recent_stock_movements.

### DashboardManagerSection
Props: data: DashboardManagerData, isLoading
Extends staff cards + Open POs, Overdue Backorders,
Total Suppliers. Extended recent activity table.

### DashboardAdminSection
Props: data: DashboardAdminData, isLoading
Extends manager + Total Users, Email Failures cards.
SystemHealthIndicator molecule below cards.

### StockLedgerTable
Props: entries, isLoading, isEmpty, error, onRetry
Carbon DataTable: Date, Product, SKU, Change, Type,
Balance After, Reference. All 4 states.

### BackorderTable
Props: backorders, isLoading, isEmpty, error, onRetry
Carbon DataTable: PO Number, Product, SKU, Ordered, Received,
Backorder Qty, Age (BackorderAgeIndicator), Supplier.
All 4 states.

### AdminUsersTable
Props: users, isLoading, isEmpty, error, onRetry, onEditRole
Carbon DataTable: Name, Email, Role, Status, Actions.
Inline role edit via Carbon Select. Toggle active status.

## Pages Detail

### DashboardPage
Route: /dashboard — all roles (staff sees limited section)
AppShell: pageTitle="Dashboard" activeView="dashboard"

Role dispatch via config map in constants — not if-else:
```typescript
// features/dashboard/constants/dashboardConfig.ts
export const DASHBOARD_SECTION = {
  warehouse_staff: DashboardStaffSection,
  procurement_manager: DashboardManagerSection,
  admin: DashboardAdminSection,
}
```
Container reads role, looks up section component, renders it.
Polling: refetchInterval 30000, refetchIntervalInBackground false.
Use isFetching for background spinner — never isLoading for refetch.

### StockLedgerPage
Route: /stock-ledger — all roles
AppShell: pageTitle="Stock Ledger" activeView="stock"

useInfiniteQuery pattern:
```typescript
useInfiniteQuery({
  queryKey: ['stock-ledger'],
  queryFn: ({ pageParam }) =>
    apiClient.get('/stock-ledger', {
      params: { page_size: 20, cursor: pageParam }
    }),
  getNextPageParam: (lastPage) => lastPage.data.next_cursor ?? undefined,
  initialPageParam: undefined,
})
```

Flatten pages for table:
```typescript
const entries = data?.pages.flatMap(p => p.data.items) ?? []
const hasNextCursor = !!data?.pages.at(-1)?.data.next_cursor
```

CursorLoadMore shown below StockLedgerTable.

### BackordersPage
Route: /backorders — all roles
AppShell: pageTitle="Backorders" activeView="backorders"

FilterBar: All / Overdue filter.
Staff: filtered to own GRN backorders.
Manager/Admin: all backorders.
BackorderAgeIndicator per row.

### AdminUsersPage
Route: /admin/users — admin only
Container: navigate to /unauthorized if role !== 'admin' on mount.
AppShell: pageTitle="Users" activeView="users"

AdminUsersTable organism.
"Create User" button → Carbon Modal with form fields:
email, username, password, role (Carbon Select), is_active.
POST /users on submit. Invalidate ['users'] on success.

### ReportsPage
Route: /reports — manager and admin only
Container: navigate to /unauthorized if role === 'warehouse_staff'.
AppShell: pageTitle="Reports" activeView="reports"

Section 1 — Supplier Performance:
- Supplier search (useSuppliersQuery for dropdown options)
- Months Carbon NumberInput (1-36, default 12)
- "Download CSV" → blob download

Section 2 — Monthly Tier Summary:
- Month input (Carbon TextInput, YYYY-MM format)
- "Download CSV" → blob download

CSV download utility:
```typescript
const downloadCSV = async (url: string, defaultFilename: string) => {
  const response = await apiClient.get(url, { responseType: 'blob' })
  const disposition = response.headers['content-disposition'] ?? ''
  const match = disposition.match(/filename="(.+)"/)
  const filename = match?.[1] ?? defaultFilename
  const blob = new Blob([response.data], { type: 'text/csv' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = filename
  link.click()
  URL.revokeObjectURL(link.href)
}
```

## Hook Specifications

### useDashboardQuery.ts
staleTime: 30000, refetchInterval: 30000,
refetchIntervalInBackground: false
queryKey: ['dashboard']

### useStockLedgerQuery.ts
useInfiniteQuery as above.
queryKey: ['stock-ledger']

### useBackordersQuery.ts
queryKey: ['backorders', params]
staleTime: 30000

### useUsersQuery.ts
queryKey: ['users', params]
staleTime: 60000

### useUpdateUserMutation.ts
PATCH /users/:id, retry: 0
onSuccess: invalidate ['users']

### useCreateUserMutation.ts
POST /users, retry: 0
onSuccess: invalidate ['users']

## Role Access Table

| Route          | staff      | manager | admin   |
|----------------|------------|---------|---------|
| /dashboard     | ✓ limited  | ✓       | ✓ full  |
| /stock-ledger  | ✓          | ✓       | ✓       |
| /backorders    | ✓ filtered | ✓       | ✓       |
| /admin/users   | ✗          | ✗       | ✓       |
| /reports       | ✗          | ✓       | ✓       |

Role guard always in container on mount — never in component.

## E2E Tests

### dashboard.spec.ts
  test_dashboard_staff_shows_limited_metrics
  test_dashboard_manager_shows_extended_metrics
  test_dashboard_admin_shows_system_health
  test_dashboard_low_stock_card_navigates_to_products
  test_dashboard_background_refetch_no_skeleton_flash

### stock-ledger.spec.ts
  test_stock_ledger_loads_initial_entries
  test_stock_ledger_load_more_appends_rows
  test_stock_ledger_empty_state_when_no_entries
  test_stock_ledger_shows_correct_columns

### backorders.spec.ts
  test_backorders_loads_open_backorders
  test_backorders_overdue_filter_works
  test_backorders_age_indicator_per_row
  test_backorders_empty_state_when_none

## Implementation Notes

- Dashboard role dispatch: DASHBOARD_SECTION map lives in
  features/dashboard/constants/dashboardConfig.ts — never
  inline if-else in container.

- isFetching vs isLoading: isLoading true only on first load.
  isFetching true on background refetch. Show spinner in
  toolbar area during isFetching, not full skeleton.

- Stock ledger cursor: backend returns next_cursor as string
  UUID or null. getNextPageParam returns undefined when null
  which tells React Query no more pages available.

- BackorderAgeIndicator age computation: use plain JS Date math
  if date-fns not in package.json:
  ```typescript
  const ageMs = Date.now() - new Date(createdAt).getTime()
  const ageDays = Math.floor(ageMs / (1000 * 60 * 60 * 24))
  ```

- AdminUsersPage modal: use Carbon ComposedModal with
  ModalHeader, ModalBody, ModalFooter pattern.

- ReportsPage: axios responseType 'blob' required for CSV.
  Content-Disposition header parsing extracts filename.
  Always revoke object URL after click to avoid memory leak.

- All new design system components exported from barrel before
  being used in features.

- MetricCard linkTo: container passes '/products' string as prop.
  MetricCard calls useNavigate internally only if linkTo provided.
  Component never hardcodes any route string.
