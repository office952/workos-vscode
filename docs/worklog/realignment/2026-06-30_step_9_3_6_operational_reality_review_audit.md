# Step 9.3.6 — Operational Reality Review Audit — 2026-06-30

## 1. Status

**PASS_WITH_GUARDS**

Read-only audit confirms a clear separation between frozen order snapshot → ExecutionPlan V2 envelope → materialized `operational_tasks[]` → plan mutations (assignment/instructions) → ExecutionReality/sessions (actuals). Guards block mutating paths on `v2_not_materialized`. Runtime GET validation on order `88001` matches code expectations. No sessions/reality rows for fixture order.

**Guards:** naming confusion (`execution_tasks_created`), operator list default status semantics, Step 10 profitability runtime missing, no first-class QA seed script.

## 2. Scope

Read-only Step 9.3.6 audit on `C:\Users\offic\Desktop\workos-active` only. No implementation, no DB writes, no POST/PUT/PATCH/DELETE, no sessions, no task start/stop, no commit, no push. Did not touch `C:\Users\offic\workos`.

## 3. Architecture readback summary

| Doc | Applied rule |
|-----|--------------|
| `README.md` | Target-arch only; 7G+ needs owner GO |
| `00_WORKOS_TARGET_ARCHITECTURE_OVERVIEW.md` | Commercial flow separate from execution minutes |
| `09_QUOTE_ORDER_SNAPSHOT_CONTRACT.md` | Frozen snapshot at order; plan derives from snapshot |
| `10_EXECUTION_PLAN_TASK_GRAPH.md` | Plan = task graph; V2 envelope; no client pricing in plan |
| `11_EXECUTION_ACTUALS_AND_TASK_SESSIONS.md` | **Real minutes collected in actuals/sessions post-order; must not mutate accepted quote** |
| `16_PROFITABILITY_ANALYSIS.md` | Step 10 missing runtime; compare after execution; no retroactive quote change |
| `17_UI_NAVIGATION_AND_LABELING_POLICY.md` | Step 11 labels only |
| `18_GOVERNANCE_SETTINGS_POLICY.md` | Settings governance boundary |
| `19_LEGACY_DEAD_PIECES_CLEANUP_POLICY.md` | Classify; no auto-delete (Step 12) |
| `20_ROADMAP_STEPS_7G_TO_12.md` | **7G runtime NOT STARTED**; Step 9 hardening in progress |

## 4. What I audited

### Code boundary (Target A)

- `backend/routers/execution_plan_v2.py`
- `backend/schemas/execution_plan_v2.py`, `execution_plan_v2_materialize.py`
- `backend/services/execution_plan_v2_preview_service.py`
- `backend/services/execution_plan_v2_persist_service.py`
- `backend/services/execution_plan_v2_materialize_service.py`
- `backend/services/execution_plan_task_parser.py`
- `backend/services/execution_plan_operational_readiness_service.py`
- `backend/services/execution_task_assignment_service.py`
- `backend/services/execution_task_instructions_service.py`
- `backend/services/task_start_gate_service.py`
- `backend/services/execution_reality_service.py`
- `backend/routers/execution.py` (plan/reality endpoints)
- `backend/routers/operator_tasks.py`
- Read models: `dashboard_stats.py`, `reports_summary.py`, `operational_reports_service.py`, `order_production_blueprint_service.py`, `divergence_service.py`, `material_procurement_status_service.py`

### Runtime GET (Target B)

- `GET /health`
- `GET /api/v1/execution/plan/88001`
- `GET /api/v1/operator/orders/88001/production-blueprint`
- `GET /api/v1/operational-reports/summary`
- `GET /api/v1/execution/reality/88001` (expect 404)
- `GET /api/v1/operator/tasks` (read-only inspect)

### Actuals / sessions boundary (Target C)

- `execution_reality_service.py` — `start_task`, `end_task`, session observation building
- `task_work_session_service.py` (referenced by reality service)
- `POST /api/v1/execution/reality/start-task` (documented only — **not called**)

## 5. What I did not audit

- Employee Mobile paths
- Pricing / `/price` / CostEngine / QuoteOrchestrator runtime
- Step 7G commercial preview implementation
- Step 10 profitability runtime (documented as missing)
- Step 11 label pass / Step 12 cleanup
- POST mutation endpoints (by design — read-only audit)
- Full pytest suite re-run
- Production deploy config

---

## 6. Code boundary findings

### ExecutionPlan V2 lifecycle

| Stage | Where | What happens |
|-------|-------|--------------|
| **Preview** | `execution_plan_v2_preview_service.build_execution_plan_v2_preview` | Read-only from `order.snapshot_v2_json`; no DB writes |
| **Persist** | `execution_plan_v2_persist_service.create_execution_plan_v2_from_order` | Inserts one `execution_plan` row; envelope with `planned_tasks[]`, `execution_tasks_created: false`, empty `operational_tasks[]` |
| **Materialize** | `execution_plan_v2_materialize_service.materialize_execution_plan_v2_operational_tasks` | Copies `planned_tasks[]` → `operational_tasks[]`; sets `execution_tasks_created: true`; **does not mutate `planned_tasks[]`** |
| **Router** | `execution_plan_v2.py` | `POST plan-v2/preview`, `plan-v2/from-order`, `plan-v2/materialize-tasks` |

### Parser (`execution_plan_task_parser.py`)

| Function | Behavior |
|----------|----------|
| `parse_tasks_json_raw()` | `legacy_list` → list is operational; `v2_envelope` → splits `planned_tasks` vs `operational_tasks`; invalid otherwise |
| `operational_tasks_only()` | Returns **only** `operational_tasks`; **no fallback** to `planned_tasks[]` when empty |
| `load_operational_tasks_from_plan_json()` | Same + parse metadata |
| `materialize_operational_tasks_from_v2_envelope()` | Builds operational dicts from `planned_tasks[]` only; validates deps |

### `execution_tasks` naming (important)

There is **no separate `execution_tasks` table**. Flag `execution_tasks_created` on V2 envelope means **operational tasks were materialized into the envelope**. Not ExecutionReality and not work sessions.

### Readiness statuses (`execution_plan_operational_readiness_service.py`)

| Status | Meaning | Mutation allowed? |
|--------|---------|-------------------|
| `no_execution_plan` | No plan row | **404** on `assert_operational_mutation_allowed` |
| `v2_not_materialized` | V2 envelope, `operational_tasks` empty | **422** |
| `v2_operational_ready` | Materialized operational tasks OK | **Allowed** |
| `legacy_operational_ready` | Legacy list format | **Allowed** |
| `v2_operational_empty` | Flag true but operational empty | **422** |
| `blocked_task_graph` | Dependency issues in operational tasks | **422** |

`MUTATION_ALLOWED_STATUSES` = `{legacy_operational_ready, v2_operational_ready}` only.

### Mutating guards (assignment / instructions / start)

| Path | Service | Guard order | HTTP codes |
|------|---------|-------------|------------|
| Assign | `execution_task_assignment_service.assign_plan_task` | `assert_operational_mutation_allowed` → task in operational list | 404 plan/employee/task; **422** readiness; **409** task completed |
| Instructions | `execution_task_instructions_service.update_plan_task_instructions` | Same readiness guard | 404 plan/task; **422** readiness/invalid JSON |
| Start | `task_start_gate_service.assert_task_startable` | `assert_operational_mutation_allowed` → task-level readiness | **422** plan readiness; **404** task not in plan; **409** task_not_ready |
| Start (reality write) | `execution.py` `POST /reality/start-task` → `ExecutionRealityService.start_task` | After gate | Creates/updates **ExecutionReality** + session observations |

**Tests confirm:** `test_execution_operational_readiness_gates.py` — assignment/instructions/start return **422** on `v2_not_materialized`; wrong task **404** after readiness OK.

**Sessions on materialize:** **No.** `ExecutionPlanV2MaterializeResult.no_sessions_created=True`; service forbids importing `execution_reality_service`.

### Read models (operational_tasks vs planned_tasks)

| Consumer | Uses | V2-safe? |
|----------|------|----------|
| `dashboard_stats.py` | `operational_tasks_only` | Yes |
| `reports_summary.py` | `operational_tasks_only` | Yes |
| `operational_reports_service.py` | `operational_tasks_only` + readiness for `plan_orders_v2_not_materialized` | Yes |
| `order_production_blueprint_service.py` | `operational_tasks_only` + readiness fields | Yes |
| `operator_tasks.py` | `operational_tasks_only` + `order_operational_readiness` | Yes |
| `execution.py` GET plan | `parse_tasks_json_raw` → returns `operational_tasks` in `tasks` | Yes |
| `divergence_service.py` | `parse_tasks_json_raw` → `operational_tasks` | Yes |
| `material_procurement_status_service.py` | `operational_tasks_only` | Yes (informational/deferred procurement) |

**Legacy risk:** V1 `POST /execution/plan/from-order` still exists for legacy orders; V2 orders should use plan-v2 path. `raise_if_legacy_plan_blocked_for_v2_order` guards v1 plan creation on V2 orders.

---

## 7. Runtime GET / read-only findings (order `88001`)

| URL | HTTP | Key fields |
|-----|------|------------|
| `GET /health` | 200 | `healthy` |
| `GET /api/v1/execution/plan/88001` | 200 | `operational_readiness_status=v2_operational_ready`, `operational_tasks_count=2`, `execution_tasks_created=true`, `plan_format=v2_envelope` |
| `GET /api/v1/operator/orders/88001/production-blueprint` | 200 | `operational_readiness_status=v2_operational_ready`, `work_sessions_count=0` on tasks |
| `GET /api/v1/operational-reports/summary` | 200 | `plan_operational_tasks_total=2`, `plan_orders_v2_not_materialized=0` |
| `GET /api/v1/execution/reality/88001` | **404** | No ExecutionReality row — **no sessions created** |
| `GET /api/v1/operator/tasks` | 200 | 2 tasks for order 88001, status `assigned` (plan-only; no reality timestamps) |

**Confirmations:**

- Materialized plan exposed correctly via GET plan and blueprint
- No reality/session data for fixture order
- Operational reports count matches materialized tasks

## 8. Actuals / sessions boundary findings

### Where runtime reality begins

| Action | Endpoint | Effect |
|--------|----------|--------|
| **Start task** | `POST /api/v1/execution/reality/start-task` | Creates `execution_reality` row if missing; appends session observation; **does not modify accepted quote** |
| **End task** | `POST /api/v1/execution/reality/end-task` | Updates reality task timestamps / minutes |
| **Materials** | `POST` reality material endpoints | Updates `execution_reality.materials_json` |

### Plan vs reality separation

| Layer | Storage | Purpose |
|-------|---------|---------|
| **Plan** | `execution_plan.tasks_json` | Planned/materialized operational tasks, assignment, instructions |
| **Reality** | `execution_reality.tasks_json` | Actual start/stop, sessions, logged minutes |

Materialization **only** updates `execution_plan.tasks_json` envelope. Operator list merges plan operational tasks with reality lookup for status display.

### Can actuals change accepted quote?

Per architecture doc 11 and 16: **No** — actuals are downstream; quote/order commercial frozen snapshot is separate. Code path reviewed does not write back to `quotes` on reality start.

### Dangerous endpoints for QA (do not call in read-only QA)

- `POST /api/v1/execution/reality/start-task`
- `POST /api/v1/execution/reality/end-task`
- `POST /api/v1/execution/plan-v2/materialize-tasks/{id}` (if already materialized → 409)
- `PATCH /api/v1/execution/plan/{order_id}/tasks/{task_id}/assign`
- `PATCH .../instructions`
- Operator mobile task-action endpoints

---

## 9. Risk register

### CONFIRMED_OK

| Item | Observation |
|------|-------------|
| V2 materialize boundary | No ExecutionReality, no sessions (`no_sessions_created`, forbidden imports) |
| Parser no fallback | `operational_tasks_only` does not use `planned_tasks[]` when operational empty |
| Readiness gates | `v2_not_materialized` → 422 on assign/instructions/start (pytest covered) |
| Read models adoption | Dashboard, reports, operational reports, blueprint, operator use shared parser |
| `planned_tasks` preserved | Materialize asserts `planned_tasks` unchanged (hash check in service) |
| Fixture order 88001 | GET confirms ready state; reality 404; no session counts |

### WATCH

| Item | Severity | Recommendation |
|------|----------|----------------|
| `execution_tasks_created` naming | Low | Document in UI/dev docs — means materialized operational tasks, not reality sessions |
| Operator task default status `assigned` | Low | When no reality row, operator list shows `assigned` from plan — can look like work started; label-only fix later (Step 11) |
| `GET /execution/plan/{id}` unauthenticated | Medium | Dev convenience; confirm prod auth policy separately |
| Parallel V1 plan path | Medium | Legacy orders still use v1; V2 orders must use plan-v2 — gate exists but dual paths remain |
| No first-class QA seed script | Low | Owner GO for `seed_qa_v2_readiness_fixture.py` |
| Step 10 profitability | Medium | Runtime missing per doc 16 — future hardening needed |

### BLOCKER

**None identified** in this read-only audit for current Step 9.3.6 boundary scope.

### OWNER_DECISION

| Item | Decision needed |
|------|-----------------|
| Dedicated V2 QA seed script | Commit idempotent dev fixture script? |
| Next slice priority | Step 10 audit vs UI slice 2 vs `v2_not_materialized` UI label QA |
| Gate strict mode on canonical order `1` | Separate from V2 boundary; legacy fixture plan generation blocked (412) |

---

## 10. Files changed

| File | Change | Commit |
|------|--------|--------|
| `docs/worklog/realignment/2026-06-30_step_9_3_6_operational_reality_review_audit.md` | Created (this file) | none |

No other repo files modified.

## 11. Tests / validation

| Action | Result |
|--------|--------|
| Git preflight | PASS — only worklogs untracked |
| Architecture readback | PASS |
| Code trace | PASS |
| Runtime GET probes | PASS |
| pytest re-run | Not executed (audit used existing test references) |

## 12. Runtime status

| Service | PID | Status |
|---------|-----|--------|
| Backend :8000 | 40396 | healthy |
| Frontend :3000 | 29544 | HTTP 200 |
| Duplicate backend | None | single LISTENING |

## 13. Commit

**No commit created.**

## 14. Forbidden path confirmation

| Constraint | Confirmed |
|------------|-----------|
| No mobile | YES |
| No pricing / `/price` / CostEngine / QuoteOrchestrator | YES |
| No ExecutionReality/session logic modified | YES |
| No sessions created | YES |
| No task assignment / start / stop | YES |
| No DB writes | YES |
| No DB reset / reseed / migrations | YES |
| No push | YES |
| No redesign / implementation | YES |
| No script changes | YES |
| No `C:\Users\offic\workos` | YES |

## 15. What remains

1. Step 10 actuals/profitability hardening audit (recommended next)
2. Optional UI slice 2 (OperatorView/ShopFloor) — boundary now confirmed safe for plan-level readiness
3. Dedicated QA seed script (owner GO)
4. Browser QA for `v2_not_materialized` label state (pre-materialize snapshot)
5. Commit worklogs when owner approves

## 16. Owner decisions needed

1. Proceed to **Step 10 audit** vs **UI slice 2**?
2. Approve **dedicated QA seed script** in repo?
3. Commit worklog files under `docs/worklog/realignment/`?

## 17. Next recommended step

**Step 10 actuals/profitability hardening audit** — boundary between plan materialization and ExecutionReality/sessions is clean; Step 10 doc says profitability runtime is missing and should be audited before implementation.

## 18. Direction score

**Cat sunt in directia stabilita: 88/100%**

- Step 9.3.4–9.3.5.1 + controlled Re-QA: complete
- Step 9.3.6 boundary audit: complete (read-only)
- Step 10/7G runtime: not started (by design)
- Minor WATCH items do not block next audit
