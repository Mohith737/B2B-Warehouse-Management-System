# backend/tests/integration/test_supplier_endpoints.py
import pytest
from httpx import AsyncClient


async def get_token(client: AsyncClient, email: str, password: str) -> str:
    response = await client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return response.json()["data"]["access_token"]


async def create_test_supplier(
    client: AsyncClient,
    token: str,
    name: str = "Test Supplier Co",
    email: str = "testsupplier@example.com",
) -> dict:
    response = await client.post(
        "/suppliers/",
        json={
            "name": name,
            "email": email,
            "payment_terms_days": 30,
            "lead_time_days": 7,
            "credit_limit": "50000.00",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    return response.json()["data"]


@pytest.mark.asyncio
async def test_create_supplier_returns_201(client, manager_user, admin_user):
    token=see .env file
    response = await client.post(
        "/suppliers/",
        json={
            "name": "Acme Corp",
            "email": "acme@corp.com",
            "payment_terms_days": 30,
            "lead_time_days": 5,
            "credit_limit": "100000.00",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["name"] == "Acme Corp"
    assert data["current_tier"] == "Silver"
    assert data["tier_locked"] is False
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_create_supplier_duplicate_email_returns_409(client, manager_user):
    token=see .env file
    await create_test_supplier(
        client,
        token,
        name="First Supplier",
        email="dupe@supplier.com",
    )
    response = await client.post(
        "/suppliers/",
        json={
            "name": "Second Supplier",
            "email": "dupe@supplier.com",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"


@pytest.mark.asyncio
async def test_create_supplier_staff_returns_403(client, staff_user):
    token=see .env file
    response = await client.post(
        "/suppliers/",
        json={
            "name": "Blocked Supplier",
            "email": "blocked@supplier.com",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"


@pytest.mark.asyncio
async def test_get_supplier_returns_200(client, manager_user):
    token=see .env file
    created = await create_test_supplier(
        client,
        token,
        name="Get Test Supplier",
        email="get.test@supplier.com",
    )
    response = await client.get(
        f"/suppliers/{created['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["id"] == created["id"]
    assert "current_tier" in data
    assert "credit_limit" in data


@pytest.mark.asyncio
async def test_get_supplier_metrics_returns_list(client, manager_user):
    token=see .env file
    created = await create_test_supplier(
        client,
        token,
        name="Metrics Test Supplier",
        email="metrics@supplier.com",
    )
    response = await client.get(
        f"/suppliers/{created['id']}/metrics",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["data"] == []


@pytest.mark.asyncio
async def test_update_supplier_returns_200(client, manager_user):
    token=see .env file
    created = await create_test_supplier(
        client,
        token,
        name="Update Test Supplier",
        email="update.test@supplier.com",
    )
    response = await client.put(
        f"/suppliers/{created['id']}",
        json={"payment_terms_days": 45},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["payment_terms_days"] == 45


@pytest.mark.asyncio
async def test_deactivate_supplier_admin_only(client, admin_user, manager_user):
    m_token=see .env file
    a_token=see .env file
    created = await create_test_supplier(
        client,
        m_token,
        name="Deactivate Test Supplier",
        email="deactivate@supplier.com",
    )
    resp_mgr = await client.post(
        f"/suppliers/{created['id']}/deactivate",
        headers={"Authorization": f"Bearer {m_token}"},
    )
    assert resp_mgr.status_code == 403

    resp_admin = await client.post(
        f"/suppliers/{created['id']}/deactivate",
        headers={"Authorization": f"Bearer {a_token}"},
    )
    assert resp_admin.status_code == 200
    assert resp_admin.json()["data"]["is_active"] is False


@pytest.mark.asyncio
async def test_activate_supplier_admin_only(client, admin_user, manager_user):
    m_token=see .env file
    a_token=see .env file
    created = await create_test_supplier(
        client,
        m_token,
        name="Activate Test Supplier",
        email="activate@supplier.com",
    )
    await client.post(
        f"/suppliers/{created['id']}/deactivate",
        headers={"Authorization": f"Bearer {a_token}"},
    )
    resp_mgr = await client.post(
        f"/suppliers/{created['id']}/activate",
        headers={"Authorization": f"Bearer {m_token}"},
    )
    assert resp_mgr.status_code == 403

    resp_admin = await client.post(
        f"/suppliers/{created['id']}/activate",
        headers={"Authorization": f"Bearer {a_token}"},
    )
    assert resp_admin.status_code == 200
    assert resp_admin.json()["data"]["is_active"] is True


@pytest.mark.asyncio
async def test_tier_lock_admin_only_returns_200(client, admin_user, manager_user):
    m_token=see .env file
    a_token=see .env file
    created = await create_test_supplier(
        client,
        m_token,
        name="Tier Lock Test Supplier",
        email="tierlock@supplier.com",
    )
    resp_mgr = await client.put(
        f"/suppliers/{created['id']}/tier-lock",
        json={"tier_locked": True},
        headers={"Authorization": f"Bearer {m_token}"},
    )
    assert resp_mgr.status_code == 403

    resp_admin = await client.put(
        f"/suppliers/{created['id']}/tier-lock",
        json={"tier_locked": True},
        headers={"Authorization": f"Bearer {a_token}"},
    )
    assert resp_admin.status_code == 200
    assert resp_admin.json()["data"]["tier_locked"] is True


@pytest.mark.asyncio
async def test_list_suppliers_pagination_default_20(client, manager_user):
    token=see .env file
    response = await client.get(
        "/suppliers/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    meta = response.json()["meta"]
    assert meta["page_size"] == 20
    assert meta["page"] == 1


@pytest.mark.asyncio
async def test_list_suppliers_filter_by_tier(client, manager_user):
    token=see .env file
    await create_test_supplier(
        client,
        token,
        name="Silver Tier Supplier",
        email="silver.tier@supplier.com",
    )
    response = await client.get(
        "/suppliers/?tier=Silver",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert all(s["current_tier"] == "Silver" for s in data)


@pytest.mark.asyncio
async def test_list_suppliers_filter_by_active(client, admin_user, manager_user):
    m_token=see .env file
    a_token=see .env file
    created = await create_test_supplier(
        client,
        m_token,
        name="Active Filter Supplier",
        email="active.filter@supplier.com",
    )
    await client.post(
        f"/suppliers/{created['id']}/deactivate",
        headers={"Authorization": f"Bearer {a_token}"},
    )
    response = await client.get(
        "/suppliers/?is_active=false",
        headers={"Authorization": f"Bearer {m_token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert all(s["is_active"] is False for s in data)


@pytest.mark.asyncio
async def test_list_suppliers_search_by_name(client, manager_user):
    token=see .env file
    await create_test_supplier(
        client,
        token,
        name="Unique Zephyr Industries",
        email="zephyr@industries.com",
    )
    response = await client.get(
        "/suppliers/?search=Zephyr",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert any("Zephyr" in s["name"] for s in data)


@pytest.mark.asyncio
async def test_delete_supplier_admin_only_returns_200(client, admin_user, manager_user):
    m_token=see .env file
    a_token=see .env file
    created = await create_test_supplier(
        client,
        m_token,
        name="Delete Test Supplier",
        email="delete.test@supplier.com",
    )
    response = await client.delete(
        f"/suppliers/{created['id']}",
        headers={"Authorization": f"Bearer {a_token}"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["message"] == "Supplier deleted successfully"


@pytest.mark.asyncio
async def test_delete_supplier_manager_returns_403(client, manager_user):
    token=see .env file
    created = await create_test_supplier(
        client,
        token,
        name="Manager Delete Attempt",
        email="mgr.delete@supplier.com",
    )
    response = await client.delete(
        f"/suppliers/{created['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


