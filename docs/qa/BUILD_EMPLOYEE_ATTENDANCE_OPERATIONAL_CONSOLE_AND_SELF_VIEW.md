# BUILD — Employee Attendance Operational Console + Self View

## Context

| Item | Value |
|------|--------|
| Branch | `local/integration-pr4-plus-svg-path` |
| HEAD before | `e4c3f13` — `fix(employee): harden attendance access control` |
| Decision | `docs/architecture/EMPLOYEE_ATTENDANCE_OPERATIONAL_CONSOLE_DECISION.md` |

## Backend endpoints added/changed

| Method | Path | Role | Purpose |
|--------|------|------|---------|
| GET | `/api/v1/employee-mobile/attendance` | self (employee_mobile/manager/admin + link) | Read-only own events |
| GET | `/api/v1/employee-attendance/effects` | admin/operator | List effects with filters |
| GET | `/api/v1/employee-attendance/effects/{id}` | admin/operator | Effect detail |
| POST | `/api/v1/employee-attendance/effects/{id}/apply` | admin/operator | Unchanged (regression) |

## Frontend pages added/changed

| Path | Component |
|------|-----------|
| `/employee-app/attendance` | `EmployeeMobileAttendancePanel` (live read-only) |
| `/attendance/effects` | `EmployeeAttendanceEffects` console |
| `/attendance` | Link to effects console |

## API clients

- `frontend/src/api/employeeMobileAttendance.ts` — `listMyAttendanceEvents`
- `frontend/src/api/employeeAttendance.ts` — `listAttendanceEffects`, `getAttendanceEffect`, `applyAttendanceEffect`

## Permission model

- Self attendance: `require_employee_self_user`; rejects client `employee_id` (422)
- Effects list/detail/apply: `require_attendance_operator` (admin/operator)
- General CRUD unchanged — admin/operator only

## Supported actions

- Employee: view own pontaj (month navigation, refresh)
- Admin/operator: list/filter effects, view detail, manual apply pending

## Forbidden / deferred

- Self write, manager team view, auto-apply, reversal, payroll/payment

## Tests run

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_employee_attendance_events.py tests/test_employee_request_attendance_effects.py tests/test_employee_mobile_requests.py tests/test_employee_request_review.py -v
```

**Backend: 116 passed**

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/pages/EmployeeMobileApp.test.tsx
```

**Frontend: 27 passed**

## Manual smoke

Not re-run in this session (dev servers optional). Verified via automated tests + UI components wired to live API paths.

Recommended manual checks:

1. `/employee-app/attendance` — empty/list states
2. `/attendance/effects` — pending filter + apply button
3. 403 for non-operator on effects API

## Known limitations

- No frontend role-based menu hiding (403 handled in UI)
- No employee name on effects cards (employee_id only)
- Generate effect still separate from this UI (service/API not exposed in console)

## Confirmations

| Guard | Status |
|-------|--------|
| Employee self view read-only | ✓ |
| No client employee_id self view | ✓ |
| CRUD admin/operator only | ✓ |
| Effects console backend guard | ✓ |
| No auto-apply | ✓ |
| No reversal/unapply | ✓ |
| No payroll/payment/cost | ✓ |
| No DB/migration | ✓ |
| Approval status-only | ✓ |
| Manager team view deferred | ✓ |

## Verdict

**PASS**

## Recommended commit message

```
feat(employee): add attendance console and self view
```
