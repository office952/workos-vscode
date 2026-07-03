# Employee Attendance Operational Console + Self View — Decision

## Status

| Item | Value |
|------|--------|
| **Status** | Decision + Implementation |
| **Runtime impact** | backend API + frontend UI |
| **DB impact** | none |
| **Payroll impact** | none |

## Ce construim

### Employee self attendance view

- Route UI: `/employee-app/attendance`
- API: `GET /api/v1/employee-mobile/attendance`
- Read-only list of own `employee_attendance_events`
- Identity via `require_employee_self_user` — no client `employee_id`
- Default range: current calendar month

### Admin/operator effects console

- Route UI: `/attendance/effects`
- API: `GET /api/v1/employee-attendance/effects`, `GET /effects/{id}`, `POST /effects/{id}/apply`
- List/filter pending/conflict/applied/cancelled
- Manual apply for pending only
- Backend guard: `require_attendance_operator` (admin/operator)

## Ce NU construim

- Payroll / salary / payment / CostEngine
- Manager team attendance view
- Self write (create/update/delete)
- General CRUD relaxation
- Auto-apply on approval
- Reversal / unapply
- DB migration (unless explicitly approved later)

## UX principles

- Employee mobile: simple, read-only, clear empty/error states
- Admin console: operational, status-visible, explicit apply action
- 403/409/422 surfaced in UI
- Backend is source of truth for permissions

## Related

- `docs/architecture/EMPLOYEE_ATTENDANCE_ACCESS_CONTROL_DECISION.md`
- `docs/architecture/EMPLOYEE_REQUEST_ATTENDANCE_EFFECTS_APPLY_STEP_DECISION.md`
