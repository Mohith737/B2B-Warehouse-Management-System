# backend/tests/integration/test_dashboard_endpoints.py
from decimal import Decimal

import pytest

from backend.tests.conftest import (
    auth_headers,
    create_product,
    get_token_for_user,
)

# ---------------------------------------------------------------------------
# GET /dashboard — role dispatch, status codes
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dashboard_staff_returns_200(client, staff_user, db_session):
    await get_token_for_user(client, staff_user)
    response = await client.get("/dashboard/", headers=auth_headers(staff_user))
    assert response.status_code == 200
    body = response.json()
    assert "data" in body


@pytest.mark.asyncio
async def test_dashboard_manager_returns_200(client, manager_user, db_session):
    await get_token_for_user(client, manager_user)
    response = await client.get("/dashboard/", headers=auth_headers(manager_user))
    assert response.status_code == 200
    body = response.json()
    assert "data" in body


@pytest.mark.asyncio
async def test_dashboard_admin_returns_200(client, admin_user, db_session):
    await get_token_for_user(client, admin_user)
    response = await client.get("/dashboard/", headers=auth_headers(admin_user))
    assert response.status_code == 200
    body = response.json()
    assert "data" in body


@pytest.mark.asyncio
async def test_dashboard_staff_response_has_staff_fields_only(
    client, staff_user, db_session
):
    await get_token_for_user(client, staff_user)
    response = await client.get("/dashboard/", headers=auth_headers(staff_user))
    assert response.status_code == 200
    data = response.json()["data"]

    # Staff-specific fields must be present
    assert "pending_grns" in data
    assert "total_products" in data
    assert "low_stock_count" in data
    assert "recent_stock_movements" in data

    # Manager / admin-only fields must NOT be present
    assert "open_pos" not in data
    assert "total_users" not in data
    assert "system_health" not in data
    assert "email_failures_unresolved" not in data


@pytest.mark.asyncio
async def test_dashboard_unauthenticated_returns_401(client, db_session):
    response = await client.get("/dashboard/")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /dashboard/low-stock
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_low_stock_returns_paginated_list(client, admin_user, db_session):
    await get_token_for_user(client, admin_user)

    # Create a product that is below its reorder threshold
    product = await create_product(db_session)
    # Set current_stock below reorder_point (reorder_point defaults to 5)
    from backend.app.models.product import Product
    from sqlalchemy import update

    await db_session.execute(
        update(Product)
        .where(Product.id == product.id)
        .values(current_stock=Decimal("2"), reorder_point=Decimal("5"))
    )
    await db_session.flush()

    response = await client.get(
        "/dashboard/low-stock", headers=auth_headers(admin_user)
    )
    assert response.status_code == 200
    body = response.json()
    assert "data" in body
    assert "meta" in body
    assert isinstance(body["data"], list)
    assert body["meta"]["page"] == 1

    skus = [item["sku"] for item in body["data"]]
    assert product.sku in skus


@pytest.mark.asyncio
async def test_low_stock_page_size_max_50(client, admin_user, db_session):
    await get_token_for_user(client, admin_user)
    response = await client.get(
        "/dashboard/low-stock?page_size=51", headers=auth_headers(admin_user)
    )
    # FastAPI Query(le=50) rejects page_size=51 with 422
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /dashboard/recent-activity
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_recent_activity_returns_list(client, manager_user, db_session):
    await get_token_for_user(client, manager_user)
    response = await client.get(
        "/dashboard/recent-activity", headers=auth_headers(manager_user)
    )
    assert response.status_code == 200
    body = response.json()
    assert "data" in body
    assert isinstance(body["data"], list)


@pytest.mark.asyncio
async def test_recent_activity_staff_filtered(client, staff_user, db_session):
    await get_token_for_user(client, staff_user)

    # Staff can access recent-activity but only sees their own GRN-linked entries.
    # With a clean DB there are no ledger entries for this user, so data is empty.
    response = await client.get(
        "/dashboard/recent-activity", headers=auth_headers(staff_user)
    )
    assert response.status_code == 200
    body = response.json()
    assert "data" in body
    # No GRNs created by this staff user in a clean test DB — list is empty
    assert body["data"] == []
