# /home/mohith/Catchup-Mohith/backend/tests/integration/test_stock_ledger.py
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.product import Product
from backend.app.models.stock_ledger import StockLedger


async def _login_manager(client: AsyncClient) -> str:
    response = await client.post(
        "/auth/login",
        json={"email": "manager@test.com", "password": "ManagerPass123!"},
    )
    assert response.status_code == 200
    return response.json()["data"]["access_token"]


async def _create_product(db: AsyncSession, name: str = "Ledger Product") -> Product:
    product = Product(
        sku=f"LEDGER-SKU-{uuid4()}",
        name=name,
        unit_of_measure="units",
        current_stock=Decimal("0.0000"),
        reorder_point=Decimal("5.0000"),
        reorder_quantity=Decimal("10.0000"),
        unit_price=Decimal("10.0000"),
        barcode=None,
        low_stock_threshold_override=None,
        version=1,
    )
    db.add(product)
    await db.flush()
    await db.refresh(product)
    return product


async def _insert_ledger_entry(
    db: AsyncSession,
    *,
    id: UUID,
    product_id: UUID,
    quantity_change: str,
    change_type: str = "grn_receipt",
    balance_after: str = "0.0000",
) -> StockLedger:
    entry = StockLedger(
        id=id,
        product_id=product_id,
        quantity_change=Decimal(quantity_change),
        change_type=change_type,
        reference_id=None,
        notes="integration-test",
        balance_after=Decimal(balance_after),
        created_at=datetime.now(timezone.utc),
    )
    db.add(entry)
    await db.flush()
    await db.refresh(entry)
    return entry


@pytest.mark.asyncio
async def test_stock_ledger_list_default_limit_and_meta(
    client, db_session, manager_user
):
    product = await _create_product(db_session)
    await _insert_ledger_entry(
        db_session,
        id=UUID("00000000-0000-0000-0000-000000000001"),
        product_id=product.id,
        quantity_change="2.0000",
        balance_after="2.0000",
    )
    token = await _login_manager(client)

    response = await client.get(
        "/stock-ledger/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["data"]) == 1
    assert body["meta"]["limit"] == 20
    assert body["meta"]["next_cursor"] is None


@pytest.mark.asyncio
async def test_stock_ledger_cursor_pagination(client, db_session, manager_user):
    product = await _create_product(db_session)
    id1 = UUID("00000000-0000-0000-0000-000000000010")
    id2 = UUID("00000000-0000-0000-0000-000000000020")
    id3 = UUID("00000000-0000-0000-0000-000000000030")
    await _insert_ledger_entry(
        db_session,
        id=id1,
        product_id=product.id,
        quantity_change="1.0000",
        balance_after="1.0000",
    )
    await _insert_ledger_entry(
        db_session,
        id=id2,
        product_id=product.id,
        quantity_change="1.0000",
        balance_after="2.0000",
    )
    await _insert_ledger_entry(
        db_session,
        id=id3,
        product_id=product.id,
        quantity_change="1.0000",
        balance_after="3.0000",
    )
    token = await _login_manager(client)

    first = await client.get(
        "/stock-ledger/?limit=2",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert first.status_code == 200
    first_body = first.json()
    assert len(first_body["data"]) == 2
    assert first_body["meta"]["next_cursor"] == str(id2)

    second = await client.get(
        f"/stock-ledger/?limit=2&cursor={first_body['meta']['next_cursor']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert second.status_code == 200
    second_body = second.json()
    assert len(second_body["data"]) == 1
    assert second_body["data"][0]["id"] == str(id3)
    assert second_body["meta"]["next_cursor"] is None


@pytest.mark.asyncio
async def test_stock_ledger_filter_by_product_id(client, db_session, manager_user):
    product_a = await _create_product(db_session, name="Product A")
    product_b = await _create_product(db_session, name="Product B")
    await _insert_ledger_entry(
        db_session,
        id=UUID("00000000-0000-0000-0000-000000000101"),
        product_id=product_a.id,
        quantity_change="2.0000",
        balance_after="2.0000",
    )
    await _insert_ledger_entry(
        db_session,
        id=UUID("00000000-0000-0000-0000-000000000102"),
        product_id=product_b.id,
        quantity_change="3.0000",
        balance_after="3.0000",
    )
    token = await _login_manager(client)

    response = await client.get(
        f"/stock-ledger/?product_id={product_a.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["data"]) == 1
    assert body["data"][0]["product_id"] == str(product_a.id)

    check = await db_session.execute(select(StockLedger))
    assert len(list(check.scalars().all())) == 2
