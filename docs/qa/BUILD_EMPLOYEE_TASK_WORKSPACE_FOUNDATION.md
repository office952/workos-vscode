# BUILD: Employee Task Workspace Foundation

## 1. Purpose

Establish the minimum end-to-end path:

```text
Order / Production (execution plan)
→ planned task in execution_plan.tasks_json
→ runtime overlay in execution_reality.tasks_json
→ Employee Mobile Task Workspace (self-only)
→ start / block / complete / unblock
→ started_at / ended_at / block_reason tracked in reality JSON
```

Boundary: no auto-assign, no task pool, no push, no migrations, no seed changes, no document viewer.

## 2. Preflight

| Check | Result |
|-------|--------|
| Branch | `local/integration-pr4-plus-svg-path` |
| HEAD (before) | `1f03e43` — `feat(employee): improve operational employee administration` |
| Working tree | clean at build start |

## 3. Audit — task model

There is **no ORM `ExecutionTask` table**. Tasks live as JSON arrays:

| Store | Model | Key fields |
|-------|-------|------------|
| Plan | `execution_plan.tasks_json` | `task_id`, `name`, `display_name`, `process_id`, `process_type`, `machine_type`, `estimated_time_minutes`, optional `assigned_employee_id` (not populated by generator today) |
| Reality | `execution_reality.tasks_json` | `task_id`, `started_at`, `ended_at`, `blocked_at`, `unblocked_at`, `paused_at`, `resumed_at`, `block_reason`, `employee_id`, `employee_name`, `completed_by_employee_id` |

**Classification:** Exists now (JSON model). Employee Mobile wraps existing reality service; no new table.

## 4. Audit — status lifecycle

Derived in `operator_tasks.py` / `employee_mobile_tasks_service.py`:

| Derived status | Condition |
|----------------|-----------|
| `assigned` | no `started_at` |
| `in_progress` | `started_at`, not ended, not blocked |
| `blocked` | `blocked_at` without `unblocked_at` |
| `paused` | `paused_at` without `resumed_at` |
| `done` | `ended_at` set |

Romanian UI labels map via `StatusBadge domain="executionTask"` (`assigned` → „Alocat”, etc.). Employee Mobile groups use friendly copy: „De făcut”, „În lucru”, „Blocate”, „Finalizate recent”.

**Not supported:** block from `assigned` without start (fail-closed 422).

## 5. Audit — Order → Production

- Orders: `backend/models/orders.py` (status includes production states).
- Execution plan generation: `POST /api/v1/execution/plan/from-order/{order_id}` via `ExecutionPlanService.from_order`.
- **No automatic task generation** when order status changes — manual/API plan creation.
- Production UI: operator/tablet paths (`OperatorView`, `TabletMode`, `Productie.jsx` legacy).

**Classification:** Plan generation exists; auto-generation on production entry = **Deferred**.

## 6. Audit — task generation

| Source | Status |
|--------|--------|
| From order snapshot processes | Exists (`ExecutionPlanService`) |
| From quote accept | Not wired |
| On order → in_productie | Not wired |
| Demo/seed tasks | Dev DB may have reality rows |

**Classification:** Generator from snapshot = Exists; production-entry auto-gen = **Deferred**.

## 7. Audit — assignment

| Mechanism | Status |
|-----------|--------|
| `assigned_employee_id` in plan JSON | Supported by new mobile filter (optional field) |
| Pre-assignment in plan generator | Not populated |
| Claim-on-start (operator) | `employee_id` written on start |
| Department/skill/station eligibility | `OperatorEmployeeGuard` soft warnings only |

Employee Mobile list returns tasks where:

- `assigned_employee_id == current employee`, OR
- `reality.employee_id == current employee`, OR
- `reality.completed_by_employee_id == current employee`

**Classification:** Minimal assignment via optional JSON field + reality ownership = **Can implement safely now**. Full admin assignment UI = **Deferred**.

## 8. Audit — documents / attachments

- Work Intake / Quote attachments are not linked to execution tasks.
- Task payload exposes `documents: []` (empty until Order Document Handoff build).

**Classification:** **Deferred** — future build: Order Document Handoff to Production Tasks.

## 9. Endpoints added

| Method | Path | Notes |
|--------|------|-------|
| GET | `/api/v1/employee-mobile/tasks` | Self-only list |
| PATCH | `/api/v1/employee-mobile/tasks/{task_id}/start` | body `{ order_id }` |
| PATCH | `/api/v1/employee-mobile/tasks/{task_id}/block` | body `{ order_id, reason? }` |
| PATCH | `/api/v1/employee-mobile/tasks/{task_id}/complete` | body `{ order_id }` |
| PATCH | `/api/v1/employee-mobile/tasks/{task_id}/unblock` | body `{ order_id }` |

Auth: `require_employee_self_user` (roles: `employee_mobile`, `manager`, `admin` + linked active employee).

## 10. Frontend — Employee Mobile Task Workspace

| Area | Change |
|------|--------|
| Route | `/employee-app/tasks` live |
| Dashboard card | „Taskurile mele” with active summary badge |
| List | Grouped: De făcut / În lucru / Blocate / Finalizate recent |
| Detail | Metadata + start / block / complete / unblock |
| Access | `tasks` added to self routes in `employeeMobileAccess.ts` |
| Nav | No bottom-nav item (homepage card + route) |

## 11. Status transitions (Employee Mobile)

| From | Action | To | Notes |
|------|--------|-----|-------|
| `assigned` | start | `in_progress` | sets `started_at`, `employee_id` |
| `in_progress` | block | `blocked` | requires reason field optional |
| `in_progress` | complete | `done` | sets `ended_at`, `completed_by_employee_id` |
| `blocked` | unblock | `in_progress` | sets `unblocked_at` |
| `assigned` | block | — | **422** task_not_started |
| `assigned` | complete | — | **422** task_not_started |
| `done` | any mutation | — | **409/422** |
| other employee's task | any | — | **403** |

## 12. Security boundary

- Employee sees only owned/assigned tasks (not global pool).
- Cross-employee start/complete/block → 403.
- No linked employee → 403 `employee_link_missing`.
- Inactive employee → 403 `employee_not_active`.
- Manager/admin in Employee Mobile see **only their own** tasks on these endpoints (global admin task view = separate build).
- Review / Echipa mea guards unchanged.

## 13. Tests

### Backend

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_employee_mobile_tasks.py -q
```

Covers: empty list, assigned filter, start, cross-employee 403, complete, block-without-start 422, no employee link 403.

### Frontend

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run `
  src/lib/employeeMobileAccess.test.ts `
  src/pages/EmployeeMobileApp.test.tsx
```

## 14. Smoke (manual)

### employee_mobile

Backend impersonation: `WORKOS_DEV_AUTH_USER_ID=dev-employee-test-001`

- `/employee-app` — card „Taskurile mele”
- `/employee-app/tasks` — empty state or owned tasks only
- No Review / Echipa mea
- Start/complete if assigned task exists in dev DB

### admin

Backend impersonation: `WORKOS_DEV_AUTH_USER_ID=dev-admin-user-00000000`

- Review + Echipa mea preserved
- Taskurile mele empty unless admin user linked to employee with tasks

## 15. Production task auto-generation plan (deferred)

```text
Order intră în producție
→ citește product/template/snapshot
→ generează ExecutionTask pe etape (execution_plan.tasks_json)
→ fiecare task primește operation_type / department / instructions / document refs
→ admin atribuie assigned_employee_id sau task intră în pool eligibil
→ angajat vede taskul în Employee Mobile
→ angajat marchează start/block/complete
```

Missing pieces:

- template task definitions per product stage
- mapping produs → operații (beyond current snapshot processes)
- document refs on tasks
- assignment rules + admin UI
- eligibility/skill matrix enforcement (hard block)
- notification center / PWA push
- auto-generation trigger on order production status

## 16. Files changed

### Backend

- `backend/services/employee_mobile_tasks_service.py` (new)
- `backend/routers/employee_mobile_tasks.py` (new)
- `backend/tests/test_employee_mobile_tasks.py` (new)

### Frontend

- `frontend/src/api/employeeMobileTasks.ts` (new)
- `frontend/src/components/workos/employee-mobile/EmployeeMobileTasksPanel.tsx` (new)
- `frontend/src/components/workos/employee-mobile/EmployeeMobileHomeDashboard.tsx`
- `frontend/src/components/workos/employee-mobile/EmployeeMobileStates.tsx` (optional hint on empty state)
- `frontend/src/lib/employeeMobileAccess.ts`
- `frontend/src/lib/employeeMobileAccess.test.ts`
- `frontend/src/pages/EmployeeMobileApp.tsx`

### Docs

- `docs/qa/BUILD_EMPLOYEE_TASK_WORKSPACE_FOUNDATION.md` (this file)

## 17. Not touched

- Seeds (Axinte Remus, Calin Cimpean)
- CostEngine / Pricing / Inventory
- Operator permission map (`execution.task_*` still operator-only; mobile uses dedicated router)
- Auto-assign, push, offline sync, payroll
- Document viewer / upload
- DB migrations

## 18. Recommended commit message (after owner confirmation)

```text
feat(employee): add mobile task execution workspace
```
