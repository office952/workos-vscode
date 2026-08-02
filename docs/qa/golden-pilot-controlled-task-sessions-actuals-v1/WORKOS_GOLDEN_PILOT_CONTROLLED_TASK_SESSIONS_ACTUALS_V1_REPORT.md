# WORKOS Golden Pilot â€” Controlled Task Sessions & ExecutionActuals V1

| Field | Value |
|-------|-------|
| Date | 2026-08-02 |
| Verdict | **PASS WITH WARNINGS** |
| Worktree | `C:\w\workos_sessions_actuals_v1` |
| Branch | `feat/controlled-task-sessions-actuals-v1` |
| Base | `2ea7de82` |
| DB | `backend/qa-dbs/sessions_actuals_v1.db` (isolated copy â€” not `dev.db`) |
| Ports (planned) | backend 8010 / frontend 3010 (domain proof via service + tests; UI start not enabled) |

---

## 1. Status

**PASS WITH WARNINGS**

Accepted warnings:

1. **Andrei (`employee_id=7`) has `user_id=null`** â€” Employee Mobile / self-actor start cannot be proven for the QA assignee. Supervisor path uses `execution.task_start` + `employee_id` that **must match assignment**.
2. **Operator / Tablet UI start button not enabled** in this slice â€” auth cannot safely present Andrei as the logged-in actor without inventing identity. Backend API + service tests are the acceptance proof.
3. **PREPRESS** remains unassigned / no invented auth â†’ start rejected as `task_unassigned`.
4. **Planning minutes** missing on LED â†’ actual duration valid; `variance_reason=planning_minutes_source_missing`.
5. Dependency-completion gate not invented (not enforced by current lifecycle for this path).

---

## 2. Research answers (summary)

1. Canonical store: `execution_reality.tasks_json` sessions (Owner Decision 07).
2. One ExecutionReality row per **order**.
3. Session identifies order + task_id + employee_id; plan id annotated on controlled writes.
4. Stable identity: operational `task_id` / `task_key`.
5. Multi-employee possible in legacy; controlled V1 blocks other active sessions on the task.
6. Controlled V1 rejects `employee_active_elsewhere`.
7. Controlled V1: one active session per task at start.
8. Pause/resume: legacy/mobile only â€” **not** in this V1.
9. Duration derived from timestamps (`compute_duration_minutes`).
10. Actual minutes on session + `total_actual_time_minutes` rollup + ExecutionActuals RM.
11. End session â‰  auto task completion (`task_auto_completed=false`).
12. Start requires assignment.
13. Supervisor start allowed via existing `execution.task_start` when `employee_id` matches assignment.
14. Actor = authenticated user; labor = `employees.id`.
15. No migration required.
16. Legacy `reality/start-task` can still bypass assignment â€” not used by controlled API.
17. No pricing/inventory/payroll writes.
18. Correct UI surface: Operator/Tablet (deferred enablement); Ops-Graph remains assign-only.

---

## 3. Architecture choice

New controlled wrapper over existing `ExecutionRealityService` â€” no parallel JSON store, no new table.

| Endpoint | Purpose |
|----------|---------|
| `POST /api/v1/execution/plan/{order_id}/tasks/{task_id}/sessions/start` | Controlled start |
| `POST /api/v1/execution/plan/{order_id}/tasks/{task_id}/sessions/end` | Controlled end |
| `GET /api/v1/execution/plan/{order_id}/execution-actuals` | Read model |

---

## 4. Fixture proof (isolated DB)

| Step | Result |
|------|--------|
| Before | assignment Andrei=7; sessions 0; reality null |
| PREPRESS start | `task_unassigned` |
| Wrong employee (5) | `employee_not_assigned` |
| Start Andrei @ 12:00Z | `ws-â€¦` active |
| Repeat start | `already_active=true` (no duplicate) |
| End @ 12:40Z | `duration_minutes=40` |
| Repeat end | same duration, `already_ended=true` |
| Assignment / plan tasks hash | unchanged |
| Protected 92401/973018 | unchanged |
| Commercial snapshot 973019 | unchanged |

Clock: injected deterministic timestamps (no sleep).

---

## 5. Files changed

- `backend/services/controlled_task_session_service.py` (new)
- `backend/routers/execution.py`
- `backend/tests/test_controlled_task_sessions.py` (new)
- QA report + `before-after.json` + worklog

---

## 6. Tests

**Run:** `tests/test_controlled_task_sessions.py` (4 passed) + live isolated DB script.
**Not run:** full backend suite; frontend e2e; Operator UI click path.

---

## 7. Boundaries held

No pause UI, no auto-complete, no materials, no HR cost, no pricing, no PREPRESS auth invention, no migration, no push of this commit, no mutation of canonical `dev.db`.

---

## 8. Dev-mode preservation

Controlled session routes use existing `get_current_user` + `require_permission("execution.task_start")`. No new bypass. Service tests inject actor_mode/clock without weakening production auth. DEV auth / `__DEV_BYPASS_TOKEN__` unchanged.

---

## 9. Progress scores

| Axis | Value |
|------|-------|
| Architecture direction | directionally sound |
| Functional spine | not yet measurable as % |
| UI/UX readiness | not yet measurable |
| Production readiness | not yet measurable |
| Overall product completion | **not yet measurable** |

## 10. Next

Functional: Profitability actual read model (separate Owner GO).
UI enablement: link Andrei `user_id` or supervisor Operator CTA after identity GO â€” not faked here.
