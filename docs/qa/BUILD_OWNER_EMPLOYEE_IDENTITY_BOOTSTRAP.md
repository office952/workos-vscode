# BUILD: Owner Employee Identity Bootstrap

## Branch / HEAD

| Item | Value |
|------|--------|
| Branch | `local/integration-pr4-plus-svg-path` |
| HEAD before | `08380b9` — `feat(employee): add formal manager reporting link` |

## Audit summary

| Item | Finding |
|------|---------|
| User model | `users`: `id`, `email`, `name`, `role` (JWT/OIDC) |
| Employee model | `employees.user_id` → `users.id`; optional `manager_employee_id` |
| Active rule | Mobile self: `status=active` |
| Roles | JWT `role` + `resolve_effective_role`; mobile self: admin/manager/employee_mobile |
| Existing seed pattern | Manual scripts under `backend/scripts/` + `seeds/`; idempotent guards |
| Best location | `owner_employee_bootstrap_service.py` + scripts |

## Implementation

| Component | Path |
|-----------|------|
| Service | `backend/services/owner_employee_bootstrap_service.py` |
| Bootstrap script | `backend/scripts/bootstrap_owner_employee.py` |
| Readiness script | `backend/scripts/check_employee_mobile_readiness.py` |
| Tests | `backend/tests/test_owner_employee_bootstrap.py` |

## Env vars

| Variable | Purpose |
|----------|---------|
| `WORKOS_OWNER_EMAIL` | Lookup user by email |
| `WORKOS_OWNER_USER_ID` | Alternative lookup by user id |
| `WORKOS_OWNER_EMPLOYEE_NAME` | Required employee name |
| `WORKOS_OWNER_EMPLOYEE_DEPARTMENT` | Optional department |
| `WORKOS_OWNER_EMPLOYEE_TITLE` | Optional `employees.role` |
| `WORKOS_OWNER_BOOTSTRAP_DRY_RUN` | `1` = no DB writes |

## Idempotency

- Existing `employees.user_id` → update safe fields only / `already_linked`
- Unlinked name match (single) → `linked_existing_employee`
- Ambiguous name → error, no auto-link
- Re-run returns same `employee_id`

## Dry-run

Actions: `dry_run_would_create`, `dry_run_would_link_existing`, `dry_run_already_linked` — no commit.

## Readiness checker

Read-only PASS/FAIL: user, employee link, active status, `manager_employee_id` null, roles, direct reports count, pending review count.

## Role readiness

Bootstrap does **not** modify JWT roles. Owner tester needs `admin` or `manager` for review/team; `admin`/`manager`/`employee_mobile` for self mobile.

## Docs

- `docs/architecture/OWNER_EMPLOYEE_IDENTITY_BOOTSTRAP_DECISION.md`
- `docs/operations/OWNER_EMPLOYEE_MOBILE_READINESS.md`
- Updated identity/formal manager/integration state docs

## Frontend

Minimal: clearer `employee_link_missing` copy in `employeeRequestErrors.ts`.

## Manual smoke

Not run — owner user not verified in local DB session. See operations doc for steps.

## Tests run

| Suite | Result |
|-------|--------|
| Backend (6 files, incl. `test_owner_employee_bootstrap.py`) | **173 passed** |
| Frontend (`EmployeeMobileApp`, `EmployeeManagerTeamWorkspace`, `App`) | **41 passed** |

## PASS/FAIL

**PASS**

## HEAD after

(filled post-commit)

- [x] Owner can be linked to employee
- [x] No runtime hardcoding
- [x] Idempotent bootstrap
- [x] Dry-run safe
- [x] No payroll/payment/cost set
- [x] No attendance/requests created
- [x] No auth rewrite
- [x] No permission relaxation
