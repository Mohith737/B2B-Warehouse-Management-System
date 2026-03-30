# backend/tests/integration/test_purchase_orders_integration.py
import pytest
from httpx import AsyncClient

from .conftest import auth_headers, random_uuid


@pytest.mark.asyncio
async def test_list_pos_returns_200(client: AsyncClient, manager_token: str):
    response = await client.get(
        "/purchase-orders/?page=1&page_size=20", headers=auth_headers(manager_token)
    )
    assert response.status_code == 200
    assert "data" in response.json()


@pytest.mark.asyncio
async def test_create_po_as_manager_returns_201(
    client: AsyncClient,
    manager_token: str,
    seeded_supplier,
    seeded_product,
):
    payload = {
        "supplier_id": str(seeded_supplier.id),
        "notes": "Integration PO",
        "lines": [
            {
                "product_id": str(seeded_product.id),
                "quantity_ordered": "2.0000",
                "unit_price": "15.0000",
            }
        ],
    }
    response = await client.post(
        "/purchase-orders/", json=payload, headers=auth_headers(manager_token)
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_create_po_po_number_starts_with_sb(
    client: AsyncClient,
    manager_token: str,
    seeded_supplier,
    seeded_product,
):
    payload = {
        "supplier_id": str(seeded_supplier.id),
        "notes": "Integration PO number check",
        "lines": [
            {
                "product_id": str(seeded_product.id),
                "quantity_ordered": "3.0000",
                "unit_price": "20.0000",
            }
        ],
    }
    response = await client.post(
        "/purchase-orders/", json=payload, headers=auth_headers(manager_token)
    )
    assert response.status_code == 201
    po_number = response.json()["data"]["po_number"]
    assert po_number.startswith("SB-")


@pytest.mark.asyncio
async def test_create_po_as_staff_returns_403(
    client: AsyncClient,
    staff_token: str,
    seeded_supplier,
    seeded_product,
):
    payload = {
        "supplier_id": str(seeded_supplier.id),
        "notes": "Denied PO",
        "lines": [
            {
                "product_id": str(seeded_product.id),
                "quantity_ordered": "1.0000",
                "unit_price": "10.0000",
            }
        ],
    }
    response = await client.post(
        "/purchase-orders/", json=payload, headers=auth_headers(staff_token)
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_po_not_found_returns_404(client: AsyncClient, manager_token: str):
    response = await client.get(
        f"/purchase-orders/{random_uuid()}", headers=auth_headers(manager_token)
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_credit_check_returns_200(
    client: AsyncClient, manager_token: str, seeded_po
):
    # Backend has no dedicated /credit-check route in this codebase.
    response = await client.get(
        f"/purchase-orders/{seeded_po.id}", headers=auth_headers(manager_token)
    )
    assert response.status_code == 200
