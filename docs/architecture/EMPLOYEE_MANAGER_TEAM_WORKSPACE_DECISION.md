# Employee Manager Team Workspace — Decision

## Status

| Field | Value |
|-------|--------|
| **Status** | Decision + Implementation |
| **Runtime impact** | Backend manager read endpoints + frontend manager workspace |
| **DB impact** | `employees.manager_employee_id` — see formal reporting decision |
| **Payroll impact** | none |

## Regula principală

> **Manager team workspace is read-only for attendance.**

Generate/apply effects, attendance CRUD, and payroll remain admin/operator paths.

## Scope

### Manager poate

- vedea pontajul echipei directe (read-only);
- vedea cererile echipei (overview read-only);
- vedea cereri pending și naviga către review inbox;
- aproba/respinge cereri prin flow-ul existent `/employee-requests/review` (status-only).

### Manager nu poate

- crea/modifica/șterge attendance events;
- genera sau aplica attendance effects;
- vedea payroll/payment/cost fields;
- folosi `employee_id` client-side pentru a ieși din scope.

## Team scope source of truth

**Current (formal reporting link):**

```text
manager linked employee (employees.user_id, status=active)
  → team = active employees where manager_employee_id = manager's employee id
  → exclude self
admin → all employees (optional employee_id filter validated server-side)
manager without link or without direct reports → empty team (HTTP 200, [])
```

**Deprecated MVP (removed):** same `employees.department` as manager — was interim only, not HR reporting.

Review inbox is **direct-report scoped** for managers. Admin review remains all-scope.

See `docs/architecture/EMPLOYEE_FORMAL_MANAGER_REPORTING_DECISION.md`.

## Endpoints

| Method | Path | Guard | Purpose |
|--------|------|-------|---------|
| GET | `/api/v1/employee-mobile/manager/team-attendance` | admin/manager | Team attendance read-only |
| GET | `/api/v1/employee-mobile/manager/team-requests` | admin/manager | Team requests overview |

Filters: date range, status, request_type, `employee_id` (validated against scope).

## Permission matrix

| Actor | Own attendance | Team attendance read | Team requests overview | Attendance write | Effects generate/apply |
|-------|----------------|----------------------|------------------------|------------------|------------------------|
| `employee_mobile` | yes (self) | no | no | no | no |
| `manager` | yes (self) | yes (direct reports) | yes (direct reports) | no | no |
| `admin` | yes (self if linked) | yes (all) | yes (all) | yes | yes |
| `operator` | no* | no | no | yes | yes |
| `viewer` / basic | no | no | no | no | no |

\*Operator uses desktop attendance console, not Employee Mobile team workspace.

## Invariants

- No client `employee_id` authority on self flows.
- Manager team filters validated server-side (`team_scope_violation` → 403).
- Frontend filters are UX only.
- Attendance CRUD remains `require_attendance_operator`.
- Effects generate/apply remain admin/operator only.
- Approval remains status-only; team endpoints never mutate requests or attendance.
- No payroll/payment/cost exposure.

## Deferred

- Manager team attendance write;
- Manager team effect generation;
- Team scheduling;
- Payroll export;
- Advanced org hierarchy nesting / org chart UI;
- Bulk manager assignment UI;
- Multi-firm tenancy rules;
- Centralized audit logger;
- Offline mobile manager mode;
- Push notifications.

## Related

- `docs/architecture/EMPLOYEE_MOBILE_IDENTITY_BOUNDARY.md`
- `docs/architecture/EMPLOYEE_FORMAL_MANAGER_REPORTING_DECISION.md`
- `docs/architecture/EMPLOYEE_MOBILE_ATTENDANCE_INTEGRATION_STATE.md`
