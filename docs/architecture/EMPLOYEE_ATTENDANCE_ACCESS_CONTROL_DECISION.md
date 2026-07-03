# Employee Attendance Access Control Decision

## Status

| Item | Value |
|------|--------|
| **Status** | Decision + Runtime Guard |
| **Runtime impact** | backend permissions only |
| **Frontend impact** | none |
| **DB impact** | none |
| **Payroll impact** | none |

## Context

Before this build, `/api/v1/employee-attendance/*` CRUD endpoints used `get_current_user` only — any authenticated user could list/create/update/delete pontaj events. Apply effect was already admin/operator only (`8f0ce07`).

Pontaj is sensitive operational data. CRUD must align with apply permissions.

## Regula principală

**Attendance CRUD is not permitted for any authenticated user.**

Only **admin** and **operator** may access attendance summary, list, create, update, delete, and apply effect.

## Endpoint matrix (after)

| Method | Path | Operation | Allowed roles |
|--------|------|-----------|---------------|
| GET | `/summary` | list/summary | admin, operator |
| GET | `/events` | list/read | admin, operator |
| POST | `/events` | create | admin, operator |
| PUT | `/events/{id}` | update | admin, operator |
| DELETE | `/events/{id}` | delete | admin, operator |
| POST | `/effects/{id}/apply` | apply | admin, operator |

## Permission matrix MVP

| Actor | List | Read | Create | Update | Delete | Apply |
|-------|------|------|--------|--------|--------|-------|
| admin | allowed | allowed | allowed | allowed | allowed | allowed |
| operator | allowed | allowed | allowed | allowed | allowed | allowed |
| manager | forbidden | forbidden | forbidden | forbidden | forbidden | forbidden |
| employee_mobile | forbidden | forbidden | forbidden | forbidden | forbidden | forbidden |
| viewer / sales / other | forbidden | forbidden | forbidden | forbidden | forbidden | forbidden |
| unauthenticated | forbidden | forbidden | forbidden | forbidden | forbidden | forbidden |

**Self-read employee:** deferred — future isolated route e.g. `/employee-app/attendance`.

**Manager team view:** deferred.

## Reguli obligatorii

1. Client does not dictate `employee_id` in self context (self routes deferred).
2. Server-side role resolution via `resolve_effective_role`.
3. Pontaj write is admin/operator operation.
4. Attendance ≠ payroll — no payment integration.
5. Apply behavior unchanged except shared guard with CRUD.
6. Request approve/reject remains status-only.
7. No auto-apply.

## Implementation

Router dependency: `require_attendance_operator` — roles `admin`, `operator`.

Uses existing `resolve_effective_role` from `dependencies/permissions.py`. No new role system.

Delete semantics unchanged (hard delete); permission restricted only.

## Deferred

- Employee self attendance view
- Manager team attendance view
- Attendance correction UI
- Advanced delegation
- Payroll export
- Centralized audit logger
- Soft-delete hardening

## Related docs

- `docs/architecture/EMPLOYEE_REQUEST_ATTENDANCE_EFFECTS_APPLY_STEP_DECISION.md`
- `docs/qa/BUILD_EMPLOYEE_REQUEST_ATTENDANCE_EFFECTS_APPLY_STEP.md`
