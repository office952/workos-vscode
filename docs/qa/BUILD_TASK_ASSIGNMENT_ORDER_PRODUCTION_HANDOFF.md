# BUILD: Task Assignment / Order Production Handoff

## 1. Purpose

Connect execution plan tasks to employee assignment and Employee Mobile visibility without a parallel task system:

```text
execution_plan.tasks_json
→ assigned_employee_id (admin/operator assignment)
→ GET /api/v1/employee-mobile/tasks (self-only)
→ start/block/complete → execution_reality.tasks_json
→ /operator, /shop-floor, /tablet read same runtime
```

## 2. Preflight

| Check | Result |
|-------|--------|
| Branch | `local/integration-pr4-plus-svg-path` |
| HEAD (start) | `5f5ea63` — `feat(employee): add mobile task execution workspace` |
| Working tree | clean at start |
| Backend | `:8000` live (Dev Admin at smoke time) |

## 3. Audit — interface coherence

### Verdict: **PARTIAL**

All production UIs read **`execution_plan.tasks_json` + `execution_reality.tasks_json`** via `/api/v1/operator/tasks` or execution APIs. No fourth task store.

| Route | Component | Data source | Mutations | Notes |
|-------|-----------|-------------|-----------|-------|
| `/shop-floor` | `ShopFloor.tsx` + `useShopFloorData` | `/api/v1/operator/tasks`, `/api/v1/machines` | none | Falls back to mock if API fails + mock enabled |
| `/operator` | `OperatorView.tsx` + `useOperatorData` | `/api/v1/operator/tasks` | `POST /api/v1/operator/task-action` | Same reality; **assignment UI added here** |
| `/tablet` | `TabletMode.tsx` | `/api/v1/operator/task-action` (same API) | same as operator | Station queue from operator tasks pattern |
| `/employee-app` | `EmployeeMobileTasksPanel` | `/api/v1/employee-mobile/tasks` | PATCH start/block/complete/unblock | Self-only; same plan/reality |

**PARTIAL because:** shop-floor still has mock fallback path; no auto-generation on order → production; documents not linked to tasks.

## 4. Audit — Order → Execution Plan → Reality

| Item | Status |
|------|--------|
| Plan model | `execution_plan` table, `tasks_json` |
| Plan create | `POST /api/v1/execution/plan/from-order/{order_id}` |
| Reality model | `execution_reality.tasks_json` |
| Runtime fields | `started_at`, `ended_at`, `blocked_at`, `block_reason`, `employee_id`, `completed_by_employee_id` |
| Auto plan on `in_productie` | **Deferred** — manual/API plan generation only |
| `assigned_employee_id` in plan JSON | Supported (this build) |

## 5. Audit — documents

No task-level document refs. Payload returns `documents: []`. **Deferred:** Order Document Handoff to Production Tasks.

## 6. Implementation

### Backend

| File | Change |
|------|--------|
| `backend/services/execution_task_assignment_service.py` | Assign `assigned_employee_id` in plan JSON |
| `backend/routers/execution.py` | `PATCH /api/v1/execution/plan/{order_id}/tasks/{task_id}/assign` |
| `backend/dependencies/permissions.py` | `execution.task_assign` for admin/manager/operator |
| `backend/routers/operator_tasks.py` | Expose `assigned_employee_id`, `assigned_employee_name` |
| `backend/tests/test_execution_task_assignment.py` | Assignment + mobile visibility tests |

### Frontend

| File | Change |
|------|--------|
| `frontend/src/api/executionTaskAssignment.ts` | Assignment API client |
| `frontend/src/components/workos/OperatorTaskAssignmentPanel.tsx` | Admin/operator assignment UI |
| `frontend/src/pages/OperatorView.tsx` | Panel + plan assignee display |
| `frontend/src/hooks/useOperatorData.ts` | Map assigned fields from operator API |
| `frontend/src/lib/mockData.ts` | Optional assigned fields on `OperatorTask` |

### Employee Mobile

No change required — existing filter on `assigned_employee_id` + reality ownership.

## 7. Assignment flow

1. Admin/operator opens `/operator`.
2. Selects employee for a plan task → **Atribuie**.
3. `PATCH /api/v1/execution/plan/{order_id}/tasks/{task_id}/assign`
4. `assigned_employee_id` persisted in `execution_plan.tasks_json`.
5. Employee Mobile lists task for linked employee only.
6. Start/block/complete updates `execution_reality.tasks_json` (unchanged from prior build).

**Rules:**

- Cannot reassign tasks with `ended_at` in reality (409).
- Inactive/missing employee → 404/422.
- Does not modify reality on assign.

## 8. Security

| Boundary | Enforcement |
|----------|-------------|
| Assignment | `execution.task_assign` — admin/manager/operator |
| Mobile list | self-only (`assigned_employee_id` or reality ownership) |
| Mobile actions | ownership checks in `employee_mobile_tasks_service` |
| No global leak | Employee mobile never returns all system tasks |

## 9. Status transitions (unchanged)

| Action | From | To |
|--------|------|-----|
| start | assigned | in_progress |
| block | in_progress | blocked |
| unblock | blocked | in_progress |
| complete | in_progress | done |
| assign | any non-done plan task | plan JSON update only |

## 10. Tests

```powershell
cd backend
pytest tests/test_employee_mobile_tasks.py tests/test_execution_task_assignment.py -q
```

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/employeeMobileAccess.test.ts src/pages/EmployeeMobileApp.test.tsx
```

## 11. Smoke

### Admin assignment

Backend: `WORKOS_DEV_AUTH_USER_ID=dev-admin-user-00000000`

- `/operator` → assignment panel
- Assign plan task to Calin Cimpean (employee id 1) if plan exists (order 1 / T-001)

### Employee mobile

Backend: `WORKOS_DEV_AUTH_USER_ID=dev-employee-test-001`

- `GET /api/v1/employee-mobile/tasks` includes assigned task
- `/employee-app/tasks` shows task; start/block/complete updates reality

## 12. Deferred

- Auto-generation when order enters production
- Eligible task pool / auto-assign
- Skill matrix
- Push notifications / offline sync
- Document handoff Order → Task
- Document viewer complex
- Order status trigger wiring

## 13. Recommended commit message (after owner confirmation)

```text
feat(employee): connect production task assignment to mobile execution
```
