# Employee Formal Manager Reporting Link — Decision

## Status

| Field | Value |
|-------|--------|
| **Status** | Decision + Implementation |
| **Runtime impact** | Backend manager scope + frontend manager workspace + review inbox |
| **DB impact** | `employees.manager_employee_id` (Alembic `s51_employee_manager_employee_id`) |
| **Payroll impact** | none |

## Decizie

**Chosen for this build:**

```text
employees.manager_employee_id → employees.id
```

**Why:**

- The manager is also an `employees` row with optional `user_id`.
- Reporting is between employees, not between user accounts alone.
- Supports managers who have login accounts and future org-chart expansion.
- Keeps HR reporting separate from auth role (`manager`).

**Alternatives documented, not implemented:**

| Alternative | Why not now |
|-------------|-------------|
| `employees.manager_user_id` | Mixes user identity with HR line; breaks when manager has no account |
| `employee_reporting_lines` table | Heavier schema; deferred until history/delegation needed |
| Department-based scope | Operational field only; not formal HR reporting (deprecated MVP) |

## Reguli

- `manager_employee_id` is nullable.
- An employee cannot be their own manager (`validate_manager_employee_id_assignment`).
- Team scope = active employees where `manager_employee_id = current manager's employee id`.
- Admin scope = all employees (optional filters validated server-side).
- Manager sees **direct reports only** — not same-department peers.
- Operator does not receive manager team scope automatically.
- `department` remains operational metadata — **not** team scope source of truth.
- No automatic backfill from `department` → manager.
- Root manager/owner employees typically have `manager_employee_id = null`; direct reports set `manager_employee_id` to the manager's employee id (manual/bootstrap — no assignment UI in bootstrap build).

## Invariants

- Manager team endpoints remain **read-only**.
- Manager review inbox uses formal direct-report scope.
- Attendance CRUD remains admin/operator only.
- Effects generate/apply remain admin/operator only.
- No payroll/payment/cost exposure.
- No client `employee_id` authority on self flows.
- Frontend filters are UX only; server validates scope.

## Deferred

- Nested hierarchy / org chart UI
- Multiple managers per employee
- Temporary delegated manager
- Historical reporting lines
- Bulk manager assignment UI
- Complex approval chains
- Multi-firm tenancy rules
- Centralized audit logger

## Related

- `docs/architecture/EMPLOYEE_MANAGER_TEAM_WORKSPACE_DECISION.md`
- `docs/architecture/EMPLOYEE_MOBILE_ATTENDANCE_INTEGRATION_STATE.md`
- `docs/architecture/OWNER_EMPLOYEE_IDENTITY_BOOTSTRAP_DECISION.md`
