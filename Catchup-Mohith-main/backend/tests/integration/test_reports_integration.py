# backend/tests/integration/test_reports_integration.py
import pytest
from httpx import AsyncClient

from .conftest import auth_headers


@pytest.mark.asyncio
async def test_supplier_report_returns_csv(
    client: AsyncClient,
    manager_token: str,
    seeded_supplier,
):
    response = await client.get(
        f"/reports/suppliers/{seeded_supplier.id}?months=12",
        headers=auth_headers(manager_token),
    )
    assert response.status_code == 200
    assert "text/csv" in response.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_monthly_tier_summary_returns_csv(
    client: AsyncClient, manager_token: str
):
    response = await client.get(
        "/reports/monthly-tier-summary?month=2026-03",
        headers=auth_headers(manager_token),
    )
    assert response.status_code == 200
    assert "text/csv" in response.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_reports_staff_returns_403(
    client: AsyncClient,
    staff_token: str,
    seeded_supplier,
):
    response = await client.get(
        f"/reports/suppliers/{seeded_supplier.id}?months=12",
        headers=auth_headers(staff_token),
    )
    assert response.status_code == 403
