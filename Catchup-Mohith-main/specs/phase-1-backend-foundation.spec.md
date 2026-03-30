<!-- specs/phase-1-backend-foundation.spec.md -->
<!-- Feature specification — written before implementation begins -->

# Phase 1 — Backend Foundation Spec

## Purpose
Phase 1 establishes the operational and architectural baseline required for every later phase: environment orchestration, backend runtime wiring, migration pipeline, authentication/security primitives, Redis-backed token controls, global exception handling, health observability, and foundational test/lint gates. It must come first because all domain features (products, suppliers, PO lifecycle, GRN, workflows, dashboard, and frontend integration) depend on this phase for shared infrastructure, auth enforcement, database schema bootstrap, and reliable CI validation.

## Scope

### In Scope — Implemented in this phase
- `.gitignore`
- `.env.example`
- `docker-compose.yml`
- `docker-compose.dev-tools.yml`
- `Makefile`
- `README.md`
- `.github/workflows/ci.yml`
- `.github/workflows/cd.yml`
- `backend/Dockerfile`
- `backend/pyproject.toml`
- `backend/alembic.ini`
- `backend/init-db.sql`
- `backend/wait-for-services.sh`
- `backend/alembic/env.py`
- `backend/alembic/script.py.mako`
- `backend/alembic/versions/001_create_users_table.py`
- `backend/alembic/versions/002_create_products_table.py`
- `backend/alembic/versions/003_create_suppliers_table.py`
- `backend/alembic/versions/004_create_supplier_metrics_history_table.py`
- `backend/alembic/versions/005_create_purchase_orders_table.py`
- `backend/alembic/versions/006_create_po_lines_table.py`
- `backend/alembic/versions/007_create_grns_table.py`
- `backend/alembic/versions/008_create_grn_lines_table.py`
- `backend/alembic/versions/009_create_backorders_table.py`
- `backend/alembic/versions/010_create_stock_ledger_table.py`
- `backend/alembic/versions/011_seed_initial_admin_user.py`
- `backend/app/main.py`
- `backend/app/core/config.py`
- `backend/app/core/security.py`
- `backend/app/core/dependencies.py`
- `backend/app/core/exceptions.py`
- `backend/app/core/health.py`
- `backend/app/db/base.py`
- `backend/app/db/session.py`
- `backend/app/cache/service.py`
- `backend/app/models/user.py`
- `backend/app/schemas/common.py`
- `backend/app/schemas/auth.py`
- `backend/app/repositories/base_repository.py`
- `backend/app/repositories/user_repository.py`
- `backend/app/services/auth_service.py`
- `backend/app/routers/auth.py`
- `backend/app/routers/health.py`
- `backend/tests/unit/test_auth_service.py`
- `backend/tests/integration/test_auth_endpoints.py`
- `backend/tests/conftest.py`

### Out of Scope — Stubbed only, implemented in later phases
- `docs/testing-matrix.md` and `docs/release-checklist.md` are stubbed only (content completed in later phases).
- All backend models except `backend/app/models/user.py` are stubbed only:
  - `backend/app/models/product.py`
  - `backend/app/models/supplier.py`
  - `backend/app/models/supplier_metrics_history.py`
  - `backend/app/models/purchase_order.py`
  - `backend/app/models/po_line.py`
  - `backend/app/models/grn.py`
  - `backend/app/models/grn_line.py`
  - `backend/app/models/backorder.py`
  - `backend/app/models/stock_ledger.py`
  - `backend/app/models/email_failure_log.py`
- All backend schemas except `common.py` and `auth.py` are stubbed only:
  - `backend/app/schemas/product.py`
  - `backend/app/schemas/supplier.py`
  - `backend/app/schemas/purchase_order.py`
  - `backend/app/schemas/grn.py`
  - `backend/app/schemas/backorder.py`
  - `backend/app/schemas/stock_ledger.py`
  - `backend/app/schemas/dashboard.py`
  - `backend/app/schemas/report.py`
- All domain repositories except `base_repository.py` and `user_repository.py` are stubbed only:
  - `backend/app/repositories/product_repository.py`
  - `backend/app/repositories/supplier_repository.py`
  - `backend/app/repositories/purchase_order_repository.py`
  - `backend/app/repositories/po_line_repository.py`
  - `backend/app/repositories/grn_repository.py`
  - `backend/app/repositories/grn_line_repository.py`
  - `backend/app/repositories/backorder_repository.py`
  - `backend/app/repositories/stock_ledger_repository.py`
  - `backend/app/repositories/email_failure_log_repository.py`
- All domain services except `auth_service.py` are stubbed only:
  - `backend/app/services/product_service.py`
  - `backend/app/services/supplier_service.py`
  - `backend/app/services/tier_scoring.py`
  - `backend/app/services/purchase_order_service.py`
  - `backend/app/services/grn_service.py`
  - `backend/app/services/stock_ledger_service.py`
  - `backend/app/services/backorder_service.py`
  - `backend/app/services/dashboard_service.py`
  - `backend/app/services/report_service.py`
- All non-auth/health routers are stubbed only:
  - `backend/app/routers/products.py`
  - `backend/app/routers/suppliers.py`
  - `backend/app/routers/purchase_orders.py`
  - `backend/app/routers/grns.py`
  - `backend/app/routers/backorders.py`
  - `backend/app/routers/stock_ledger.py`
  - `backend/app/routers/dashboard.py`
  - `backend/app/routers/reports.py`
- Temporal layer files are stubbed only:
  - `backend/app/temporal/worker.py`
  - `backend/app/temporal/workflows/auto_reorder.py`
  - `backend/app/temporal/workflows/tier_recalculation.py`
  - `backend/app/temporal/workflows/backorder_followup.py`
  - `backend/app/temporal/activities/reorder_activities.py`
  - `backend/app/temporal/activities/tier_activities.py`
  - `backend/app/temporal/activities/email_activities.py`
  - `backend/app/temporal/activities/backorder_activities.py`
- All frontend files under `frontend/` are stubbed only and not implemented in this phase.
- All Postman files under `postman/` are stubbed only and completed in later testing phases.
- Spec files for phases 2 through 10 are stubbed only and populated in their respective phases.
- `backend/scripts/seed_demo.py` is stubbed only and implemented in Phase 10.

## Acceptance Criteria
1. `docker compose up` starts all 7 services without error.
2. `make dev` starts all services with hot reload.
3. `GET /health` returns HTTP 200 with db, redis, temporal status.
4. `GET /health` shows `default_password_warning: true` when `INITIAL_ADMIN_PASSWORD` is still `"change-me-immediately"`.
5. `POST /auth/login` with valid credentials returns `access_token` and `refresh_token`.
6. `POST /auth/login` with wrong password returns HTTP 401 `INVALID_CREDENTIALS`.
7. `POST /auth/logout` blacklists the access token; next request with that token returns HTTP 401 `TOKEN_REVOKED`.
8. `POST /auth/logout` also blacklists the refresh token.
9. The 6th `POST /auth/login` attempt from the same IP within 15 minutes returns HTTP 429 `AUTH_RATE_LIMITED`.
10. `POST /auth/refresh` with a blacklisted refresh token returns HTTP 401 `TOKEN_REVOKED`.
11. `POST /auth/refresh` for an inactive user returns HTTP 401 `ACCOUNT_INACTIVE` even with a valid refresh token.
12. Incrementing `user_version` in Redis causes the next authenticated request with the old token to return HTTP 401 `SESSION_INVALIDATED`.
13. `alembic upgrade head` runs all 11 migrations cleanly on a fresh PostgreSQL database.
14. Migration 011 is idempotent; running it twice does not create a duplicate admin user.
15. `pytest backend/tests/unit/` passes with zero failures.
16. `pytest backend/tests/integration/` passes with zero failures.
17. `auth_service.py` has minimum 85% test coverage.
18. `ruff check backend/` produces zero errors.
19. `black --check backend/` produces zero errors.
20. Redis failure does not cause HTTP 500; requests succeed with cache-miss fallthrough to database.
21. git commit with a non-conventional message is blocked by the commit-msg hook.
22. git commit on a Python file with ruff errors is blocked by the pre-commit hook.
23. git push runs backend unit tests and blocks if any fail.

## Edge Cases
- Inactive user is blocked on both login and refresh, even when the refresh token is cryptographically valid.
- Rate limit key uses the client IP address, never user identity; unauthenticated attempts are still counted.
- JWT blacklist uses the `jti` claim only, never the full token string.
- `user_version` mismatch returns HTTP 401 `SESSION_INVALIDATED`, never HTTP 403 (403 is authorization, 401 is authentication).
- `GET /health` includes `default_password_warning: true` when the env var matches the fallback value `"change-me-immediately"`.
- Redis unavailable: CacheService returns `None` or `False`, logs `WARNING`, never raises, never causes a 500 response.
- Both tokens on logout: access and refresh are blacklisted with their own individual remaining TTL values.
- `user_version` check happens on every authenticated request inside `get_current_user`, not only on login.
- Blacklist TTL equals the token's remaining validity, not the original full TTL, to avoid Redis memory bloat.
- Migration 011 must hash the password with bcrypt and never store plaintext; it must log `WARNING` if using the fallback password.

## Error Scenarios

| Scenario | HTTP | Error Code |
|-----------------------------|------|--------------------------|
| Wrong password | 401 | INVALID_CREDENTIALS |
| Inactive user — login | 401 | ACCOUNT_INACTIVE |
| Inactive user — refresh | 401 | ACCOUNT_INACTIVE |
| Rate limit exceeded | 429 | AUTH_RATE_LIMITED |
| Blacklisted token | 401 | TOKEN_REVOKED |
| Expired token | 401 | TOKEN_EXPIRED |
| user_version mismatch | 401 | SESSION_INVALIDATED |
| Missing token | 401 | AUTHENTICATION_REQUIRED |
| Redis unavailable | — | Log WARNING and continue |

All error responses use this envelope:
{
  "error": {
    "code": "ERROR_CODE_STRING",
    "message": "Human readable description",
    "details": {}
  }
}

## Test Cases

### Unit Tests (no infrastructure, all dependencies mocked)
- test_login_success_returns_access_and_refresh_tokens
- test_login_wrong_password_raises_invalid_credentials
- test_login_inactive_user_raises_account_inactive
- test_login_rate_limit_exceeded_raises_auth_rate_limited
- test_login_rate_limit_allows_fifth_attempt
- test_refresh_blacklisted_token_raises_token_revoked
- test_refresh_inactive_user_raises_account_inactive
- test_logout_blacklists_both_tokens
- test_cache_service_returns_none_on_redis_failure
- test_cache_service_never_raises_on_connection_error
- test_create_access_token_contains_correct_claims
- test_decode_expired_token_raises_token_expired_exception
- test_decode_invalid_token_raises_authentication_required
- test_rate_limit_blocks_sixth_attempt_not_fifth

### Integration Tests (real PostgreSQL and Redis)
- test_login_endpoint_returns_200_and_tokens
- test_login_wrong_password_returns_401
- test_login_rate_limit_blocks_sixth_attempt
- test_logout_then_request_with_old_token_returns_401
- test_logout_blacklists_refresh_token
- test_refresh_token_returns_new_access_token
- test_refresh_with_blacklisted_token_returns_401
- test_refresh_with_inactive_user_returns_401
- test_user_version_mismatch_returns_401_session_invalidated
  Logs in, increments user_version in Redis directly, makes
  authenticated request with old token, asserts HTTP 401 with
  error code SESSION_INVALIDATED.
- test_health_endpoint_returns_200_all_services_healthy
- test_health_endpoint_shows_default_password_warning

## Implementation Notes
- CacheService wraps all Redis calls; services never import Redis directly and must always go through CacheService.
- Use two Redis connection pools: db0 for cache (no persistence) and db1 for auth (AOF persistence).
- Rate limit key format is `stockbridge:ratelimit:auth:{ip_address}` using INCR + TTL of 900 seconds set only on first increment (`SET NX`).
- Blacklist key format is `stockbridge:blacklist:{jti}` with TTL equal to remaining token validity.
- `user_version` key format is `stockbridge:user_version:{user_id}` as an integer counter incremented on role changes.
- `get_current_user` sequence is decode token, blacklist check, user_version check, fetch user from DB, `is_active` check, then return user.
- All 18 exception subclasses are defined in `exceptions.py` with code strings matching the error table.
- Global exception handler in `main.py` maps all `StockBridgeException` subclasses to the standardized error envelope.
- Slow query logging uses SQLAlchemy event listeners with 300ms threshold at `WARNING` level.
- Migration 011 uses `op.get_bind()` to `SELECT` before `INSERT`, imports passlib bcrypt inside migration, and reads `INITIAL_ADMIN_PASSWORD` from `os.environ`.
- `wait-for-services.sh` polls `pg_isready`, `redis-cli ping`, and `nc` for `temporal:7233` with retry loop and timeout.
- `init-db.sql` uses idempotent `DO $$ BEGIN ... EXCEPTION WHEN duplicate_database THEN NULL; END $$;` blocks.
