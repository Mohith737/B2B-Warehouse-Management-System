# StockBridge — Implementation Plan

## Project Overview
StockBridge is a B2B warehouse inventory and purchase order
management system that eliminates stock-outs and procurement chaos
for small warehouses. It replaces spreadsheets with a real-time,
role-aware platform that enforces business rules at every stage —
from supplier catalog management to goods receipt. The system
serves three roles: warehouse_staff who perform goods receipt
operations, procurement_managers who manage suppliers and the full
purchase order lifecycle, and admins who have full access to
configuration, reporting, and user management. Technically,
StockBridge demands atomic stock updates under concurrent writes
using optimistic locking, partial receipt tracking with automatic
backorder creation, credit limit validation across variable PO
totals, Temporal-driven background job scheduling for auto-reorder
and supplier tier recalculation, and a clean state machine for the
PO lifecycle. The frontend requires a multi-step PO creation
wizard, live stock status indicators, and a GRN form with
barcode-to-product auto-fill — all built on IBM Carbon Design
System.

## Architecture Summary
StockBridge uses a strict four-layer backend architecture:
Router → Service → Repository → Model. Routers handle HTTP
concerns only and never contain business logic. Services own all
business rules and transaction boundaries. Repositories handle
database access only and never commit. Models are pure SQLAlchemy
declarations. Side effects such as emails and cache invalidation
always happen after a transaction commits, never inside one.

### Tech Stack

| Layer          | Technology                | Version  |
|----------------|---------------------------|----------|
| Language       | Python                    | 3.11     |
| API            | FastAPI                   | 0.111+   |
| ORM            | SQLAlchemy async          | 2.0      |
| Validation     | Pydantic                  | v2       |
| Migrations     | Alembic                   | 1.13+    |
| Cache/Auth     | redis-py                  | 5.0+     |
| JWT            | python-jose               | latest   |
| Passwords      | passlib[bcrypt]           | latest   |
| Database       | PostgreSQL                | 15       |
| Workflows      | Temporal                  | 1.22     |
| Frontend       | React                     | 18       |
| UI Library     | IBM Carbon Design System  | 11       |
| Server State   | TanStack Query            | v5       |
| UI State       | Zustand                   | v4       |
| Runtime        | Node                      | 20       |
| Git Hooks      | Husky                     | v9+      |
| Staged Lint    | lint-staged               | v15+     |
| Commit Lint    | commitlint                | v19+     |

## Branch Strategy
One branch per core feature and engineering challenge. Solo
developer. If one branch fails after merging, all other branches
remain stable and independently reviewable.

  feature/backend-foundation       — Docker, DB, auth, migrations,
                                     health, base patterns
  feature/auth-and-rbac            — RBAC dependencies, role guards
  feature/product-catalog          — Product CRUD, stock badges,
                                     barcode lookup
  feature/supplier-directory       — Supplier CRUD, credit limits
  feature/supplier-tier-scoring    — Pure tier scoring function,
                                     metrics history
  feature/po-lifecycle             — PO state machine, credit check,
                                     all transitions
  feature/grn-and-stock            — GRN, stock ledger, optimistic
                                     locking, backorder creation
  feature/backorder-management     — Backorder tracking and
                                     fulfilment
  feature/temporal-auto-reorder    — Cron every 2h, parallel
                                     per-product
  feature/temporal-tier-recalculation — Cron last day of month
  feature/temporal-backorder-followup — Event-driven workflow
  feature/dashboard-and-reports    — Role-specific dashboard,
                                     CSV reports
  feature/frontend-foundation      — Carbon setup, auth flow,
                                     atoms, routing
  feature/frontend-product-pages   — Product list and detail pages
  feature/frontend-supplier-pages  — Supplier list and detail pages
  feature/frontend-po-wizard       — Multi-step PO creation wizard
  feature/frontend-grn-form        — GRN form with barcode input
  feature/frontend-dashboard       — Role-specific dashboard views
  feature/frontend-admin           — Admin user management pages
  feature/seed-data-and-ci         — Demo seed script, full CI
                                     verification

## Implementation Phases

### Phase 1 — Backend Foundation
  backend/init-db.sql               Creates stockbridge + temporal DBs
  backend/wait-for-services.sh      Service readiness probe
  docker-compose.yml                7 services with healthchecks
  docker-compose.dev-tools.yml      pgAdmin dev-tools profile
  .env.example                      All env vars with section comments
  Makefile                          13 standard targets
  backend/Dockerfile                Multi-stage Python 3.11 build
  backend/pyproject.toml            All pinned dependencies
  backend/alembic.ini               Alembic config for async engine
  backend/alembic/env.py            Async env with all model imports
  backend/alembic/script.py.mako    Migration template
  backend/alembic/versions/001–011  All migrations including admin seed
  backend/app/core/config.py        Pydantic BaseSettings
  backend/app/core/exceptions.py    18 typed exceptions
  backend/app/core/security.py      JWT, bcrypt, blacklist
  backend/app/core/dependencies.py  get_current_user, require_role
  backend/app/core/health.py        DB/Redis/Temporal checks
  backend/app/db/base.py            DeclarativeBase + mixins
  backend/app/db/session.py         Async engine, get_db dependency
  backend/app/cache/service.py      CacheService, graceful degradation
  backend/app/models/user.py        User model
  backend/app/schemas/common.py     Response envelopes
  backend/app/schemas/auth.py       Auth schemas
  backend/app/repositories/base_repository.py   Generic CRUD
  backend/app/repositories/user_repository.py   User queries
  backend/app/services/auth_service.py           Login/refresh/logout
  backend/app/routers/auth.py       Auth endpoints
  backend/app/routers/health.py     Health endpoints
  backend/app/main.py               App wiring, middleware, handlers
  backend/tests/conftest.py         Shared fixtures
  backend/tests/unit/test_auth_service.py
  backend/tests/unit/test_jwt.py
  backend/tests/integration/test_auth_endpoints.py
  backend/tests/integration/test_health_endpoint.py
  .github/workflows/ci.yml          7-job CI pipeline
  .github/workflows/cd.yml          3-job CD pipeline
  .husky/pre-commit                 lint-staged on commit
  .husky/pre-push                   unit tests on push
  .husky/commit-msg                 conventional commit enforcement
  commitlint.config.js              Commit message rules
  .lintstagedrc.json                Staged file lint config

### Phase 2 — Core Domain (Products + Suppliers + RBAC)
  Depends on: Phase 1 complete and merged
  backend/app/models/product.py
  backend/app/models/supplier.py
  backend/app/models/supplier_metrics_history.py
  backend/app/schemas/product.py
  backend/app/schemas/supplier.py
  backend/app/repositories/product_repository.py
  backend/app/repositories/supplier_repository.py
  backend/app/services/product_service.py
  backend/app/services/supplier_service.py
  backend/app/services/tier_scoring.py       (pure function, 100% coverage)
  backend/app/routers/products.py
  backend/app/routers/suppliers.py
  backend/tests/unit/test_tier_scoring.py    (100% coverage gate)
  backend/tests/unit/test_product_service.py
  backend/tests/integration/test_product_endpoints.py
  backend/tests/integration/test_supplier_endpoints.py
  specs/phase-2-product-catalog.spec.md
  specs/phase-2-supplier-directory.spec.md
  specs/phase-2-tier-scoring.spec.md
  specs/phase-2-rbac.spec.md

### Phase 3 — PO Lifecycle
  Depends on: Phase 2 complete
  State transitions: Draft→Submitted→Acknowledged→Shipped→
                     Received→Closed (+ Cancelled from Draft/Submitted)
  backend/app/models/purchase_order.py
  backend/app/models/po_line.py
  backend/app/schemas/purchase_order.py
  backend/app/repositories/purchase_order_repository.py
  backend/app/repositories/po_line_repository.py
  backend/app/services/purchase_order_service.py
  backend/app/routers/purchase_orders.py
  backend/tests/unit/test_po_service.py
  backend/tests/integration/test_po_endpoints.py
  specs/phase-3-po-lifecycle.spec.md

### Phase 4 — GRN and Stock Management
  Depends on: Phase 3 complete
  Atomic requirements: stock update + ledger entry in same transaction
  backend/app/models/grn.py
  backend/app/models/grn_line.py
  backend/app/models/backorder.py
  backend/app/models/stock_ledger.py
  backend/app/schemas/grn.py
  backend/app/schemas/backorder.py
  backend/app/schemas/stock_ledger.py
  backend/app/repositories/grn_repository.py
  backend/app/repositories/grn_line_repository.py
  backend/app/repositories/backorder_repository.py
  backend/app/repositories/stock_ledger_repository.py
  backend/app/services/grn_service.py
  backend/app/services/stock_ledger_service.py
  backend/app/services/backorder_service.py
  backend/app/routers/grns.py
  backend/app/routers/backorders.py
  backend/app/routers/stock_ledger.py
  backend/tests/unit/test_grn_service.py
  backend/tests/integration/test_grn_endpoints.py
  specs/phase-4-grn-and-stock.spec.md
  specs/phase-4-backorder-management.spec.md

### Phase 5 — Temporal Workflows
  Depends on: Phase 4 complete
  backend/app/temporal/worker.py
  backend/app/temporal/workflows/auto_reorder.py
  backend/app/temporal/workflows/tier_recalculation.py
  backend/app/temporal/workflows/backorder_followup.py
  backend/app/temporal/activities/reorder_activities.py
  backend/app/temporal/activities/tier_activities.py
  backend/app/temporal/activities/email_activities.py
  backend/app/temporal/activities/backorder_activities.py
  backend/app/models/email_failure_log.py
  backend/app/repositories/email_failure_log_repository.py
  specs/phase-5-temporal-auto-reorder.spec.md
  specs/phase-5-temporal-tier-recalculation.spec.md
  specs/phase-5-temporal-backorder-followup.spec.md

### Phase 6 — Dashboard and Reports
  Depends on: Phase 5 complete
  backend/app/schemas/dashboard.py
  backend/app/schemas/report.py
  backend/app/services/dashboard_service.py
  backend/app/services/report_service.py
  backend/app/routers/dashboard.py
  backend/app/routers/reports.py
  specs/phase-6-dashboard-and-reports.spec.md

### Phase 7 — Frontend Foundation
  Depends on: Phase 1 backend running
  frontend/src/main.tsx
  frontend/src/App.tsx
  frontend/src/lib/queryClient.ts
  frontend/src/lib/axios.ts
  frontend/src/lib/constants.ts
  frontend/src/store/authStore.ts
  frontend/src/store/uiStore.ts
  frontend/src/store/grnStore.ts
  frontend/src/store/wizardStore.ts
  frontend/src/hooks/useAuth.ts
  frontend/src/routes/index.tsx
  frontend/src/routes/ProtectedRoute.tsx
  frontend/src/styles/globals.scss
  frontend/src/styles/variables.scss
  All 9 atoms (StatusBadge, FormInput, EmptyState, LoadingSkeleton,
    ProgressBar, ConfirmationBanner, Tooltip, PageTitle, FormSection)
  frontend/src/pages/LoginPage.tsx
  specs/phase-7-frontend-foundation.spec.md

### Phase 8 — Frontend Core Pages
  Depends on: Phase 7 complete
  All 10 molecules
  ProductListPage, ProductDetailPage
  SupplierListPage, SupplierDetailPage
  POListPage, PODetailPage, POCreatePage (MultiStepPOWizard)
  GRNListPage, GRNCreatePage
  All relevant hooks
  specs/phase-8-frontend-core-pages.spec.md

### Phase 9 — Frontend Dashboard and Admin
  Depends on: Phase 8 complete
  All 10 organisms
  DashboardPage (all 3 role views)
  BackorderListPage, StockLedgerPage
  AdminUsersPage, ReportsPage
  specs/phase-9-frontend-dashboard-admin.spec.md

### Phase 10 — Integration, Testing, Seed Data
  Depends on: All phases complete
  backend/scripts/seed_demo.py      5 suppliers, 30 products,
                                    3 users, 5 POs
  postman/stockbridge.postman_collection.json
  postman/stockbridge.postman_environment.json
  Full test suite verification
  CI pipeline end-to-end verification
  specs/phase-10-integration-testing.spec.md

## Feature Specifications
  specs/phase-1-backend-foundation.spec.md
  specs/phase-2-product-catalog.spec.md
  specs/phase-2-supplier-directory.spec.md
  specs/phase-2-tier-scoring.spec.md
  specs/phase-2-rbac.spec.md
  specs/phase-3-po-lifecycle.spec.md
  specs/phase-4-grn-and-stock.spec.md
  specs/phase-4-backorder-management.spec.md
  specs/phase-5-temporal-auto-reorder.spec.md
  specs/phase-5-temporal-tier-recalculation.spec.md
  specs/phase-5-temporal-backorder-followup.spec.md
  specs/phase-6-dashboard-and-reports.spec.md
  specs/phase-7-frontend-foundation.spec.md
  specs/phase-8-frontend-core-pages.spec.md
  specs/phase-9-frontend-dashboard-admin.spec.md
  specs/phase-10-integration-testing.spec.md

## Testing Strategy

### Unit Tests
No infrastructure. Mock all external dependencies.
Coverage thresholds:
  tier_scoring.py: 100% (CI gate — build fails if not met)
  All other services: 85% minimum
  Frontend components: 70% minimum
Run with: pytest backend/tests/unit/

### Integration Tests
Real PostgreSQL and Redis required.
Alembic migrations run before test suite.
Tests cover complete flows through real DB.
Run with: pytest backend/tests/integration/

### API Flow Tests (Postman/Newman)
Postman collection covers all 25 endpoints.
Newman runs in CI as smoke test job.
Tests complete user journeys for all 3 roles.

### Key Test Cases for Critical Business Logic
Tier scoring: worst-metric-wins, promotion/demotion, streak
  counters, 20 PO line minimum, all edge cases
GRN atomicity: stock update + ledger entry in same transaction,
  rollback on failure
Credit check: limit exceeded raises exception inside transaction,
  accounts for all open POs for supplier
Optimistic locking: concurrent updates, version mismatch → 409,
  deterministic version simulation
Auto-reorder: no duplicate POs for same product-supplier
Partial receipt: backorder auto-created with correct quantity

## Key Engineering Decisions

UUID Primary Keys — all entities use UUIDs for distributed safety
Decimal fields — NUMERIC for all financial and stock quantities,
  never FLOAT
Optimistic Locking — version column on Product, ConflictException
  → HTTP 409
Soft Deletes — deleted_at on all major entities for audit trail
Redis Two Databases — db0 cache / db1 auth for separation
JWT Dual Token — access 60min / refresh 7days with blacklist
CacheService Graceful Degradation — Redis failure never causes 500
Worst-Metric-Wins — supplier tier set by lowest-performing metric
Tier Scoring Pure Function — zero DB calls, 100% testable
Stock via Ledger Only — current_stock never written directly
Credit Check in Transaction — inside PO submit, not before
Side Effects After Commit — emails after commit, never inside
Temporal for Emails — SendGrid only via Temporal activities
Temporal Version Pinned — temporalio/auto-setup:1.22 for stability
PostgreSQL 15 — pinned for SQLAlchemy/Alembic stability
Two Separate Databases — app uses stockbridge, Temporal uses
  temporal database
Cursor Pagination for Ledger — offset impractical for
  high-volume append-only table
StreamingResponse for CSV — avoids memory issues on large reports
Carbon Design System — IBM Carbon only, no custom component library
Four-State Components — every component handles all 4 states
Component Reusability — atoms before molecules before organisms
sessionStorage for GRN Session — wizard and GRN survive refresh
Zero Retries on Mutations — non-idempotent operations never
  auto-retried by TanStack Query
Barcode Lookup Single Endpoint — same code path dev and prod
Auto-Reorder Idempotency — duplicate PO guard on product-supplier
20 PO Lines Minimum — tier evaluation requires meaningful volume
Husky Git Hooks — pre-commit lint, pre-push unit tests,
  commit-msg conventional commit enforcement

## Definition of Done Per Feature
A feature is complete when ALL of these are true:
  - spec file exists in specs/ with edge cases and acceptance criteria
  - all planned files created with full path comment on line 1
  - unit tests written and passing with coverage thresholds met
  - integration tests written and passing
  - no linting errors (ruff + black backend, eslint frontend)
  - PR created on feature branch with descriptive title
  - review feedback documented and attached to PR
