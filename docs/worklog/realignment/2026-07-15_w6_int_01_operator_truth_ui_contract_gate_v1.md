# W6-INT-01 — Operator execution truth and blocker visibility gate

**Date:** 2026-07-15  
**Task:** W6-INT-01 `OPERATOR_EXECUTION_TRUTH_AND_BLOCKER_VISIBILITY_GATE_V1`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Starting HEAD:** `da381c1`  
**Trusted backend:** `http://127.0.0.1:8001`  
**Frontend:** `http://127.0.0.1:3000`  
**Gate order:** `23099` (`ORD-W5INT02-GATE`)  
**Verdict:** `W6_INT_01_PASS_WITH_BACKEND_PREREQUISITE`

## Summary

Backend frozen-to-runtime truth is **strong** after Wave 5. Operator desktop UI **partially** surfaces readiness via production-blueprint, but **does not** expose `frozen_task_identity/v1`, production-release owner decisions, or a unified canonical read model. Wave 6 implementation is authorized **only after** a backend read-model prerequisite (W6-T01).

## Primary question answers

| # | Question | Answer |
|---|----------|--------|
| 1 | Desktop pages showing ExecutionPlan tasks | `/execution/:order_id`, `/operator` (blueprint + assignment list), `/shop-floor` (machine mapping only), `/execution` dashboard |
| 2 | Canonical operator start surface | **`/execution/:order_id`** (admin mutation + blueprint prefetch); operator `/operator` uses same `task-action` but weaker error surfacing |
| 3 | ShopFloor read vs mutation | **Read-only** machine dashboard; no task start |
| 4 | `frozen_task_identity/v1` on frontend | **None** — zero TS references; only on `GET /api/v1/execution/plan/{order_id}` |
| 5 | Component role visible | **NO** |
| 6 | Component template identity visible | **NO** (only embedded in raw `task_id` string) |
| 7 | Source operation / task rule visible | **PARTIAL** — `process_type` + display name; no explicit task-rule source field |
| 8 | Dependencies visible | **PARTIAL** — blueprint `blocking_tasks`, `readiness_reasons` |
| 9 | Startability before Start | **PARTIAL** — blueprint + ExecutionDetail prefetch; operator main timeline does not show `is_startable` |
| 10 | Production blockers translated | **NO UI** — API `production-release-status` only |
| 11 | Unresolved owner decisions listed | **NO** |
| 12 | Acknowledgement vs resolution | **NOT distinguishable** in UI |
| 13 | Manager resolve via existing UI | **NO** — `POST .../owner-decisions/{code}/resolve` has no frontend client |
| 14 | Resolver / audit visible | **NO** |
| 15 | Partial 7H vs client price | **PARTIAL** — ExecutionDetail profitability panel separates accepted revenue vs estimated internal cost |
| 16 | Execution-blocked vs Offer/Order allowed | **NOT surfaced** — policy `ORDER_AND_PLAN_ALLOWED_TASK_START_BLOCKED` exists backend-only |
| 17 | Frontend infers readiness | **NO** on canonical mutation surfaces; `is_startable` consumed from blueprint API |
| 18 | OperatorView same contract as ShopFloor | **NO** — blueprint + task-action vs machine-centric tasks |
| 19 | Stale legacy labels | **YES** — raw deterministic keys as primary labels |
| 20 | W6 implementation sequence | See spine below |

## Surface classification

| Surface | Route | Classification |
|---------|-------|----------------|
| ExecutionDetail | `/execution/:order_id` | `CANONICAL_OPERATOR_MUTATION_SURFACE` |
| OperatorView | `/operator` | `LEGACY_ACTIVE_SURFACE` (mutation + blueprint embed) |
| OperatorProductionBlueprintPanel | embedded in OperatorView | `CANONICAL_READ_ONLY_SURFACE` |
| ShopFloor | `/shop-floor` | `CANONICAL_READ_ONLY_SURFACE` |
| ExecutionDashboard | `/execution` | `LEGACY_ACTIVE_SURFACE` |
| ExecutionPlanV2TruthPanel | unwired component | `DEAD_SURFACE` |
| Employee Mobile V2 | `/employee-app-v2/*` | `CANONICAL_OPERATOR_MUTATION_SURFACE` — **deferred** |
| ProductSystem owner catalog | `/product-system/*` | `NOT_PROVEN` for execution resolution |

## Read-model authority

- **Classification:** `BACKEND_FIELDS_EXIST_HTTP_SCHEMA_DROPS_THEM` (operator/blueprint) + `MULTIPLE_READ_MODELS_NEED_COMPOSITION` overall
- **Plan admin:** full `frozen_identity` on tasks
- **Operator list:** drops identity + readiness
- **Production blueprint:** readiness + `is_startable`; drops `frozen_identity`
- **Production release:** complete evaluation; **no UI consumer**

## Frontend authority search

| Finding | Classification |
|---------|----------------|
| `is_startable` from blueprint API | `BACKEND_BOUND_VALIDATION` |
| ExecutionDetail action errors map `task_not_ready` | `DISPLAY_ONLY` |
| `useOperatorData` fabricates `inputDependencies` | `LEGACY_ISOLATED` (display placeholder, not gate) |
| `performAction` returns boolean, logs error | `GENERIC_ERROR_BLOCKS_OPERATOR` |
| No client-side commercial/internal cost on execution surfaces | `DISPLAY_ONLY` |
| No frontend production-release branching | — |

**No `ACTIVE_FRONTEND_AUTHORITY`** blocking Wave 6 authorization.

## Classifications (gate enums)

| Dimension | Value |
|-----------|-------|
| Task identity presentation | `EXISTING_LAYOUT_WITH_IDENTITY_METADATA` |
| Component grouping | `FLAT_LIST_WITH_COMPONENT_BADGES` (badges **missing** — keys only) |
| Frozen/runtime distinction | `PARTIAL` (runtime readiness only) |
| Owner-decision resolution UI | `MANAGER_RESOLUTION_UI_REQUIRED` |
| Role visibility | `ADMIN_MANAGER_INTERNAL_COST_VISIBLE` + `OPERATOR_STATUS_ONLY`; formal RBAC `ROLE_POLICY_MISSING` |
| Partial 7H presentation | `PARTIAL` |
| Start-action behavior | `HYBRID_PREFETCH_AND_BACKEND_ENFORCEMENT` (ExecutionDetail); `GENERIC_ERROR_BLOCKS_OPERATOR` (OperatorView) |
| Employee Mobile | `BACKEND_GUARDED_UI_DEFERRED` |
| Logo UI | `SAFE_WITH_SEGMENT_IDENTITY` / `REQUIRES_LOGO_LABEL_MAPPING_ONLY` |

## Tests

| Category | Passed | Failed | Skipped | Collection errors |
|----------|--------|--------|---------|-------------------|
| Backend focused (W5 + operator blueprint + guard + identity) | 71 | 0 | 0 | 0 |
| Frontend vitest (OperatorView/ShopFloor badges) | 5 | 9 | 0 | 0 |
| **Combined** | **76** | **9** | **0** | **0** |

Frontend failures: `PREEXISTING_UI_FIXTURE_DEBT` (Provider/context missing in badge tests).

## UI evidence

6 screenshots under `docs/qa/product-system-active-path-isolation-v1/screenshots/w6_int_01_*`.  
Machine-readable index: `docs/qa/product-system-active-path-isolation-v1/w6_int_01_gate_evidence.json`.

## Owner visual verification

1. **Task identity (raw keys):** `http://127.0.0.1:3000/execution/23099` → scroll to “Acțiuni operaționale” → TASK column shows `node:root_product:...` keys.
2. **Readiness before start:** `http://127.0.0.1:3000/operator` → select `#23099` → Blueprint panel → “Face CNC Cut” shows readiness “Așteaptă pregătire fișiere/vectori”.
3. **Partial 7H:** same ExecutionDetail page → “Profitability analysis” → Accepted revenue 1500 vs Estimated internal cost 620.
4. **Production release (API only):** `GET /api/v1/execution/orders/23099/production-release-status` → `RELEASE_ALLOWED` after W5-INT-02 resolutions.
5. **Blocked start payload:** `POST /api/v1/operator/task-action` start on `cnc_face_cut` → 409 `task_not_ready` with structured `blocking_reasons`.

## Implementation authorization

**`READY_WITH_BACKEND_READ_MODEL_PREREQUISITE`**

**First allowed task:** `W6-T01_OPERATOR_TASK_TRUTH_READ_MODEL`

## Wave 6 implementation spine

1. Canonical operator task/readiness read model (backend — expose `frozen_identity` + production-release summary)
2. Task identity presentation (desktop)
3. Production blocker visibility
4. Manager resolution UI
5. Audit/history
6. Partial 7H role-based presentation
7. Operator/ShopFloor alignment
8. W6 integration gate

Employee Mobile UI remains **outside** this spine.

## Parallel-safe work (non-mutation)

- Translation labels for `frozen_identity` fields
- Read-only task grouping by `source_component_role`
- Screenshot fixtures / gate scripts
- Permission tests for `execution.owner_decision_resolve`
- Terminology alignment Operator vs ShopFloor

## Wave 7

`KEEP_WAVE_7_BLOCKED_WAVE_6`

## Debt accepted (nonblocking)

- Logo label mapping only (not full PD correction)
- Legacy plan-generation gate panel on V2 orders
- OperatorView generic start errors
- Frontend badge test fixture debt

## Next

Authorize **W6-T01** implementation (backend read model first). Do not start broad UI polish or Employee Mobile.
