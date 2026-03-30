# specs/phase-6-dashboard-reports.spec.md
# Phase 6 — Dashboard and Reports Spec

## Purpose
This phase implements the read-heavy analytics layer of StockBridge.
The dashboard gives each role a real-time view of the system state.
The reports give managers downloadable audit trails for supplier
performance and tier decisions. All endpoints are read-only. No
state changes happen here.

## Scope

### In Scope
backend/app/routers/dashboard.py
backend/app/routers/reports.py
backend/app/services/dashboard_service.py
backend/app/services/report_service.py
backend/app/schemas/dashboard.py
backend/app/schemas/report.py
backend/tests/unit/test_dashboard_service.py
backend/tests/unit/test_report_service.py
backend/tests/integration/test_dashboard_endpoints.py
backend/tests/integration/test_report_endpoints.py

### Out of Scope
Frontend dashboard components — Phase 9.
PDF report format — not planned for this project.
Bulk export of all suppliers — not in scope.
Real-time WebSocket dashboard updates — not planned.
Pandas — never use it. Python csv module only.

## Acceptance Criteria

1.  GET /dashboard returns role-specific metrics — warehouse_staff
    sees different data than procurement_manager and admin
2.  GET /dashboard returns HTTP 200 for all authenticated roles
3.  GET /dashboard/low-stock returns products below reorder threshold
    paginated default 20 max 50
4.  GET /dashboard/recent-activity returns last 20 stock ledger
    entries across all products
5.  GET /reports/suppliers/{supplier_id} returns CSV file download
    with Content-Disposition attachment header
6.  GET /reports/suppliers/{supplier_id}?months=12 returns 12 months
    of SupplierMetricsHistory data
7.  GET /reports/suppliers/{supplier_id} with months > 36 returns
    HTTP 400 DATE_RANGE_TOO_LARGE
8.  GET /reports/suppliers/{supplier_id} with months < 1 returns
    HTTP 400 INVALID_PARAMETER
9.  GET /reports/suppliers/{supplier_id} for supplier with no history
    returns CSV with summary block and no-data message row
10. GET /reports/monthly-tier-summary?month=YYYY-MM returns CSV
    with one row per supplier
11. GET /reports/monthly-tier-summary with invalid month format
    returns HTTP 400 INVALID_PARAMETER
12. All CSV responses use StreamingResponse with
    Content-Type text/csv
13. CSV filenames follow locked naming convention
14. Staff cannot access supplier reports — HTTP 403
15. All unit tests pass
16. All integration tests pass
17. ruff check backend/ passes
18. black --check backend/ passes

## Dashboard Endpoint Contracts

### GET /dashboard
Auth: all authenticated roles
Response: SingleResponse[DashboardRead]

DashboardRead schema is role-aware. Fields returned depend on role.

**warehouse_staff sees:**
- total_products: int — count of active products
- low_stock_count: int — products below reorder threshold
- pending_grns: int — open GRNs created by this user
- recent_stock_movements: list[StockMovementSummary] — last 5
  ledger entries for products this user has receipted

**procurement_manager sees:**
- total_products: int
- low_stock_count: int
- open_pos: int — POs in submitted or acknowledged status
- pending_grns: int — all open GRNs system-wide
- total_suppliers: int — active suppliers
- overdue_backorders: int — open backorders older than 7 days
- recent_activity: list[StockMovementSummary] — last 10 entries

**admin sees:**
- Everything procurement_manager sees plus:
- total_users: int
- inactive_suppliers: int
- auto_reorder_triggered_today: int — GRNs with
  auto_reorder_triggered=true completed today
- email_failures_unresolved: int — unresolved email_failure_log rows
- system_health: SystemHealthSummary

SystemHealthSummary:
- database_ok: bool
- redis_ok: bool
- temporal_ok: bool — check by listing temporal workflows
- last_tier_recalc: datetime | None — completed_at of last
  TierRecalculationWorkflow run

StockMovementSummary:
- product_name: str
- product_sku: str
- quantity_change: int
- change_type: str
- balance_after: Decimal
- created_at: datetime

### GET /dashboard/low-stock
Auth: all authenticated roles
Query params: page (default 1), page_size (default 20, max 50)
Response: ListResponse[LowStockProductRead]

LowStockProductRead:
- id: UUID
- name: str
- sku: str
- current_stock: int
- reorder_point: int
- low_stock_threshold_override: int | None
- effective_threshold: int — COALESCE(NULLIF(override,0), reorder_point)
- stock_badge: str — out_of_stock | low_stock
- preferred_supplier_name: str | None

### GET /dashboard/recent-activity
Auth: all authenticated roles
Query params: limit (default 20, max 100)
Response: ListResponse[StockMovementSummary]

Returns most recent stock ledger entries ordered by created_at DESC.
Staff: filtered to products they have receipted via GRN.
Manager and Admin: all products.

## Report Endpoint Contracts

### GET /reports/suppliers/{supplier_id}
Auth: procurement_manager and admin only — staff returns 403
Query params: months (default 12, min 1, max 36)
Response: StreamingResponse, Content-Type: text/csv
Content-Disposition: attachment; filename="{filename}"

Filename format: supplier_{name_slug}_{id_short}_{YYYY-MM-DD}.csv
- name_slug: supplier name lowercased, spaces to hyphens,
  non-alphanumeric-or-hyphen characters removed
- id_short: first 8 characters of supplier UUID
- date: today's date YYYY-MM-DD
Example: supplier_primeparts-ltd_abc12345_2025-01-15.csv

CSV structure:
Row 1: StockBridge Supplier Performance Report
Row 2: Supplier: {name} (ID: {id})
Row 3: Report Period: {start_month} to {end_month}
Row 4: Generated: {YYYY-MM-DD}
Row 5: Current Status: {tier} Tier | Credit Limit: ${amount} |
       Tier Locked: {Yes/No}
Row 6: (blank)
Row 7: Column headers
Rows 8+: Monthly data rows

Column headers (locked from planning):
Report_Generated_Date, Supplier_ID, Supplier_Name, Current_Tier,
Current_Credit_Limit, Tier_Locked, Month, Total_PO_Lines,
Backorder_Rate_Pct, On_Time_Delivery_Pct, Computed_Rating,
Tier_Assigned, Insufficient_Data, Consecutive_Qualifying_Months,
Consecutive_Underperforming_Months, Decision_Reason

Monthly data row values:
- Report_Generated_Date: today YYYY-MM-DD (same for all rows)
- Supplier_ID: supplier UUID string
- Supplier_Name: supplier.name
- Current_Tier: supplier.current_tier (at report time)
- Current_Credit_Limit: supplier.credit_limit (2 decimal places)
- Tier_Locked: Yes or No
- Month: YYYY-MM from SupplierMetricsHistory.period_year and
  period_month formatted as f"{year}-{month:02d}"
- Total_PO_Lines: metrics_history.total_po_lines
- Backorder_Rate_Pct: metrics_history.backorder_rate * 100
  formatted to 1 decimal place
- On_Time_Delivery_Pct: metrics_history.on_time_rate * 100
  formatted to 1 decimal place
- Computed_Rating: computed as (on_time_rate * 0.6 +
  (1 - backorder_rate) * 0.4) * 5.0, formatted to 2 decimal
  places, range 0.00 to 5.00
- Tier_Assigned: metrics_history.tier_assigned
- Insufficient_Data: Yes or No
- Consecutive_Qualifying_Months: supplier.consecutive_on_time
  (snapshot at report time — same for all rows)
- Consecutive_Underperforming_Months: supplier.consecutive_late
  (snapshot at report time — same for all rows)
- Decision_Reason: derived by comparing adjacent months.
  If tier_assigned changed from month N-1 to month N:
    If promoted: "Promoted after {n} consecutive qualifying months"
    If demoted: "Demoted after {n} consecutive underperforming months"
  If no change: "Tier maintained"
  First row (no prior month to compare): "Initial record"
  If insufficient_data=true: "Insufficient data (< 20 PO lines)"

No history case: CSV contains summary block (rows 1-6) plus
column headers row then one data row:
  All fields empty except Month="No data" and
  Decision_Reason="No historical data available for this period"

### GET /reports/monthly-tier-summary
Auth: procurement_manager and admin only — staff returns 403
Query params: month (required, format YYYY-MM)
Response: StreamingResponse, Content-Type: text/csv
Content-Disposition: attachment; filename=
  "stockbridge_tier_summary_{YYYY-MM}.csv"

CSV structure:
Row 1: StockBridge Monthly Tier Summary
Row 2: Period: {YYYY-MM}
Row 3: Generated: {YYYY-MM-DD}
Row 4: (blank)
Row 5: Column headers
Rows 6+: One row per supplier

Column headers:
Supplier_Name, Supplier_ID, Previous_Tier, New_Tier,
Tier_Changed, Change_Direction, Consecutive_Qualifying_Months,
Consecutive_Underperforming_Months, Backorder_Rate_Pct,
On_Time_Delivery_Pct, Computed_Rating, Insufficient_Data,
Credit_Limit_After

Sort order:
1. Tier changes first (Tier_Changed=Yes), sorted by
   Change_Direction (Promoted first, then Demoted)
2. Then no-change rows sorted by supplier name
3. Insufficient data rows last

Column values:
- Previous_Tier: tier_assigned from month N-1 history row,
  or "New Supplier" if no prior record
- New_Tier: tier_assigned from this month's history row
- Tier_Changed: Yes or No
- Change_Direction: Promoted / Demoted / None
- Computed_Rating: same formula as supplier report
- Credit_Limit_After: supplier.credit_limit at report time

No data case: if no SupplierMetricsHistory rows exist for
requested month, return CSV with header block and one row:
"No tier recalculation data found for {YYYY-MM}"

## Error Scenarios

| Scenario                           | HTTP | Error Code            |
|------------------------------------|------|-----------------------|
| Supplier not found                 | 404  | NOT_FOUND             |
| months > 36                        | 400  | DATE_RANGE_TOO_LARGE  |
| months < 1                         | 400  | INVALID_PARAMETER     |
| Invalid month format               | 400  | INVALID_PARAMETER     |
| Staff accesses supplier report     | 403  | PERMISSION_DENIED     |
| Report generation DB timeout       | 503  | REPORT_GENERATION_FAILED |
| Dashboard DB timeout               | 503  | SERVICE_UNAVAILABLE   |

Add to exceptions.py:
  DateRangeTooLargeException — DATE_RANGE_TOO_LARGE → 400
  ReportGenerationFailedException — REPORT_GENERATION_FAILED → 503
  ServiceUnavailableException — SERVICE_UNAVAILABLE → 503

Add to EXCEPTION_STATUS_MAP in main.py:
  DateRangeTooLargeException: 400
  ReportGenerationFailedException: 503
  ServiceUnavailableException: 503

## Test Cases

### Unit Tests — test_dashboard_service.py
  test_warehouse_staff_sees_only_staff_fields
  test_procurement_manager_sees_manager_fields
  test_admin_sees_all_fields_including_system_health
  test_low_stock_uses_effective_threshold
  test_low_stock_excludes_inactive_products
  test_recent_activity_staff_filtered_to_own_receipts
  test_recent_activity_manager_sees_all
  test_system_health_db_ok_when_query_succeeds
  test_system_health_db_not_ok_when_query_fails

### Unit Tests — test_report_service.py
  test_supplier_report_generates_summary_block
  test_supplier_report_months_limited_to_requested
  test_supplier_report_no_history_returns_no_data_row
  test_supplier_report_months_gt_36_raises_date_range_too_large
  test_supplier_report_months_lt_1_raises_invalid_parameter
  test_supplier_report_decision_reason_promoted
  test_supplier_report_decision_reason_demoted
  test_supplier_report_decision_reason_maintained
  test_supplier_report_computed_rating_formula
  test_monthly_summary_sorted_promotions_first
  test_monthly_summary_sorted_demotions_before_no_change
  test_monthly_summary_no_data_returns_no_data_row
  test_filename_slugifies_supplier_name
  test_filename_includes_id_short_and_date

### Integration Tests — test_dashboard_endpoints.py
  test_dashboard_staff_returns_200
  test_dashboard_manager_returns_200
  test_dashboard_admin_returns_200
  test_dashboard_staff_response_has_staff_fields_only
  test_dashboard_unauthenticated_returns_401
  test_low_stock_returns_paginated_list
  test_low_stock_page_size_max_50
  test_recent_activity_returns_list
  test_recent_activity_staff_filtered

### Integration Tests — test_report_endpoints.py
  test_supplier_report_returns_csv_content_type
  test_supplier_report_has_content_disposition_header
  test_supplier_report_filename_format_correct
  test_supplier_report_staff_returns_403
  test_supplier_report_months_param_respected
  test_supplier_report_months_37_returns_400
  test_supplier_report_invalid_supplier_returns_404
  test_monthly_summary_returns_csv
  test_monthly_summary_invalid_month_format_returns_400
  test_monthly_summary_staff_returns_403

## Implementation Notes

- dashboard_service.py builds the response dict dynamically based
  on role. Use a single get_dashboard(user_id, role, session) method
  that calls private methods per role: _get_staff_data(),
  _get_manager_data(), _get_admin_data(). Admin calls manager data
  first then adds admin-only fields.

- report_service.py has two public methods:
  generate_supplier_report(supplier_id, months, session) → tuple[str, io.StringIO]
    Returns (filename, csv_buffer)
  generate_monthly_summary(month_str, session) → tuple[str, io.StringIO]
    Returns (filename, csv_buffer)
  Both raise appropriate exceptions for invalid inputs.
  Both use Python's csv.writer on io.StringIO — no pandas, no files.

- Router returns StreamingResponse:
  ```python
  return StreamingResponse(
      iter([buffer.getvalue()]),
      media_type="text/csv",
      headers={"Content-Disposition": f'attachment; filename="{filename}"'}
  )
  ```

- Computed_Rating formula (locked):
  rating = (on_time_rate * 0.6 + (1 - backorder_rate) * 0.4) * 5.0
  Clamp to 0.00-5.00 range.
  Format to 2 decimal places in CSV.

- Decision_Reason derivation: iterate SupplierMetricsHistory rows
  sorted by period_year ASC, period_month ASC. Keep previous row's
  tier_assigned. Compare to current row's tier_assigned.
  Use TIER_ORDER dict from tier_scoring.py to determine direction.

- Effective threshold for low stock:
  COALESCE(NULLIF(low_stock_threshold_override, 0), reorder_point)
  Same logic as badge computation in Phase 2.

- System health check implementation:
  database_ok: try SELECT 1, catch Exception → False
  redis_ok: try redis.ping(), catch Exception → False
  temporal_ok: try list temporal schedules, catch Exception → False
  last_tier_recalc: query email_failure_log or a separate
  mechanism — actually query SupplierMetricsHistory for the most
  recent created_at to approximate last recalculation time.

- Register dashboard router in main.py with prefix /dashboard
- Register reports router in main.py with prefix /reports
- Add DateRangeTooLargeException, ReportGenerationFailedException,
  ServiceUnavailableException to exceptions.py and main.py map
