# BUILD: Employee Manager Team Workspace

## Meta

| Field | Value |
|-------|--------|
| **Branch** | `local/integration-pr4-plus-svg-path` |
| **HEAD before** | `ac35b03` — `docs(employee): close attendance integration group` |
| **Status** | PASS |

## Manager relationship audit

| Question | Finding |
|----------|---------|
| `manager_id` on employee? | **No** |
| `team_id` / `supervisor_id`? | **No** |
| Manager role | JWT/RBAC `manager` + optional `employees.user_id` link |
| Review scope today | **Global** — all submitted requests for any manager/admin |
| Helper for managed employees? | **Added** — `resolve_manager_team_scope` / `get_manager_team_employee_ids` |
| Fixtures | Tests seed manager + workers with `department` |

**Safest MVP:** department-based team (`employees.department` match), no schema change. Documented as interim until reporting FK.

## Team scope source of truth

```text
manager + active employee link → same department, exclude self
admin → all employees
manager without department/link → empty lists (200)
```

## Backend endpoints added

| Method | Path | Guard |
|--------|------|-------|
| GET | `/api/v1/employee-mobile/manager/team-attendance` | admin/manager |
| GET | `/api/v1/employee-mobile/manager/team-requests` | admin/manager |

## Frontend

| Route | Component |
|-------|-----------|
| `/employee-app/team` | `EmployeeManagerTeamWorkspace` |
| Dashboard card | „Echipa mea” → team workspace |

Tabs: Pontaj echipă | Cereri echipă. Read-only guard copy. Pending → link to `/employee-app/review`.

## Permission matrix

See `docs/architecture/EMPLOYEE_MANAGER_TEAM_WORKSPACE_DECISION.md`.

## Data isolation

- Manager: department-scoped queries; `employee_id` filter → 403 if outside team
- Admin: all employees; filter allowed
- Operator / employee_mobile / viewer: 403

## Read-only guarantees

- Team endpoints GET only; no attendance/event/request mutations
- Manager still blocked on attendance CRUD and effects generate/apply (regression tests)

## Tests added

- `backend/tests/test_employee_manager_team_workspace.py` (18 tests)
- `frontend/src/pages/EmployeeManagerTeamWorkspace.test.tsx` (5 tests)
- `EmployeeMobileApp.test.tsx` (+1 dashboard/team route)

## Tests run + results

```text
test_employee_manager_team_workspace.py + 4 regression files → 150 passed
EmployeeManagerTeamWorkspace.test.tsx + EmployeeMobileApp.test.tsx → 33 passed
```

## Manual smoke

Not run — stack local not started.

## Confirmations

- [x] Manager team attendance read-only
- [x] Manager cannot attendance write
- [x] Manager cannot generate/apply effects
- [x] Attendance CRUD admin/operator only
- [x] Self flows unchanged
- [x] Approval status-only (review path unchanged)
- [x] No payroll/payment/cost
- [x] No DB/migration
- [x] No auth rewrite
- [x] No auto-apply
- [x] No reversal/unapply
