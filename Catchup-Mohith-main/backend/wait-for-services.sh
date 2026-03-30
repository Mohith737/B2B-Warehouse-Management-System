#!/usr/bin/env bash
# backend/wait-for-services.sh
# Polls db, redis, and temporal before starting the api.
set -eu

MAX_RETRIES=30
SLEEP_SECONDS=2
DB_HOST="${DB_HOST:-}"
if [ -z "$DB_HOST" ]; then
  DB_HOST="${DATABASE_HOST:-db}"
fi
REDIS_HOST="${REDIS_HOST:-}"
if [ -z "$REDIS_HOST" ]; then
  REDIS_HOST="${REDIS_HOSTNAME:-redis}"
fi
TEMPORAL_HOST="${TEMPORAL_HOST:-temporal-server}"
TEMPORAL_PORT="${TEMPORAL_PORT:-7233}"

# If URL env vars are set, prefer extracting hostnames from them.
if [ -n "${DATABASE_URL:-}" ]; then
  parsed_db_host="$(printf '%s' "$DATABASE_URL" | sed -n 's|.*://[^@]*@\([^:/?]*\).*|\1|p')"
  if [ -n "$parsed_db_host" ]; then
    DB_HOST="$parsed_db_host"
  fi
fi

if [ -n "${REDIS_URL:-}" ]; then
  parsed_redis_host="$(printf '%s' "$REDIS_URL" | sed -n 's|.*://\([^:/?]*\).*|\1|p')"
  if [ -n "$parsed_redis_host" ]; then
    REDIS_HOST="$parsed_redis_host"
  fi
fi

wait_for_postgres() {
  attempt=1
  while [ "$attempt" -le "$MAX_RETRIES" ]; do
    echo "[postgres] attempt ${attempt}/${MAX_RETRIES}: checking readiness"
    if command -v pg_isready >/dev/null 2>&1; then
      if pg_isready -h "$DB_HOST" -U "$POSTGRES_USER" >/dev/null 2>&1; then
        echo "[postgres] ready"
        return 0
      fi
    elif nc -z "$DB_HOST" 5432 >/dev/null 2>&1; then
      echo "[postgres] ready"
      return 0
    fi
    attempt=$((attempt + 1))
    sleep "$SLEEP_SECONDS"
  done
  echo "[postgres] timed out after ${MAX_RETRIES} attempts" >&2
  exit 1
}

wait_for_redis() {
  attempt=1
  while [ "$attempt" -le "$MAX_RETRIES" ]; do
    echo "[redis] attempt ${attempt}/${MAX_RETRIES}: checking readiness"
    if redis-cli -h "$REDIS_HOST" ping | grep -q '^PONG$'; then
      echo "[redis] ready"
      return 0
    fi
    attempt=$((attempt + 1))
    sleep "$SLEEP_SECONDS"
  done
  echo "[redis] timed out after ${MAX_RETRIES} attempts" >&2
  exit 1
}

wait_for_temporal() {
  attempt=1
  while [ "$attempt" -le "$MAX_RETRIES" ]; do
    echo "[temporal] attempt ${attempt}/${MAX_RETRIES}: checking readiness"
    if nc -z "$TEMPORAL_HOST" "$TEMPORAL_PORT" >/dev/null 2>&1; then
      echo "[temporal] ready"
      return 0
    fi
    attempt=$((attempt + 1))
    sleep "$SLEEP_SECONDS"
  done
  echo "[temporal] timed out after ${MAX_RETRIES} attempts" >&2
  exit 1
}

wait_for_postgres
wait_for_redis
wait_for_temporal

exec "$@"
