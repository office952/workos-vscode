# Capacity Batch 15 — Track B: UI Visibility / Operator Admin Surface

**Scope:** Read-only admin/operator surface for the already-materialized operational task graph of fixture `FIX-DEC009-MAT-01`.  
**Non-goals:** No materialize POST · no sessions/actuals invent · no start/stop/assign/complete · no Employee Mobile · no CostEngine/Pricing/ProductDefinition/Aggregate logic · no Capacity formula changes.

---

## Route

| Item | Value |
|------|-------|
| **URL** | `/execution/ops-graph` |
| **Default fixture** | `orderId=973010` (`FIX-DEC009-MAT-01`) when query omitted |
| **Optional query** | `?orderId=<n>` |
| **Entry** | Execution Dashboard → **Ops graph (RO)** (`data-testid=execution-ops-graph-link`) |

---

## What it shows (live fixture)

Observed against local stack (`GET` only) for order **973010** / plan **12**:

| Field | Observed | Source |
|-------|----------|--------|
| Fixture identity | `FIX-DEC009-MAT-01` · `ORD-FIX-DEC009-MAT-01` | GET plan `order_code` + fixture label |
| Order / plan | `973010` / `12` | GET `/execution/plan/973010` |
| Snapshot | `OSN2-FIX-DEC009-MAT-01-973010` | GET materialization-audit |
| Task count | **12** | `operational_tasks_count` / envelope tasks |
| Sessions | **0** | `audit.guards.creates_sessions === false` |
| Actuals | **0** | GET reality → `reality_not_found` / empty rows |
| DEC-009 / Capacity | `DEC-009=A` · `materialize=BLOCKED` · audit `already_materialized_in_envelope` | dashboard-stats strip + audit |
| Ops list / dependency strip | 12 rows · sequence + `depends_on` | GET plan `tasks[]` |
| Null / owner-accepted warnings | `estimated_time_minutes` · `planning_minutes_source` · `machine_code` · `workcenter` (F7 OD1) · `assigned_employee_id` · `PLANNING_MINUTES_SOURCE_REQUIRED` | per-task field presence + task.warnings |

---

## Read-only confirmation

| Control | Present? |
|---------|----------|
| Start / stop task | **No** |
| Assign employee | **No** |
| Complete task | **No** |
| POST materialize | **No** |
| Employee Mobile wiring | **No** (`guards.employee_mobile_scope=false` · footer states out of scope) |
| Refresh / Load orderId | Yes (GET re-fetch only) |

Footer `data-testid=ops-graph-readonly-footer` states the contract explicitly.

---

## Empty / loading / error

| State | Behavior | Evidence |
|-------|----------|----------|
| Loading | Spinner + “Se încarcă planul operațional…” (`ops-graph-loading`) | Component |
| Empty ops | Plan present but `tasks.length===0` → empty panel (`ops-graph-empty`) | Component |
| Error | Banner for plan GET failure (`ops-graph-error`) | Unit test + component |
| Soft audit miss | Plan still renders; sessions show `—` until audit loads | Component |

---

## Screenshots

| File | Viewport |
|------|----------|
| [`screenshots/ops-graph-desktop.png`](screenshots/ops-graph-desktop.png) | 1440×1100 full page |
| [`screenshots/ops-graph-narrow.png`](screenshots/ops-graph-narrow.png) | 390×900 full page |
| [`screenshots/ops-graph-narrow-content.png`](screenshots/ops-graph-narrow-content.png) | Main content crop (narrow) |

Captured via Playwright against local Vite + live backend GETs (no invent).

---

## Files changed

| Path | Role |
|------|------|
| `frontend/src/pages/MaterializedOpsGraph.tsx` | Read-only ops graph page |
| `frontend/src/pages/MaterializedOpsGraph.test.tsx` | Unit tests (fixture metrics · no action buttons · error) |
| `frontend/src/api/execution.ts` | Audit/preview types + GET clients; optional operational task fields |
| `frontend/src/App.tsx` | Route `/execution/ops-graph` (before `:order_id`) |
| `frontend/src/pages/ExecutionDashboard.tsx` | Link into ops graph |
| `frontend/scripts/ci-unit-tests.txt` | Allowlist new unit test |
| `docs/qa/capacity-batch-15/ui-visibility.md` | This report |
| `docs/qa/capacity-batch-15/screenshots/*` | Desktop + narrow evidence |

---

## Reuse

- `ExecutionPlanStatesStrip` (Operational Plan active when ops present)
- `OwnerGoNotice` (DEC-009 POST still gated)
- Capacity / DEC-009 strip pattern from Execution Dashboard (`useDashboardStats`)
- `MetricTile` / `DataTableWrapper` / `chromeBanner` design-system atoms

---

## SMART CODE COMPLIANCE

| Gate | Evidence |
|------|----------|
| No materialize | Page uses GET plan + GET audit + GET reality only |
| No sessions/actuals invent | Sessions from `audit.guards`; actuals from reality row count / 404→0 |
| No frontend business truth calc | Display backend fields; null → `—` + warning chips |
| No CostEngine / Pricing / PD / Aggregate | Untouched |
| No Capacity formula change | Display-only strip from existing dashboard-stats |
| No Employee Mobile implication | Footer + `employee_mobile_scope` display |
| Read-only operator surface | No start/stop/assign/complete controls (unit test asserts) |

---

## Return summary

| Item | Value |
|------|-------|
| **Route** | `/execution/ops-graph` |
| **Fixture** | `FIX-DEC009-MAT-01` · `973010` / plan `12` · tasks **12** · sessions **0** · actuals **0** |
| **Read-only** | **Confirmed** |
| **Screenshots** | `docs/qa/capacity-batch-15/screenshots/` |
