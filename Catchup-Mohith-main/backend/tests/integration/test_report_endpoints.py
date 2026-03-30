# backend/tests/integration/test_report_endpoints.py
import csv
import io
import re
from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from backend.app.models.supplier_metrics_history import SupplierMetricsHistory
from backend.tests.conftest import (
    auth_headers,
    create_supplier,
    get_token_for_user,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _create_metrics_history(
    db_session,
    supplier_id,
    period_year: int,
    period_month: int,
    tier_at_period_end: str = "Silver",
    total_po_lines: int = 25,
    total_pos: int = 10,
    on_time_deliveries: int = 9,
    defect_count: int = 1,
) -> SupplierMetricsHistory:
    row = SupplierMetricsHistory(
        supplier_id=supplier_id,
        period_year=period_year,
        period_month=period_month,
        total_pos=total_pos,
        on_time_deliveries=on_time_deliveries,
        total_po_lines=total_po_lines,
        defect_count=defect_count,
        avg_fulfilment_rate=Decimal("0.90"),
        computed_score=Decimal("0.85"),
        tier_at_period_end=tier_at_period_end,
    )
    db_session.add(row)
    await db_session.flush()
    return row


def _parse_csv_text(text: str) -> list[list[str]]:
    return list(csv.reader(io.StringIO(text)))


# ---------------------------------------------------------------------------
# GET /reports/suppliers/{supplier_id} — content type and headers
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_supplier_report_returns_csv_content_type(
    client, manager_user, db_session
):
    supplier = await create_supplier(db_session)
    await get_token_for_user(client, manager_user)

    response = await client.get(
        f"/reports/suppliers/{supplier.id}",
        headers=auth_headers(manager_user),
    )
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_supplier_report_has_content_disposition_header(
    client, manager_user, db_session
):
    supplier = await create_supplier(db_session)
    await get_token_for_user(client, manager_user)

    response = await client.get(
        f"/reports/suppliers/{supplier.id}",
        headers=auth_headers(manager_user),
    )
    assert response.status_code == 200

    disposition = response.headers.get("content-disposition", "")
    assert "attachment" in disposition
    assert "filename=" in disposition
    assert ".csv" in disposition


@pytest.mark.asyncio
async def test_supplier_report_filename_format_correct(
    client, manager_user, db_session
):
    supplier = await create_supplier(db_session)
    supplier.name = "Test Supplier Co"
    await db_session.flush()

    await get_token_for_user(client, manager_user)
    response = await client.get(
        f"/reports/suppliers/{supplier.id}",
        headers=auth_headers(manager_user),
    )
    assert response.status_code == 200

    disposition = response.headers.get("content-disposition", "")
    match = re.search(r'filename="([^"]+)"', disposition)
    assert match, f"No filename in Content-Disposition: {disposition}"
    filename = match.group(1)

    id_short = str(supplier.id)[:8]
    today = date.today().isoformat()

    assert filename.startswith("supplier_")
    assert id_short in filename
    assert today in filename
    assert filename.endswith(".csv")


# ---------------------------------------------------------------------------
# GET /reports/suppliers/{supplier_id} — access control
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_supplier_report_staff_returns_403(client, staff_user, db_session):
    supplier = await create_supplier(db_session)
    await get_token_for_user(client, staff_user)

    response = await client.get(
        f"/reports/suppliers/{supplier.id}",
        headers=auth_headers(staff_user),
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"


# ---------------------------------------------------------------------------
# GET /reports/suppliers/{supplier_id} — months param
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_supplier_report_months_param_respected(client, manager_user, db_session):
    supplier = await create_supplier(db_session)

    # Create 5 history rows; request only 2 — CSV must have exactly 2 data rows
    for month in range(1, 6):
        await _create_metrics_history(
            db_session,
            supplier_id=supplier.id,
            period_year=2024,
            period_month=month,
        )

    await get_token_for_user(client, manager_user)
    response = await client.get(
        f"/reports/suppliers/{supplier.id}?months=2",
        headers=auth_headers(manager_user),
    )
    assert response.status_code == 200

    rows = _parse_csv_text(response.text)
    # Rows 0-4: summary block (5 rows), row 5: blank, row 6: headers, rows 7+: data
    data_rows = [r for r in rows[7:] if any(cell.strip() for cell in r)]
    assert len(data_rows) == 2


@pytest.mark.asyncio
async def test_supplier_report_months_37_returns_400(client, manager_user, db_session):
    supplier = await create_supplier(db_session)
    await get_token_for_user(client, manager_user)

    response = await client.get(
        f"/reports/suppliers/{supplier.id}?months=37",
        headers=auth_headers(manager_user),
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "DATE_RANGE_TOO_LARGE"


@pytest.mark.asyncio
async def test_supplier_report_invalid_supplier_returns_404(
    client, manager_user, db_session
):
    nonexistent_id = uuid4()
    await get_token_for_user(client, manager_user)

    response = await client.get(
        f"/reports/suppliers/{nonexistent_id}",
        headers=auth_headers(manager_user),
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


# ---------------------------------------------------------------------------
# GET /reports/monthly-tier-summary
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_monthly_summary_returns_csv(client, manager_user, db_session):
    await get_token_for_user(client, manager_user)

    response = await client.get(
        "/reports/monthly-tier-summary?month=2024-01",
        headers=auth_headers(manager_user),
    )
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "StockBridge Monthly Tier Summary" in response.text


@pytest.mark.asyncio
async def test_monthly_summary_invalid_month_format_returns_400(
    client, manager_user, db_session
):
    await get_token_for_user(client, manager_user)

    # "2024-1" fails the YYYY-MM regex — single-digit month is invalid
    response = await client.get(
        "/reports/monthly-tier-summary?month=2024-1",
        headers=auth_headers(manager_user),
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_PARAMETER"


@pytest.mark.asyncio
async def test_monthly_summary_staff_returns_403(client, staff_user, db_session):
    await get_token_for_user(client, staff_user)

    response = await client.get(
        "/reports/monthly-tier-summary?month=2024-01",
        headers=auth_headers(staff_user),
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"
