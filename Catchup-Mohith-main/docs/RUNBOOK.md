<!-- docs/RUNBOOK.md -->
# StockBridge Developer Runbook

## Prerequisites
- Docker and Docker Compose
- Python 3.11
- Node.js 20
- pnpm (9+ recommended)
- PostgreSQL client tools (`psql`) and Redis CLI (`redis-cli`) are helpful for debugging

## First-time setup
1. Clone and enter the repository:
```bash
git clone <repo-url>
cd Catchup-Mohith
```
2. Create local env file:
```bash
cp .env.example .env
```
3. Edit `.env` and set real values for at least:
- `SECRET_KEY`
- `SENDGRID_API_KEY`
- `SENDGRID_FROM_EMAIL`
- `INITIAL_ADMIN_PASSWORD`
- `DATABASE_URL`
- `REDIS_URL`

4. Install frontend dependencies:
```bash
cd client
pnpm install
cd ..
```

5. Install backend dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
if [ -f backend/requirements.txt ]; then
  pip install -r backend/requirements.txt
else
  pip install fastapi "uvicorn[standard]" sqlalchemy asyncpg alembic pydantic pydantic-settings python-jose "passlib[bcrypt]" redis python-dotenv httpx pytest pytest-asyncio ruff black
fi
```

## Running the full stack locally
1. Start infrastructure services:
```bash
docker compose up -d postgres redis temporal-server
```

2. Run migrations:
```bash
PYTHONPATH=. alembic -c backend/alembic.ini upgrade head
```

3. Seed deterministic demo/test data:
```bash
python3 scripts/seed.py
```

4. Start backend API:
```bash
PYTHONPATH=. uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

5. Start frontend in another terminal:
```bash
cd client
pnpm dev
```

6. Open app:
- Frontend: `http://localhost:5173`
- Backend docs (if debug enabled): `http://localhost:8000/docs`

## Running backend tests
### Unit tests
```bash
PYTHONPATH=. python3 -m pytest backend/tests/unit/ -v --tb=short
```

### Integration tests
- Ensure test database is reachable.
- Set `TEST_DATABASE_URL` (or rely on default in test config).

```bash
PYTHONPATH=. python3 -m pytest backend/tests/integration/ -v --tb=short
```

### Lint backend
```bash
ruff check backend/
black --check backend/
```

## Running frontend E2E tests
1. Ensure backend is running and seeded.
2. Ensure frontend is running.
3. Run E2E suite:
```bash
cd client
pnpm test:e2e
```

## Seed script usage
Run from repository root:
```bash
python3 scripts/seed.py
```

Properties:
- Deterministic IDs via `seed_uuid()`
- Idempotent inserts (safe to run multiple times)
- Seeds users, suppliers, products, purchase orders, GRNs, and ledger entries

## Smoke test usage
Run from repository root after backend is up and seed is loaded:
```bash
bash scripts/smoke_main_apis.sh
```

Useful overrides:
```bash
BASE_URL=http://localhost:8000 \
ADMIN_EMAIL=admin@stockbridge.com \
ADMIN_PASSWORD=REDACTED_SEE_ENV
bash scripts/smoke_main_apis.sh
```

## Verifying Temporal Worker
```bash
python3 scripts/verify_temporal.py
```

Expected output:
```text
  PASS: Connected to Temporal
  PASS: Task queue 'stockbridge-main' is reachable
  All Temporal checks passed.
```

## Environment variables reference
| Variable | Required | Example | Purpose |
|---|---|---|---|
| `DATABASE_URL` | Yes | `postgresql+asyncpg://stockbridge:stockbridge@localhost:5432/stockbridge` | Main backend database |
| `TEST_DATABASE_URL` | For integration tests | `postgresql+asyncpg://stockbridge:stockbridge@localhost:5432/stockbridge_test` | Test database |
| `POSTGRES_USER` | Yes | `stockbridge` | Postgres user |
| `POSTGRES_PASSWORD` | Yes | `stockbridge` | Postgres password |
| `POSTGRES_DB` | Yes | `stockbridge` | Postgres database |
| `REDIS_URL` | Yes | `redis://localhost:6379` | Redis connection |
| `SECRET_KEY` | Yes | `replace-with-strong-random` | JWT signing key |
| `ALGORITHM` | No | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `60` | Access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | `7` | Refresh token TTL |
| `AUTH_RATE_LIMIT_ATTEMPTS` | No | `5` | Login rate limit attempts |
| `AUTH_RATE_LIMIT_WINDOW_SECONDS` | No | `900` | Rate limit window |
| `TEMPORAL_HOST` | Yes | `localhost` | Temporal host |
| `TEMPORAL_PORT` | Yes | `7233` | Temporal port |
| `TEMPORAL_NAMESPACE` | No | `default` | Temporal namespace |
| `TEMPORAL_TASK_QUEUE` | Yes (worker config) | `stockbridge-main` | Temporal worker task queue |
| `SENDGRID_API_KEY` | In non-local/email tests | `SG....` | SendGrid API key |
| `SENDGRID_FROM_EMAIL` | In non-local/email tests | `noreply@example.com` | Sender address |
| `INITIAL_ADMIN_EMAIL` | No | `admin@stockbridge.local` | Bootstrap admin email |
| `INITIAL_ADMIN_PASSWORD` | Yes | `ChangeMe!` | Bootstrap admin password |
| `CORS_ORIGINS` | Yes | `http://localhost:5173` or `["http://localhost:5173"]` | Allowed frontend origins |

## Common issues and fixes
### 1) `CORS_ORIGINS` parsing error in tests/CI
Symptom:
- `pydantic_settings ... error parsing value for field "cors_origins"`

Fix:
- Use JSON array form in env when needed:
```bash
export CORS_ORIGINS='["http://localhost:5173"]'
```
- Or set comma-separated list in `.env` consistent with parser expectations.

### 2) Temporal worker task queue mismatch
Symptom:
- Workflows enqueue but are never processed.

Fix:
- Ensure both backend and worker use the same `TEMPORAL_TASK_QUEUE` value.
- Verify `.env` contains:
```bash
TEMPORAL_TASK_QUEUE=stockbridge-main
```
- Restart worker after changes.

### 3) `pnpm install` network errors/timeouts
Symptom:
- `ERR_PNPM_FETCH_*`, `ECONNRESET`, or registry timeout.

Fix:
```bash
pnpm config set fetch-retries 5
pnpm config set fetch-timeout 120000
pnpm store prune
pnpm install --frozen-lockfile
```
- If behind a corporate proxy, set npm/pnpm proxy config before install.


