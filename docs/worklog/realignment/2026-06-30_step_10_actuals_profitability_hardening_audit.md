# Step 10 — Actuals / Profitability Hardening Audit — 2026-06-30

## 1. Status

**PASS_WITH_GUARDS**

Read-only audit confirms Step 10 **ProfitabilityAnalysis runtime is NOT implemented** (no backend router/service, no frontend page). Foundations exist for a future read-only profitability layer: frozen `OrderSnapshotV2` (commercial + estimated internal), `ExecutionReality` actuals boundary, `DivergenceService` (plan vs reality minutes), `OperationalReports` (no profit). Guards on actuals/reality are documented in code. **Guards:** generic `PUT /orders/{id}` can mutate snapshot fields; divergence uses `order.total_amount` not full dual-snapshot breakdown; actual labor cost for margin needs owner decision.

## 2. Scope

Read-only Step 10 audit on `C:\Users\offic\Desktop\workos-active`. No implementation, no DB writes, no sessions, no POST mutations, no commit, no push. Did not touch `C:\Users\offic\workos`.

## 3. Architecture readback summary

| Doc | Rule applied |
|-----|--------------|
| `README.md` | Target-arch only; implementation needs owner GO |
| `00_WORKOS_TARGET_ARCHITECTURE_OVERVIEW.md` | Commercial vs internal vs actuals separation |
| `09_QUOTE_ORDER_SNAPSHOT_CONTRACT.md` | Quote/order freeze commercial + estimated side-by-side; no retroactive reprice from actuals |
| `10_EXECUTION_PLAN_TASK_GRAPH.md` | Plan from frozen snapshot; not a price source |
| `11_EXECUTION_ACTUALS_AND_TASK_SESSIONS.md` | Real minutes post-order; **must not mutate accepted quote** |
| `16_PROFITABILITY_ANALYSIS.md` | **MISSING runtime**; compare after execution; recommendations only |
| `17_UI_NAVIGATION_AND_LABELING_POLICY.md` | Step 11 labels only — out of scope |
| `18_GOVERNANCE_SETTINGS_POLICY.md` | Governance boundary |
| `19_LEGACY_DEAD_PIECES_CLEANUP_POLICY.md` | No auto-delete (Step 12) |
| `20_ROADMAP_STEPS_7G_TO_12.md` | Step 10 requires Steps 8+9; **7G preview exists**; Step 10 **NOT STARTED** |

## 4. What I audited

### Code / docs search

- `Profitability`, `CommercialPriceProposal`, `EstimatedInternalCost`, `ExecutionReality`, `DivergenceService`, `operational_reports_service`, `order_snapshot_v2_*`, `quote_snapshot_v2_*`
- Routers: `commercial_price_proposal.py`, `estimated_internal_cost.py`, `quote_snapshot_v2.py`, `execution.py`, `orders.py`
- Services: `execution_reality_service.py`, `task_work_session_service.py`, `divergence_service.py`, `execution_observability_service.py`
- Frontend: `ExecutionDetail.tsx`, `ExecutionDashboard.tsx`, `OperationalReports.tsx`, `Quotes.tsx` (margin at quote stage only)

### Runtime GET (read-only)

- `GET /health`
- `GET /api/v1/execution/divergence/88001`
- `GET /api/v1/execution/reality/88001` (404 expected)
- Prior session data: plan/blueprint/reports for order `88001`

## 5. What I did not audit

- Employee Mobile session paths (forbidden)
- CostEngine / QuoteOrchestrator / `/price` runtime (frozen)
- Full pytest re-run
- HR payroll / inventory cost valuation
- Production deploy auth policies
- Step 10 implementation

---

## 6. Profitability architecture findings

### What exists in code

| Component | Location | Role |
|-----------|----------|------|
| **CommercialPriceProposal preview (7G)** | `commercial_price_proposal_service.py`, router | Read-only commercial lines from rules; **no CostEngine** |
| **EstimatedInternalCost preview (7H)** | `estimated_internal_cost_service.py`, router | Read-only internal estimate; **no CostEngine** |
| **Quote Snapshot V2** | `quote_snapshot_v2_service.py` | Freezes commercial + internal previews |
| **Order Snapshot V2 convert** | `order_snapshot_v2_convert_service.py` | Locks `accepted_commercial_total`, `estimated_internal_total`, `no_reprice_policy=True` |
| **ExecutionPlan V2** | Step 9 services | Planned/materialized operational tasks; not profitability |
| **ExecutionReality** | `execution_reality_service.py` | Actual sessions, minutes, observational materials |
| **DivergenceService** | `divergence_service.py` | **Read-only** plan minutes vs reality minutes vs `order.total_amount` |
| **ExecutionObservabilityService** | Uses divergence | OK/WARNING/CRITICAL/UNCONFIRMED alerts |
| **OperationalReports** | `operational_reports_service.py` | Workforce/reality completeness; **explicitly no cost/profit** |

### What exists only in docs

| Item | Doc |
|------|-----|
| **ProfitabilityAnalysis** system | `16_PROFITABILITY_ANALYSIS.md` |
| Target endpoint `GET /api/v1/profitability-analysis/order/{order_id}` | Doc 16 §10 |
| Per-unit effective price (lei/ml, lei/m²) | Doc 16 |
| Recommendation loop to commercial rules | Doc 16 §7 |
| Step 10 acceptance criteria | Doc 16 §12, roadmap §Step 10 |

### What is missing

- `profitability` string: **zero matches** in `backend/`
- No `ProfitabilityAnalysisService`, router, schema, or DB table
- No frontend profitability page/route
- No actual internal cost rollup from sessions + materials + inventory
- No gross margin actual vs estimated report
- No recommendation persistence model

### Legacy / dead / misleading

| Item | Tag |
|------|-----|
| Quote `marginPct` in UI (`Quotes.tsx`) | Pre-accept commercial context — **not** Step 10 profitability |
| Legacy `/price` + CostEngine path | Frozen per roadmap; not profitability baseline |
| `order.total_amount` in divergence | Proxy for sold price — **not** full `OrderSnapshotV2` commercial breakdown |
| Operational reports label | Correctly states no profit — not misleading |
| Test order `88001` | Has `accepted_commercial_total=1500` in snapshot; `plan_total_estimated_minutes=0` (planning minutes warning) |

### Where the correct boundary must sit

```
Frozen Quote/Order Snapshot (commercial + estimated internal)
    → ExecutionPlan (planned operational tasks / minutes estimate)
    → ExecutionReality + sessions (actual minutes/materials observations)
    → ProfitabilityAnalysis (NEW read model — compare only)
    ✗ No write-back to quotes/orders/CostEngine/registry
```

---

## 7. Accepted quote / frozen snapshot safety findings

### Where price freezes

| Stage | Mechanism | Fields |
|-------|-----------|--------|
| Quote accept V2 | `quote_snapshot_v2_accept_gate_service` | `commercial_price_proposal_snapshot`, `estimated_internal_cost_snapshot` |
| Order convert V2 | `order_snapshot_v2_convert_service` | `snapshot_v2_json` with `accepted_commercial_total`, `estimated_internal_total`, `no_reprice_policy=True` |
| Legacy order | `snapshot_line_items` + `total_amount` + `locked_at` | `final_price` in snapshot JSON |

### Source of truth for Step 10 estimated side

- **Revenue:** `OrderSnapshotV2.accepted_commercial_total` (+ currency)
- **Estimated internal:** `OrderSnapshotV2.estimated_internal_total` + `estimated_internal_cost_snapshot` lines
- **Commercial lines:** `commercial_price_proposal_snapshot` (frozen copy)

### Can actuals/profitability modify accepted quote?

- **ExecutionRealityService** doc: writes **only** `execution_reality`; does not modify orders/quotes
- **No profitability service exists** to write anything
- **Risk (WATCH):** `PUT /api/v1/entities/orders/{id}` accepts `snapshot_line_items`, `total_amount` in `OrdersUpdateData` — generic `OrdersService.update` without explicit immutability guard for locked/V2 orders

### Reprice / snapshot rewrite endpoints (frozen — not called)

- `POST /api/v1/entities/quotes/price` — frozen
- QuoteOrchestrator — not in Step 10 scope
- Order convert is one-way at accept time

### Step 10 must be

**Strict read model / analysis** over frozen snapshots + actuals. No recalculation of offer. No registry auto-update.

---

## 8. ExecutionActuals / sessions findings

### Where actuals begin

| Event | Endpoint | Writes |
|-------|----------|--------|
| First reality write | `POST /api/v1/execution/reality/start-task` | Creates `execution_reality` row; session observation in `tasks_json` |
| End task | `POST /api/v1/execution/reality/end-task` | Updates task `ended_at`, recomputes `total_actual_time_minutes` |
| Materials | `POST` reality material endpoints | Appends to `materials_json` (observational) |

### Session creation

- `ExecutionRealityService.start_task` → `task_work_session_service.build_work_session_observation` / `new_session_id()`
- **Materialize V2 plan does NOT create sessions** (confirmed Step 9.3.6)

### Real fields (model + JSON)

| Field | Purpose |
|-------|---------|
| `execution_reality.tasks_json[]` | `task_id`, `started_at`, `ended_at`, `session_id`, `employee_id`, `actual_minutes`, pause/block timestamps |
| `execution_reality.materials_json[]` | Observational consumption |
| `execution_reality.total_actual_time_minutes` | Aggregated from completed sessions |
| Plan `operational_tasks[].estimated_time_minutes` | **Planned** — not actual |

### Can actual cost be calculated today?

**Partially:**

- Actual **minutes** — yes, from `ExecutionReality` when sessions exist
- Actual **materials** — observational list only; no automatic inventory cost rollup in profitability path
- Actual **labor cost** — **missing** (doc 16: NEEDS_OWNER_DECISION for HR internal rates)
- **Margin actual** — **cannot** be computed without Step 10 service

### Dangerous endpoints for QA (do not call)

- `POST /execution/reality/start-task`, `end-task`
- `POST /execution/plan-v2/materialize-tasks/{id}` (if already done → 409)
- `PATCH /execution/plan/.../assign`, `.../instructions`
- `PUT /orders/{id}` with snapshot/total fields

### Order 88001 runtime

- `GET /execution/reality/88001` → **404** (no actuals)
- `GET /execution/divergence/88001` → `has_reality=false`, `sold_total_amount=1500`, `plan_total_estimated_minutes=0`, note `reality_not_recorded`

---

## 9. Proposed Step 10 contract (documentation only — not implemented)

### A. Estimated side (read from frozen snapshot)

| Field | Source |
|-------|--------|
| `quoted_commercial_total` | `OrderSnapshotV2.accepted_commercial_total` or legacy `order.total_amount` |
| `quoted_currency` | `accepted_currency` |
| `estimated_internal_total` | `estimated_internal_total` |
| `estimated_materials` | `estimated_internal_cost_snapshot.lines` (material-classified) |
| `estimated_operations` | internal snapshot operation lines |
| `estimated_labor/capacity` | internal snapshot capacity hints (if present) |
| `estimated_overhead` | internal snapshot overhead lines (if present) |
| `margin_expected_pct` | derived: `(commercial - estimated_internal) / commercial` — **display only** |

### B. Actual side (read from ExecutionReality + inventory hooks)

| Field | Source |
|-------|--------|
| `actual_session_minutes` | `execution_reality.total_actual_time_minutes` + per-task sessions |
| `actual_task_completion` | reality task `ended_at` / status |
| `actual_material_usage` | `materials_json` (observational) |
| `actual_labor_cost` | **OWNER_DECISION** — HR rate × minutes or absent |
| `actual_external_services` | future / manual observations |
| `actual_overhead` | optional approximation — owner GO |

### C. Profitability read model (new GET endpoint)

```text
GET /api/v1/profitability-analysis/order/{order_id}
```

Response shape (conceptual):

- `revenue_accepted`, `estimated_internal_cost`, `actual_internal_cost` (nullable until actuals)
- `delta_estimated_vs_actual` (material, time, total)
- `gross_margin_estimated_pct`, `gross_margin_actual_pct` (nullable)
- `per_unit_effective` (lei/m² etc. — when geometry available in snapshot)
- `warning_flags[]` (e.g. `reality_missing`, `plan_minutes_zero`, `dual_snapshot_missing`)
- `recommendations[]` (read-only suggestions)
- `retroactive_change_allowed: false`

### D. Hard guardrails (implementation must enforce)

- No mutation of `quotes`, `orders.snapshot_*`, accepted totals
- No `/price`, CostEngine, QuoteOrchestrator calls
- No using actual minutes as commercial price
- No session creation from profitability path
- No execution status mutation
- **Read-only by default**; recommendations persisted only with owner GO
- Build on **dual snapshot** when present; legacy fallback explicitly labeled

### Minimal recommended implementation slice (future, owner GO)

1. Read-only service + router + schema (no DB writes except optional report cache with GO)
2. Input: `OrderSnapshotV2` + `ExecutionPlan` operational minutes + `ExecutionReality`
3. Output: variance report + warnings; no recommendations engine in v1
4. Tests: frozen snapshot immutability; no quote/order writes; legacy order path labeled

---

## 10. Owner visual verification locations

**Nu există încă UI dedicat pentru Step 10 profitability.**

### Existing pages useful for boundary verification

#### 1. ExecutionDetail — plan vs reality (not profitability)

- **URL:** `http://127.0.0.1:3000/execution/88001`
- **Tab/section:** Observabilitate + „Înregistrare execuție reală”
- **IDs:** `order_id=88001`, `plan_id=1`
- **Ce verific:** Readiness badge `Operational tasks ready`; PLANIFICAT `0.0 min`; ACTUAL `—` (no reality)
- **Pași:** Execuție → click order / navigate direct URL → Refresh
- **Date necesare:** V2 plan materializat (fixture QA)

#### 2. ExecutionDetail — observability / divergence

- **URL:** `http://127.0.0.1:3000/execution/88001`
- **Ce verific:** NECONFIRMAT când reality lipsește; PLAN `prezent`, REALITATE `lipsă`
- **Așteptat:** Nu arată profit/marjă — doar plan/reality gap

#### 3. ExecutionDashboard

- **URL:** `http://127.0.0.1:3000/execution`
- **Ce verific:** `divergence_status` column (OK/WARNING/CRITICAL/UNCONFIRMED)
- **Date necesare:** orders cu plan; reality optional

#### 4. OperationalReports

- **URL:** `http://127.0.0.1:3000/reports/operational`
- **Ce verific:** Header „fără cost intern, profit sau salarii”; plan metrics `2` / `0`
- **Confirmă:** Operational reporting intentionally excludes Step 10 economics

#### 5. Divergence API (admin/dev)

- **URL:** `GET http://127.0.0.1:8000/api/v1/execution/divergence/88001`
- **Așteptat:** `sold_total_amount=1500`, `has_reality=false`, `reality_not_recorded` note

### After future Step 10 implementation — verify visually

- New admin route (TBD) showing quoted vs estimated vs actual margin
- Same order `88001` **after** controlled session QA (separate GO) — actual minutes populated
- Explicit `retroactive_change_allowed: false` badge

---

## 11. Risk register

### CONFIRMED_OK

| Item | Observation |
|------|-------------|
| No profitability runtime yet | Cannot accidentally retroactive-reprice via Step 10 |
| ExecutionReality boundaries | Documented + enforced: no order/plan/CE writes |
| Dual snapshot V2 on convert | `no_reprice_policy=True`; commercial + internal frozen |
| 7G/7H preview services | Read-only; forbidden CostEngine/QuoteOrchestrator imports in tests |
| DivergenceService | Read-only plan vs reality vs sold total |
| OperationalReports | Explicitly no profit/cost |
| Materialize ≠ sessions | Step 9 boundary confirmed |

### WATCH

| Item | Severity | Recommendation |
|------|----------|----------------|
| `PUT /orders/{id}` generic update | Medium | Add immutability guard for `snapshot_*`, `total_amount` on locked/V2 orders before Step 10 |
| Divergence uses `order.total_amount` only | Low | Step 10 should read `OrderSnapshotV2` dual snapshot when available |
| Plan minutes zero on QA order | Low | `PLANNING_MINUTES_SOURCE_REQUIRED` — profitability time variance needs plan minutes or explicit warning |
| Actual labor cost for margin | Medium | Owner decision on HR rate source (doc 16) |
| Legacy orders without `snapshot_v2_json` | Medium | Step 10 must branch: V2 dual snapshot vs legacy `snapshot_line_items` |

### BLOCKER

**None** for starting Step 10 **design/implementation plan** — prerequisites from Step 9 are sufficiently hardened per 9.3.6 audit.

### OWNER_DECISION

| Item | Decision |
|------|------------|
| Step 10 implementation GO | Approve read-only profitability service scope |
| HR labor cost in margin | Include or exclude v1 |
| Recommendations engine | v1 variance only vs v1+recommendations |
| Order update immutability fix | Separate small fix GO before or with Step 10 |
| Commit worklogs | Docs commit approval |

---

## 12. Files changed

| File | Change | Commit |
|------|--------|--------|
| `docs/worklog/realignment/2026-06-30_step_10_actuals_profitability_hardening_audit.md` | Created | none |

## 13. Tests / validation

| Action | Result |
|--------|--------|
| Git preflight | PASS — only worklogs untracked |
| Architecture readback | PASS |
| Code/doc trace | PASS |
| Runtime GET probes | PASS |
| pytest | Not run |

## 14. Runtime status

| Service | PID | Status |
|---------|-----|--------|
| Backend :8000 | 40396 | healthy |
| Frontend :3000 | 29544 | HTTP 200 |
| Duplicate backend | None | |

## 15. Commit

**No commit created.**

## 16. Forbidden path confirmation

All confirmed **not done / not touched**: mobile, pricing, `/price`, CostEngine, QuoteOrchestrator, reality/session writes, sessions, assignment, start/stop, DB writes/reset, migrations, push, implementation, scripts, `C:\Users\offic\workos`.

## 17. What remains

1. Owner GO for Step 10 implementation plan
2. Optional: order snapshot immutability guard on `PUT /orders/{id}`
3. Step 10 v1: read-only `GET /profitability-analysis/order/{id}`
4. Controlled session QA on order `88001` (separate GO) to populate actuals for future profitability demo
5. Commit worklogs when approved

## 18. Owner decisions needed

1. Approve Step 10 v1 scope (variance read model only vs recommendations)
2. HR labor cost inclusion in margin actual
3. Priority: order immutability fix vs Step 10 service first
4. Worklog docs commit

## 19. Next recommended step

**Owner GO → Step 10 implementation plan** (read-only `ProfitabilityAnalysisService` + contract tests + optional GET endpoint). Do **not** start UI slice 2 before Step 10 contract is approved — profitability boundary is the natural next architectural gate.

## 20. Direction score

**Cat sunt in directia stabilita: 87/100%**

- Steps 9.3.x + 9.3.6: hardened
- Dual snapshot + actuals boundaries: documented and mostly enforced in code
- Step 10 runtime: correctly absent (not half-built on CostEngine)
- Minor WATCH on order update immutability prevents 90+
