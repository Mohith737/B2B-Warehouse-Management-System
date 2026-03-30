# backend/tests/integration/test_suppliers_integration.py
import pytest
from httpx import AsyncClient

from .conftest import auth_headers, random_uuid


@pytest.mark.asyncio
async def test_list_suppliers_returns_200(client: AsyncClient, manager_token: str):
    response = await client.get(
        "/suppliers/?page=1&page_size=20", headers=auth_headers(manager_token)
    )
    assert response.status_code == 200
    assert "data" in response.json()


@pytest.mark.asyncio
async def test_create_supplier_as_manager_returns_201(
    client: AsyncClient, manager_token: str
):
    payload = {
        "name": "Integration Supplier",
        "email": "integration-supplier@example.com",
        "phone": "+1-555-0001",
        "address": "123 Integration Way",
        "payment_terms_days": 30,
        "lead_time_days": 7,
        "credit_limit": "25000.00",
    }
    response = await client.post(
        "/suppliers/", json=payload, headers=auth_headers(manager_token)
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_create_supplier_as_staff_returns_403(
    client: AsyncClient, staff_token: str
):
    payload = {
        "name": "Denied Supplier",
        "email": "denied-supplier@example.com",
        "credit_limit": "1000.00",
    }
    response = await client.post(
        "/suppliers/", json=payload, headers=auth_headers(staff_token)
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_supplier_not_found_returns_404(
    client: AsyncClient, manager_token: str
):
    response = await client.get(
        f"/suppliers/{random_uuid()}", headers=auth_headers(manager_token)
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_suppliers_tier_filter(client: AsyncClient, manager_token: str):
    response = await client.get(
        "/suppliers/?tier=Gold&page=1&page_size=20",
        headers=auth_headers(manager_token),
    )
    assert response.status_code == 200
    body = response.json()
    assert "data" in body
