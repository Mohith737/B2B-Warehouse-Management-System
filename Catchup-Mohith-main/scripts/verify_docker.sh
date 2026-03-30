# /home/mohith/Catchup-Mohith/scripts/verify_docker.sh
#!/usr/bin/env bash
set -euo pipefail

pass=0
fail=0

if command -v docker-compose >/dev/null 2>&1; then
  compose_cmd="docker-compose"
else
  compose_cmd="docker compose"
fi

check() {
  local name="$1"
  local result="$2"
  if [ "$result" = "0" ]; then
    echo "  PASS: $name"
    pass=$((pass + 1))
  else
    echo "  FAIL: $name"
    fail=$((fail + 1))
  fi
}

echo "=== Docker Stack Verification ==="

for service in db redis temporal-server api frontend; do
  running="$($compose_cmd ps --services --filter "status=running" 2>/dev/null | grep -c "^${service}$" || true)"
  if [ "$running" = "1" ]; then
    check "$service is running" "0"
  else
    check "$service is running" "1"
  fi
done

if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
  check "Backend health endpoint" "0"
else
  check "Backend health endpoint" "1"
fi

if curl -sf http://localhost:5173 >/dev/null 2>&1 || curl -sf http://localhost:80 >/dev/null 2>&1; then
  check "Frontend serving" "0"
else
  check "Frontend serving" "1"
fi

echo ""
echo "Results: $pass passed, $fail failed"
if [ "$fail" -eq 0 ]; then
  exit 0
fi
exit 1
