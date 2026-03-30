# backend/tests/integration/test_stock_ledger_integration.py
import pytest
from httpx import AsyncClient

from .conftest import auth_headers


@pytest.mark.asyncio
async def test_stock_ledger_unauthenticated_returns_401(client: AsyncClient):
    response = await client.get("/stock-ledger/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_stock_ledger_returns_200(client: AsyncClient, manager_token: str):
    response = await client.get(
        "/stock-ledger/?limit=20", headers=auth_headers(manager_token)
    )
    assert response.status_code == 200
    assert "data" in response.json()


@pytest.mark.asyncio
async def test_cursor_pagination_returns_next_cursor(
    client: AsyncClient, manager_token: str
):
    response = await client.get(
        "/stock-ledger/?limit=1", headers=auth_headers(manager_token)
    )
    assert response.status_code == 200
    assert "next_cursor" in response.json()["meta"]


@pytest.mark.asyncio
async def test_stock_ledger_entry_created_after_grn_receipt(
    client: AsyncClient,
    staff_token: str,
    manager_token: str,
    seeded_po,
    seeded_product,
):
    create_response = await client.post(
        "/grns/",
        json={"po_id": str(seeded_po.id)},
        headers=auth_headers(staff_token),
    )
    assert create_response.status_code == 201
    grn_id = create_response.json()["data"]["id"]

    add_line_response = await client.post(
        f"/grns/{grn_id}/lines",
        json={
            "product_id": str(seeded_product.id),
            "quantity_received": "5.0000",
            "unit_cost": "20.0000",
            "barcode_scanned": seeded_product.barcode,
        },
        headers=auth_headers(staff_token),
    )
    assert add_line_response.status_code in (200, 201)

    complete_response = await client.post(
        f"/grns/{grn_id}/complete",
        headers=auth_headers(manager_token),
    )
    assert complete_response.status_code == 200

    ledger_response = await client.get(
        f"/stock-ledger/?product_id={seeded_product.id}&limit=20",
        headers=auth_headers(manager_token),
    )
    assert ledger_response.status_code == 200
    entries = ledger_response.json()["data"]
    assert any(entry["change_type"] == "grn_receipt" for entry in entries)
