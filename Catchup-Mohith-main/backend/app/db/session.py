# /home/mohith/Catchup-Mohith/backend/app/db/session.py
import logging
import time
from collections.abc import AsyncGenerator

from backend.app.core.config import settings
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

logger = logging.getLogger(__name__)
_DB_PING_QUERY = text("SELECT 1")

engine = create_async_engine(
    settings.database_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=settings.debug,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@event.listens_for(engine.sync_engine, "before_cursor_execute")
def before_cursor_execute(
    conn,
    cursor,
    statement,
    parameters,
    context,
    executemany,
):
    conn.info.setdefault("query_start_time", []).append(time.time())


@event.listens_for(engine.sync_engine, "after_cursor_execute")
def after_cursor_execute(
    conn,
    cursor,
    statement,
    parameters,
    context,
    executemany,
):
    total = time.time() - conn.info["query_start_time"].pop(-1)
    if total > 0.3:
        logger.warning(f"Slow query detected ({total:.3f}s): " f"{statement[:200]}")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
