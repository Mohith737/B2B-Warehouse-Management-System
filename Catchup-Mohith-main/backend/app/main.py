# backend/app/main.py
import logging
from contextlib import asynccontextmanager

from backend.app.core.config import settings
from backend.app.core.exceptions import (
    AccountInactiveException,
    AuthenticationRequiredException,
    AuthRateLimitedException,
    BarcodeMismatchException,
    ConflictException,
    CreditLimitExceededException,
    DateRangeTooLargeException,
    InsufficientStockException,
    InvalidCursorException,
    InvalidParameterException,
    InvalidStateTransitionException,
    InvalidCredentialsException,
    NotFoundException,
    OverReceiptException,
    PermissionDeniedException,
    ReportGenerationFailedException,
    ServiceUnavailableException,
    SessionInvalidatedException,
    StockBridgeException,
    SupplierInactiveException,
    TokenExpiredException,
    TokenRevokedException,
)
from backend.app.db.session import engine
from backend.app.routers import auth as auth_router
from backend.app.routers import dashboard as dashboard_router
from backend.app.routers import grns as grns_router
from backend.app.routers import health as health_router
from backend.app.routers import products as products_router
from backend.app.routers import purchase_orders as purchase_orders_router
from backend.app.routers import reports as reports_router
from backend.app.routers import stock_ledger as stock_ledger_router
from backend.app.routers import suppliers as suppliers_router
from backend.app.routers import users as users_router
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

EXCEPTION_STATUS_MAP: dict[type, int] = {
    BarcodeMismatchException: 400,
    ConflictException: 409,
    CreditLimitExceededException: 400,
    DateRangeTooLargeException: 400,
    InsufficientStockException: 400,
    InvalidCursorException: 400,
    InvalidParameterException: 400,
    InvalidStateTransitionException: 400,
    NotFoundException: 404,
    OverReceiptException: 400,
    PermissionDeniedException: 403,
    ReportGenerationFailedException: 503,
    ServiceUnavailableException: 503,
    SupplierInactiveException: 400,
    AuthRateLimitedException: 429,
    InvalidCredentialsException: 401,
    AccountInactiveException: 401,
    TokenRevokedException: 401,
    TokenExpiredException: 401,
    SessionInvalidatedException: 401,
    AuthenticationRequiredException: 401,
}


def get_status_code(exc: StockBridgeException) -> int:
    return EXCEPTION_STATUS_MAP.get(type(exc), 400)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"StockBridge API starting — environment={settings.environment}")
    try:
        async with engine.connect() as conn:
            from sqlalchemy import text

            await conn.execute(text("SELECT 1"))
        logger.info("Database connection verified at startup")
    except Exception as e:
        logger.error(f"Database connection failed at startup: {e}")

    yield

    logger.info("StockBridge API shutting down")
    await engine.dispose()
    logger.info("Database connection pool closed")


app = FastAPI(
    title="StockBridge API",
    version="1.0.0",
    description=("B2B warehouse inventory and purchase order management system"),
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(StockBridgeException)
async def stockbridge_exception_handler(
    request: Request,
    exc: StockBridgeException,
) -> JSONResponse:
    status_code = get_status_code(exc)
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    logger.error(
        f"Unhandled exception on {request.method} " f"{request.url.path}: {exc}",
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "details": {},
            }
        },
    )


app.include_router(
    auth_router.router,
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    health_router.router,
    tags=["health"],
)
app.include_router(
    products_router.router,
    prefix="/products",
    tags=["products"],
)
app.include_router(
    suppliers_router.router,
    prefix="/suppliers",
    tags=["suppliers"],
)
app.include_router(
    purchase_orders_router.router,
    prefix="/purchase-orders",
    tags=["purchase-orders"],
)
app.include_router(
    grns_router.router,
    prefix="/grns",
    tags=["grns"],
)
app.include_router(
    stock_ledger_router.router,
    prefix="/stock-ledger",
    tags=["stock-ledger"],
)
app.include_router(
    dashboard_router.router,
    prefix="/dashboard",
    tags=["dashboard"],
)
app.include_router(
    reports_router.router,
    prefix="/reports",
    tags=["reports"],
)
app.include_router(
    users_router.router,
    prefix="/users",
    tags=["users"],
)


@app.get("/", include_in_schema=False)
async def root():
    return {
        "service": "StockBridge API",
        "version": "1.0.0",
        "status": "running",
    }
