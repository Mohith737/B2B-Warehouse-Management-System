# AGENTS.md — StockBridge Coding Agent Instructions

## What This Project Is
StockBridge is a B2B warehouse inventory and purchase order
management system that eliminates stock-outs and procurement chaos
for small warehouses. It replaces spreadsheets with a real-time,
role-aware platform enforcing business rules at every stage from
supplier catalog to goods receipt. Three roles use the system:
warehouse_staff (GRN operations only), procurement_manager
(suppliers and full PO lifecycle), and admin (full access including
configuration, reporting, and user management). Core features
include product catalog with live stock badges, supplier directory
with credit tier scoring (Silver/Gold/Diamond), PO lifecycle state
machine with credit limit enforcement, barcode-scan GRN with
automatic backorder creation, Temporal-driven auto-reorder engine,
full stock movement ledger, and role-specific dashboards. The
project demands atomic stock updates under concurrent writes,
optimistic locking, partial receipt tracking, background job
scheduling, and clean state machine design — all grounded in real
B2B warehouse operations.

## How To Use This File
Read this file completely before starting any implementation task.
Read plan.md to understand the full project scope and all phases.
Read the relevant spec file in specs/ before implementing any
feature. Never start implementation without a spec file existing.
After completing each phase, update the Lessons Learned section
with concrete observations. This file is a living document.

## Absolute Rules (Never Violate)

Rule 1  — File Paths: Every file begins with its full path from
          project root as a comment on line 1. No exceptions.
          Python:  # backend/app/core/config.py
          YAML:    # docker-compose.yml
          SQL:     -- backend/init-db.sql
          Shell:   # backend/wait-for-services.sh
          TSX:     // frontend/src/components/atoms/StatusBadge.tsx

Rule 2  — Production Quality: No TODO comments. No placeholder
          logic. No ellipsis (...) standing in for code. Every
          file must be complete and immediately runnable.

Rule 3  — Layer Enforcement: Router → Service → Repository →
          Model. Routers: HTTP only. Services: business logic and
          transactions. Repositories: DB access only. Models:
          SQLAlchemy declarations only. Violating this is a
          critical error that will cause PR rejection.

Rule 4  — Four Component States: Every frontend component must
          handle loading, empty, error, and success states.
          A component that renders success state only is
          incomplete and will not pass review.

Rule 5  — No Hardcoded Visual Values: All colors, spacing, and
          typography must come from Carbon design tokens only.
          Zero hardcoded hex values, pixel values, or font sizes.

Rule 6  — Typed Exceptions Only: Every service method raises a
          typed exception from the StockBridgeException hierarchy.
          Never raise generic Exception or ValueError.

Rule 7  — Transaction and Side Effect Boundary: Services own all
          transactions. Emails, cache invalidation, and all other
          side effects happen AFTER the transaction commits. Never
          inside a transaction block.

Rule 8  — Component Reusability Protocol:
          Before creating any UI component, follow these steps:
          Step 1: Check frontend/src/components/atoms/ — does
                  this atom already exist?
          Step 2: Check frontend/src/components/molecules/ —
                  does this molecule already exist?
          Step 3: If yes, use the existing component. Never
                  reimplement it inline in a feature component.
          Step 4: If no, create the atom or molecule first as a
                  standalone file, then use it in the feature.
          PRs that define atoms or molecules locally inside
          feature components are rejected without review.

Rule 9  — Semantic Labels: Status values shown to users are
          always human-readable. Never display raw enum values,
          internal IDs, snake_case strings, or color names
          directly in the UI.

Rule 10 — Coverage Gates (enforced as CI blockers):
          tier_scoring.py: 100% coverage — build fails if missed.
          All other services: 85% minimum.
          Frontend components: 70% minimum.

Rule 11 — Spec First: A spec file must exist in specs/ before
          any feature implementation begins. No exceptions.

Rule 12 — Branch Per Feature: Every feature is developed on its
          own branch named feature/{feature-name}. Never commit
          feature code directly to main.

Rule 13 — Conflict Flagging: If any instruction conflicts with
          a locked decision in plan.md, output a clearly labelled
          ⚠ CONFLICT block describing the issue before generating
          anything. Do not silently deviate.

Rule 14 — Stock Writes via Ledger Only: current_stock on the
          Product model is never written directly. All stock
          changes must go through StockLedgerService. Any direct
          write to current_stock is a critical bug.

Rule 15 — Emails via Temporal Only: SendGrid is never called
          directly from the service layer. All 9 email types are
          sent exclusively via Temporal activities. All failures
          are logged to the email_failure_log table.

Rule 16 — Commit Standards: Every commit message must follow
          conventional commit format. Type must be one of: feat,
          fix, chore, test, docs, refactor, style, ci, perf.
          Husky commit-msg hook enforces this on every commit.
          Never use --no-verify on feature branches. Only
          permitted in genuine emergencies, never on main.

## Architecture

### Backend Layer Diagram
  HTTP Request
      ↓
  Router
  (HTTP handling only — validate input, call service, return envelope)
      ↓
  Service
  (all business logic — owns transactions, raises typed exceptions)
      ↓
  Repository
  (DB access only — never commits, returns SQLAlchemy models)
      ↓
  SQLAlchemy Model → PostgreSQL

  Service also coordinates:
      ├── CacheService → Redis db0 (cache layer, no persistence)
      ├── CacheService → Redis db1 (auth: blacklist, versions,
      │                             rate limits, AOF persistence)
      └── TemporalClient → Temporal Worker
                               ↓
                           Activities
                               ↓
                           SendGrid (email only)
                           StockLedgerService (reorder)

### Frontend Component Hierarchy
  Pages
    └── Organisms (complex composed UI sections)
          └── Molecules (mid-level reusable combinations)
                └── Atoms (smallest single-purpose components)

  Atoms (9):
    StatusBadge, FormInput, EmptyState, LoadingSkeleton,
    ProgressBar, ConfirmationBanner, Tooltip, PageTitle,
    FormSection

  Molecules (10):
    ProductCard, BarcodeInput, CreditWarning, GRNSessionLine,
    POLineSummary, SupplierSelectCard, MetricsHistoryRow,
    BackorderSummaryCard, FormActionBar, DateRangeFilter

  Organisms (10):
    ProductListTable, MultiStepPOWizard, GRNFormSection,
    DashboardGrid, SupplierMetricsTimeline, BackorderListTable,
    StockLedgerTable, AdminUserTable, SystemHealthSection,
    ReportDownloadSection

  Pages (15):
    LoginPage, DashboardPage, ProductListPage, ProductDetailPage,
    SupplierListPage, SupplierDetailPage, POListPage, PODetailPage,
    POCreatePage, GRNListPage, GRNCreatePage, BackorderListPage,
    StockLedgerPage, AdminUsersPage, ReportsPage

## Tech Stack with Exact Versions

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
One branch per feature. Branch naming: feature/{feature-name}
Every feature requires a spec file in specs/ before implementation.
Merge strategy: squash merge to keep main history clean.
If one branch fails after merging, all other branches remain
stable and independently reviewable.
See plan.md Branch Strategy section for complete branch list.

## Spec-First Development Workflow
1. git checkout -b feature/{name}
2. Create specs/phase-{n}-{feature}.spec.md
3. Spec must define: purpose, scope, edge cases, error scenarios,
   acceptance criteria, test cases
4. Implementation begins only after spec is written and confirmed
5. Write unit tests alongside implementation
6. Write integration tests
7. Commit with conventional commit message
8. Output git push command for user to run manually
9. Create PR with descriptive title and scope description
10. Attach review feedback to PR

## Recurring Patterns

### Repository Method Pattern
  async def get_by_id(self, id: UUID) -> Model | None:
      result = await self.session.execute(
          select(Model)
          .where(Model.id == id)
          .where(Model.deleted_at.is_(None))
      )
      return result.scalar_one_or_none()

### Service Method Pattern
  async def do_something(self, data: InputSchema) -> OutputSchema:
      # 1. Validate business rules — raise typed exceptions
      # 2. Call repository methods (read phase)
      # 3. async with self.session.begin():
      #       perform all writes
      # 4. Side effects AFTER commit (cache, emails via Temporal)
      # 5. Return output schema

### Router Endpoint Pattern
  @router.post("/path", response_model=SingleResponse[Schema])
  async def endpoint(
      request: RequestSchema,
      service: ServiceClass = Depends(get_service),
      current_user: User = Depends(get_current_user),
  ) -> SingleResponse[Schema]:
      result = await service.method(request)
      return SingleResponse(data=result)

### React Query Hook Pattern
  export function useProducts(filters: ProductFilters) {
    return useQuery({
      queryKey: ['products', filters],
      queryFn: () => api.getProducts(filters),
      staleTime: 30_000,
    })
  }
  export function useCreateProduct() {
    const queryClient = useQueryClient()
    return useMutation({
      mutationFn: api.createProduct,
      retry: 0,  // 0 retries on all non-idempotent mutations
      onSuccess: () => queryClient.invalidateQueries(['products']),
    })
  }

### Component Four-State Pattern
  export function ProductCard({ id }: Props) {
    const { data, isLoading, isError } = useProduct(id)
    if (isLoading) return <LoadingSkeleton />
    if (isError)   return <EmptyState message="Failed to load" />
    if (!data)     return <EmptyState message="Not found" />
    return <div className={styles.card}>...success state...</div>
  }

### Error Response Envelope Pattern
  {
    "error": {
      "code": "CREDIT_LIMIT_EXCEEDED",
      "message": "Order total exceeds supplier credit limit",
      "details": {
        "credit_limit": 10000.00,
        "order_total": 12500.00,
        "existing_open_po_total": 8000.00
      }
    }
  }

## Critical Business Rules (Never Implement Differently)

- current_stock is never written directly. All stock changes go
  through StockLedgerService. Direct writes are a critical bug.
- Credit check runs inside the PO submit transaction, not before
  opening it. The check and the status change are atomic.
- Worst-metric-wins: a supplier's tier is their lowest-performing
  metric, not an average across metrics.
- Auto-reorder never creates a duplicate PO for the same
  product-supplier combination. Always check for open POs first.
- Emails are always sent via Temporal activities. Never call
  SendGrid directly from the service layer.
- Partial GRN receipt automatically creates a backorder record for
  the outstanding quantity. This is not optional.
- Tier scoring requires minimum 20 PO lines in the evaluation
  period. Below this threshold: InsufficientDataException.
- ConflictException → HTTP 409 on optimistic lock mismatch.
  Frontend must fetch fresh version and retry.
- Soft delete only: never hard delete major entities. Set
  deleted_at. All queries filter WHERE deleted_at IS NULL.
- Migration 011 is idempotent: check for existing admin before
  inserting. Safe to run multiple times.
- tier_locked = true prevents all automatic tier changes. Only
  admin can override manually.
- All monetary and quantity fields use NUMERIC type. Never FLOAT.
- SendGrid runs in sandbox mode in all non-production environments.
- Barcode lookup uses the same code path in dev and prod.
- StockLedger uses cursor-based pagination, not offset.
- CSV reports use StreamingResponse to avoid memory issues.
- user_version in Redis invalidates tokens immediately on role
  change. No waiting for token expiry.
- Rate limit: 5 login attempts per IP per 15 minutes via Redis db1.
- sessionStorage persists GRN session and wizard state across
  page refresh via Zustand persist middleware.
- 0 retries on all non-idempotent mutations in TanStack Query.

## Known Edge Cases Per Feature

### Auth
- Logout from one device must not affect other active sessions.
  Use jti-based blacklist per token, never user-wide invalidation.
- Role changes take effect immediately via user_version increment
  in Redis. Old tokens are rejected on next request.
- Inactive users cannot refresh tokens even with a valid token.
- Blacklist TTL equals remaining token validity, not original TTL.
- Rate limit key uses client IP address, never user identity.

### Products
- Stock can never go negative (NegativeStockNotAllowedException).
- Optimistic lock conflict on concurrent GRN → HTTP 409 → retry.
- Reorder triggers only when stock falls BELOW threshold, not equal.

### Purchase Orders
- Credit check accounts for ALL open POs for the supplier,
  not just the current one being submitted.
- PO can only be cancelled from Draft or Submitted states.
- Acknowledged→Shipped is supplier-driven.
- Shipped→Received is triggered by GRN completion.

### GRN
- A GRN line cannot exceed the ordered quantity on the PO line
  (OverReceiptException).
- Completing a GRN with partial lines auto-creates backorders.
- Barcode scan must match a PO line on the specific PO being
  received, not any open PO.
- GRN session in sessionStorage must be cleared on completion.

### Supplier Tier Scoring
- tier_locked = true: never promote or demote automatically.
- Consecutive streak counters reset on direction change.
- Scoring uses monthly aggregated data only, never raw PO data.
- Less than 20 PO lines in period: InsufficientDataException.

### Temporal Auto-Reorder
- Check for open PO on same product-supplier before creating.
- If preferred supplier is inactive: skip and log. Do not fail.
- Auto-reorder POs start in submitted state, not draft.

### Reports
- Date range too large raises DateRangeTooLargeException.
- Empty result set returns empty CSV with headers, not an error.

## Lessons Learned
Phase 1 — Husky setup: Added pre-commit lint-staged hook, pre-push
  unit test gate, and commit-msg conventional commit enforcement.
  Husky v9 uses core.hooksPath — run npm install in frontend/ to
  activate hooks after cloning. Update this section after every
  phase with concrete lessons.

## Definition of Done
A task is done when ALL of these are true:
  ☐ Spec file exists in specs/ with edge cases and acceptance
    criteria fully described
  ☐ All planned files created with full path comment on line 1
  ☐ Unit tests written and passing (coverage thresholds met)
  ☐ Integration tests written and passing
  ☐ No linting errors (ruff + black for backend, eslint frontend)
  ☐ Feature branch pushed to remote repository
  ☐ Pull request created with descriptive title and scope summary
  ☐ Review feedback documented and attached to the PR
