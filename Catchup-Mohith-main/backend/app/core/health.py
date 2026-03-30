# /home/mohith/Catchup-Mohith/backend/app/core/health.py
import asyncio
import logging

from backend.app.cache.service import cache_service
from backend.app.core.config import settings
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def check_database(session: AsyncSession) -> dict:
    try:
        await session.execute(text("SELECT 1"))
        return {"status": "healthy"}
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


async def check_redis() -> dict:
    result = {"db0_cache": {}, "db1_auth": {}}

    try:
        client_cache = cache_service._get_client(settings.redis_cache_db)
        await client_cache.ping()
        result["db0_cache"] = {"status": "healthy"}
    except Exception as e:
        logger.warning(f"Redis db0 health check failed: {e}")
        result["db0_cache"] = {"status": "unhealthy", "error": str(e)}

    try:
        client_auth = cache_service._get_client(settings.redis_auth_db)
        await client_auth.ping()
        result["db1_auth"] = {"status": "healthy"}
    except Exception as e:
        logger.warning(f"Redis db1 health check failed: {e}")
        result["db1_auth"] = {"status": "unhealthy", "error": str(e)}

    overall = (
        "healthy"
        if result["db0_cache"].get("status") == "healthy"
        and result["db1_auth"].get("status") == "healthy"
        else "degraded"
    )
    return {"status": overall, "databases": result}


async def check_temporal() -> dict:
    try:
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(
                settings.temporal_host,
                settings.temporal_port,
            ),
            timeout=3.0,
        )
        writer.close()
        await writer.wait_closed()
        return {"status": "healthy"}
    except asyncio.TimeoutError:
        logger.warning("Temporal health check timed out")
        return {
            "status": "unhealthy",
            "error": "Connection timed out after 3 seconds",
        }
    except Exception as e:
        logger.warning(f"Temporal health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


async def check_seed_status(session: AsyncSession) -> dict:
    try:
        result = await session.execute(
            text(
                "SELECT COUNT(*) FROM users "
                "WHERE role = 'ADMIN' "
                "AND deleted_at IS NULL"
            )
        )
        admin_count = result.scalar_one()
        admin_seeded = admin_count > 0

        default_password_warning = (
            settings.initial_admin_password == "change-me-immediately"
        )

        return {
            "admin_seeded": admin_seeded,
            "default_password_warning": default_password_warning,
        }
    except Exception as e:
        logger.error(f"Seed status check failed: {e}")
        return {
            "admin_seeded": False,
            "default_password_warning": True,
            "error": str(e),
        }
