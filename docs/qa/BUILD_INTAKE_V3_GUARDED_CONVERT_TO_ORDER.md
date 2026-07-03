# BUILD: INTAKE_V3_GUARDED_CONVERT_TO_ORDER

**Date:** 2026-06-18  
**Base commit:** `934b8fc` — guarded accept flow for IV3 priced draft quotes  
**Verdict:** PASS (after tests green)

## Purpose

Enable a guarded, explicit convert flow for **Intake V3 accepted quotes** that creates **Order only** — no ExecutionPlan, ExecutionTask, Inventory mutation, or production start.

## Convert endpoint audit

| Question | Answer |
|----------|--------|
| Existing convert endpoint | `POST /api/v1/entities/orders/from-quote/{quote_id}` (`backend/routers/orders.py`) |
| Quote statuses accepted | `priced`, `accepted` |
| Creates | Order with `status=locked`, `quote_id` linkage, snapshot from `QuoteCalculationSnapshot` in `line_items` |
| Execution / Inventory in endpoint | **No** — Order creation only in reviewed path |
| Duplicate guard | **Yes** — 409 if order already exists for `quote_id` |
| IV3 compatible via existing path? | **No** — IV3 quotes use simplified `line_items` array, not canonical snapshot JSON |

## Order model / linkage audit

| Field | IV3 usage |
|-------|-----------|
| `quote_id` | Set — primary Quote → Order linkage |
| `status` | `locked` (system default for new orders) |
| `snapshot_line_items` | JSON with `intake_v3_order_linkage_v1` marker |
| `notes` | JSON with `intake_v3_order_linkage_v1` (source quote, workspace, flags) |
| `readiness_snapshot` | Minimal IV3 commercial snapshot (totals, no execution) |

## Strategy: **Variant B**

Existing `from-quote` rejected because IV3 `line_items` lack `QuoteCalculationSnapshot`. Guarded service creates Order via `OrdersService.create()` using pricing-review totals + EUR→RON conversion — same commercial totals, no CostEngine re-run.

## Backend

- **Service:** `backend/services/intake_v3_guarded_convert_to_order_service.py`
- **Endpoints:**
  - `GET /api/v1/intake-v3/quotes/{quote_id}/convert-to-order-state`
  - `POST /api/v1/intake-v3/quotes/{quote_id}/convert-to-order`
  - `GET /api/v1/intake-v3/workspaces/{workspace_id}/convert-to-order-state`
  - `POST /api/v1/intake-v3/workspaces/{workspace_id}/convert-to-order`
- **Schemas:** `IntakeV3ConvertToOrderRequest/Response/State`, `IntakeV3ConvertDecisionRecord`, `IntakeV3OrderSnapshotPayload`
- **Notes:** merges `intake_v3_linkage_v1.convert_decision` without removing accept/snapshot/pricing_review
- **Readiness:** after convert → `converted_to_order`, `order_created=true`, `can_convert_now=false`

## Validation (fail-closed)

- IV3 linkage + intake_code prefix
- quote status `accepted`, `accept_decision` present
- `pricing_review_completed=true`, final price present
- all explicit confirmations + non-empty reason
- duplicate order blocked (existing order for quote_id or convert_decision)
- invalid notes JSON blocked before linkage parse
- ExecutionPlan / ExecutionTask / Inventory counts unchanged after convert

## Proof: no Execution / Inventory

Service uses `OrdersService.create()` only. Tests assert ExecutionPlan and Inventory table counts unchanged. Response flags: `execution_plan_created=false`, `execution_task_created=false`, `inventory_mutated=false`, `production_started=false`.

## Boundary

**In scope:** Order creation from IV3 accepted quote via guarded endpoints; quote notes convert_decision; readiness updates  
**Out of scope:** ExecutionPlan, ExecutionTask, Inventory, CostEngine, pricing formulas, production dispatch, generic non-IV3 convert changes

## Tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v3_guarded_convert_to_order.py tests/test_intake_v3_guarded_accept_flow.py tests/test_intake_v3_priced_draft_accept_convert_readiness.py -q
```

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/pages/IntakeV3App.test.tsx src/lib/intakeV3/flowState.test.ts src/lib/intakeV3QuoteCommercialGuard.test.ts src/lib/quoteCommercialGuidance.test.ts
```

## Next build

**Order handoff / production readiness audit** — evaluate production handoff from IV3 Order without auto-creating Execution tasks.

## Recommended commit message

```
feat(intake-v3): add guarded convert to order flow for IV3 accepted quotes
```
