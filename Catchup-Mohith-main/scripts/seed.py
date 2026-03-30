# scripts/seed.py
import asyncio
import os
import sys
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, TypeVar

from dotenv import load_dotenv
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from backend.app.core.security import hash_password
from backend.app.models.backorder import Backorder, BackorderStatus
from backend.app.models.grn import GRN, GRNStatus
from backend.app.models.grn_line import GRNLine
from backend.app.models.po_line import POLine
from backend.app.models.product import Product
from backend.app.models.purchase_order import POStatus, PurchaseOrder
from backend.app.models.stock_ledger import StockLedger, StockLedgerChangeType
from backend.app.models.supplier import Supplier
from backend.app.models.user import User, UserRole

SEED_NAMESPACE = uuid.UUID("12345678-1234-5678-1234-567812345678")

T = TypeVar("T")


def seed_uuid(name: str) -> uuid.UUID:
    return uuid.uuid5(SEED_NAMESPACE, name)


async def exists_by_id(session: AsyncSession, model: type[T], entity_id: uuid.UUID) -> bool:
    result = await session.execute(select(model).where(model.id == entity_id))
    return result.scalar_one_or_none() is not None


async def create_if_missing(
    session: AsyncSession,
    model: type[T],
    entity_id: uuid.UUID,
    payload: dict[str, Any],
) -> bool:
    if await exists_by_id(session, model, entity_id):
        return False
    session.add(model(id=entity_id, **payload))
    return True


USERS = [
    {
        "key": "user-admin",
        "email": "admin@stockbridge.com",
        "password": "StockAdmin123!",
        "full_name": "StockBridge Admin",
        "role": UserRole.ADMIN,
    },
    {
        "key": "user-manager",
        "email": "manager@stockbridge.com",
        "password": "StockManager123!",
        "full_name": "StockBridge Manager",
        "role": UserRole.PROCUREMENT_MANAGER,
    },
    {
        "key": "user-staff",
        "email": "staff@stockbridge.com",
        "password": "StockStaff123!",
        "full_name": "StockBridge Staff",
        "role": UserRole.WAREHOUSE_STAFF,
    },
]

SUPPLIERS = [
    {
        "key": "supplier-alpha",
        "name": "AlphaSupply Co",
        "email": "alpha@supply.com",
        "tier": "Silver",
        "credit_limit": Decimal("50000.00"),
    },
    {
        "key": "supplier-beta",
        "name": "BetaGoods Ltd",
        "email": "beta@goods.com",
        "tier": "Gold",
        "credit_limit": Decimal("100000.00"),
    },
    {
        "key": "supplier-gamma",
        "name": "GammaTrade Inc",
        "email": "gamma@trade.com",
        "tier": "Diamond",
        "credit_limit": Decimal("200000.00"),
    },
    {
        "key": "supplier-delta",
        "name": "DeltaMart Corp",
        "email": "delta@mart.com",
        "tier": "Silver",
        "credit_limit": Decimal("30000.00"),
    },
    {
        "key": "supplier-epsilon",
        "name": "EpsilonWholesale",
        "email": "eps@wholesale.com",
        "tier": "Gold",
        "credit_limit": Decimal("75000.00"),
    },
]


def product_payload(index: int) -> dict[str, Any]:
    if index <= 7:
        stock = Decimal("120.0000")
        reorder_point = Decimal("50.0000")
    elif index <= 14:
        stock = Decimal("20.0000")
        reorder_point = Decimal("20.0000")
    else:
        stock = Decimal("0.0000")
        reorder_point = Decimal("15.0000")

    return {
        "sku": f"SB-PROD-{index:03d}",
        "name": f"Warehouse Product {index}",
        "description": f"Seeded product {index}",
        "unit_of_measure": "pcs",
        "current_stock": stock,
        "reorder_point": reorder_point,
        "reorder_quantity": Decimal("40.0000"),
        "unit_price": Decimal("12.5000") + Decimal(str(index)),
        "barcode": f"8900000000{index:03d}",
        "version": 1,
    }


PO_DEFS = [
    {
        "key": "po-1",
        "po_number": "SB-PO-0001",
        "supplier_key": "supplier-beta",
        "status": POStatus.ACKNOWLEDGED.value,
        "line_count": 3,
        "created_by": "user-manager",
        "submitted_offset_days": 20,
    },
    {
        "key": "po-2",
        "po_number": "SB-PO-0002",
        "supplier_key": "supplier-gamma",
        "status": POStatus.RECEIVED.value,
        "line_count": 2,
        "created_by": "user-manager",
        "submitted_offset_days": 15,
    },
    {
        "key": "po-3",
        "po_number": "SB-PO-0003",
        "supplier_key": "supplier-alpha",
        "status": POStatus.DRAFT.value,
        "line_count": 2,
        "created_by": "user-manager",
        "submitted_offset_days": 2,
    },
    {
        "key": "po-4",
        "po_number": "SB-PO-0004",
        "supplier_key": "supplier-delta",
        "status": POStatus.SHIPPED.value,
        "line_count": 2,
        "created_by": "user-manager",
        "submitted_offset_days": 5,
    },
    {
        "key": "po-5",
        "po_number": "SB-PO-0005",
        "supplier_key": "supplier-epsilon",
        "status": POStatus.SUBMITTED.value,
        "line_count": 1,
        "created_by": "user-manager",
        "submitted_offset_days": 1,
    },
]


async def seed_users(session: AsyncSession) -> int:
    created = 0
    for entry in USERS:
        user_id = seed_uuid(entry["key"])
        did_create = await create_if_missing(
            session,
            User,
            user_id,
            {
                "email": entry["email"],
                "hashed_password": hash_password(entry["password"]),
                "full_name": entry["full_name"],
                "role": entry["role"],
                "is_active": True,
                "token_version": 0,
            },
        )
        created += int(did_create)
    return created


async def seed_suppliers(session: AsyncSession) -> int:
    created = 0
    for entry in SUPPLIERS:
        supplier_id = seed_uuid(entry["key"])
        did_create = await create_if_missing(
            session,
            Supplier,
            supplier_id,
            {
                "name": entry["name"],
                "email": entry["email"],
                "phone": "+1-555-0100",
                "address": "Seeded supplier address",
                "payment_terms_days": 30,
                "lead_time_days": 7,
                "credit_limit": entry["credit_limit"],
                "current_tier": entry["tier"],
                "tier_locked": False,
                "consecutive_on_time": 0,
                "consecutive_late": 0,
                "is_active": True,
            },
        )
        created += int(did_create)
    return created


async def seed_products(session: AsyncSession) -> int:
    created = 0
    for i in range(1, 21):
        product_id = seed_uuid(f"product-{i}")
        did_create = await create_if_missing(session, Product, product_id, product_payload(i))
        created += int(did_create)
    return created


def po_line_payloads() -> list[dict[str, Any]]:
    return [
        {
            "key": "po-1-line-1",
            "po_key": "po-1",
            "product_key": "product-8",
            "quantity_ordered": Decimal("100.0000"),
            "quantity_received": Decimal("30.0000"),
            "unit_price": Decimal("20.0000"),
        },
        {
            "key": "po-1-line-2",
            "po_key": "po-1",
            "product_key": "product-9",
            "quantity_ordered": Decimal("60.0000"),
            "quantity_received": Decimal("0.0000"),
            "unit_price": Decimal("18.5000"),
        },
        {
            "key": "po-1-line-3",
            "po_key": "po-1",
            "product_key": "product-10",
            "quantity_ordered": Decimal("40.0000"),
            "quantity_received": Decimal("0.0000"),
            "unit_price": Decimal("16.0000"),
        },
        {
            "key": "po-2-line-1",
            "po_key": "po-2",
            "product_key": "product-15",
            "quantity_ordered": Decimal("80.0000"),
            "quantity_received": Decimal("80.0000"),
            "unit_price": Decimal("22.0000"),
        },
        {
            "key": "po-2-line-2",
            "po_key": "po-2",
            "product_key": "product-16",
            "quantity_ordered": Decimal("120.0000"),
            "quantity_received": Decimal("120.0000"),
            "unit_price": Decimal("19.0000"),
        },
        {
            "key": "po-3-line-1",
            "po_key": "po-3",
            "product_key": "product-3",
            "quantity_ordered": Decimal("25.0000"),
            "quantity_received": Decimal("0.0000"),
            "unit_price": Decimal("14.5000"),
        },
        {
            "key": "po-3-line-2",
            "po_key": "po-3",
            "product_key": "product-4",
            "quantity_ordered": Decimal("35.0000"),
            "quantity_received": Decimal("0.0000"),
            "unit_price": Decimal("13.0000"),
        },
        {
            "key": "po-4-line-1",
            "po_key": "po-4",
            "product_key": "product-11",
            "quantity_ordered": Decimal("50.0000"),
            "quantity_received": Decimal("0.0000"),
            "unit_price": Decimal("17.2500"),
        },
        {
            "key": "po-4-line-2",
            "po_key": "po-4",
            "product_key": "product-12",
            "quantity_ordered": Decimal("75.0000"),
            "quantity_received": Decimal("0.0000"),
            "unit_price": Decimal("21.0000"),
        },
        {
            "key": "po-5-line-1",
            "po_key": "po-5",
            "product_key": "product-5",
            "quantity_ordered": Decimal("20.0000"),
            "quantity_received": Decimal("0.0000"),
            "unit_price": Decimal("11.0000"),
        },
    ]


async def seed_purchase_orders(session: AsyncSession) -> tuple[int, int]:
    pos_created = 0
    lines_created = 0
    now = datetime.now(UTC)

    for entry in PO_DEFS:
        po_id = seed_uuid(entry["key"])
        supplier_id = seed_uuid(entry["supplier_key"])
        created_by = seed_uuid(entry["created_by"])

        line_payloads = [line for line in po_line_payloads() if line["po_key"] == entry["key"]]
        total_amount = sum(
            (line["quantity_ordered"] * line["unit_price"] for line in line_payloads),
            Decimal("0.0000"),
        )

        submitted_at = now - timedelta(days=entry["submitted_offset_days"])
        acknowledged_at = submitted_at + timedelta(days=2) if entry["status"] in {
            POStatus.ACKNOWLEDGED.value,
            POStatus.SHIPPED.value,
            POStatus.RECEIVED.value,
            POStatus.CLOSED.value,
        } else None
        shipped_at = submitted_at + timedelta(days=5) if entry["status"] in {
            POStatus.SHIPPED.value,
            POStatus.RECEIVED.value,
            POStatus.CLOSED.value,
        } else None
        received_at = submitted_at + timedelta(days=8) if entry["status"] in {
            POStatus.RECEIVED.value,
            POStatus.CLOSED.value,
        } else None

        did_create = await create_if_missing(
            session,
            PurchaseOrder,
            po_id,
            {
                "po_number": entry["po_number"],
                "supplier_id": supplier_id,
                "created_by": created_by,
                "status": entry["status"],
                "total_amount": total_amount.quantize(Decimal("0.01")),
                "notes": f"Seeded purchase order {entry['po_number']}",
                "auto_generated": False,
                "submitted_at": submitted_at if entry["status"] != POStatus.DRAFT.value else None,
                "acknowledged_at": acknowledged_at,
                "shipped_at": shipped_at,
                "received_at": received_at,
            },
        )
        pos_created += int(did_create)

    for line in po_line_payloads():
        line_id = seed_uuid(line["key"])
        qty_ordered = line["quantity_ordered"]
        unit_price = line["unit_price"]
        did_create = await create_if_missing(
            session,
            POLine,
            line_id,
            {
                "po_id": seed_uuid(line["po_key"]),
                "product_id": seed_uuid(line["product_key"]),
                "quantity_ordered": qty_ordered,
                "quantity_received": line["quantity_received"],
                "unit_price": unit_price,
                "line_total": (qty_ordered * unit_price).quantize(Decimal("0.0001")),
            },
        )
        lines_created += int(did_create)

    return pos_created, lines_created


async def seed_grns(session: AsyncSession) -> tuple[int, int, int]:
    grns_created = 0
    lines_created = 0
    ledger_created = 0
    now = datetime.now(UTC)

    grn_defs = [
        {
            "key": "grn-1",
            "po_key": "po-1",
            "status": GRNStatus.OPEN.value,
            "created_by": "user-staff",
            "completed_at": None,
        },
        {
            "key": "grn-2",
            "po_key": "po-2",
            "status": GRNStatus.COMPLETED.value,
            "created_by": "user-staff",
            "completed_at": now - timedelta(days=6),
        },
    ]

    for entry in grn_defs:
        did_create = await create_if_missing(
            session,
            GRN,
            seed_uuid(entry["key"]),
            {
                "po_id": seed_uuid(entry["po_key"]),
                "status": entry["status"],
                "created_by": seed_uuid(entry["created_by"]),
                "completed_at": entry["completed_at"],
                "auto_reorder_triggered": False,
            },
        )
        grns_created += int(did_create)

    grn_line_defs = [
        {
            "key": "grn-1-line-1",
            "grn_key": "grn-1",
            "product_key": "product-8",
            "qty": Decimal("30.0000"),
            "unit_cost": Decimal("20.0000"),
            "barcode": "8900000000008",
            "created_at": now - timedelta(days=4),
        },
        {
            "key": "grn-2-line-1",
            "grn_key": "grn-2",
            "product_key": "product-15",
            "qty": Decimal("80.0000"),
            "unit_cost": Decimal("22.0000"),
            "barcode": "8900000000015",
            "created_at": now - timedelta(days=6),
        },
        {
            "key": "grn-2-line-2",
            "grn_key": "grn-2",
            "product_key": "product-16",
            "qty": Decimal("120.0000"),
            "unit_cost": Decimal("19.0000"),
            "barcode": "8900000000016",
            "created_at": now - timedelta(days=6),
        },
    ]

    for entry in grn_line_defs:
        did_create = await create_if_missing(
            session,
            GRNLine,
            seed_uuid(entry["key"]),
            {
                "grn_id": seed_uuid(entry["grn_key"]),
                "product_id": seed_uuid(entry["product_key"]),
                "quantity_received": entry["qty"],
                "unit_cost": entry["unit_cost"],
                "barcode_scanned": entry["barcode"],
                "created_at": entry["created_at"],
                "updated_at": entry["created_at"],
            },
        )
        lines_created += int(did_create)

    ledger_entries = [
        {
            "key": "ledger-grn-2-line-1",
            "product_key": "product-15",
            "qty": Decimal("80.0000"),
            "balance_after": Decimal("80.0000"),
            "reference": "grn-2-line-1",
            "created_at": now - timedelta(days=6),
        },
        {
            "key": "ledger-grn-2-line-2",
            "product_key": "product-16",
            "qty": Decimal("120.0000"),
            "balance_after": Decimal("120.0000"),
            "reference": "grn-2-line-2",
            "created_at": now - timedelta(days=6),
        },
    ]

    for entry in ledger_entries:
        did_create = await create_if_missing(
            session,
            StockLedger,
            seed_uuid(entry["key"]),
            {
                "product_id": seed_uuid(entry["product_key"]),
                "quantity_change": entry["qty"],
                "change_type": StockLedgerChangeType.GRN_RECEIPT.value,
                "reference_id": seed_uuid(entry["reference"]),
                "notes": "Seeded ledger entry from completed GRN",
                "balance_after": entry["balance_after"],
                "created_at": entry["created_at"],
            },
        )
        ledger_created += int(did_create)

    return grns_created, lines_created, ledger_created


async def seed_backorders(session: AsyncSession) -> int:
    created = 0
    backorder_defs = [
        {
            "key": "backorder-1",
            "original_po_key": "po-1",
            "product_key": "product-9",
            "quantity_ordered": Decimal("60.0000"),
            "quantity_received": Decimal("0.0000"),
            "quantity_outstanding": Decimal("60.0000"),
            "status": BackorderStatus.OPEN.value,
            "grn_key": "grn-1",
        },
        {
            "key": "backorder-2",
            "original_po_key": "po-1",
            "product_key": "product-10",
            "quantity_ordered": Decimal("40.0000"),
            "quantity_received": Decimal("0.0000"),
            "quantity_outstanding": Decimal("40.0000"),
            "status": BackorderStatus.CLOSED.value,
            "grn_key": "grn-1",
        },
    ]

    for entry in backorder_defs:
        did_create = await create_if_missing(
            session,
            Backorder,
            seed_uuid(entry["key"]),
            {
                "original_po_id": seed_uuid(entry["original_po_key"]),
                "product_id": seed_uuid(entry["product_key"]),
                "quantity_ordered": entry["quantity_ordered"],
                "quantity_received": entry["quantity_received"],
                "quantity_outstanding": entry["quantity_outstanding"],
                "status": entry["status"],
                "grn_id": seed_uuid(entry["grn_key"]),
            },
        )
        created += int(did_create)

    return created


async def seed() -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is required")

    engine = create_async_engine(database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        # Ensure enum-backed custom types exist even if migrations were generated
        # against varchar/check-constraint schema in some environments.
        async with engine.begin() as conn:
            await conn.run_sync(
                lambda sync_conn: User.__table__.c.role.type.create(
                    sync_conn,
                    checkfirst=True,
                )
            )
            # Some historical schemas keep a stale lowercase role check
            # constraint while the enum labels are uppercase.
            await conn.execute(text("ALTER TABLE users DROP CONSTRAINT IF EXISTS ck_users_role"))

        async with session_factory() as session:
            users_created = await seed_users(session)
            suppliers_created = await seed_suppliers(session)
            products_created = await seed_products(session)
            pos_created, po_lines_created = await seed_purchase_orders(session)
            grns_created, grn_lines_created, ledger_created = await seed_grns(session)
            backorders_created = await seed_backorders(session)
            await session.commit()

        print("Seed completed successfully")
        print(f"users created: {users_created}")
        print(f"suppliers created: {suppliers_created}")
        print(f"products created: {products_created}")
        print(f"purchase orders created: {pos_created}")
        print(f"po lines created: {po_lines_created}")
        print(f"grns created: {grns_created}")
        print(f"grn lines created: {grn_lines_created}")
        print(f"stock ledger entries created: {ledger_created}")
        print(f"backorders created: {backorders_created}")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
