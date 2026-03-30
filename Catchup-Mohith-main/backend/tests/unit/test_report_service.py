# backend/tests/unit/test_report_service.py
import csv
import io
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from backend.app.core.exceptions import (
    DateRangeTooLargeException,
    InvalidParameterException,
)
from backend.app.services.report_service import (
    ReportService,
    _build_supplier_filename,
    _compute_rating,
    _sort_monthly_rows,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_supplier(name="Acme Ltd", tier="Silver", tier_locked=False):
    s = MagicMock()
    s.id = uuid4()
    s.name = name
    s.current_tier = tier
    s.credit_limit = Decimal("10000.00")
    s.tier_locked = tier_locked
    s.consecutive_on_time = 3
    s.consecutive_late = 0
    s.deleted_at = None
    return s


def _make_history_row(
    period_year=2024,
    period_month=1,
    total_po_lines=25,
    total_pos=10,
    on_time_deliveries=9,
    defect_count=1,
    tier_at_period_end="Silver",
    avg_fulfilment_rate=Decimal("0.90"),
):
    h = MagicMock()
    h.period_year = period_year
    h.period_month = period_month
    h.total_po_lines = total_po_lines
    h.total_pos = total_pos
    h.on_time_deliveries = on_time_deliveries
    h.defect_count = defect_count
    h.tier_at_period_end = tier_at_period_end
    h.avg_fulfilment_rate = avg_fulfilment_rate
    return h


def _make_session():
    session = AsyncMock()
    return session


def _parse_csv(buffer: io.StringIO) -> list[list[str]]:
    buffer.seek(0)
    return list(csv.reader(buffer))


# ---------------------------------------------------------------------------
# generate_supplier_report — validation and structure
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_supplier_report_months_gt_36_raises_date_range_too_large():
    service = ReportService()
    session = _make_session()

    with pytest.raises(DateRangeTooLargeException):
        await service.generate_supplier_report(
            supplier_id=uuid4(), months=37, session=session
        )


@pytest.mark.asyncio
async def test_supplier_report_months_lt_1_raises_invalid_parameter():
    service = ReportService()
    session = _make_session()

    with pytest.raises(InvalidParameterException):
        await service.generate_supplier_report(
            supplier_id=uuid4(), months=0, session=session
        )


@pytest.mark.asyncio
async def test_supplier_report_generates_summary_block():
    service = ReportService()
    supplier = _make_supplier(name="Acme Ltd")
    history = [_make_history_row(period_year=2024, period_month=1)]

    with (
        patch(
            "backend.app.services.report_service._fetch_supplier",
            new=AsyncMock(return_value=supplier),
        ),
        patch(
            "backend.app.services.report_service._fetch_supplier_history",
            new=AsyncMock(return_value=history),
        ),
    ):
        filename, buffer = await service.generate_supplier_report(
            supplier_id=supplier.id, months=12, session=_make_session()
        )

    rows = _parse_csv(buffer)
    assert rows[0][0] == "StockBridge Supplier Performance Report"
    assert "Acme Ltd" in rows[1][0]
    assert "Generated" in rows[3][0]
    assert "Silver Tier" in rows[4][0]


@pytest.mark.asyncio
async def test_supplier_report_months_limited_to_requested():
    service = ReportService()
    supplier = _make_supplier()
    # Simulate service receiving only 3 rows back (DB already limited)
    history = [_make_history_row(period_year=2024, period_month=m) for m in range(1, 4)]

    with (
        patch(
            "backend.app.services.report_service._fetch_supplier",
            new=AsyncMock(return_value=supplier),
        ),
        patch(
            "backend.app.services.report_service._fetch_supplier_history",
            new=AsyncMock(return_value=history),
        ),
    ):
        _, buffer = await service.generate_supplier_report(
            supplier_id=supplier.id, months=3, session=_make_session()
        )

    rows = _parse_csv(buffer)
    # Row 0-4 = summary block, row 5 = blank, row 6 = headers, rows 7+ = data
    data_rows = [r for r in rows[7:] if any(r)]
    assert len(data_rows) == 3


@pytest.mark.asyncio
async def test_supplier_report_no_history_returns_no_data_row():
    service = ReportService()
    supplier = _make_supplier()

    with (
        patch(
            "backend.app.services.report_service._fetch_supplier",
            new=AsyncMock(return_value=supplier),
        ),
        patch(
            "backend.app.services.report_service._fetch_supplier_history",
            new=AsyncMock(return_value=[]),
        ),
    ):
        _, buffer = await service.generate_supplier_report(
            supplier_id=supplier.id, months=12, session=_make_session()
        )

    content = buffer.getvalue()
    assert "No historical data available for this period" in content


# ---------------------------------------------------------------------------
# Decision_Reason derivation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_supplier_report_decision_reason_promoted():
    service = ReportService()
    supplier = _make_supplier(tier="Gold")
    supplier.consecutive_on_time = 3
    history = [
        _make_history_row(
            period_year=2024, period_month=1, tier_at_period_end="Silver"
        ),
        _make_history_row(period_year=2024, period_month=2, tier_at_period_end="Gold"),
    ]

    with (
        patch(
            "backend.app.services.report_service._fetch_supplier",
            new=AsyncMock(return_value=supplier),
        ),
        patch(
            "backend.app.services.report_service._fetch_supplier_history",
            new=AsyncMock(return_value=history),
        ),
    ):
        _, buffer = await service.generate_supplier_report(
            supplier_id=supplier.id, months=12, session=_make_session()
        )

    content = buffer.getvalue()
    assert "Promoted" in content


@pytest.mark.asyncio
async def test_supplier_report_decision_reason_demoted():
    service = ReportService()
    supplier = _make_supplier(tier="Silver")
    supplier.consecutive_late = 2
    history = [
        _make_history_row(period_year=2024, period_month=1, tier_at_period_end="Gold"),
        _make_history_row(
            period_year=2024, period_month=2, tier_at_period_end="Silver"
        ),
    ]

    with (
        patch(
            "backend.app.services.report_service._fetch_supplier",
            new=AsyncMock(return_value=supplier),
        ),
        patch(
            "backend.app.services.report_service._fetch_supplier_history",
            new=AsyncMock(return_value=history),
        ),
    ):
        _, buffer = await service.generate_supplier_report(
            supplier_id=supplier.id, months=12, session=_make_session()
        )

    content = buffer.getvalue()
    assert "Demoted" in content


@pytest.mark.asyncio
async def test_supplier_report_decision_reason_maintained():
    service = ReportService()
    supplier = _make_supplier(tier="Gold")
    history = [
        _make_history_row(period_year=2024, period_month=1, tier_at_period_end="Gold"),
        _make_history_row(period_year=2024, period_month=2, tier_at_period_end="Gold"),
    ]

    with (
        patch(
            "backend.app.services.report_service._fetch_supplier",
            new=AsyncMock(return_value=supplier),
        ),
        patch(
            "backend.app.services.report_service._fetch_supplier_history",
            new=AsyncMock(return_value=history),
        ),
    ):
        _, buffer = await service.generate_supplier_report(
            supplier_id=supplier.id, months=12, session=_make_session()
        )

    content = buffer.getvalue()
    assert "Tier maintained" in content


# ---------------------------------------------------------------------------
# Computed_Rating formula
# ---------------------------------------------------------------------------


def test_supplier_report_computed_rating_formula():
    # on_time_rate=0.9, backorder_rate=0.1
    # (0.9 * 0.6 + (1 - 0.1) * 0.4) * 5.0 = (0.54 + 0.36) * 5.0 = 4.50
    result = _compute_rating(Decimal("0.9"), Decimal("0.1"))
    assert result == "4.50"


# ---------------------------------------------------------------------------
# Monthly tier summary sorting
# ---------------------------------------------------------------------------


def _make_summary_row(
    name, prev_tier, new_tier, tier_changed, change_direction, insufficient="No"
):
    return [
        name,  # 0 Supplier_Name
        str(uuid4()),  # 1 Supplier_ID
        prev_tier,  # 2 Previous_Tier
        new_tier,  # 3 New_Tier
        tier_changed,  # 4 Tier_Changed
        change_direction,  # 5 Change_Direction
        "3",  # 6 Consecutive_Qualifying_Months
        "0",  # 7 Consecutive_Underperforming_Months
        "5.0",  # 8 Backorder_Rate_Pct
        "95.0",  # 9 On_Time_Delivery_Pct
        "4.50",  # 10 Computed_Rating
        insufficient,  # 11 Insufficient_Data
        "10000.00",  # 12 Credit_Limit_After
    ]


def test_monthly_summary_sorted_promotions_first():
    rows = [
        _make_summary_row("Alpha", "Silver", "Silver", "No", "None"),
        _make_summary_row("Beta", "Silver", "Gold", "Yes", "Promoted"),
        _make_summary_row("Gamma", "Gold", "Silver", "Yes", "Demoted"),
    ]

    sorted_rows = _sort_monthly_rows(rows)

    names = [r[0] for r in sorted_rows]
    assert names.index("Beta") < names.index("Gamma")
    assert names.index("Beta") < names.index("Alpha")
    assert names.index("Gamma") < names.index("Alpha")


def test_monthly_summary_sorted_demotions_before_no_change():
    rows = [
        _make_summary_row("NoChange", "Gold", "Gold", "No", "None"),
        _make_summary_row("Demoted", "Gold", "Silver", "Yes", "Demoted"),
    ]

    sorted_rows = _sort_monthly_rows(rows)

    names = [r[0] for r in sorted_rows]
    assert names.index("Demoted") < names.index("NoChange")


@pytest.mark.asyncio
async def test_monthly_summary_no_data_returns_no_data_row():
    service = ReportService()

    with patch(
        "backend.app.services.report_service._fetch_monthly_history",
        new=AsyncMock(return_value=[]),
    ):
        _, buffer = await service.generate_monthly_summary(
            month_str="2024-01", session=_make_session()
        )

    content = buffer.getvalue()
    assert "No tier recalculation data found for 2024-01" in content


# ---------------------------------------------------------------------------
# Filename helpers
# ---------------------------------------------------------------------------


def test_filename_slugifies_supplier_name():
    supplier = _make_supplier(name="Prime Parts Ltd!")
    filename = _build_supplier_filename(supplier, "2025-01-15")
    assert "prime-parts-ltd" in filename


def test_filename_includes_id_short_and_date():
    supplier = _make_supplier()
    today = date.today().isoformat()
    filename = _build_supplier_filename(supplier, today)
    id_short = str(supplier.id)[:8]
    assert id_short in filename
    assert today in filename
