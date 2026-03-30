# backend/tests/integration/test_dashboard_integration.py
import pytest
from httpx import AsyncClient

from .conftest import auth_headers


@pytest.mark.asyncio
async def test_dashboard_unauthenticated_returns_401(client: AsyncClient):
    response = await client.get("/dashboard/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_dashboard_staff_returns_staff_fields(
    client: AsyncClient, staff_token: str
):
    response = await client.get("/dashboard/", headers=auth_headers(staff_token))
    assert response.status_code == 200
    body = response.json()["data"]
    assert "total_products" in body
    assert "recent_stock_movements" in body


@pytest.mark.asyncio
async def test_dashboard_manager_returns_manager_fields(
    client: AsyncClient, manager_token: str
):
    response = await client.get("/dashboard/", headers=auth_headers(manager_token))
    assert response.status_code == 200
    body = response.json()["data"]
    assert "open_pos" in body
    assert "recent_activity" in body


@pytest.mark.asyncio
async def test_dashboard_admin_returns_admin_fields_with_system_health(
    client: AsyncClient,
    admin_token: str,
):
    response = await client.get("/dashboard/", headers=auth_headers(admin_token))
    assert response.status_code == 200
    body = response.json()["data"]
    assert "system_health" in body


@pytest.mark.asyncio
async def test_dashboard_low_stock_returns_200(client: AsyncClient, manager_token: str):
    response = await client.get(
        "/dashboard/low-stock?page=1&page_size=20",
        headers=auth_headers(manager_token),
    )
    assert response.status_code == 200
    assert "data" in response.json()
