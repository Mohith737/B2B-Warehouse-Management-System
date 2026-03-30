# /home/mohith/Catchup-Mohith/backend/tests/integration/test_po_lifecycle_api.py
import pytest
from backend.tests.conftest import (
    create_po_via_api,
    create_product,
    create_supplier,
    get_token_for_user,
    transition_po,
)


@pytest.mark.asyncio
async def test_create_po_returns_201_with_po_number(client, manager_user, db_session):
    supplier = await create_supplier(
        db_session, credit_limit="10000.00", is_active=True
    )
    product = await create_product(db_session)

    response = await create_po_via_api(
        client,
        manager_user,
        supplier.id,
        product.id,
        quantity="2.0000",
        unit_price="50.0000",
        notes="PO create",
    )
    assert response.status_code == 201
    assert response.json()["data"]["po_number"].startswith("SB-")


@pytest.mark.asyncio
async def test_create_po_staff_returns_403(client, staff_user, db_session):
    supplier = await create_supplier(
        db_session, credit_limit="10000.00", is_active=True
    )
    product = await create_product(db_session)

    response = await create_po_via_api(client, staff_user, supplier.id, product.id)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_po_inactive_supplier_returns_400(
    client, manager_user, db_session
):
    supplier = await create_supplier(
        db_session, credit_limit="10000.00", is_active=False
    )
    product = await create_product(db_session)

    response = await create_po_via_api(client, manager_user, supplier.id, product.id)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "SUPPLIER_INACTIVE"


@pytest.mark.asyncio
async def test_get_po_returns_200_with_lines(client, manager_user, db_session):
    supplier = await create_supplier(db_session)
    product = await create_product(db_session)
    create_resp = await create_po_via_api(client, manager_user, supplier.id, product.id)
    po_id = create_resp.json()["data"]["id"]

    token=see .env file
    response = await client.get(
        f"/purchase-orders/{po_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert len(response.json()["data"]["lines"]) == 1


@pytest.mark.asyncio
async def test_get_po_not_found_returns_404(client, manager_user):
    token=see .env file
    response = await client.get(
        "/purchase-orders/00000000-0000-0000-0000-000000000000",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_pos_pagination_default_20(client, manager_user):
    token=see .env file
    response = await client.get(
        "/purchase-orders/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["meta"]["page_size"] == 20


@pytest.mark.asyncio
async def test_list_pos_filter_by_status(client, manager_user, db_session):
    supplier = await create_supplier(db_session)
    product = await create_product(db_session)
    created = await create_po_via_api(client, manager_user, supplier.id, product.id)
    po_id = created.json()["data"]["id"]
    await transition_po(client, manager_user, po_id, "submit")

    token=see .env file
    response = await client.get(
        "/purchase-orders/?status=submitted",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert all(item["status"] == "submitted" for item in response.json()["data"])


@pytest.mark.asyncio
async def test_list_pos_filter_by_supplier(client, manager_user, db_session):
    supplier = await create_supplier(db_session)
    product = await create_product(db_session)
    await create_po_via_api(client, manager_user, supplier.id, product.id)

    token=see .env file
    response = await client.get(
        f"/purchase-orders/?supplier_id={supplier.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert all(
        item["supplier_id"] == str(supplier.id) for item in response.json()["data"]
    )


@pytest.mark.asyncio
async def test_staff_sees_only_own_pos(client, manager_user, staff_user, db_session):
    supplier = await create_supplier(db_session)
    product = await create_product(db_session)
    await create_po_via_api(client, manager_user, supplier.id, product.id)

    staff_token=see .env file
    response = await client.get(
        "/purchase-orders/",
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_submit_po_returns_200_submitted_status(client, manager_user, db_session):
    supplier = await create_supplier(db_session)
    product = await create_product(db_session)
    created = await create_po_via_api(client, manager_user, supplier.id, product.id)
    po_id = created.json()["data"]["id"]

    response = await transition_po(client, manager_user, po_id, "submit")
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "submitted"


@pytest.mark.asyncio
async def test_submit_po_sets_submitted_at_timestamp(client, manager_user, db_session):
    supplier = await create_supplier(db_session)
    product = await create_product(db_session)
    created = await create_po_via_api(client, manager_user, supplier.id, product.id)
    po_id = created.json()["data"]["id"]

    response = await transition_po(client, manager_user, po_id, "submit")
    assert response.status_code == 200
    assert response.json()["data"]["submitted_at"] is not None


@pytest.mark.asyncio
async def test_acknowledge_po_returns_200(client, manager_user, db_session):
    supplier = await create_supplier(db_session)
    product = await create_product(db_session)
    created = await create_po_via_api(client, manager_user, supplier.id, product.id)
    po_id = created.json()["data"]["id"]
    await transition_po(client, manager_user, po_id, "submit")

    response = await transition_po(client, manager_user, po_id, "acknowledge")
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "acknowledged"


@pytest.mark.asyncio
async def test_mark_shipped_returns_200(client, manager_user, db_session):
    supplier = await create_supplier(db_session)
    product = await create_product(db_session)
    created = await create_po_via_api(client, manager_user, supplier.id, product.id)
    po_id = created.json()["data"]["id"]
    await transition_po(client, manager_user, po_id, "submit")
    await transition_po(client, manager_user, po_id, "acknowledge")

    response = await transition_po(client, manager_user, po_id, "mark-shipped")
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "shipped"


@pytest.mark.asyncio
async def test_cancel_from_draft_returns_200(client, manager_user, db_session):
    supplier = await create_supplier(db_session)
    product = await create_product(db_session)
    created = await create_po_via_api(client, manager_user, supplier.id, product.id)
    po_id = created.json()["data"]["id"]

    response = await transition_po(client, manager_user, po_id, "cancel")
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "cancelled"


@pytest.mark.asyncio
async def test_cancel_from_acknowledged_returns_400(client, manager_user, db_session):
    supplier = await create_supplier(db_session)
    product = await create_product(db_session)
    created = await create_po_via_api(client, manager_user, supplier.id, product.id)
    po_id = created.json()["data"]["id"]
    await transition_po(client, manager_user, po_id, "submit")
    await transition_po(client, manager_user, po_id, "acknowledge")

    response = await transition_po(client, manager_user, po_id, "cancel")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_STATE_TRANSITION"


@pytest.mark.asyncio
async def test_update_draft_po_returns_200(client, manager_user, db_session):
    supplier = await create_supplier(db_session)
    product = await create_product(db_session)
    created = await create_po_via_api(client, manager_user, supplier.id, product.id)
    po_id = created.json()["data"]["id"]

    token=see .env file
    response = await client.put(
        f"/purchase-orders/{po_id}",
        json={
            "notes": "updated",
            "lines": [
                {
                    "product_id": str(product.id),
                    "quantity_ordered": "5.0000",
                    "unit_price": "10.0000",
                }
            ],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_submitted_po_returns_400(client, manager_user, db_session):
    supplier = await create_supplier(db_session)
    product = await create_product(db_session)
    created = await create_po_via_api(client, manager_user, supplier.id, product.id)
    po_id = created.json()["data"]["id"]
    await transition_po(client, manager_user, po_id, "submit")

    token=see .env file
    response = await client.put(
        f"/purchase-orders/{po_id}",
        json={
            "notes": "updated",
            "lines": [
                {
                    "product_id": str(product.id),
                    "quantity_ordered": "5.0000",
                    "unit_price": "10.0000",
                }
            ],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_delete_draft_po_admin_only(client, admin_user, manager_user, db_session):
    supplier = await create_supplier(db_session)
    product = await create_product(db_session)
    created = await create_po_via_api(client, manager_user, supplier.id, product.id)
    po_id = created.json()["data"]["id"]

    manager_token=see .env file
    admin_token=see .env file

    manager_resp = await client.delete(
        f"/purchase-orders/{po_id}",
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert manager_resp.status_code == 403

    admin_resp = await client.delete(
        f"/purchase-orders/{po_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_resp.status_code == 200


