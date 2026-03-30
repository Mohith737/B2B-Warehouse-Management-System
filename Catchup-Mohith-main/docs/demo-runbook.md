<!-- /home/mohith/Catchup-Mohith/docs/demo-runbook.md -->
# StockBridge Demo Runbook (30 Minutes)

## 1. Demo Bootstrap (5 minutes)

```bash
cd ~/Catchup-Mohith
docker compose up -d
docker compose exec -T api alembic -c /app/alembic.ini upgrade head
docker compose exec -T api python /workspace/scripts/seed.py
bash scripts/verify_docker.sh
python3 scripts/verify_temporal.py
```

Open:
- UI: `http://localhost:5173`
- API docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`

Seed users:
- Admin: `admin@stockbridge.com` / `REDACTED_SEE_ENV`
- Procurement Manager: `manager@stockbridge.com` / `REDACTED_SEE_ENV`
- Warehouse Staff: `staff@stockbridge.com` / `REDACTED_SEE_ENV`

## 2. Suggested Demo Timeline (30 minutes)

### 0:00 - 3:00 Login + RBAC
- Login as `admin`.
- Show role-based nav breadth (Dashboard, Users, Reports, etc.).
- Logout and login as `warehouse_staff`.
- Show restricted workflow focus (GRN operations).

### 3:00 - 8:00 Product + Supplier Core Features
- `/products`: show stock statuses (stable/warning/critical style).
- `/suppliers`: show supplier details (lead time, credit limit, tiers).
- Explain how this feeds PO validation and reorder logic.

### 8:00 - 14:00 Purchase Order Lifecycle
- `/purchase-orders`: show multiple statuses seeded:
  - draft (`SB-PO-0003`)
  - submitted (`SB-PO-0005`)
  - acknowledged (`SB-PO-0001`)
  - shipped (`SB-PO-0004`) for GRN start
  - received (`SB-PO-0002`)
- Explain state machine path: `Draft -> Submitted -> Acknowledged -> Shipped -> Received -> Closed`.

### 14:00 - 22:00 GRN + Barcode + Negative Paths
- Login as `warehouse_staff`, open `/grns`.
- Select shipped PO (`SB-PO-0004`) and click `Start GRN`.
- In scanner:
  - Positive scan barcode: `8900000000011` (product 11).
  - Positive scan barcode: `8900000000012` (product 12).
- Mock keyboard scanner (dev simulator box):
  - type `MOCK-DEMO-001` then Enter to simulate scanner input.
- Negative path 1 (invalid barcode):
  - scan `9999999999999` and show handled error toast/message.
- Negative path 2 (barcode mismatch):
  - scan a valid barcode not in this PO, e.g. `8900000000003`.
- Complete GRN and show processed summary/backorder behavior.

### 22:00 - 26:00 Stock Ledger + Backorders + Auditability
- `/stock-ledger`: show clean net movement formatting and movement history.
- Highlight audit fields: reason/change type, timestamps, references.
- `/backorders`: show open vs closed seeded backorders and handling path.

### 26:00 - 30:00 Engineering Proof (Postman + Temporal)
- Use Postman collection:
  - `postman/stockbridge.postman_collection.json`
  - `postman/stockbridge.postman_environment.json`
- Hit:
  - `POST /auth/login`
  - `GET /purchase-orders/?status=shipped&page=1&page_size=50`
  - `POST /grns/`
  - `POST /grns/{id}/lines`
  - `POST /grns/{id}/complete`
- Temporal proof:
```bash
python3 scripts/verify_temporal.py
docker compose logs temporal-worker --tail=120
```
- Call out schedule IDs in logs:
  - `auto-reorder-schedule`
  - `tier-recalculation-schedule`

## 3. Negative Path Talking Points

- Invalid barcode is handled gracefully (error response, no crash).
- Mismatched barcode vs PO line is rejected.
- GRN complete without valid lines is blocked.
- RBAC: non-admin blocked from admin-only operations.
- Stock movement updates remain auditable in ledger.

## 4. Safety Checklist Before Live Demo

```bash
cd ~/Catchup-Mohith
bash scripts/verify_docker.sh
python3 scripts/verify_temporal.py
curl -sf http://localhost:8000/health
curl -sf http://localhost:5173 >/dev/null
```

If all green, start demo.
