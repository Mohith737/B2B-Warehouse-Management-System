# /home/mohith/Catchup-Mohith/backend/tests/integration/test_po_credit_limit.py
from decimal import Decimal

import pytest
from backend.tests.conftest import (
    create_po_via_api,
    create_product,
    create_supplier,
    transition_po,
)


@pytest.mark.asyncio
async def test_submit_within_limit_succeeds(client, manager_user, db_session):
    supplier = await create_supplier(db_session, credit_limit="100.00")
    product = await create_product(db_session)
    created = await create_po_via_api(
        client,
        manager_user,
        supplier.id,
        product.id,
        quantity="2.0000",
        unit_price="20.0000",
    )

    response = await transition_po(
        client, manager_user, created.json()["data"]["id"], "submit"
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_submit_exactly_at_limit_succeeds(client, manager_user, db_session):
    supplier = await create_supplier(db_session, credit_limit="40.00")
    product = await create_product(db_session)
    created = await create_po_via_api(
        client,
        manager_user,
        supplier.id,
        product.id,
        quantity="2.0000",
        unit_price="20.0000",
    )

    response = await transition_po(
        client, manager_user, created.json()["data"]["id"], "submit"
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_submit_one_cent_over_limit_fails(client, manager_user, db_session):
    supplier = await create_supplier(db_session, credit_limit="39.99")
    product = await create_product(db_session)
    created = await create_po_via_api(
        client,
        manager_user,
        supplier.id,
        product.id,
        quantity="2.0000",
        unit_price="20.0000",
    )

    response = await transition_po(
        client, manager_user, created.json()["data"]["id"], "submit"
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "CREDIT_LIMIT_EXCEEDED"


@pytest.mark.asyncio
async def test_credit_check_includes_all_open_pos(client, manager_user, db_session):
    supplier = await create_supplier(db_session, credit_limit="60.00")
    product = await create_product(db_session)

    po1 = await create_po_via_api(
        client, manager_user, supplier.id, product.id, quantity="2", unit_price="20"
    )
    po2 = await create_po_via_api(
        client, manager_user, supplier.id, product.id, quantity="2", unit_price="20"
    )

    await transition_po(client, manager_user, po1.json()["data"]["id"], "submit")
    response = await transition_po(
        client, manager_user, po2.json()["data"]["id"], "submit"
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_credit_check_excludes_received_pos(client, manager_user, db_session):
    supplier = await create_supplier(db_session, credit_limit="40.00")
    product = await create_product(db_session)

    created = await create_po_via_api(
        client, manager_user, supplier.id, product.id, quantity="2", unit_price="20"
    )
    response = await transition_po(
        client, manager_user, created.json()["data"]["id"], "submit"
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_credit_check_excludes_closed_pos(client, manager_user, db_session):
    supplier = await create_supplier(db_session, credit_limit="40.00")
    product = await create_product(db_session)

    created = await create_po_via_api(
        client, manager_user, supplier.id, product.id, quantity="2", unit_price="20"
    )
    response = await transition_po(
        client, manager_user, created.json()["data"]["id"], "submit"
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_credit_check_excludes_cancelled_pos(client, manager_user, db_session):
    supplier = await create_supplier(db_session, credit_limit="40.00")
    product = await create_product(db_session)

    created = await create_po_via_api(
        client, manager_user, supplier.id, product.id, quantity="2", unit_price="20"
    )
    await transition_po(client, manager_user, created.json()["data"]["id"], "cancel")

    created2 = await create_po_via_api(
        client, manager_user, supplier.id, product.id, quantity="2", unit_price="20"
    )
    response = await transition_po(
        client, manager_user, created2.json()["data"]["id"], "submit"
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_error_details_contain_gap_amount(client, manager_user, db_session):
    supplier = await create_supplier(db_session, credit_limit="10.00")
    product = await create_product(db_session)
    created = await create_po_via_api(
        client,
        manager_user,
        supplier.id,
        product.id,
        quantity="2.0000",
        unit_price="20.0000",
    )

    response = await transition_po(
        client, manager_user, created.json()["data"]["id"], "submit"
    )
    assert response.status_code == 400
    details = response.json()["error"]["details"]
    assert "gap" in details
    assert Decimal(details["gap"]) > Decimal("0")
