# backend/tests/integration/test_grns_integration.py
import pytest
from httpx import AsyncClient

from .conftest import auth_headers


@pytest.mark.asyncio
async def test_grn_unauthenticated_returns_401(client: AsyncClient):
    response = await client.get("/grns/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_grn_returns_201(client: AsyncClient, staff_token: str, seeded_po):
    response = await client.post(
        "/grns/",
        json={"po_id": str(seeded_po.id)},
        headers=auth_headers(staff_token),
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_get_grn_returns_200(client: AsyncClient, staff_token: str, seeded_po):
    create_response = await client.post(
        "/grns/",
        json={"po_id": str(seeded_po.id)},
        headers=auth_headers(staff_token),
    )
    grn_id = create_response.json()["data"]["id"]

    get_response = await client.get(
        f"/grns/{grn_id}", headers=auth_headers(staff_token)
    )
    assert get_response.status_code == 200


@pytest.mark.asyncio
async def test_receive_line_returns_200(
    client: AsyncClient,
    staff_token: str,
    seeded_po,
    seeded_product,
):
    create_response = await client.post(
        "/grns/",
        json={"po_id": str(seeded_po.id)},
        headers=auth_headers(staff_token),
    )
    grn_id = create_response.json()["data"]["id"]

    response = await client.post(
        f"/grns/{grn_id}/lines",
        json={
            "product_id": str(seeded_product.id),
            "quantity_received": "2.0000",
            "unit_cost": "20.0000",
            "barcode_scanned": seeded_product.barcode,
        },
        headers=auth_headers(staff_token),
    )
    assert response.status_code in (200, 201)


@pytest.mark.asyncio
async def test_complete_grn_returns_200(
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
    grn_id = create_response.json()["data"]["id"]

    line_response = await client.post(
        f"/grns/{grn_id}/lines",
        json={
            "product_id": str(seeded_product.id),
            "quantity_received": "5.0000",
            "unit_cost": "20.0000",
            "barcode_scanned": seeded_product.barcode,
        },
        headers=auth_headers(staff_token),
    )
    assert line_response.status_code in (200, 201)

    complete_response = await client.post(
        f"/grns/{grn_id}/complete",
        headers=auth_headers(manager_token),
    )
    assert complete_response.status_code == 200


@pytest.mark.asyncio
async def test_create_grn_as_staff_allowed(
    client: AsyncClient, staff_token: str, seeded_po
):
    response = await client.post(
        "/grns/",
        json={"po_id": str(seeded_po.id)},
        headers=auth_headers(staff_token),
    )
    assert response.status_code == 201
