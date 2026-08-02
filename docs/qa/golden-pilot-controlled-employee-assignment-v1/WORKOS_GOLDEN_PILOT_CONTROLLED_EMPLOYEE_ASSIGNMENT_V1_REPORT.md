# WORKOS Golden Pilot — Controlled Employee Assignment V1

| Field | Value |
|-------|-------|
| Date | 2026-08-02 |
| Verdict | **PASS WITH WARNINGS** |
| Worktree | `C:\w\psiso` |
| Branch | `feat/capacity-batch-20d-scoped-b-92401` |
| Initial HEAD | `75e31d46` (pushed, ahead/behind 0/0) |
| Runtime | backend `http://127.0.0.1:8000` · frontend `http://127.0.0.1:3000` · DB `backend/dev.db` |
| Fixture | order **973019** / ExecutionPlan **21** / OD3 golden-pilot-eligibility-rm-v1 |

---

## 1. Status

**PASS WITH WARNINGS**

Accepted warnings:

- PREPRESS remains `blocked_no_matching_employee` (no invented WC_PREPRESS auth).
- Planning minutes missing for 17/18 tasks (`source_missing`) — eligibility `ready_with_warnings`.
- Full pytest suites not run; targeted assignment + eligibility + legacy-path tests only.
- UI “before” full-page on unassigned LED was not frozen before service mutation; evidence uses post-assign full page + remaining unassigned ready tasks for picker + PREPRESS blocked copy. Baseline JSON proves pre-assign `assign.unassigned=18`.

---

## 2. Scope

Implemented:

- Controlled assignment service wrapping existing `assign_plan_task`
- Default API path `controlled=true` with eligibility revalidation
- Ops-Graph compact assign UI (candidates from eligibility RM only)
- Targeted tests + QA fixture mutation on one LED task

Not implemented (boundaries):

- sessions / start-stop / actuals / scheduling / capacity / auto-assign / ranking / Employee Mobile / migrations / PREPRESS fake auth / 973018 repair

---

## 3. Research answers (canonical)

1. **Storage:** `execution_plan.tasks_json` → `operational_tasks[].assigned_employee_id` (+ `assignment_source`, `assignment_updated_at`).
2. **Cardinality:** one employee per task (0..1).
3. **Reusable service:** `assign_plan_task` — wrapped by `assign_operational_task_controlled`.
4. **Task identity:** stable `task_id` / `task_key` string (node:… path).
5. **Non-materialized:** eligibility RM status `blocked_not_materialized` → `task_not_materialized`.
6. **Ineligible employee:** must appear in current `eligible_employees[]`.
7. **Eligibility drift after assign:** next mutation revalidates; existing assignment not auto-cleared (V1).
8. **Unassign:** no public unassign; reassign only with explicit `allow_reassign=true` (V1 UI/API default false).
9. **Audit:** `assignment_updated_at`, `assignment_source=controlled_ops_graph_assign_v1`; actor passed as `actor_user_id` on response when auth present.
10. **Allowed statuses:** eligibility `ready` / `ready_with_warnings`; completed reality task still rejected by underlying service.
11. **Sessions/reality:** assignment does not create sessions/actuals (`sessions_created=0`, `actuals_created=0`; no reality row for 973019).
12. **Migration:** not required.

---

## 4. Gate A — PREPRESS/CNC authorization

- PREPRESS: no active employee with explicit WC_PREPRESS (or required) authorizations in registry → leave blocked.
- No name/title/heuristic authorizations added.
- Does not block LED assignment.

---

## 5. Gate B — Guards

Fail-closed errors exercised:

| Error | Evidence |
|-------|----------|
| `blocked_no_matching_employee` | PREPRESS assign rejected 422 |
| `employee_not_eligible` | employee_id=1 on LED rejected 422 |
| `assignment_conflict` / `task_already_assigned` | second employee while assigned → 409 |
| `task_not_materialized` | controlled default on legacy planner JSON → 422 (test) |
| Idempotent same employee | second assign Andrei → `already_assigned=true` |

---

## 6. Fixture mutation (QA only — not an operational recommendation)

| Field | Value |
|-------|-------|
| Order | 973019 |
| Task | `node:root_product:TPL-VOLUMETRIC-LETTERS_v2:INSTALL_LED_MODULES` |
| Operation | LED install / `WC_LED_ASSEMBLY` |
| Employee | **Andrei Goghi** (`employee_id=7`) — deterministic QA pick among Andrei/Costi/Vali |
| Source | `controlled_ops_graph_assign_v1` |

Before: 18 unassigned (`_tmp_baseline_before.json`).  
After: exactly 1 assignment (Andrei on LED install); other 17 tasks unchanged identity/WC/minutes.

---

## 7. Protected baseline

Orders `92401…973018`: snapshot + tasks_json SHA prefixes **identical** to pre-mutation baseline.

`973019`: snapshot hash identical (`2d412e6e…`); tasks_json changed only via assignment fields on the selected task.

Sessions/actuals for 973019: reality row absent; no session creation by this mutation path.

---

## 8. UI

Route: `http://127.0.0.1:3000/execution/ops-graph?orderId=973019`

- Eligible: `Neasignat` + `Eligibili: N` + `[Alege angajat]` → picker lists backend candidates only.
- Assigned: `Asignat: <name>`.
- PREPRESS: blocked copy, no active assign button.
- No auto-assign / ranking / cost / start-stop.

Screenshots: `docs/qa/golden-pilot-controlled-employee-assignment-v1/screenshots/`.

Honest page opinion: Ops-Graph remains dense and diagnostic-heavy; assignment fits the eligibility column without becoming a redesign. Day mode still inherits shell slate sidebar. Technical blockers correctly tucked under “Detalii tehnice”.

---

## 9. Files touched (product)

- `backend/services/controlled_employee_assignment_service.py` (new)
- `backend/routers/execution.py`
- `backend/tests/test_controlled_employee_assignment.py` (new)
- `backend/tests/test_execution_task_assignment.py` (legacy `controlled=false`)
- `frontend/src/api/executionTaskAssignment.ts`
- `frontend/src/pages/MaterializedOpsGraph.tsx`

---

## 10. Tests run / not run

**Run (14 passed):**

- `tests/test_controlled_employee_assignment.py`
- `tests/test_execution_task_assignment.py` (incl. controlled reject non-materialized)
- `tests/test_employee_eligibility_read_model.py`

**Not run:** full backend suite, full frontend suite, e2e Playwright CI.

Live script proofs: PREPRESS reject, ineligible reject, assign Andrei, idempotent repeat, conflict on other employee.

---

## 11. Boundaries / next

Next Functional GO: **Sessions / ExecutionActuals controlled vertical slice**.  
Next UI GO: **App Shell + Day Mode Foundation + Role-Based Navigation** (baseline already recorded in parallel track).

Employee Mobile remains deferred.

---

## 12. Progress scores (separate)

| Score | Value |
|-------|-------|
| Architecture direction | directionally sound (eligibility ≠ assignment) |
| Functional spine completion | not yet measurable as % |
| UI/UX readiness | not yet measurable as % |
| Production readiness | not yet measurable |
| Overall product completion | **not yet measurable** |
