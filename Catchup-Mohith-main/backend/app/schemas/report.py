# backend/app/schemas/report.py
# Report schemas are minimal — CSV generation is handled in
# report_service.py using io.StringIO and csv.writer.
# These dataclasses carry typed intermediate data between
# the DB query layer and the CSV writer.

from dataclasses import dataclass


@dataclass
class SupplierReportRow:
    report_generated_date: str
    supplier_id: str
    supplier_name: str
    current_tier: str
    current_credit_limit: str
    tier_locked: str
    month: str
    total_po_lines: int
    backorder_rate_pct: str
    on_time_delivery_pct: str
    computed_rating: str
    tier_assigned: str
    insufficient_data: str
    consecutive_qualifying_months: int
    consecutive_underperforming_months: int
    decision_reason: str


@dataclass
class MonthlyTierSummaryRow:
    supplier_name: str
    supplier_id: str
    previous_tier: str
    new_tier: str
    tier_changed: str
    change_direction: str
    consecutive_qualifying_months: int
    consecutive_underperforming_months: int
    backorder_rate_pct: str
    on_time_delivery_pct: str
    computed_rating: str
    insufficient_data: str
    credit_limit_after: str


SUPPLIER_REPORT_HEADERS = [
    "Report_Generated_Date",
    "Supplier_ID",
    "Supplier_Name",
    "Current_Tier",
    "Current_Credit_Limit",
    "Tier_Locked",
    "Month",
    "Total_PO_Lines",
    "Backorder_Rate_Pct",
    "On_Time_Delivery_Pct",
    "Computed_Rating",
    "Tier_Assigned",
    "Insufficient_Data",
    "Consecutive_Qualifying_Months",
    "Consecutive_Underperforming_Months",
    "Decision_Reason",
]

MONTHLY_SUMMARY_HEADERS = [
    "Supplier_Name",
    "Supplier_ID",
    "Previous_Tier",
    "New_Tier",
    "Tier_Changed",
    "Change_Direction",
    "Consecutive_Qualifying_Months",
    "Consecutive_Underperforming_Months",
    "Backorder_Rate_Pct",
    "On_Time_Delivery_Pct",
    "Computed_Rating",
    "Insufficient_Data",
    "Credit_Limit_After",
]
