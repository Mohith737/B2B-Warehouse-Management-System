# backend/app/services/report_service.py
import csv
import io
import logging
import re
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.exceptions import (
    DateRangeTooLargeException,
    InvalidParameterException,
    NotFoundException,
    ReportGenerationFailedException,
)
from backend.app.models.supplier import Supplier
from backend.app.models.supplier_metrics_history import SupplierMetricsHistory
from backend.app.schemas.report import (
    MONTHLY_SUMMARY_HEADERS,
    SUPPLIER_REPORT_HEADERS,
)
from backend.app.services.tier_scoring import TIER_ORDER

logger = logging.getLogger(__name__)

_MAX_MONTHS = 36
_MIN_MONTHS = 1


class ReportService:
    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    async def generate_supplier_report(
        self,
        supplier_id: UUID,
        months: int,
        session: AsyncSession,
    ) -> tuple[str, io.StringIO]:
        """Return (filename, csv_buffer) for a supplier performance report."""
        if months < _MIN_MONTHS:
            raise InvalidParameterException(
                message=f"months must be >= {_MIN_MONTHS}",
                details={"months": months, "minimum": _MIN_MONTHS},
            )
        if months > _MAX_MONTHS:
            raise DateRangeTooLargeException(
                message=f"months must be <= {_MAX_MONTHS}",
                details={"months": months, "maximum": _MAX_MONTHS},
            )

        supplier = await _fetch_supplier(supplier_id, session)

        history = await _fetch_supplier_history(supplier_id, months, session)

        today_str = date.today().isoformat()
        filename = _build_supplier_filename(supplier, today_str)

        try:
            buffer = io.StringIO()
            writer = csv.writer(buffer)

            _write_supplier_summary_block(writer, supplier, history, today_str)

            writer.writerow(SUPPLIER_REPORT_HEADERS)

            if not history:
                _write_no_data_row(writer, supplier, today_str)
            else:
                _write_supplier_data_rows(writer, supplier, history, today_str)

            buffer.seek(0)
            return filename, buffer

        except Exception as exc:
            logger.error(
                "Supplier report generation failed for %s: %s",
                supplier_id,
                exc,
                exc_info=True,
            )
            raise ReportGenerationFailedException(
                details={"supplier_id": str(supplier_id), "error": str(exc)}
            ) from exc

    async def generate_monthly_summary(
        self,
        month_str: str,
        session: AsyncSession,
    ) -> tuple[str, io.StringIO]:
        """Return (filename, csv_buffer) for a monthly tier summary report."""
        year, month = _parse_month_str(month_str)

        history_rows = await _fetch_monthly_history(year, month, session)

        today_str = date.today().isoformat()
        filename = f"stockbridge_tier_summary_{month_str}.csv"

        try:
            buffer = io.StringIO()
            writer = csv.writer(buffer)

            _write_monthly_summary_header_block(writer, month_str, today_str)
            writer.writerow(MONTHLY_SUMMARY_HEADERS)

            if not history_rows:
                writer.writerow(
                    [f"No tier recalculation data found for {month_str}"]
                    + [""] * (len(MONTHLY_SUMMARY_HEADERS) - 1)
                )
                buffer.seek(0)
                return filename, buffer

            rows = await _build_monthly_summary_rows(history_rows, year, month, session)
            sorted_rows = _sort_monthly_rows(rows)
            for row in sorted_rows:
                writer.writerow(row)

            buffer.seek(0)
            return filename, buffer

        except (InvalidParameterException, ReportGenerationFailedException):
            raise
        except Exception as exc:
            logger.error(
                "Monthly summary generation failed for %s: %s",
                month_str,
                exc,
                exc_info=True,
            )
            raise ReportGenerationFailedException(
                details={"month": month_str, "error": str(exc)}
            ) from exc


# ------------------------------------------------------------------
# Filename helpers
# ------------------------------------------------------------------


def _build_supplier_filename(supplier: Supplier, today_str: str) -> str:
    name_slug = re.sub(r"[^a-z0-9-]", "", supplier.name.lower().replace(" ", "-"))
    id_short = str(supplier.id)[:8]
    return f"supplier_{name_slug}_{id_short}_{today_str}.csv"


# ------------------------------------------------------------------
# Summary block writers
# ------------------------------------------------------------------


def _write_supplier_summary_block(
    writer: csv.writer,
    supplier: Supplier,
    history: list[SupplierMetricsHistory],
    today_str: str,
) -> None:
    if history:
        period_years_months = [(h.period_year, h.period_month) for h in history]
        start_ym = min(period_years_months)
        end_ym = max(period_years_months)
        start_month = f"{start_ym[0]}-{start_ym[1]:02d}"
        end_month = f"{end_ym[0]}-{end_ym[1]:02d}"
    else:
        start_month = "N/A"
        end_month = "N/A"

    tier_locked_str = "Yes" if supplier.tier_locked else "No"
    credit_str = f"{supplier.credit_limit:.2f}"

    writer.writerow(["StockBridge Supplier Performance Report"])
    writer.writerow([f"Supplier: {supplier.name} (ID: {supplier.id})"])
    writer.writerow([f"Report Period: {start_month} to {end_month}"])
    writer.writerow([f"Generated: {today_str}"])
    writer.writerow(
        [
            f"Current Status: {supplier.current_tier} Tier | "
            f"Credit Limit: ${credit_str} | "
            f"Tier Locked: {tier_locked_str}"
        ]
    )
    writer.writerow([])


def _write_monthly_summary_header_block(
    writer: csv.writer,
    month_str: str,
    today_str: str,
) -> None:
    writer.writerow(["StockBridge Monthly Tier Summary"])
    writer.writerow([f"Period: {month_str}"])
    writer.writerow([f"Generated: {today_str}"])
    writer.writerow([])


# ------------------------------------------------------------------
# Data row writers
# ------------------------------------------------------------------


def _write_no_data_row(
    writer: csv.writer,
    supplier: Supplier,
    today_str: str,
) -> None:
    writer.writerow(
        [
            today_str,  # Report_Generated_Date
            str(supplier.id),  # Supplier_ID
            supplier.name,  # Supplier_Name
            supplier.current_tier,  # Current_Tier
            f"{supplier.credit_limit:.2f}",  # Current_Credit_Limit
            "Yes" if supplier.tier_locked else "No",  # Tier_Locked
            "No data",  # Month
            "",  # Total_PO_Lines
            "",  # Backorder_Rate_Pct
            "",  # On_Time_Delivery_Pct
            "",  # Computed_Rating
            "",  # Tier_Assigned
            "",  # Insufficient_Data
            "",  # Consecutive_Qualifying_Months
            "",  # Consecutive_Underperforming_Months
            "No historical data available for this period",  # Decision_Reason
        ]
    )


def _write_supplier_data_rows(
    writer: csv.writer,
    supplier: Supplier,
    history: list[SupplierMetricsHistory],
    today_str: str,
) -> None:
    tier_locked_str = "Yes" if supplier.tier_locked else "No"
    credit_str = f"{supplier.credit_limit:.2f}"
    consec_qualifying = supplier.consecutive_on_time
    consec_underperforming = supplier.consecutive_late

    prev_tier: str | None = None

    for row in history:
        month_str = f"{row.period_year}-{row.period_month:02d}"

        # Determine tier_assigned — use tier_at_period_end if present,
        # otherwise fall back to supplier's current_tier (best available).
        tier_assigned = row.tier_at_period_end or supplier.current_tier

        # Insufficient data flag — total_po_lines < 20
        insufficient = row.total_po_lines < 20
        insufficient_str = "Yes" if insufficient else "No"

        # Computed_Rating
        # SupplierMetricsHistory stores avg_fulfilment_rate (0–1 scale).
        # The spec computed_score column maps to our avg_fulfilment_rate.
        # We derive on_time_rate from on_time_deliveries / total_pos
        # when total_pos > 0, else use avg_fulfilment_rate as proxy.
        if row.total_pos > 0:
            on_time_rate_val = Decimal(row.on_time_deliveries) / Decimal(row.total_pos)
        else:
            on_time_rate_val = Decimal("0")

        # backorder_rate derived from defect_count / total_po_lines
        if row.total_po_lines > 0:
            backorder_rate_val = Decimal(row.defect_count) / Decimal(row.total_po_lines)
        else:
            backorder_rate_val = Decimal("0")

        computed_rating = _compute_rating(on_time_rate_val, backorder_rate_val)
        backorder_pct = f"{float(backorder_rate_val) * 100:.1f}"
        ontime_pct = f"{float(on_time_rate_val) * 100:.1f}"

        # Decision_Reason
        decision_reason = _derive_decision_reason(
            insufficient=insufficient,
            tier_assigned=tier_assigned,
            prev_tier=prev_tier,
            consec_qualifying=consec_qualifying,
            consec_underperforming=consec_underperforming,
        )

        writer.writerow(
            [
                today_str,
                str(supplier.id),
                supplier.name,
                supplier.current_tier,
                credit_str,
                tier_locked_str,
                month_str,
                row.total_po_lines,
                backorder_pct,
                ontime_pct,
                computed_rating,
                tier_assigned,
                insufficient_str,
                consec_qualifying,
                consec_underperforming,
                decision_reason,
            ]
        )

        prev_tier = tier_assigned


# ------------------------------------------------------------------
# Monthly summary builders
# ------------------------------------------------------------------


async def _build_monthly_summary_rows(
    history_rows: list[SupplierMetricsHistory],
    year: int,
    month: int,
    session: AsyncSession,
) -> list[list[str]]:
    rows: list[list[str]] = []

    # Determine prior month
    if month == 1:
        prior_year, prior_month = year - 1, 12
    else:
        prior_year, prior_month = year, month - 1

    # Bulk fetch prior month history for all supplier_ids
    supplier_ids = [h.supplier_id for h in history_rows]
    prior_map = await _fetch_prior_month_map(
        supplier_ids, prior_year, prior_month, session
    )

    # Fetch supplier objects
    supplier_map = await _fetch_supplier_map(supplier_ids, session)

    for h in history_rows:
        supplier = supplier_map.get(h.supplier_id)
        if supplier is None:
            continue

        tier_assigned = h.tier_at_period_end or supplier.current_tier
        prior_h = prior_map.get(h.supplier_id)
        previous_tier = (
            prior_h.tier_at_period_end or supplier.current_tier
            if prior_h
            else "New Supplier"
        )

        tier_changed = (
            tier_assigned != previous_tier and previous_tier != "New Supplier"
        )
        tier_changed_str = "Yes" if tier_changed else "No"

        if previous_tier == "New Supplier":
            change_direction = "None"
        elif tier_changed:
            prev_rank = TIER_ORDER.get(previous_tier, 0)
            new_rank = TIER_ORDER.get(tier_assigned, 0)
            change_direction = "Promoted" if new_rank > prev_rank else "Demoted"
        else:
            change_direction = "None"

        insufficient = h.total_po_lines < 20
        insufficient_str = "Yes" if insufficient else "No"

        if h.total_pos > 0:
            on_time_rate_val = Decimal(h.on_time_deliveries) / Decimal(h.total_pos)
        else:
            on_time_rate_val = Decimal("0")
        if h.total_po_lines > 0:
            backorder_rate_val = Decimal(h.defect_count) / Decimal(h.total_po_lines)
        else:
            backorder_rate_val = Decimal("0")

        computed_rating = _compute_rating(on_time_rate_val, backorder_rate_val)
        backorder_pct = f"{float(backorder_rate_val) * 100:.1f}"
        ontime_pct = f"{float(on_time_rate_val) * 100:.1f}"

        rows.append(
            [
                supplier.name,
                str(supplier.id),
                previous_tier,
                tier_assigned,
                tier_changed_str,
                change_direction,
                supplier.consecutive_on_time,
                supplier.consecutive_late,
                backorder_pct,
                ontime_pct,
                computed_rating,
                insufficient_str,
                f"{supplier.credit_limit:.2f}",
            ]
        )

    return rows


def _sort_monthly_rows(rows: list[list[str]]) -> list[list[str]]:
    # Columns by index: 4=Tier_Changed, 5=Change_Direction, 11=Insufficient_Data,
    # 0=Supplier_Name
    def sort_key(row: list[str]) -> tuple[int, int, str]:
        tier_changed = row[4]  # "Yes" / "No"
        change_direction = row[5]  # "Promoted" / "Demoted" / "None"
        insufficient = row[11]  # "Yes" / "No"
        supplier_name = row[0]

        if insufficient == "Yes":
            primary = 2  # insufficient data last
        elif tier_changed == "Yes":
            primary = 0  # changes first
        else:
            primary = 1  # no-change middle

        if change_direction == "Promoted":
            secondary = 0
        elif change_direction == "Demoted":
            secondary = 1
        else:
            secondary = 2

        return (primary, secondary, supplier_name)

    return sorted(rows, key=sort_key)


# ------------------------------------------------------------------
# Formula and derivation helpers
# ------------------------------------------------------------------


def _compute_rating(on_time_rate: Decimal, backorder_rate: Decimal) -> str:
    """Locked formula: (on_time_rate * 0.6 + (1 - backorder_rate) * 0.4) * 5.0"""
    raw = (
        on_time_rate * Decimal("0.6") + (Decimal("1") - backorder_rate) * Decimal("0.4")
    ) * Decimal("5.0")
    clamped = max(Decimal("0.00"), min(Decimal("5.00"), raw))
    return f"{clamped:.2f}"


def _derive_decision_reason(
    insufficient: bool,
    tier_assigned: str,
    prev_tier: str | None,
    consec_qualifying: int,
    consec_underperforming: int,
) -> str:
    if insufficient:
        return "Insufficient data (< 20 PO lines)"
    if prev_tier is None:
        return "Initial record"
    if tier_assigned == prev_tier:
        return "Tier maintained"
    prev_rank = TIER_ORDER.get(prev_tier, 0)
    new_rank = TIER_ORDER.get(tier_assigned, 0)
    if new_rank > prev_rank:
        return f"Promoted after {consec_qualifying} consecutive qualifying months"
    return f"Demoted after {consec_underperforming} consecutive underperforming months"


# ------------------------------------------------------------------
# Month string parser
# ------------------------------------------------------------------


def _parse_month_str(month_str: str) -> tuple[int, int]:
    """Parse YYYY-MM string, raise InvalidParameterException if invalid."""
    if not re.fullmatch(r"\d{4}-\d{2}", month_str):
        raise InvalidParameterException(
            message="month must be in YYYY-MM format",
            details={"month": month_str},
        )
    year, month = int(month_str[:4]), int(month_str[5:7])
    if month < 1 or month > 12:
        raise InvalidParameterException(
            message="month value must be between 01 and 12",
            details={"month": month_str},
        )
    return year, month


# ------------------------------------------------------------------
# DB query helpers
# ------------------------------------------------------------------


async def _fetch_supplier(supplier_id: UUID, session: AsyncSession) -> Supplier:
    result = await session.execute(
        select(Supplier).where(
            Supplier.id == supplier_id,
            Supplier.deleted_at.is_(None),
        )
    )
    supplier = result.scalar_one_or_none()
    if supplier is None:
        raise NotFoundException(
            message="Supplier not found",
            details={"supplier_id": str(supplier_id)},
        )
    return supplier


async def _fetch_supplier_history(
    supplier_id: UUID,
    months: int,
    session: AsyncSession,
) -> list[SupplierMetricsHistory]:
    result = await session.execute(
        select(SupplierMetricsHistory)
        .where(SupplierMetricsHistory.supplier_id == supplier_id)
        .order_by(
            SupplierMetricsHistory.period_year.desc(),
            SupplierMetricsHistory.period_month.desc(),
        )
        .limit(months)
    )
    rows = result.scalars().all()
    return list(reversed(rows))


async def _fetch_monthly_history(
    year: int,
    month: int,
    session: AsyncSession,
) -> list[SupplierMetricsHistory]:
    result = await session.execute(
        select(SupplierMetricsHistory)
        .where(
            SupplierMetricsHistory.period_year == year,
            SupplierMetricsHistory.period_month == month,
        )
        .order_by(SupplierMetricsHistory.supplier_id)
    )
    return list(result.scalars().all())


async def _fetch_prior_month_map(
    supplier_ids: list[UUID],
    prior_year: int,
    prior_month: int,
    session: AsyncSession,
) -> dict[UUID, SupplierMetricsHistory]:
    if not supplier_ids:
        return {}
    result = await session.execute(
        select(SupplierMetricsHistory).where(
            SupplierMetricsHistory.supplier_id.in_(supplier_ids),
            SupplierMetricsHistory.period_year == prior_year,
            SupplierMetricsHistory.period_month == prior_month,
        )
    )
    return {h.supplier_id: h for h in result.scalars().all()}


async def _fetch_supplier_map(
    supplier_ids: list[UUID],
    session: AsyncSession,
) -> dict[UUID, Supplier]:
    if not supplier_ids:
        return {}
    result = await session.execute(
        select(Supplier).where(
            Supplier.id.in_(supplier_ids),
            Supplier.deleted_at.is_(None),
        )
    )
    return {s.id: s for s in result.scalars().all()}
