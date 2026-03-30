# specs/phase-10-integration-testing.spec.md
# Phase 10 — Integration Testing, Seed Script and CI Pipeline Spec

## Purpose
This is the final phase. It wires together everything built in
Phases 1-9 into a verified, runnable, and automatically tested
system. After this phase the project can be run end-to-end by
any developer with a single command, and every PR is validated
by CI before merge.

## Scope

### In Scope
scripts/seed.py — deterministic seed script
scripts/smoke_main_apis.sh — full smoke test of backend endpoints
backend/tests/integration/ — integration tests per router
client/tests/e2e/ — full E2E suite verification
.github/workflows/ci.yml — CI pipeline
docker-compose.yml — verify all services start cleanly
docs/RUNBOOK.md — developer runbook

### Out of Scope
Production deployment configuration
SSL/TLS setup
External monitoring or alerting

## Acceptance Criteria

1.  `docker-compose up -d` starts all services cleanly — backend,
    postgres, redis, temporal
2.  `python scripts/seed.py` runs without errors and creates
    deterministic test data
3.  Seed creates: 1 admin, 1 procurement_manager, 1 warehouse_staff,
    5 suppliers (mix of Silver/Gold/Diamond), 20 products,
    3 purchase orders (various statuses), 2 GRNs, stock ledger
    entries from GRN receipts
4.  Seed is idempotent — running twice does not create duplicates
5.  `bash scripts/smoke_main_apis.sh` passes all assertions against
    a running backend
6.  Backend integration tests cover all 9 routers
7.  Integration tests use a real test database (not mocks)
8.  `pytest backend/tests/integration/ -v` passes with zero failures
9.  `pnpm test:e2e` passes against a running frontend + backend
10. `pnpm build` passes with zero TypeScript errors
11. CI pipeline runs on every PR to main
12. CI pipeline runs: lint, typecheck, backend unit tests, backend
    integration tests, frontend build, frontend lint
13. CI pipeline fails fast — if lint fails it does not run tests
14. All secrets managed via GitHub Actions secrets — never hardcoded
15. docs/RUNBOOK.md documents how to run the project locally

## Seed Script — scripts/seed.py

### Design Principles
- Idempotent: look up by unique field before creating
- Deterministic: same UUIDs every run using uuid5 with a namespace
- Order-safe: respects FK dependencies
- Self-contained: reads .env for DB connection, no manual config

### Seed Data

**Users (3):**
```
admin@stockbridge.com     / StockAdmin123!   / admin
manager@stockbridge.com   / StockManager123! / procurement_manager
staff@stockbridge.com     / StockStaff123!   / warehouse_staff
```

**Suppliers (5):**
```
AlphaSupply Co      / alpha@supply.com   / Silver  / credit_limit 50000
BetaGoods Ltd       / beta@goods.com     / Gold    / credit_limit 100000
GammaTrade Inc      / gamma@trade.com    / Diamond / credit_limit 200000
DeltaMart Corp      / delta@mart.com     / Silver  / credit_limit 30000
EpsilonWholesale    / eps@wholesale.com  / Gold    / credit_limit 75000
```

**Products (20):**
Mix of in-stock, low-stock, and out-of-stock items. Assign
preferred_supplier_id to one of the 5 suppliers per product.
Products 1-7: current_stock above reorder_point
Products 8-14: current_stock at or below reorder_point (low stock)
Products 15-20: current_stock = 0 (out of stock)

**Purchase Orders (3):**
- PO1: supplier=BetaGoods, status=acknowledged, 3 lines
- PO2: supplier=GammaTrade, status=received, 2 lines
- PO3: supplier=AlphaSupply, status=draft, 2 lines

**GRNs (2, linked to PO1 and PO2):**
- GRN1: linked to PO1, status=open, partial receipt
- GRN2: linked to PO2, status=completed, full receipt
- Stock ledger entries created for GRN2 receipts

### Seed Implementation

```python
# scripts/seed.py
import asyncio
import os
import uuid
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

# Import models
from backend.app.models.user import User, UserRole
from backend.app.models.supplier import Supplier, SupplierTier
from backend.app.models.product import Product
from backend.app.models.purchase_order import PurchaseOrder, POStatus
from backend.app.models.grn import GRN, GRNStatus
from backend.app.core.security import get_password_hash

SEED_NAMESPACE = uuid.UUID("12345678-1234-5678-1234-567812345678")

def seed_uuid(name: str) -> uuid.UUID:
    """Deterministic UUID from name."""
    return uuid.uuid5(SEED_NAMESPACE, name)

async def seed():
    engine = create_async_engine(os.environ["DATABASE_URL"])
    async_session = sessionmaker(engine, class_=AsyncSession,
                                  expire_on_commit=False)
    async with async_session() as session:
        await seed_users(session)
        await seed_suppliers(session)
        await seed_products(session)
        await seed_purchase_orders(session)
        await seed_grns(session)
        await session.commit()
    print("Seed completed successfully.")

if __name__ == "__main__":
    asyncio.run(seed())
```

Each seed_* function:
1. Builds the deterministic UUID via seed_uuid(unique_name)
2. Checks if record exists via SELECT WHERE id = seed_uuid(...)
3. Creates only if not found
4. Never updates existing records

## Smoke Test — scripts/smoke_main_apis.sh

Full replacement of the existing placeholder smoke test.

### Structure
```bash
#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
ADMIN_EMAIL="${ADMIN_EMAIL:-admin@stockbridge.com}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-StockAdmin123!}"
MANAGER_EMAIL="${MANAGER_EMAIL:-manager@stockbridge.com}"
MANAGER_PASSWORD="${MANAGER_PASSWORD:-StockManager123!}"
STAFF_EMAIL="${STAFF_EMAIL:-staff@stockbridge.com}"
STAFF_PASSWORD="${STAFF_PASSWORD:-StockStaff123!}"

pass=0
fail=0

check() {
  local name="$1"
  local expected="$2"
  local actual="$3"
  if [ "$actual" = "$expected" ]; then
    echo "  PASS: $name"
    ((pass++))
  else
    echo "  FAIL: $name (expected=$expected, actual=$actual)"
    ((fail++))
  fi
}
```

### Smoke Test Scenarios (minimum 30 checks)

**Auth:**
- POST /auth/login admin → 200, token returned
- POST /auth/login manager → 200
- POST /auth/login staff → 200
- POST /auth/login bad password → 401
- GET /auth/me with admin token → 200, correct role

**Products:**
- GET /products → 200, items array present
- GET /products?search=nonexistent999 → 200, items empty
- POST /products (admin) → 201
- POST /products (staff) → 403

**Suppliers:**
- GET /suppliers → 200
- POST /suppliers (manager) → 201
- POST /suppliers (staff) → 403

**Purchase Orders:**
- GET /purchase-orders → 200
- POST /purchase-orders (manager) → 201, po_number starts with SB-
- POST /purchase-orders (staff) → 403
- GET /purchase-orders/:id → 200
- GET /purchase-orders/:id/credit-check → 200

**GRNs:**
- POST /grns → 201
- GET /grns/:id → 200
- POST /grns/:id/lines/:line_id/receive → 200
- POST /grns/:id/complete → 200

**Stock Ledger:**
- GET /stock-ledger → 200, items present after GRN completion

**Dashboard:**
- GET /dashboard (staff) → 200, has total_products
- GET /dashboard (manager) → 200, has open_pos
- GET /dashboard (admin) → 200, has system_health
- GET /dashboard/low-stock → 200

**Reports:**
- GET /reports/suppliers/:id?months=12 → 200, content-type text/csv

**Health:**
- GET /health → 200

**Final summary:**
```bash
echo ""
echo "Results: $pass passed, $fail failed"
[ $fail -eq 0 ] && exit 0 || exit 1
```

## Backend Integration Tests

Location: backend/tests/integration/
One file per router. Use pytest-asyncio. Use real PostgreSQL test DB.
Test DB URL: set via TEST_DATABASE_URL env var.

### conftest.py (backend/tests/integration/conftest.py)
```python
# Fixtures:
# - engine: creates test DB schema before session, drops after
# - session: AsyncSession per test, rolls back after each test
# - client: AsyncClient with app, overrides get_db dependency
# - admin_token, manager_token, staff_token: JWT tokens for each role
# - seeded_data: runs seed functions with test session, returns IDs
```

### Test Files
- test_auth_integration.py — login, refresh, logout, me endpoint
- test_products_integration.py — CRUD, pagination, search, RBAC
- test_suppliers_integration.py — CRUD, tier filter, RBAC
- test_purchase_orders_integration.py — lifecycle, credit check, RBAC
- test_grns_integration.py — create, receive line, complete, RBAC
- test_stock_ledger_integration.py — entries after GRN, cursor pagination
- test_dashboard_integration.py — role-specific responses
- test_reports_integration.py — CSV response, correct content-type

### Key Test Patterns

Every router test file covers:
1. Happy path — correct role, valid data → correct response
2. RBAC — wrong role → 403
3. Not found — invalid UUID → 404
4. Validation — missing required field → 422
5. Business rule — e.g. over-receipt → 409 or 400

Example structure:
```python
class TestListProducts:
    async def test_returns_200_for_authenticated_user(self, client, staff_token):
        ...
    async def test_returns_401_without_token(self, client):
        ...
    async def test_pagination_returns_correct_page(self, client, admin_token):
        ...
    async def test_search_filters_by_name(self, client, admin_token):
        ...
```

## CI Pipeline — .github/workflows/ci.yml

### Trigger
```yaml
on:
  pull_request:
    branches: [main]
  push:
    branches: [main]
```

### Jobs (in order, fail fast)

**Job 1: backend-lint**
- Python 3.11
- Install ruff and black
- Run: `ruff check backend/ && black --check backend/`
- Fail → stop all downstream jobs

**Job 2: backend-unit-tests** (needs: backend-lint)
- Python 3.11
- Install dependencies: `pip install -r backend/requirements.txt`
- Run: `pytest backend/tests/unit/ -v --tb=short`

**Job 3: backend-integration-tests** (needs: backend-lint)
- Services: postgres:15, redis:7
- Python 3.11
- Install dependencies
- Run migrations: `alembic upgrade head`
- Run seed: `python scripts/seed.py`
- Run: `pytest backend/tests/integration/ -v --tb=short`
- Env vars from GitHub secrets:
  DATABASE_URL, TEST_DATABASE_URL, SECRET_KEY, REDIS_URL

**Job 4: frontend-lint** (runs in parallel with backend jobs)
- Node 20
- Install pnpm
- Run: `cd client && pnpm install --frozen-lockfile`
- Run: `cd client && pnpm lint`
- Run: `cd client && pnpm tsc --noEmit`

**Job 5: frontend-build** (needs: frontend-lint)
- Node 20
- Run: `cd client && pnpm build`

### GitHub Secrets Required
```
DATABASE_URL
TEST_DATABASE_URL
SECRET_KEY
REDIS_URL
SENDGRID_API_KEY
SENDGRID_FROM_EMAIL
INITIAL_ADMIN_PASSWORD
```

### CI Notes
- E2E tests NOT in CI — they require running frontend + backend +
  seed data together. Run locally before PR.
- pnpm lockfile: use --frozen-lockfile in CI to catch lockfile drift
- ruff and black versions pinned in requirements-dev.txt

## RUNBOOK — docs/RUNBOOK.md

### Sections Required
1. Prerequisites (Docker, Node 20, pnpm, Python 3.11)
2. First-time setup
3. Running the full stack locally
4. Running backend tests
5. Running frontend E2E tests
6. Seed script usage
7. Smoke test usage
8. Environment variables reference
9. Common issues and fixes

### First-Time Setup Steps
```bash
# Clone and configure
git clone <repo>
cd Catchup-Mohith
cp .env.example .env
# Edit .env with real values for SECRET_KEY, SENDGRID_*, INITIAL_ADMIN_PASSWORD

# Start services
docker-compose up -d postgres redis temporal temporal-ui

# Run migrations
cd backend
alembic upgrade head

# Seed database
python scripts/seed.py

# Start backend
uvicorn backend.app.main:app --reload

# Start frontend (new terminal)
cd client
pnpm install
pnpm dev
```

### Running Tests
```bash
# Backend unit tests
pytest backend/tests/unit/ -v

# Backend integration tests (requires running postgres)
pytest backend/tests/integration/ -v

# Frontend lint and typecheck
cd client && pnpm lint && pnpm tsc --noEmit

# Frontend E2E (requires running frontend + backend + seed data)
cd client && pnpm test:e2e

# Smoke test (requires running backend + seed data)
bash scripts/smoke_main_apis.sh
```

## Implementation Notes

- Seed script must import from backend.app — run from project root
  not from scripts/ directory: `python scripts/seed.py` from
  ~/Catchup-Mohith/

- Seed idempotency: use SELECT before INSERT, never upsert or
  delete+recreate. If record exists skip silently.

- Integration test DB: use a separate database
  stockbridge_test to avoid polluting development data.
  TEST_DATABASE_URL=postgresql+asyncpg://user:pass@localhost/stockbridge_test

- Integration tests rollback: each test uses a savepoint/rollback
  pattern so tests are isolated without recreating schema each time.

- CI postgres service: use
  `postgres:15-alpine` with health check before running tests.

- CI pnpm cache: use actions/cache with key based on
  pnpm-lock.yaml hash to speed up installs.

- requirements-dev.txt: add pytest, pytest-asyncio, httpx,
  ruff, black — separate from production requirements.txt

- Smoke test credential order: always login first, capture token,
  use token for all subsequent requests in that role's block.

- RUNBOOK must be accurate — test every command in the runbook
  against the actual running system before committing.
