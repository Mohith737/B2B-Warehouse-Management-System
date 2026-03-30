# /home/mohith/Catchup-Mohith/backend/tests/integration/test_product_endpoints.py
import pytest
from httpx import AsyncClient


async def get_token(client: AsyncClient, email: str, password: str) -> str:
    response = await client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return response.json()["data"]["access_token"]


async def create_test_product(
    client: AsyncClient,
    token: str,
    sku: str = "TEST-SKU-001",
    barcode: str | None = None,
) -> dict:
    body = {
        "sku": sku,
        "name": "Test Widget",
        "unit_of_measure": "units",
        "unit_price": "9.99",
        "reorder_point": "5.0000",
        "reorder_quantity": "20.0000",
    }
    if barcode:
        body["barcode"] = barcode
    response = await client.post(
        "/products/",
        json=body,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    return response.json()["data"]


@pytest.mark.asyncio
async def test_create_product_returns_201_with_stock_badge(client, manager_user):
    token=see .env file
    response = await client.post(
        "/products/",
        json={
            "sku": "BADGE-TEST-001",
            "name": "Badge Test Product",
            "unit_of_measure": "units",
            "unit_price": "10.00",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["stock_badge"] == "out_of_stock"
    assert data["version"] == 1
    assert "current_stock" in data


@pytest.mark.asyncio
async def test_create_product_duplicate_sku_returns_409(client, manager_user):
    token=see .env file
    await create_test_product(client, token, sku="DUPE-001")
    response = await client.post(
        "/products/",
        json={
            "sku": "DUPE-001",
            "name": "Duplicate",
            "unit_of_measure": "units",
            "unit_price": "5.00",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"


@pytest.mark.asyncio
async def test_create_product_warehouse_staff_returns_403(
    client, staff_user, manager_user
):
    token=see .env file
    response = await client.post(
        "/products/",
        json={
            "sku": "STAFF-ATTEMPT",
            "name": "Should Fail",
            "unit_of_measure": "units",
            "unit_price": "5.00",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"


@pytest.mark.asyncio
async def test_get_product_returns_200_with_badge(client, manager_user):
    token=see .env file
    created = await create_test_product(client, token, sku="GET-TEST-001")
    response = await client.get(
        f"/products/{created['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert "stock_badge" in data
    assert data["id"] == created["id"]


@pytest.mark.asyncio
async def test_get_soft_deleted_product_returns_404(client, admin_user, manager_user):
    m_token=see .env file
    a_token=see .env file
    created = await create_test_product(client, m_token, sku="SOFT-DEL-001")
    await client.delete(
        f"/products/{created['id']}",
        headers={"Authorization": f"Bearer {a_token}"},
    )
    response = await client.get(
        f"/products/{created['id']}",
        headers={"Authorization": f"Bearer {m_token}"},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_update_product_returns_200_incremented_version(client, manager_user):
    token=see .env file
    created = await create_test_product(client, token, sku="UPD-TEST-001")
    assert created["version"] == 1
    response = await client.put(
        f"/products/{created['id']}",
        json={
            "name": "Updated Widget Name",
            "version": 1,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["version"] == 2
    assert data["name"] == "Updated Widget Name"


@pytest.mark.asyncio
async def test_update_product_stale_version_returns_409(client, manager_user):
    token=see .env file
    created = await create_test_product(client, token, sku="STALE-VER-001")
    response = await client.put(
        f"/products/{created['id']}",
        json={
            "name": "Should Fail",
            "version": 999,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 409
    error = response.json()["error"]
    assert error["code"] == "CONFLICT"
    assert "current_version" in error["details"]


@pytest.mark.asyncio
async def test_delete_product_admin_only_returns_200(client, admin_user, manager_user):
    m_token=see .env file
    a_token=see .env file
    created = await create_test_product(client, m_token, sku="DEL-ADMIN-001")
    response = await client.delete(
        f"/products/{created['id']}",
        headers={"Authorization": f"Bearer {a_token}"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["message"] == "Product deleted successfully"


@pytest.mark.asyncio
async def test_delete_product_manager_returns_403(client, manager_user):
    token=see .env file
    created = await create_test_product(client, token, sku="DEL-MGR-001")
    response = await client.delete(
        f"/products/{created['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_products_pagination_default_20(client, manager_user):
    token=see .env file
    response = await client.get(
        "/products/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    meta = response.json()["meta"]
    assert meta["page_size"] == 20
    assert meta["page"] == 1


@pytest.mark.asyncio
async def test_list_products_page_size_over_100_returns_400(client, manager_user):
    token=see .env file
    response = await client.get(
        "/products/?page_size=101",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "PAGE_LIMIT_EXCEEDED"


@pytest.mark.asyncio
async def test_list_products_filter_by_badge(client, manager_user):
    token=see .env file
    await create_test_product(client, token, sku="BADGE-FILTER-001")
    response = await client.get(
        "/products/?badge=out_of_stock",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert all(p["stock_badge"] == "out_of_stock" for p in data)


@pytest.mark.asyncio
async def test_list_products_search_by_name(client, manager_user):
    token=see .env file
    await client.post(
        "/products/",
        json={
            "sku": "SEARCH-NAME-001",
            "name": "Unique Banana Product",
            "unit_of_measure": "units",
            "unit_price": "1.00",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    response = await client.get(
        "/products/?search=Unique+Banana",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert any("Unique Banana" in p["name"] for p in data)


@pytest.mark.asyncio
async def test_list_products_search_by_sku(client, manager_user):
    token=see .env file
    await create_test_product(client, token, sku="FINDME-SKU-XYZ")
    response = await client.get(
        "/products/?search=FINDME-SKU",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert any("FINDME-SKU-XYZ" in p["sku"] for p in data)


@pytest.mark.asyncio
async def test_barcode_lookup_returns_product(client, manager_user):
    token=see .env file
    await create_test_product(
        client,
        token,
        sku="BARCODE-PROD-001",
        barcode="BC-123456789",
    )
    response = await client.get(
        "/products/barcode-lookup?barcode=BC-123456789",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["barcode"] == "BC-123456789"


@pytest.mark.asyncio
async def test_barcode_lookup_not_found_returns_404(client, manager_user):
    token=see .env file
    response = await client.get(
        "/products/barcode-lookup?barcode=NONEXISTENT-BC",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "BARCODE_NOT_FOUND"


