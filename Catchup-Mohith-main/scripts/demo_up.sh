# /home/mohith/Catchup-Mohith/scripts/demo_up.sh
#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if command -v docker-compose >/dev/null 2>&1; then
  compose_cmd="docker-compose"
elif command -v docker >/dev/null 2>&1; then
  compose_cmd="docker compose"
else
  echo "ERROR: docker compose command not found."
  exit 1
fi

host_db_url() {
  local raw="${DATABASE_URL:-}"
  if [ -z "$raw" ] && [ -f .env ]; then
    raw="$(grep -E '^DATABASE_URL=' .env | head -1 | cut -d'=' -f2-)"
  fi
  if [ -z "$raw" ]; then
    echo ""
    return 0
  fi
  printf '%s' "$raw" | sed -E 's/@db(:|\/)/@localhost\1/'
}

activate_venv_if_present() {
  if [ -f "$PROJECT_ROOT/venv/bin/activate" ]; then
    # shellcheck disable=SC1091
    source "$PROJECT_ROOT/venv/bin/activate"
  elif [ -f "$PROJECT_ROOT/.venv/bin/activate" ]; then
    # shellcheck disable=SC1091
    source "$PROJECT_ROOT/.venv/bin/activate"
  fi
}

echo "=== StockBridge Demo Bootstrap ==="
echo "Project root: $PROJECT_ROOT"

echo "[1/8] Checking .env"
if [ ! -f .env ]; then
  if [ -f .env.example ]; then
    cp .env.example .env
    echo "  Created .env from .env.example"
  else
    echo "ERROR: .env and .env.example are missing"
    exit 1
  fi
fi

echo "[2/8] Starting Docker services"
$compose_cmd up -d db redis temporal-server temporal-worker api frontend

echo "[3/8] Waiting for API health"
api_ok=0
for _ in $(seq 1 60); do
  if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
    api_ok=1
    break
  fi
  sleep 2
done
if [ "$api_ok" -ne 1 ]; then
  echo "ERROR: API did not become healthy in time"
  $compose_cmd ps
  exit 1
fi

echo "[4/8] Running Alembic migrations"
if ! $compose_cmd exec -T api alembic -c /app/alembic.ini upgrade head; then
  echo "  In-container migration failed. Falling back to host migration."
  activate_venv_if_present
  HOST_DATABASE_URL="REDACTED_SEE_ENV"
  if [ -z "$HOST_DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL is not configured"
    exit 1
  fi
  DATABASE_URL=REDACTED_SEE_ENV
fi

echo "[5/8] Seeding deterministic demo data"
if ! $compose_cmd exec -T api python /workspace/scripts/seed.py; then
  echo "  In-container seeding failed. Falling back to host seeding."
  activate_venv_if_present
  HOST_DATABASE_URL="REDACTED_SEE_ENV"
  if [ -z "$HOST_DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL is not configured"
    exit 1
  fi
  DATABASE_URL=REDACTED_SEE_ENV
fi

echo "[6/8] Verifying Docker stack"
bash scripts/verify_docker.sh

echo "[7/8] Verifying Temporal worker"
if ! python3 scripts/verify_temporal.py; then
  echo "  WARN: Host Temporal check failed. Trying inside api container..."
  $compose_cmd exec -T api env TEMPORAL_HOST=temporal-server TEMPORAL_PORT=7233 python /workspace/scripts/verify_temporal.py || true
fi

echo "[8/8] Printing demo info"
echo ""
echo "=== Demo Is Ready ==="
echo "Frontend:        http://localhost:5173"
echo "Backend API:     http://localhost:8000"
echo "Swagger Docs:    http://localhost:8000/docs"
echo "Health:          http://localhost:8000/health"
echo "Temporal gRPC:   localhost:7233"
echo ""
echo "Demo Accounts"
echo "  Admin:    admin@stockbridge.com / REDACTED_SEE_ENV"
echo "  Manager:  manager@stockbridge.com / REDACTED_SEE_ENV"
echo "  Staff:    staff@stockbridge.com / REDACTED_SEE_ENV"
echo ""
echo "Quick demo checks"
echo "  1) Login in UI and verify role-based routes"
echo "  2) Hit Swagger: /docs and run auth + products"
echo "  3) Run Postman collection from postman/"
echo "  4) Watch Temporal logs: $compose_cmd logs -f temporal-worker"
