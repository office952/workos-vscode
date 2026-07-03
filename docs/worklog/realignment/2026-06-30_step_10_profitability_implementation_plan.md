# Step 10 — ProfitabilityAnalysis Implementation Plan — 2026-06-30

## 1. Status

**PASS_WITH_GUARDS**

Read-only implementation plan for Step 10. Scope fits **read-only service + schema + GET endpoint + tests** without CostEngine/QuoteOrchestrator/sessions. **Recommendation:** Slice **10.1 immutability guard** before or in parallel with 10.2–10.3 (small, high-value). **7G preview services exist;** full Step 7G commercial runtime per roadmap remains NOT STARTED.

## 2. Scope

Implementation **plan only** on `C:\Users\offic\Desktop\workos-active`. No code, no DB writes, no commit, no push. Did not touch `C:\Users\offic\workos`.

## 3. Architecture readback summary

| Doc | Rule for Step 10 plan |
|-----|----------------------|
| `README.md` | Owner GO required for runtime |
| `00_WORKOS_TARGET_ARCHITECTURE_OVERVIEW.md` | Commercial / internal / actuals separation |
| `09_QUOTE_ORDER_SNAPSHOT_CONTRACT.md` | Dual freeze at accept; no retroactive reprice |
| `10_EXECUTION_PLAN_TASK_GRAPH.md` | Plan minutes = baseline estimate, not commercial price |
| `11_EXECUTION_ACTUALS_AND_TASK_SESSIONS.md` | Sessions post-order; no quote mutation |
| `16_PROFITABILITY_ANALYSIS.md` | Compare after execution; `retroactive_change_allowed: false` |
| `17_UI_NAVIGATION_AND_LABELING_POLICY.md` | UI slice 10.4 = minimal read-only section only |
| `18_GOVERNANCE_SETTINGS_POLICY.md` | Settings not in MVP |
| `19_LEGACY_DEAD_PIECES_CLEANUP_POLICY.md` | No Step 12 cleanup in Step 10 |
| `20_ROADMAP_STEPS_7G_TO_12.md` | Step 10 after 8+9; **GO required** |

## 4. Plan overview

### Proposed service

**`ProfitabilityAnalysisService`** (`backend/services/profitability_analysis_service.py`)

| Responsibility | Detail |
|----------------|--------|
| Load order | `Orders` by `order_id` |
| Parse snapshot V2 | `order.snapshot_v2_json` → `OrderSnapshotV2` when present |
| Revenue | `accepted_commercial_total` from V2 snapshot; legacy fallback `order.total_amount` |
| Estimated internal | `estimated_internal_total` + lines from frozen internal snapshot |
| Optional plan | `ExecutionPlan.total_estimated_time_minutes` + operational task count (context only) |
| Optional reality | `ExecutionReality` if row exists |
| Actual cost MVP | **Partial** — minutes from reality; materials observational count only; **no HR labor rate** in v1 |
| Variance / margin | Estimated margin always when both totals present; actual margin **null** until actual cost computable |
| Writes | **None** |
| Forbidden imports | `cost_engine*`, `quote_orchestrator*`, `execution_reality_service` (no start/stop) |

### Proposed schema

**`ProfitabilityAnalysisResponse`** (`backend/schemas/profitability_analysis.py`)

Pydantic model matching GET response below. Include `ProfitabilityStatus` literal enum: `ready`, `estimated_only`, `actual_incomplete`, `snapshot_missing`, `blocked`.

### Proposed router

**`backend/routers/profitability_analysis.py`**

```text
GET /api/v1/profitability-analysis/order/{order_id}
```

- `dependencies=[Depends(get_current_user)]`
- Permission: `require_permission("profitability.read")` **or** reuse `order.read` / `execution.read` — **OWNER_DECISION** (prefer new `profitability.read` for clarity)
- Returns `ProfitabilityAnalysisResponse`
- 404 if order not found
- 422 only for invalid `order_id <= 0`

Auto-registered via existing `include_routers_from_package` in `main.py`.

---

## 5. Proposed backend contract (MVP)

### `GET /api/v1/profitability-analysis/order/{order_id}`

| Field | Type | MVP null? | Source |
|-------|------|-----------|--------|
| `order_id` | int | never | param |
| `order_code` | str | never if order exists | `orders.code` |
| `snapshot_version` | int \| null | yes (legacy) | `orders.snapshot_version` |
| `has_snapshot_v2` | bool | never | `snapshot_v2_json` present |
| `revenue_source` | str | never | `order_snapshot_v2.accepted_commercial_total` \| `order.total_amount` \| `missing` |
| `accepted_commercial_total` | float \| null | yes if no revenue | V2 or legacy |
| `accepted_currency` | str \| null | yes | V2 `accepted_currency` |
| `estimated_internal_total` | float \| null | yes | V2 `estimated_internal_total` |
| `has_execution_reality` | bool | never | reality row exists |
| `actual_total_cost` | float \| null | **yes in MVP** | null until labor/material costing defined |
| `actual_labor_minutes` | float \| null | yes if no reality | `execution_reality.total_actual_time_minutes` |
| `actual_materials_total` | float \| null | **yes in MVP** | null (materials observational only, no cost rollup) |
| `estimated_margin_amount` | float \| null | yes if missing inputs | `commercial - estimated_internal` |
| `estimated_margin_percent` | float \| null | yes if commercial ≤ 0 | derived |
| `actual_margin_amount` | float \| null | **yes in MVP** | requires `actual_total_cost` |
| `actual_margin_percent` | float \| null | **yes in MVP** | requires actual margin |
| `variance_estimated_vs_actual` | object \| null | **yes in MVP** | `{ "cost_delta": null, "minutes_delta": float \| null }` — minutes from divergence logic |
| `profitability_status` | str | never | see status rules |
| `warnings` | list[str] | never (may be empty) | see warnings table |
| `retroactive_change_allowed` | bool | never | **always `false`** |
| `write_back_performed` | bool | never | **always `false`** |

### MVP status rules

| Condition | `profitability_status` |
|-----------|------------------------|
| No order | 404 (not in body) |
| No V2 and no `total_amount` | `snapshot_missing` |
| V2 + commercial + estimated, no reality | `estimated_only` |
| V2 + reality with minutes | `actual_incomplete` (cost null) |
| Future: actual_total_cost computed | `ready` |

### MVP warnings (non-exhaustive)

| Code | When |
|------|------|
| `legacy_revenue_fallback` | Used `order.total_amount` not V2 |
| `estimated_internal_missing` | V2 without `estimated_internal_total` |
| `execution_reality_missing` | No reality row |
| `actual_cost_not_computed_mvp` | Always in v1 until labor/material costing |
| `plan_minutes_zero` | Plan exists but `total_estimated_time_minutes == 0` |
| `order_mutability_guard_missing` | If Slice 10.1 not done — document risk |
| `hr_labor_cost_not_included` | Always in v1 |

---

## 6. Source of truth mapping

| Concept | Source of truth | File / model | Exists? | Read-only? | MVP use | Risk if wrong |
|---------|-----------------|--------------|---------|------------|---------|---------------|
| Accepted commercial revenue | `OrderSnapshotV2.accepted_commercial_total` | `orders.snapshot_v2_json`, schema `order_snapshot_v2.py` | Yes (V2 orders) | Yes | Primary revenue | Using `total_amount` alone skews margin |
| Legacy commercial revenue | `orders.total_amount` | `models/orders.py` | Yes | Yes | Fallback with warning | May diverge from dual snapshot |
| Estimated internal total | `OrderSnapshotV2.estimated_internal_total` | `snapshot_v2_json` | Yes (V2) | Yes | Estimated cost | Null → no estimated margin |
| Commercial lines detail | `commercial_price_proposal_snapshot` | frozen in V2 JSON | Yes | Yes | Future breakdown; MVP totals only | Low for v1 |
| Internal lines detail | `estimated_internal_cost_snapshot.lines` | frozen in V2 JSON | Yes | Yes | Future breakdown | Low for v1 |
| Snapshot line items (legacy) | `orders.snapshot_line_items` | JSON `final_price`, `cost_result` | Yes | Yes | Legacy path only | BLK-08 legacy types |
| Plan estimated minutes | `execution_plan.total_estimated_time_minutes` | `models/execution_plan.py` | Yes | Yes | Variance context / warnings | Zero on QA order 88001 |
| Plan operational tasks | `operational_tasks_only(plan.tasks_json)` | parser | Yes | Yes | Count / time context | Not cost |
| Session minutes (actual) | `execution_reality.total_actual_time_minutes` | `models/execution_reality.py` | Yes if reality exists | Yes | `actual_labor_minutes`, minutes variance | No reality → null |
| Session detail | `execution_reality.tasks_json[]` | reality service | Yes | Yes | Per-task (future) | — |
| Actual materials | `execution_reality.materials_json[]` | observational | Yes | Yes | Count only in MVP | **No cost** without inventory/HR |
| Actual extra costs | — | — | **Missing** | — | Defer | — |
| Divergence status | `ExecutionObservabilityService` / `DivergenceService` | `divergence_service.py` | Yes | Yes | Optional cross-check warning | Read-only duplicate OK |
| Profitability warnings | Computed in service | new service | **Missing** | N/A | Output only | — |
| HR labor rate | — | — | **Missing** | — | Defer (owner GO) | Cannot compute actual margin $ |

---

## 7. Immutability guard analysis

### Problem

`PUT /api/v1/entities/orders/{id}` (`orders.py` → `OrdersUpdateData`) accepts:

- `total_amount`
- `snapshot_line_items`
- `snapshot_version`
- `locked_at`

`OrdersService.update()` applies any provided fields without checking locked/V2 immutability.

**Note:** `snapshot_v2_json` is **not** in `OrdersUpdateData` today — V2 JSON is not directly PATCHable via this endpoint. Risk is primarily **legacy snapshot + total_amount** and undermining profitability inputs.

### Option 1 — Pre-Step 10 guard (recommended)

| Item | Detail |
|------|--------|
| Scope | New helper `assert_order_financial_immutable(order, update_dict)` in `orders.py` or small `order_immutability_service.py` |
| Trigger | Order has `locked_at` **OR** `snapshot_v2_json` **OR** status `locked` |
| Block fields | `total_amount`, `snapshot_line_items`, `snapshot_version` |
| HTTP | **422** `order_financial_fields_immutable` (or **409** if prefer conflict semantics) |
| Allow | `notes`, `promised_delivery`, `payment_status`, `job_id`, status transitions per lifecycle |
| Tests | `test_order_financial_immutability.py` |
| Files | `backend/routers/orders.py`, optional `backend/services/order_immutability_service.py`, tests |

**Why recommend:** ProfitabilityAnalysis trusts frozen commercial/estimated totals. Silent PUT undermines Step 10 truth. Small diff, high safety.

### Option 2 — Warning only

Service adds `order_mutability_guard_missing` to every profitability response.

**Why not sufficient alone:** Does not fail-closed; audit/compliance gap remains.

### Recommendation

**Slice 10.1 (Option 1) before or parallel with 10.2–10.3.** If owner defers, ship 10.2–10.3 with Option 2 warning and explicit GO acceptance of risk.

---

## 8. Proposed tests (not implemented)

### Service contract tests (`test_profitability_analysis_service.py`)

| Test | Assert |
|------|--------|
| V2 order, no reality | `estimated_only`, margins from snapshot, `actual_*` null |
| V2 order + reality minutes | `actual_labor_minutes` set, `actual_total_cost` null (MVP) |
| Legacy order (no V2) | `legacy_revenue_fallback` warning, uses `total_amount` |
| Missing order | raises not found |
| Missing `estimated_internal_total` | warning, `estimated_margin_*` null |
| Incomplete actuals | `actual_incomplete` status |
| After service call | order `total_amount` unchanged (read-only) |

### Endpoint tests (`test_profitability_analysis_router.py`)

| Test | Assert |
|------|--------|
| GET valid order | 200, schema fields |
| GET missing order | 404 |
| GET invalid id | 422 |
| No DB mutation | count orders/reality unchanged |
| Response flags | `retroactive_change_allowed=false`, `write_back_performed=false` |
| Forbidden imports | static analysis / existing pattern from 7G tests |

### Optional guard tests (Slice 10.1)

| Test | Assert |
|------|--------|
| Locked V2 PUT `total_amount` | 422 |
| Locked PUT `snapshot_line_items` | 422 |
| PUT `notes` on locked order | 200 allowed |

---

## 9. Proposed implementation slices

### Slice 10.1 — Order financial immutability guard (recommended first)

| | |
|-|-|
| **Scope** | Block financial snapshot mutation on locked/V2 orders |
| **Files** | `backend/routers/orders.py`, `backend/services/order_immutability_service.py` (new, ~40 lines), `backend/tests/test_order_financial_immutability.py` |
| **Tests** | 4–6 pytest cases |
| **Risk** | Low; may block admin scripts that relied on PUT — document |
| **Visual** | API/test only; no UI |
| **GO** | **Required** |

### Slice 10.2 — ProfitabilityAnalysisService + schema

| | |
|-|-|
| **Scope** | Read-only analysis logic + Pydantic response |
| **Files** | `backend/services/profitability_analysis_service.py`, `backend/schemas/profitability_analysis.py`, `backend/tests/test_profitability_analysis_service.py` |
| **Tests** | Service table above |
| **Risk** | Medium — must not import CE/QO; legacy path labeling |
| **GO** | **Required** |

### Slice 10.3 — GET endpoint + router registration

| | |
|-|-|
| **Scope** | Thin router calling service |
| **Files** | `backend/routers/profitability_analysis.py`, `backend/tests/test_profitability_analysis_router.py` |
| **Tests** | Endpoint table above |
| **Risk** | Low if 10.2 solid |
| **GO** | **Required** (with 10.2) |

### Slice 10.4 — Optional minimal UI (later GO)

| | |
|-|-|
| **Scope** | Read-only panel on `ExecutionDetail` — e.g. collapsible „Profitabilitate (estimativ)” below observability |
| **Files** | `frontend/src/api/profitabilityAnalysis.ts`, `ExecutionDetail.tsx` (minimal section), vitest for API types |
| **Constraints** | No redesign, no charts, no new route, labels only per Step 11 deferral |
| **Risk** | UI scope creep — **separate GO** |
| **GO** | **Optional, after 10.3** |

### Recommended order

1. **10.1** (if owner agrees — strongly recommended)
2. **10.2 + 10.3** (same PR or 10.2 then 10.3)
3. **10.4** only with explicit UI GO

---

## 10. Owner visual verification locations

### Acum (plan baseline — no Step 10 UI)

#### 1. ExecutionDetail

- **URL:** `http://127.0.0.1:3000/execution/88001`
- **Ce verific:** Readiness `Operational tasks ready`; PLANIFICAT `0.0 min`; ACTUAL `—` (no reality)
- **IDs:** `order_id=88001`, `plan_id=1`
- **Pași:** Execuție → order sau URL direct → Refresh

#### 2. OperationalReports

- **URL:** `http://127.0.0.1:3000/reports/operational`
- **Ce verific:** „fără cost intern, profit sau salarii”; plan metrics `2` / `0`
- **Confirmă:** Operational layer excludes profitability economics

#### 3. Divergence API

- **URL:** `GET http://127.0.0.1:8000/api/v1/execution/divergence/88001`
- **Așteptat:** `has_reality=false`, `sold_total_amount=1500`, `reality_not_recorded`

### După Slice 10.2–10.3 (fără UI)

- **URL:** `GET http://127.0.0.1:8000/api/v1/profitability-analysis/order/88001`
- **Așteptat:** `accepted_commercial_total=1500`, `estimated_internal_total` from snapshot, `profitability_status=estimated_only`, `retroactive_change_allowed=false`, warnings include `actual_cost_not_computed_mvp`

### După Slice 10.4 (dacă aprobat)

- **URL:** `http://127.0.0.1:3000/execution/88001` — secțiune nouă read-only
- **Așteptat:** Estimated margin visible; actual margin „N/A” until costing

**Nu există încă UI dedicat pentru Step 10 ProfitabilityAnalysis.**

---

## 11. Risk register

### CONFIRMED_OK

| Item | Notes |
|------|-------|
| No half-built profitability on CostEngine | Correct gap |
| Dual snapshot V2 at convert | `no_reprice_policy=True` |
| ExecutionReality write boundary | Unchanged by Step 10 plan |
| DivergenceService read-only | Complementary, not replaced |
| Plan scope fits read-only MVP | No migration required |

### WATCH

| Item | Severity | Recommendation |
|------|----------|----------------|
| `PUT /orders/{id}` financial fields | High | Slice 10.1 |
| `actual_total_cost` null in MVP | Medium | Document; owner GO for HR/inventory costing v2 |
| Legacy orders without V2 | Medium | Explicit fallback + warning |
| Permission naming | Low | `profitability.read` vs reuse |
| Plan minutes zero on 88001 | Low | Warning only |

### BLOCKER

**None** for plan approval. Implementation blocked on **owner GO** only.

### OWNER_DECISION

| Decision | Options |
|----------|---------|
| Approve Slice 10.1 | Yes / defer with accepted risk |
| Approve 10.2+10.3 MVP | Yes / revise scope |
| HR labor in actual cost | v1 exclude (recommended) / v1 include |
| Slice 10.4 UI | Later / never in Step 10 |
| Commit worklogs | When ready |

---

## 12. Files changed

| File | Change | Commit |
|------|--------|--------|
| `docs/worklog/realignment/2026-06-30_step_10_profitability_implementation_plan.md` | Created | none |

## 13. Tests / validation

| Action | Result |
|--------|--------|
| Git preflight | PASS |
| Architecture readback | PASS |
| Plan within scope | PASS — no larger refactor proposed |
| pytest | Not run (plan only) |

## 14. Runtime status

| Service | PID | Status |
|---------|-----|--------|
| Backend :8000 | 40396 | healthy |
| Frontend :3000 | 29544 | HTTP 200 |

## 15. Commit

**No commit created.**

## 16. Forbidden path confirmation

All confirmed not done: mobile, pricing, `/price`, CostEngine, QuoteOrchestrator, reality/session writes, sessions, assignment, start/stop, DB writes, reset, migrations, push, implementation, scripts, `C:\Users\offic\workos`.

## 17. What remains

1. Owner GO on slice order (10.1 yes/no)
2. Owner GO on 10.2+10.3 implementation
3. Optional 10.4 UI GO later
4. HR labor costing decision for v2
5. Commit worklogs when approved

## 18. Owner decisions needed

1. **Approve Slice 10.1** immutability guard? (recommended **yes**)
2. **Approve MVP** 10.2+10.3 without actual $ margin (minutes-only actuals)?
3. **Permission** `profitability.read` — new or reuse?
4. **Defer Slice 10.4** UI?

## 19. Next recommended step

**Owner GO for Slice 10.1** (order financial immutability guard) — then **10.2 + 10.3** in one bounded build with contract tests. If owner rejects 10.1, **GO for 10.2+10.3** only with explicit acceptance of `order_mutability_guard_missing` warning.

## 20. Direction score

**Cat sunt in directia stabilita: 89/100%**

- Audits complete; plan is narrow and aligned with doc 16
- Immutability guard is the main gap before trustworthy profitability reads
- 7G/10 runtime correctly not started beyond preview services
