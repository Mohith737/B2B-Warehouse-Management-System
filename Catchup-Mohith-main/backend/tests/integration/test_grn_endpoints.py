# /home/mohith/Catchup-Mohith/backend/tests/integration/test_grn_endpoints.py
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.backorder import Backorder
from backend.app.models.po_line import POLine
from backend.app.models.product import Product
from backend.app.models.purchase_order import POStatus, PurchaseOrder
from backend.app.models.supplier import Supplier
from backend.app.models.user import User


async def _login_manager(client: AsyncClient) -> str:
    response = await client.post(
        "/auth/login",
        json={"email": "manager@test.com", "password": "ManagerPass123!"},
    )
    assert response.status_code == 200
    return response.json()["data"]["access_token"]


async def _create_supplier(db: AsyncSession) -> Supplier:
    supplier = Supplier(
        name=f"Supplier-{uuid4()}",
        email=f"supplier-{uuid4()}@example.com",
        payment_terms_days=30,
        lead_time_days=7,
        credit_limit=Decimal("10000.00"),
        current_tier="Silver",
        tier_locked=False,
        consecutive_on_time=0,
        consecutive_late=0,
        is_active=True,
    )
    db.add(supplier)
    await db.flush()
    await db.refresh(supplier)
    return supplier


async def _create_product(
    db: AsyncSession,
    barcode: str | None = None,
    stock: str = "0.0000",
) -> Product:
    product = Product(
        sku=f"SKU-{uuid4()}",
        name="GRN Test Product",
        unit_of_measure="units",
        current_stock=Decimal(stock),
        reorder_point=Decimal("5.0000"),
        reorder_quantity=Decimal("10.0000"),
        unit_price=Decimal("12.0000"),
        barcode=barcode,
        low_stock_threshold_override=None,
        version=1,
    )
    db.add(product)
    await db.flush()
    await db.refresh(product)
    return product


async def _create_po_with_line(
    db: AsyncSession,
    user: User,
    supplier: Supplier,
    product: Product,
    po_status: POStatus = POStatus.SHIPPED,
    qty: str = "10.0000",
) -> tuple[PurchaseOrder, POLine]:
    now = datetime.now(timezone.utc)
    po = PurchaseOrder(
        po_number=f"SB-GRN-{uuid4()}",
        supplier_id=supplier.id,
        created_by=user.id,
        status=po_status.value,
        total_amount=Decimal("120.00"),
        notes="GRN integration test",
        shipped_at=now if po_status == POStatus.SHIPPED else None,
    )
    db.add(po)
    await db.flush()

    line = POLine(
        po_id=po.id,
        product_id=product.id,
        quantity_ordered=Decimal(qty),
        quantity_received=Decimal("0.0000"),
        unit_price=Decimal("12.0000"),
        line_total=Decimal("120.0000"),
    )
    db.add(line)
    await db.flush()
    await db.refresh(po)
    await db.refresh(line)
    return po, line


@pytest.mark.asyncio
async def test_create_grn_returns_201(client, db_session, manager_user):
    supplier = await _create_supplier(db_session)
    product = await _create_product(db_session)
    po, _ = await _create_po_with_line(db_session, manager_user, supplier, product)
    token=see .env file

    response = await client.post(
        "/grns/",
        json={"po_id": str(po.id)},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    assert response.json()["data"]["po_id"] == str(po.id)
    assert response.json()["data"]["status"] == "open"


@pytest.mark.asyncio
async def test_create_grn_against_draft_po_returns_400(
    client, db_session, manager_user
):
    supplier = await _create_supplier(db_session)
    product = await _create_product(db_session)
    po, _ = await _create_po_with_line(
        db_session,
        manager_user,
        supplier,
        product,
        po_status=POStatus.DRAFT,
    )
    token=see .env file

    response = await client.post(
        "/grns/",
        json={"po_id": str(po.id)},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_STATE_TRANSITION"


@pytest.mark.asyncio
async def test_add_grn_line_over_receipt_returns_400(client, db_session, manager_user):
    supplier = await _create_supplier(db_session)
    product = await _create_product(db_session)
    po, _ = await _create_po_with_line(
        db_session, manager_user, supplier, product, qty="2.0000"
    )
    token=see .env file

    create_response = await client.post(
        "/grns/",
        json={"po_id": str(po.id)},
        headers={"Authorization": f"Bearer {token}"},
    )
    grn_id = create_response.json()["data"]["id"]

    add_line = await client.post(
        f"/grns/{grn_id}/lines",
        json={
            "product_id": str(product.id),
            "quantity_received": "3.0000",
            "unit_cost": "12.0000",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert add_line.status_code == 400
    assert add_line.json()["error"]["code"] == "OVER_RECEIPT"


@pytest.mark.asyncio
async def test_add_grn_line_barcode_mismatch_returns_400(
    client, db_session, manager_user
):
    supplier = await _create_supplier(db_session)
    expected_product = await _create_product(db_session)
    scanned_product = await _create_product(db_session, barcode="BARCODE-MISMATCH-1")
    po, _ = await _create_po_with_line(
        db_session,
        manager_user,
        supplier,
        expected_product,
    )
    token=see .env file

    create_response = await client.post(
        "/grns/",
        json={"po_id": str(po.id)},
        headers={"Authorization": f"Bearer {token}"},
    )
    grn_id = create_response.json()["data"]["id"]

    add_line = await client.post(
        f"/grns/{grn_id}/lines",
        json={
            "product_id": str(expected_product.id),
            "quantity_received": "1.0000",
            "unit_cost": "12.0000",
            "barcode_scanned": scanned_product.barcode,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert add_line.status_code == 400
    assert add_line.json()["error"]["code"] == "BARCODE_MISMATCH"


@pytest.mark.asyncio
async def test_complete_grn_partial_creates_backorder(client, db_session, manager_user):
    supplier = await _create_supplier(db_session)
    product = await _create_product(db_session, stock="4.0000")
    po, _ = await _create_po_with_line(
        db_session, manager_user, supplier, product, qty="10.0000"
    )
    token=see .env file

    create_response = await client.post(
        "/grns/",
        json={"po_id": str(po.id)},
        headers={"Authorization": f"Bearer {token}"},
    )
    grn_id = create_response.json()["data"]["id"]

    add_line = await client.post(
        f"/grns/{grn_id}/lines",
        json={
            "product_id": str(product.id),
            "quantity_received": "4.0000",
            "unit_cost": "12.0000",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert add_line.status_code == 201

    complete = await client.post(
        f"/grns/{grn_id}/complete",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert complete.status_code == 200
    assert complete.json()["data"]["status"] == "completed"
    assert complete.json()["data"]["auto_reorder_triggered"] is True

    backorder_result = await db_session.execute(
        select(Backorder).where(Backorder.original_po_id == po.id)
    )
    backorders = list(backorder_result.scalars().all())
    assert len(backorders) == 1
    assert backorders[0].quantity_outstanding == Decimal("6.0000")


