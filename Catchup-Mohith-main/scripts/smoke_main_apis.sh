# scripts/smoke_main_apis.sh
#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"

ADMIN_EMAIL="${ADMIN_EMAIL:-admin@stockbridge.com}"
ADMIN_PASSWORD=REDACTED_SEE_ENV
MANAGER_EMAIL="${MANAGER_EMAIL:-manager@stockbridge.com}"
MANAGER_PASSWORD=REDACTED_SEE_ENV
STAFF_EMAIL="${STAFF_EMAIL:-staff@stockbridge.com}"
STAFF_PASSWORD=REDACTED_SEE_ENV

HAS_JQ=0
if command -v jq >/dev/null 2>&1; then
  HAS_JQ=1
fi

pass=0
fail=0

check() {
  local name="$1"
  local expected="$2"
  local actual="$3"

  if [ "$actual" = "$expected" ]; then
    echo "  PASS: $name"
    pass=$((pass + 1))
  else
    echo "  FAIL: $name (expected=$expected, actual=$actual)"
    fail=$((fail + 1))
  fi
}

contains_text() {
  local haystack="$1"
  local needle="$2"
  if printf '%s' "$haystack" | grep -q "$needle"; then
    printf 'yes'
  else
    printf 'no'
  fi
}

json_get() {
  local json="$1"
  local jq_expr="$2"
  local grep_key="$3"

  if [ "$HAS_JQ" -eq 1 ]; then
    printf '%s' "$json" | jq -r "$jq_expr" 2>/dev/null || true
  else
    printf '%s' "$json" | grep -oE '"'"$grep_key"'"\s*:\s*"[^"]*"' | head -1 | sed -E 's/.*"[^"]*"\s*:\s*"([^"]*)"/\1/'
  fi
}

api_request() {
  local method="$1"
  local url="$2"
  local token="${3:-}"
  local data="${4:-}"

  local headers_file
  local body_file
  headers_file="$(mktemp)"
  body_file="$(mktemp)"

  local curl_args
  curl_args=(
    -sS
    -X "$method"
    "$url"
    -D "$headers_file"
    -o "$body_file"
  )

  if [ -n "$token" ]; then
    curl_args+=( -H "Authorization: Bearer $token" )
  fi

  if [ -n "$data" ]; then
    curl_args+=( -H "Content-Type: application/json" -d "$data" )
  fi

  RESP_STATUS="$(curl "${curl_args[@]}" -w "%{http_code}")"
  RESP_BODY="$(cat "$body_file")"
  RESP_HEADERS="$(cat "$headers_file")"

  rm -f "$headers_file" "$body_file"
}

extract_token() {
  local json="$1"
  if [ "$HAS_JQ" -eq 1 ]; then
    printf '%s' "$json" | jq -r '.data.access_token // empty' 2>/dev/null
  else
    printf '%s' "$json" | grep -oE '"access_token"\s*:\s*"[^"]+"' | head -1 | sed -E 's/.*"access_token"\s*:\s*"([^"]+)"/\1/'
  fi
}

extract_refresh() {
  local json="$1"
  if [ "$HAS_JQ" -eq 1 ]; then
    printf '%s' "$json" | jq -r '.data.refresh_token // empty' 2>/dev/null
  else
    printf '%s' "$json" | grep -oE '"refresh_token"\s*:\s*"[^"]+"' | head -1 | sed -E 's/.*"refresh_token"\s*:\s*"([^"]+)"/\1/'
  fi
}

echo "Running smoke tests against: $BASE_URL"
echo "jq parser: $([ "$HAS_JQ" -eq 1 ] && echo "enabled" || echo "grep fallback")"

# Login admin -> capture ADMIN_TOKEN
api_request POST "$BASE_URL/auth/login" "" "{\"email\":\"$ADMIN_EMAIL\",\"password\":\"$ADMIN_PASSWORD\"}"
check "auth_login_admin_status" "200" "$RESP_STATUS"
ADMIN_TOKEN="$(extract_token "$RESP_BODY")"
ADMIN_REFRESH="$(extract_refresh "$RESP_BODY")"
check "auth_login_admin_token_present" "yes" "$( [ -n "$ADMIN_TOKEN" ] && echo yes || echo no )"

# Login manager -> capture MANAGER_TOKEN
api_request POST "$BASE_URL/auth/login" "" "{\"email\":\"$MANAGER_EMAIL\",\"password\":\"$MANAGER_PASSWORD\"}"
check "auth_login_manager_status" "200" "$RESP_STATUS"
MANAGER_TOKEN="$(extract_token "$RESP_BODY")"
MANAGER_REFRESH="$(extract_refresh "$RESP_BODY")"
check "auth_login_manager_token_present" "yes" "$( [ -n "$MANAGER_TOKEN" ] && echo yes || echo no )"

# Login staff -> capture STAFF_TOKEN
api_request POST "$BASE_URL/auth/login" "" "{\"email\":\"$STAFF_EMAIL\",\"password\":\"$STAFF_PASSWORD\"}"
check "auth_login_staff_status" "200" "$RESP_STATUS"
STAFF_TOKEN="$(extract_token "$RESP_BODY")"
STAFF_REFRESH="$(extract_refresh "$RESP_BODY")"
check "auth_login_staff_token_present" "yes" "$( [ -n "$STAFF_TOKEN" ] && echo yes || echo no )"

# Auth bad password
api_request POST "$BASE_URL/auth/login" "" "{\"email\":\"$ADMIN_EMAIL\",\"password\":\"WrongPassword!\"}"
check "auth_login_bad_password_401" "401" "$RESP_STATUS"

# No /auth/me endpoint exists; validate tokens on protected dashboard endpoint.
api_request GET "$BASE_URL/dashboard" "$ADMIN_TOKEN"
check "auth_token_admin_dashboard_200" "200" "$RESP_STATUS"

api_request GET "$BASE_URL/dashboard" "$MANAGER_TOKEN"
check "auth_token_manager_dashboard_200" "200" "$RESP_STATUS"

api_request GET "$BASE_URL/dashboard" "$STAFF_TOKEN"
check "auth_token_staff_dashboard_200" "200" "$RESP_STATUS"

# Products
api_request GET "$BASE_URL/products?page=1&page_size=20" "$ADMIN_TOKEN"
check "products_list_status" "200" "$RESP_STATUS"
check "products_list_has_data" "yes" "$(contains_text "$RESP_BODY" '"data":[')"

PRODUCT_ID="$(json_get "$RESP_BODY" '.data[0].id // empty' 'id')"
PRODUCT_BARCODE=""
if [ "$HAS_JQ" -eq 1 ]; then
  PRODUCT_BARCODE="$(printf '%s' "$RESP_BODY" | jq -r '.data[0].barcode // empty')"
else
  PRODUCT_BARCODE="$(printf '%s' "$RESP_BODY" | grep -oE '"barcode"\s*:\s*"[^"]*"' | head -1 | sed -E 's/.*"barcode"\s*:\s*"([^"]*)"/\1/')"
fi

NEW_PRODUCT_SKU="SB-SMOKE-$(date +%s)"
api_request POST "$BASE_URL/products" "$ADMIN_TOKEN" "{\"sku\":\"$NEW_PRODUCT_SKU\",\"name\":\"Smoke Product\",\"description\":\"Smoke test product\",\"unit_of_measure\":\"pcs\",\"reorder_point\":5,\"reorder_quantity\":10,\"unit_price\":12.5,\"barcode\":\"$NEW_PRODUCT_SKU\"}"
check "products_create_admin_status" "201" "$RESP_STATUS"
check "products_create_admin_id_present" "yes" "$(contains_text "$RESP_BODY" '"id":"')"

api_request POST "$BASE_URL/products" "$STAFF_TOKEN" "{\"sku\":\"$NEW_PRODUCT_SKU-STF\",\"name\":\"Denied Product\",\"unit_of_measure\":\"pcs\",\"reorder_point\":5,\"reorder_quantity\":10,\"unit_price\":12.5}"
check "products_create_staff_forbidden" "403" "$RESP_STATUS"

# Suppliers
api_request GET "$BASE_URL/suppliers?page=1&page_size=20" "$MANAGER_TOKEN"
check "suppliers_list_status" "200" "$RESP_STATUS"
check "suppliers_list_has_data" "yes" "$(contains_text "$RESP_BODY" '"data":[')"

SUPPLIER_ID="$(json_get "$RESP_BODY" '.data[0].id // empty' 'id')"
NEW_SUPPLIER_EMAIL="smoke-supplier-$(date +%s)@example.com"
api_request POST "$BASE_URL/suppliers" "$MANAGER_TOKEN" "{\"name\":\"Smoke Supplier\",\"email\":\"$NEW_SUPPLIER_EMAIL\",\"phone\":\"+1-555-2000\",\"address\":\"Smoke Street\",\"payment_terms_days\":30,\"lead_time_days\":7,\"credit_limit\":25000}"
check "suppliers_create_manager_status" "201" "$RESP_STATUS"
check "suppliers_create_manager_id_present" "yes" "$(contains_text "$RESP_BODY" '"id":"')"

api_request POST "$BASE_URL/suppliers" "$STAFF_TOKEN" "{\"name\":\"Denied Supplier\",\"email\":\"denied-$(date +%s)@example.com\",\"credit_limit\":1000}"
check "suppliers_create_staff_forbidden" "403" "$RESP_STATUS"

# Purchase orders
api_request GET "$BASE_URL/purchase-orders?page=1&page_size=20" "$MANAGER_TOKEN"
check "purchase_orders_list_status" "200" "$RESP_STATUS"

if [ -z "$SUPPLIER_ID" ]; then
  SUPPLIER_ID="$(json_get "$RESP_BODY" '.data[0].supplier_id // empty' 'supplier_id')"
fi

if [ -z "$PRODUCT_ID" ]; then
  api_request GET "$BASE_URL/products?page=1&page_size=20" "$MANAGER_TOKEN"
  PRODUCT_ID="$(json_get "$RESP_BODY" '.data[0].id // empty' 'id')"
fi

PO_CREATE_PAYLOAD="{\"supplier_id\":\"$SUPPLIER_ID\",\"notes\":\"Smoke PO\",\"lines\":[{\"product_id\":\"$PRODUCT_ID\",\"quantity_ordered\":5,\"unit_price\":10.0}]}"
api_request POST "$BASE_URL/purchase-orders" "$MANAGER_TOKEN" "$PO_CREATE_PAYLOAD"
check "purchase_orders_create_manager_status" "201" "$RESP_STATUS"
NEW_PO_ID="$(json_get "$RESP_BODY" '.data.id // empty' 'id')"
NEW_PO_NUMBER="$(json_get "$RESP_BODY" '.data.po_number // empty' 'po_number')"
check "purchase_orders_po_number_prefix" "yes" "$(printf '%s' "$NEW_PO_NUMBER" | grep -q '^SB-' && echo yes || echo no)"

api_request POST "$BASE_URL/purchase-orders" "$STAFF_TOKEN" "$PO_CREATE_PAYLOAD"
check "purchase_orders_create_staff_forbidden" "403" "$RESP_STATUS"

api_request POST "$BASE_URL/purchase-orders/$NEW_PO_ID/submit" "$MANAGER_TOKEN"
check "purchase_orders_submit_status" "200" "$RESP_STATUS"

api_request POST "$BASE_URL/purchase-orders/$NEW_PO_ID/acknowledge" "$MANAGER_TOKEN"
check "purchase_orders_acknowledge_status" "200" "$RESP_STATUS"

api_request POST "$BASE_URL/purchase-orders/$NEW_PO_ID/mark-shipped" "$MANAGER_TOKEN"
check "purchase_orders_mark_shipped_status" "200" "$RESP_STATUS"

api_request GET "$BASE_URL/purchase-orders/$NEW_PO_ID" "$MANAGER_TOKEN"
check "purchase_orders_get_by_id_status" "200" "$RESP_STATUS"

# GRNs
api_request POST "$BASE_URL/grns" "$STAFF_TOKEN" "{\"po_id\":\"$NEW_PO_ID\"}"
check "grns_create_status" "201" "$RESP_STATUS"
NEW_GRN_ID="$(json_get "$RESP_BODY" '.data.id // empty' 'id')"

api_request GET "$BASE_URL/grns/$NEW_GRN_ID" "$STAFF_TOKEN"
check "grns_get_by_id_status" "200" "$RESP_STATUS"

GRN_LINE_PAYLOAD="{\"product_id\":\"$PRODUCT_ID\",\"quantity_received\":5,\"unit_cost\":10.0,\"barcode_scanned\":\"$PRODUCT_BARCODE\"}"
api_request POST "$BASE_URL/grns/$NEW_GRN_ID/lines" "$STAFF_TOKEN" "$GRN_LINE_PAYLOAD"
check "grns_receive_line_status" "201" "$RESP_STATUS"

api_request POST "$BASE_URL/grns/$NEW_GRN_ID/complete" "$MANAGER_TOKEN"
check "grns_complete_status" "200" "$RESP_STATUS"

# Stock ledger
api_request GET "$BASE_URL/stock-ledger?limit=20" "$MANAGER_TOKEN"
check "stock_ledger_list_status" "200" "$RESP_STATUS"
check "stock_ledger_has_data" "yes" "$(contains_text "$RESP_BODY" '"data":[')"

# Dashboard
api_request GET "$BASE_URL/dashboard" "$STAFF_TOKEN"
check "dashboard_staff_status" "200" "$RESP_STATUS"
check "dashboard_staff_total_products" "yes" "$(contains_text "$RESP_BODY" '"total_products"')"

api_request GET "$BASE_URL/dashboard" "$MANAGER_TOKEN"
check "dashboard_manager_status" "200" "$RESP_STATUS"
check "dashboard_manager_open_pos" "yes" "$(contains_text "$RESP_BODY" '"open_pos"')"

api_request GET "$BASE_URL/dashboard" "$ADMIN_TOKEN"
check "dashboard_admin_status" "200" "$RESP_STATUS"
check "dashboard_admin_system_health" "yes" "$(contains_text "$RESP_BODY" '"system_health"')"

api_request GET "$BASE_URL/dashboard/low-stock?page=1&page_size=20" "$MANAGER_TOKEN"
check "dashboard_low_stock_status" "200" "$RESP_STATUS"
check "dashboard_low_stock_has_data_field" "yes" "$(contains_text "$RESP_BODY" '"data":[')"

# Reports
if [ -z "$SUPPLIER_ID" ]; then
  api_request GET "$BASE_URL/suppliers?page=1&page_size=1" "$MANAGER_TOKEN"
  SUPPLIER_ID="$(json_get "$RESP_BODY" '.data[0].id // empty' 'id')"
fi

api_request GET "$BASE_URL/reports/suppliers/$SUPPLIER_ID?months=12" "$MANAGER_TOKEN"
check "reports_supplier_status" "200" "$RESP_STATUS"
check "reports_supplier_content_type_csv" "yes" "$(contains_text "$RESP_HEADERS" 'text/csv')"

# Health
api_request GET "$BASE_URL/health" "" ""
check "health_status" "200" "$RESP_STATUS"

# Optional extra auth check: refresh token flow
api_request POST "$BASE_URL/auth/refresh" "" "{\"refresh_token\":\"$ADMIN_REFRESH\"}"
check "auth_refresh_admin_status" "200" "$RESP_STATUS"


echo ""
echo "Results: $pass passed, $fail failed"
if [ "$fail" -eq 0 ]; then
  exit 0
fi
exit 1
