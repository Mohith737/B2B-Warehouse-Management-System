# /home/mohith/Catchup-Mohith/backend/tests/conftest.py
import asyncio
import os
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
import pytest_asyncio
from alembic.config import Config
from backend.app.cache.service import CacheService, cache_service
from backend.app.core.dependencies import get_cache
from backend.app.core.security import hash_password
from backend.app.db.base import Base
from backend.app.db.session import get_db
from backend.app.main import app
from backend.app.models.product import Product
from backend.app.models.supplier import Supplier
from backend.app.models.user import User, UserRole
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from alembic import command

TEST_DATABASE_URL=REDACTED_SEE_ENV
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://stockbridge:stockbridge@localhost:5432/stockbridge_test",
)


@pytest.fixture(scope="session")
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=None,
    )

    def run_migrations():
        alembic_cfg = Config("backend/alembic.ini")
        alembic_cfg.set_main_option(
            "sqlalchemy.url",
            TEST_DATABASE_URL.replace("postgresql+asyncpg", "postgresql+psycopg2"),
        )
        command.upgrade(alembic_cfg, "head")

    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor() as pool:
        await asyncio.get_event_loop().run_in_executor(pool, run_migrations)

    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine):
    # Create all tables fresh for this test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Provide a clean session — rollback after test
    async with AsyncSession(test_engine) as session:
        yield session
        await session.rollback()

    # Drop all tables after test to ensure isolation
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_cache] = lambda: cache_service
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_user(db_session) -> User:
    user = User(
        email="admin@test.com",
        hashed_password=see .env file
        full_name="Test Admin",
        role=UserRole.ADMIN,
        is_active=True,
        token_version=see .env file
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def manager_user(db_session) -> User:
    user = User(
        email="manager@test.com",
        hashed_password=see .env file
        full_name="Test Manager",
        role=UserRole.PROCUREMENT_MANAGER,
        is_active=True,
        token_version=see .env file
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def staff_user(db_session) -> User:
    user = User(
        email="staff@test.com",
        hashed_password=see .env file
        full_name="Test Staff",
        role=UserRole.WAREHOUSE_STAFF,
        is_active=True,
        token_version=see .env file
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def inactive_user(db_session) -> User:
    user = User(
        email="inactive@test.com",
        hashed_password=see .env file
        full_name="Inactive User",
        role=UserRole.WAREHOUSE_STAFF,
        is_active=False,
        token_version=see .env file
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_token(client, admin_user) -> str:
    response = await client.post(
        "/auth/login",
        json={
            "email": "admin@test.com",
            "password": "see .env file",
        },
    )
    assert response.status_code == 200
    return response.json()["data"]["access_token"]


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


async def get_token_for_user(client: AsyncClient, user: User) -> str:
    password_map=see .env file
        "admin@test.com": "AdminPass123!",
        "manager@test.com": "ManagerPass123!",
        "staff@test.com": "StaffPass123!",
        "inactive@test.com": "InactivePass123!",
    }
    password=see .env file
    if password is None:
        raise RuntimeError(
            "No test password configured for user " f"email={user.email}"
        )

    response = await client.post(
        "/auth/login",
        json={"email": user.email, "password": password},
    )
    if response.status_code != 200:
        raise RuntimeError(
            "Failed login for test user "
            f"{user.email}: {response.status_code} "
            f"{response.text}"
        )
    token=see .env file
    setattr(user, "_access_token", token)
    return token


def auth_headers(user: User) -> dict[str, str]:
    token=see .env file
    if not token:
        raise RuntimeError(
            "User has no cached access token. Call get_token_for_user() first."
        )
    return {"Authorization": f"Bearer {token}"}


async def create_supplier(
    db: AsyncSession,
    credit_limit: str | Decimal = "10000.00",
    is_active: bool = True,
) -> Supplier:
    supplier = Supplier(
        name=f"Supplier {uuid4()}",
        email=f"supplier-{uuid4()}@example.com",
        phone=None,
        address=None,
        payment_terms_days=30,
        lead_time_days=7,
        credit_limit=Decimal(str(credit_limit)),
        current_tier="Silver",
        tier_locked=False,
        consecutive_on_time=0,
        consecutive_late=0,
        is_active=is_active,
    )
    db.add(supplier)
    await db.flush()
    await db.refresh(supplier)
    return supplier


async def create_product(db: AsyncSession) -> Product:
    product = Product(
        sku=f"SKU-{uuid4()}",
        name="Test Product",
        description=None,
        unit_of_measure="units",
        current_stock=Decimal("0"),
        reorder_point=Decimal("5"),
        reorder_quantity=Decimal("20"),
        unit_price=Decimal("10.0000"),
        barcode=None,
        low_stock_threshold_override=None,
        version=1,
    )
    db.add(product)
    await db.flush()
    await db.refresh(product)
    return product


async def create_po_via_api(
    client: AsyncClient,
    user: User,
    supplier_id,
    product_id,
    quantity: str = "2.0000",
    unit_price: str = "10.0000",
    notes: str = "Test PO",
):
    if not getattr(user, "_access_token", None):
        await get_token_for_user(client, user)
    return await client.post(
        "/purchase-orders/",
        json={
            "supplier_id": str(supplier_id),
            "notes": notes,
            "lines": [
                {
                    "product_id": str(product_id),
                    "quantity_ordered": quantity,
                    "unit_price": unit_price,
                }
            ],
        },
        headers=auth_headers(user),
    )


async def transition_po(client: AsyncClient, user: User, po_id, action: str):
    if not getattr(user, "_access_token", None):
        await get_token_for_user(client, user)

    action_map = {
        "submit": f"/purchase-orders/{po_id}/submit",
        "acknowledge": f"/purchase-orders/{po_id}/acknowledge",
        "mark-shipped": f"/purchase-orders/{po_id}/mark-shipped",
        "cancel": f"/purchase-orders/{po_id}/cancel",
    }
    path = action_map.get(action)
    if path is None:
        raise RuntimeError(f"Unknown PO transition action: {action}")

    return await client.post(path, headers=auth_headers(user))


