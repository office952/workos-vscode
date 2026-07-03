# Slice 10.1 — Order Financial Immutability Guard

**Date:** 2026-06-30  
**Repo:** `C:\Users\offic\Desktop\workos-active`  
**Branch:** `feature/step-7g-commercial-price-proposal`  
**Scope:** PUT `/api/v1/entities/orders/{id}` only — no UI, no profitability service, no CostEngine

---

## Purpose

Fail-closed guard blocking mutation of financial snapshot fields on locked or V2 orders. Protects `accepted_commercial_total` (inside `snapshot_v2_json`) and legacy `total_amount` / `snapshot_line_items` from silent PUT updates before Step 10 profitability work.

---

## Implementation

| Item | Detail |
|------|--------|
| Service | `backend/services/order_immutability_service.py` |
| Router hook | `backend/routers/orders.py` — `update_orders` calls `assert_order_financial_fields_mutable` before `OrdersService.update` |
| Blocked fields | `total_amount`, `snapshot_line_items`, `snapshot_version` |
| Frozen when | `locked_at` set, non-empty `snapshot_v2_json`, or status in `locked` / `in_execution` / `completed` |
| HTTP | **422** `ORDER_FINANCIAL_FIELDS_IMMUTABLE` with `blocked_fields` list |
| Allowed | `notes`, `promised_delivery`, `payment_status`, `job_id`, status transitions per lifecycle |

---

## Tests

**File:** `backend/tests/test_orders_update_immutability.py`

| Case | Expected |
|------|----------|
| V2 locked + `total_amount` | 422 |
| V2 locked + `snapshot_line_items` | 422 |
| V2 locked + `snapshot_version` | 422 |
| V2 locked + `notes` | 200; `snapshot_v2_json` and `accepted_commercial_total` unchanged |
| Unlocked legacy + `total_amount` | 200 (legacy behavior preserved) |
| Locked legacy + financial field | 422 |
| Locked legacy + `notes` | 200 |
| Forbidden imports | No CostEngine / QuoteOrchestrator in slice paths |

**Command:** `cd backend && .\.venv\Scripts\python.exe -m pytest tests/test_orders_update_immutability.py -q`  
**Result:** 8 passed

**Optional regression:** `test_execution_plan_v2_persist.py` + `test_execution_plan_v2_materialize.py` — run after commit if needed.

---

## Files changed

- `backend/services/order_immutability_service.py` (new)
- `backend/routers/orders.py` (guard + single fetch for status/immutability)
- `backend/tests/test_orders_update_immutability.py` (new)
- `docs/worklog/realignment/2026-06-30_slice_10_1_order_financial_immutability_guard.md` (this file)

---

## Boundary / not in scope

- Batch PUT `/orders/batch` (unchanged — narrow slice)
- ProfitabilityAnalysis, UI, pricing, `/price`, CostEngine, QuoteOrchestrator
- ExecutionReality / session changes, migrations, seeds

---

## Next step

Owner GO for **Slice 10.2 + 10.3** — `ProfitabilityAnalysisService` read-only contract + GET endpoint with tests.
