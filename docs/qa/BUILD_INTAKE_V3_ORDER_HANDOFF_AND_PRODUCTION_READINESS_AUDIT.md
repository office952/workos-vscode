# BUILD: INTAKE_V3_ORDER_HANDOFF_AND_PRODUCTION_READINESS_AUDIT

**Date:** 2026-06-18  
**Base commit:** `2336bbd` — guarded convert to order for IV3 accepted quotes  
**Verdict:** PASS (after tests green)

## Purpose

Read-only production handoff readiness audit for IV3 Orders created via guarded convert — blockers, available data, handoff preview, task/material preview contracts. No Execution/Inventory/production start.

## Order IV3 audit

| Field | Location after guarded convert |
|-------|-------------------------------|
| `quote_id` | `orders.quote_id` |
| IV3 order linkage | `orders.notes` + `snapshot_line_items.intake_v3_order_linkage_v1` |
| Commercial snapshot | `orders.snapshot_line_items` (intake_v3_guarded_convert_order_snapshot_v1) |
| Production truth | `quotes.notes.intake_v3_linkage_v1.snapshot.sections.*` |
| Confirmed model | `confirmed_production_model_snapshot` |
| Finish assignments | `finish_assignment_snapshot` (+ workspace payload fallback) |
| Accept/convert audit | `accept_decision`, `convert_decision` in quote linkage |

## Production readiness model

Statuses: `not_iv3_order`, `missing_order`, `missing_quote_linkage`, `missing_intake_v3_linkage`, `missing_confirmed_production_model`, `missing_finish_assignments`, `missing_pricing_review`, `missing_accept_decision`, `missing_convert_decision`, `ready_for_handoff_preview`, `blocked`.

All action flags hardcoded **false**: `can_generate_execution_plan_now`, `can_generate_execution_tasks_now`, `can_mutate_inventory_now`, `can_start_production_now`.

## Backend

- **Service:** `backend/services/intake_v3_order_production_readiness_service.py` (read-only)
- **Endpoints:**
  - `GET /api/v1/intake-v3/orders/{order_id}/production-readiness`
  - `GET /api/v1/intake-v3/quotes/{quote_id}/order-production-readiness`
  - `GET /api/v1/intake-v3/workspaces/{workspace_id}/order-production-readiness`
- **Readiness service update:** `IntakeV3PricedDraftAcceptConvertReadiness` includes production fields when order exists

## Finish assignments decision (12.6)

**Blocking** if neither `finish_assignment_snapshot` nor workspace `finish_assignment` present. **Warning** (`finish_assignments_snapshot_incomplete`) if workspace payload has finish data but snapshot section missing.

## Accept decision

Production handoff requires **explicit** `accept_decision.status=approved` — quote status alone is insufficient.

## Task / material preview contracts

- Task groups derived from `build_task_seed_candidates(workspace)` when workspace payload in snapshot; fallback static list otherwise
- Materials from `derive_material_intent` + baseline list; `material_cost_breakdown=future_build`, `inventory_mutation_allowed=false`

## Boundary

**In scope:** GET readiness audit, UI panel, guidance/badges, docs  
**Out of scope:** ExecutionPlan, ExecutionTask, Inventory, production start, CostEngine, material cost breakdown calculator

## Tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v3_order_production_readiness.py tests/test_intake_v3_guarded_convert_to_order.py tests/test_intake_v3_guarded_accept_flow.py tests/test_intake_v3_priced_draft_accept_convert_readiness.py -q
```

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/pages/IntakeV3App.test.tsx src/lib/intakeV3/flowState.test.ts src/lib/intakeV3QuoteCommercialGuard.test.ts src/lib/quoteCommercialGuidance.test.ts
```

## Next build options

1. Material quantity + geometry + material cost breakdown (informative)
2. Production task generation dry-run contract
3. Guarded production handoff foundation

## Recommended commit message

```
feat(intake-v3): add order production readiness audit for IV3 converted orders
```
