# /home/mohith/Catchup-Mohith/backend/app/routers/health.py
from backend.app.core.health import (
    check_database,
    check_redis,
    check_seed_status,
    check_temporal,
)
from backend.app.db.session import get_db
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get(
    "/health",
    summary="Full system health check",
    tags=["health"],
)
async def health_check(
    session: AsyncSession = Depends(get_db),
) -> JSONResponse:
    db = await check_database(session)
    redis = await check_redis()
    temporal = await check_temporal()
    seed = await check_seed_status(session)

    if db["status"] != "healthy" or temporal["status"] != "healthy":
        overall = "unhealthy"
        http_status = 503
    elif redis["status"] != "healthy":
        overall = "degraded"
        http_status = 200
    else:
        overall = "healthy"
        http_status = 200

    body = {
        "data": {
            "status": overall,
            "database": db,
            "redis": redis,
            "temporal": temporal,
            "seed": seed,
        }
    }
    return JSONResponse(content=body, status_code=http_status)


@router.get(
    "/health/temporal",
    summary="Temporal service reachability check",
    tags=["health"],
)
async def temporal_health() -> JSONResponse:
    result = await check_temporal()
    http_status = 200 if result["status"] == "healthy" else 503
    return JSONResponse(
        content={"data": result},
        status_code=http_status,
    )
