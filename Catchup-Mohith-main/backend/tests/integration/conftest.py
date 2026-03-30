# backend/tests/integration/conftest.py
import os
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
import pytest_asyncio
from backend.app.cache.service import CacheService
from backend.app.core import security as security_module
from backend.app.core.dependencies import get_cache, get_current_user, oauth2_scheme
from backend.app.core.exceptions import (
    AccountInactiveException,
    AuthenticationRequiredException,
    SessionInvalidatedException,
)
from backend.app.core.security import decode_token
from backend.app.core.security import hash_password
from backend.app.db.base import Base
from backend.app.db.session import get_db
from backend.app.main import app
from backend.app.models.po_line import POLine
from backend.app.models.product import Product
from backend.app.models.purchase_order import POStatus, PurchaseOrder
from backend.app.models.supplier import Supplier
from backend.app.models.user import User, UserRole
from fastapi import Depends
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://stockbridge:stockbridge@localhost:5432/stockbridge_test",
)


@pytest_asyncio.fixture
async def engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, pool_pre_ping=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def session(engine):
    async with engine.connect() as connection:
        transaction = await connection.begin()
        test_session = AsyncSession(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        try:
            yield test_session
        finally:
            await test_session.close()
            await transaction.rollback()


@pytest.fixture
def mock_cache() -> MagicMock:
    mock = MagicMock(spec=CacheService)
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=True)
    mock.increment = AsyncMock(return_value=1)
    mock.acquire_lock = AsyncMock(return_value=True)
    mock.release_lock = AsyncMock(return_value=True)
    mock.delete_pattern = AsyncMock(return_value=0)
    return mock


@pytest_asyncio.fixture
async def client(
    session: AsyncSession,
    mock_cache: MagicMock,
    seeded_users: dict[str, User],
    monkeypatch: pytest.MonkeyPatch,
):
    users_by_id = {str(user.id): user for user in seeded_users.values()}

    async def override_get_db():
        yield session

    async def override_get_current_user(
        token: str = Depends(oauth2_scheme),
    ) -> User:
        payload = decode_token(token)
        if payload.type != "access":
            raise AuthenticationRequiredException(
                details={"reason": "not an access token"}
            )
        user = users_by_id.get(payload.sub)
        if user is None or not user.is_active:
            raise AccountInactiveException()
        if user.token_version != payload.version:
            raise SessionInvalidatedException()
        return user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_cache] = lambda: mock_cache
    app.dependency_overrides[get_current_user] = override_get_current_user
    monkeypatch.setattr(security_module, "cache_service", mock_cache)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def seeded_users(session: AsyncSession) -> dict[str, User]:
    admin = User(
        id=uuid4(),
        email="admin@stockbridge.com",
        hashed_password=hash_password("StockAdmin123!"),
        full_name="Admin User",
        role=UserRole.ADMIN,
        is_active=True,
        token_version=0,
    )
    manager = User(
        id=uuid4(),
        email="manager@stockbridge.com",
        hashed_password=hash_password("StockManager123!"),
        full_name="Manager User",
        role=UserRole.PROCUREMENT_MANAGER,
        is_active=True,
        token_version=0,
    )
    staff = User(
        id=uuid4(),
        email="staff@stockbridge.com",
        hashed_password=hash_password("StockStaff123!"),
        full_name="Staff User",
        role=UserRole.WAREHOUSE_STAFF,
        is_active=True,
        token_version=0,
    )
    session.add_all([admin, manager, staff])
    await session.flush()
    return {"admin": admin, "manager": manager, "staff": staff}


async def _login(client: AsyncClient, email: str, password: str) -> str:
    response = await client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return response.json()["data"]["access_token"]


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient, seeded_users: dict[str, User]) -> str:
    return await _login(client, "admin@stockbridge.com", "StockAdmin123!")


@pytest_asyncio.fixture
async def manager_token(client: AsyncClient, seeded_users: dict[str, User]) -> str:
    return await _login(client, "manager@stockbridge.com", "StockManager123!")


@pytest_asyncio.fixture
async def staff_token(client: AsyncClient, seeded_users: dict[str, User]) -> str:
    return await _login(client, "staff@stockbridge.com", "StockStaff123!")


@pytest_asyncio.fixture
async def seeded_supplier(session: AsyncSession) -> Supplier:
    supplier = Supplier(
        id=uuid4(),
        name="Seed Supplier",
        email=f"seed-supplier-{uuid4()}@example.com",
        phone="+1-555-1111",
        address="Seed Street",
        payment_terms_days=30,
        lead_time_days=7,
        credit_limit=Decimal("100000.00"),
        current_tier="Gold",
        tier_locked=False,
        consecutive_on_time=0,
        consecutive_late=0,
        is_active=True,
    )
    session.add(supplier)
    await session.flush()
    return supplier


@pytest_asyncio.fixture
async def seeded_product(session: AsyncSession) -> Product:
    product = Product(
        id=uuid4(),
        sku=f"SEED-SKU-{uuid4().hex[:8]}",
        name="Seed Product",
        description="Integration seeded product",
        unit_of_measure="pcs",
        current_stock=Decimal("0.0000"),
        reorder_point=Decimal("10.0000"),
        reorder_quantity=Decimal("20.0000"),
        unit_price=Decimal("25.0000"),
        barcode=f"89{uuid4().int % 10**10:010d}",
        low_stock_threshold_override=None,
        version=1,
    )
    session.add(product)
    await session.flush()
    return product


@pytest_asyncio.fixture
async def seeded_po(
    session: AsyncSession,
    seeded_users: dict[str, User],
    seeded_supplier: Supplier,
    seeded_product: Product,
) -> PurchaseOrder:
    po = PurchaseOrder(
        id=uuid4(),
        po_number=f"SB-IT-{uuid4().hex[:8].upper()}",
        supplier_id=seeded_supplier.id,
        created_by=seeded_users["manager"].id,
        status=POStatus.SHIPPED.value,
        total_amount=Decimal("100.00"),
        notes="Integration seeded PO",
        auto_generated=False,
        submitted_at=datetime.now(UTC),
        acknowledged_at=datetime.now(UTC),
        shipped_at=datetime.now(UTC),
    )
    session.add(po)
    await session.flush()

    po_line = POLine(
        id=uuid4(),
        po_id=po.id,
        product_id=seeded_product.id,
        quantity_ordered=Decimal("5.0000"),
        quantity_received=Decimal("0.0000"),
        unit_price=Decimal("20.0000"),
        line_total=Decimal("100.0000"),
    )
    session.add(po_line)
    await session.flush()
    return po


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def random_uuid() -> str:
    return str(uuid4())
