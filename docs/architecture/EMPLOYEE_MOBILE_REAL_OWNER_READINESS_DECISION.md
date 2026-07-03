# Employee Mobile Real Owner Readiness — Decision

## Status

| Field | Value |
|-------|--------|
| **Status** | Decision + Implementation |
| **Runtime impact** | explicit scripts/checkers only |
| **Backend impact** | operational scripts/services/tests |
| **Frontend impact** | none expected |
| **DB impact** | no schema expected |
| **Payroll impact** | none |

## Decizie

Testarea reală Employee Mobile cu ownerul cere:

```text
1. Owner user exists with effective admin/manager role (JWT/OIDC).
2. Owner user linked to active Employee (bootstrap script).
3. Direct reports explicitly assigned via employees.manager_employee_id.
```

## Reguli

**Owner employee**

- root operational employee;
- `manager_employee_id = null` (recommended);
- formal manager for direct reports;
- review/team when effective role is admin/manager;
- not a payroll record.

**Direct reports**

- assigned explicitly only;
- never inferred from department/workcenter/name alone;
- idempotent assignment script;
- overwrite requires `WORKOS_DIRECT_REPORTS_FORCE_REASSIGN=1`.

## Source of truth

| Concern | Source |
|---------|--------|
| Mobile self identity | `employees.user_id` |
| Manager team scope | `employees.manager_employee_id` |
| Auth capabilities | JWT/OIDC effective role |

## Scripts

| Script | Purpose |
|--------|---------|
| `bootstrap_owner_employee.py` | Link owner User → Employee |
| `assign_owner_direct_reports.py` | Set `manager_employee_id` on direct reports |
| `check_employee_mobile_readiness.py` | PASS/WARN/FAIL readiness report |

## Deferred

- Admin UI for manager assignment;
- org chart;
- bulk employee management UI;
- nested hierarchy;
- delegated approval;
- push/offline/native app;
- payroll separation UI.

## Related

- `docs/architecture/OWNER_EMPLOYEE_IDENTITY_BOOTSTRAP_DECISION.md`
- `docs/architecture/EMPLOYEE_FORMAL_MANAGER_REPORTING_DECISION.md`
- `docs/operations/OWNER_EMPLOYEE_MOBILE_READINESS.md`
- `docs/qa/BUILD_EMPLOYEE_MOBILE_REAL_OWNER_READINESS.md`
