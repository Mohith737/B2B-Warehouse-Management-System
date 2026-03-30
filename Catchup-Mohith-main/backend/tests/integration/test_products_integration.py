# backend/tests/integration/test_products_integration.py
import pytest
from httpx import AsyncClient

from .conftest import auth_headers, random_uuid


@pytest.mark.asyncio
async def test_list_products_returns_200(client: AsyncClient, admin_token: str):
    response = await client.get(
        "/products/?page=1&page_size=20", headers=auth_headers(admin_token)
    )
    assert response.status_code == 200
    assert "data" in response.json()


@pytest.mark.asyncio
async def test_create_product_as_admin_returns_201(
    client: AsyncClient, admin_token: str
):
    payload = {
        "sku": "IT-PROD-ADMIN-001",
        "name": "Integration Product",
        "description": "Created in integration test",
        "unit_of_measure": "pcs",
        "reorder_point": "5",
        "reorder_quantity": "10",
        "unit_price": "12.50",
        "barcode": "ITBARCODE0001",
    }
    response = await client.post(
        "/products/", json=payload, headers=auth_headers(admin_token)
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_create_product_as_staff_returns_403(
    client: AsyncClient, staff_token: str
):
    payload = {
        "sku": "IT-PROD-STAFF-001",
        "name": "Denied Product",
        "unit_of_measure": "pcs",
        "reorder_point": "5",
        "reorder_quantity": "10",
        "unit_price": "12.50",
    }
    response = await client.post(
        "/products/", json=payload, headers=auth_headers(staff_token)
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_product_not_found_returns_404(client: AsyncClient, admin_token: str):
    response = await client.get(
        f"/products/{random_uuid()}", headers=auth_headers(admin_token)
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_products_pagination(client: AsyncClient, admin_token: str):
    response = await client.get(
        "/products/?page=1&page_size=1", headers=auth_headers(admin_token)
    )
    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["page"] == 1
    assert body["meta"]["page_size"] == 1
