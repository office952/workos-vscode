# Lane B — Wave 3 page cards

Wave 1 already owns `/shop-floor` as a role-home card. This file adds **operational depth** for Wave 3. No product writes.

## `/shop-floor` — Atelier

| Field | Value |
|-------|--------|
| PURPOSE | Monitor ready/blocked machines and queues. Not the action surface. |
| PRIMARY USER | operator / manager |
| PRIMARY DECISION | What is blocked vs idle vs queued? |
| SYSTEM OWNER | Shop-floor projection of machines + operator tasks (read) |
| READS | `GET /machines`, `GET /operator/tasks` |
| WRITES | none on this page |
| UPSTREAM | `/execution`, `/orders` |
| DOWNSTREAM | `/operator`, `/tablet` (compat action) |
| Disposition | KEEP + SIMPLIFY (WC keys; next-step sends operator to COMPAT) |

Runtime: admin/operator/manager × light/dark. Sales denied → `/quotes`. Scroll PASS 0→818. H1 honest: monitor only. Cards titled `CNC_ROUTING`, `LETTER_FORMING`. Only live job seen: `print - ORD-92400` (not the Wave 2 IV6 order). **RESOLVED_BY_GAP_CLOSURE:** `DIFFERENT_ACTIVE_WORK` — not same-work identity drift. See `WAVE_3_ORDER_EXECUTION_ATELIER_IDENTITY.md`.

Blocks: machine grid OPERATOR_CRITICAL; FLUX + “Următorul pas: Acționează pe task” MANAGER/TECHNICAL (sends to compat); English “Shop Floor” breadcrumb TECHNICAL.

## `/execution` — Planificare

| Field | Value |
|-------|--------|
| PURPOSE | Read-only plan vs reality list |
| PRIMARY USER | manager / admin / sales (view) |
| PRIMARY DECISION | Which order’s execution to open |
| SYSTEM OWNER | Execution observability (not task action) |
| WRITES | none |
| Disposition | KEEP |

Operator denied → `/shop-floor`. Sales allowed. Row click → `/execution/{numericId}` (e.g. 21099, 973024).

## `/execution/973024` — Execution detail (Wave 2 order)

| Field | Value |
|-------|--------|
| PURPOSE | Frozen-order execution result / plan / actuals / readiness |
| PRIMARY USER | manager / admin |
| PRIMARY DECISION | Is production allowed / what is blocked? |
| SYSTEM OWNER | ExecutionPlan + reality (display) |
| WRITES | generate plan / start-end / assign — **not executed** |
| Disposition | KEEP + SIMPLIFY (stacked panels; numeric URL) |

Handoff: `/orders/ORD-IV6-V2-1786318810-31` **Vezi execuția** → `/execution/973024` (GOOD_EDGE, CONTEXT_PRESERVED=PARTIAL). URL is DB id, not order code.

## `/execution/machine-runs` — Rulări utilaj

| Field | Value |
|-------|--------|
| PURPOSE | Machine grouping/reservation; copy says not task/session |
| PRIMARY USER | operator / manager / admin |
| WRITES | create/start — **not executed** |
| Disposition | KEEP |

List empty of selectable rows in this fixture. Detail STATE_NOT_REACHED (would require create). Sales denied.

## `/execution/ops-graph` — Ops-Graph

| Field | Value |
|-------|--------|
| PURPOSE | Audit materialized V2 task graph |
| PRIMARY USER | admin / manager |
| Disposition | AUDIT_ONLY |
| WRITES | controlled assign exists — **not executed** |

Sales/operator denied (sales → `/quotes`). Nav chip AUDIT.

## `/execution/reality-review`

| Field | Value |
|-------|--------|
| PURPOSE | Read-only operational gaps |
| Disposition | AUDIT_ONLY / MANAGER_ONLY |
| Note | Very long page (~7.6k px) |

## `/operator` — Acțiune task (COMPAT)

| Field | Value |
|-------|--------|
| PURPOSE | Legacy desktop start/complete/assign |
| Disposition | COMPAT / DUPLICATE_ENTRY vs tablet + employee-app-v2 |
| WRITES | task-action / assign — **not executed** |

Scroll FAIL: MAIN max=74425, 20 segments, NEW_CONTENT_AFTER_FINAL_SCROLL=YES (live list). Policy string leaked: `ORDER AND PLAN ALLOWED TASK START BLOCKED`. Row: `assigned - Neatribuit`.

## `/tablet` — Stații (COMPAT)

| Field | Value |
|-------|--------|
| PURPOSE | Station queue over same operator API |
| Disposition | COMPAT / SPECIALIZED_STATION_UI |
| Note | Selector captured; station/task children not drilled (would invite start) |
