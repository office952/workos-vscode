# Batch PUT Order Financial Immutability Guard

**Date:** 2026-06-30  
**Branch:** `feature/step-7g-commercial-price-proposal`  
**Slice:** 10.1 extension (batch bypass close-out)

## Status

**PASS** — `PUT /api/v1/entities/orders/batch` now enforces the same financial immutability guard as single-order `PUT /{id}`. All contract tests green.

## Scope

- Audit `PUT /orders/batch`
- Narrow guard for financial fields in batch update
- Contract tests in `test_orders_update_immutability.py`
- Local commit (no push)

**Out of scope (forbidden):** UI, mobile, pricing, `/price`, CostEngine, QuoteOrchestrator, ExecutionReality/session logic, order/execution_plan/task creation, DB schema/migration, seed, push, redesign, cleanup.

## Architecture readback summary

Slice 10.1 established `order_immutability_service.py` with:

- Frozen criteria: `locked_at` set, non-empty `snapshot_v2_json`, or status in `locked` / `in_execution` / `completed`
- Blocked fields: `total_amount`, `snapshot_line_items`, `snapshot_version`
- Response: HTTP 422, `ORDER_FINANCIAL_FIELDS_IMMUTABLE`, `blocked_fields[]`, `order_id`

Single-order `PUT /{id}` already called `assert_order_financial_fields_mutable`. Batch `PUT /batch` looped `OrdersService.update` without pre-check — WATCH item from Slice 10.1.

## Batch endpoint audited

| Item | Detail |
|------|--------|
| **Route** | `PUT /api/v1/entities/orders/batch` |
| **Handler** | `update_orderss_batch` in `backend/routers/orders.py` |
| **Schema** | `OrdersBatchUpdateRequest` → `OrdersBatchUpdateItem` → `OrdersUpdateData` (same partial-update shape as single PUT) |
| **Service** | `OrdersService.get_by_id` + `OrdersService.update` per item |
| **Was unprotected** | Yes — financial fields on locked/V2 orders could be mutated via batch |
| **Risk closed** | Pre-flight immutability check on every item before any update; fail-closed on mixed batches |

## What changed

1. **`backend/routers/orders.py`** — `update_orderss_batch`:
   - Two-phase loop: validate all items with `assert_order_financial_fields_mutable`, then apply updates
   - Re-raise `HTTPException` (422) instead of converting to 500
2. **`backend/tests/test_orders_update_immutability.py`** — 8 batch contract cases + batch `/price` absence check

## What not changed

- `order_immutability_service.py` — reused as-is (no logic duplication)
- Single-order PUT behavior unchanged
- Non-financial batch updates unchanged
- Unlocked legacy batch financial updates unchanged
- No schema/migration, no UI, no pricing/CostEngine/QuoteOrchestrator

## Files changed

| File | Change |
|------|--------|
| `backend/routers/orders.py` | Batch pre-flight immutability guard |
| `backend/tests/test_orders_update_immutability.py` | Batch contract tests |
| `docs/worklog/realignment/2026-06-30_batch_put_order_financial_immutability_guard.md` | This worklog |

## Tests / validation

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_orders_update_immutability.py -q
```

**Result:** 16 passed

| # | Case | Expected |
|---|------|----------|
| 1 | batch locked/V2 + `total_amount` | 422 |
| 2 | batch locked/V2 + `snapshot_line_items` | 422 |
| 3 | batch locked/V2 + `snapshot_version` | 422 |
| 4 | batch locked/V2 + `notes` | 200 |
| 5 | batch unlocked legacy + `total_amount` | 200 (prior behavior) |
| 6 | mixed batch locked + unlocked + financial | 422 fail-closed, neither mutated |
| 7 | response contains `ORDER_FINANCIAL_FIELDS_IMMUTABLE` | yes |
| 8 | `snapshot_v2_json` / `accepted_commercial_total` unchanged after block | yes |
| 9–11 | no CostEngine / QuoteOrchestrator / `/price` in slice paths | AST + batch section scan |

Optional related suites not required (no common-code change beyond router guard).

## Runtime status

Backend health check not re-run in this slice (no runtime dependency). Guard is router-level only; dev stack unchanged.

## Guard behavior

For each batch item:

1. Build partial `update_dict` (non-None fields only)
2. Load order via `get_by_id`
3. If order exists → `assert_order_financial_fields_mutable(order, update_dict)`
4. After all items pass → apply updates sequentially

Mixed batch with any frozen order + financial field → entire request rejected with 422 before any DB write.

## Owner verification

Review `backend/tests/test_orders_update_immutability.py` — batch section from `_BATCH_OID_BASE`. Run pytest command above. No browser UI required.

## Forbidden scope confirmation

No touches to UI, mobile, pricing, `/price`, CostEngine, QuoteOrchestrator, ExecutionReality, order/execution_plan/task creation, DB schema, seed, or push.

## Commit

```
fix(orders): guard batch financial updates
```

## What remains

- Step 7G commercial price proposal (NOT STARTED)
- Step 8 DB schema owner decision (parallel track)
- Step 11 UI labels/navigation policy sync

## Next step

**Recommended:** Step 8 DB schema owner decision OR Step 8 docs sync OR Step 11 labels — per roadmap priority.

## Cat sunt in directia stabilita: 73/100%

Batch PUT WATCH from Slice 10.1 closed. Immutability surface for order financial fields now consistent on single and batch PUT. Direction holds; 7G commercial proposal still ahead.
