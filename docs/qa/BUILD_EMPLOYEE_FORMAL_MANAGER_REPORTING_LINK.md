# BUILD: Employee Formal Manager Reporting Link

## Branch / HEAD

| Item | Value |
|------|--------|
| Branch | `local/integration-pr4-plus-svg-path` |
| HEAD before | `28ba744` — `fix(employee): isolate mobile app from desktop shell` |
| Build | Formal manager reporting link |

## Audit (pre-implementation)

| Question | Finding |
|----------|---------|
| Existing formal manager FK? | **No** — only `department` MVP scope |
| Migration system | Alembic under `backend/alembic/versions/` |
| Recommended field | `employees.manager_employee_id → employees.id` |
| Services affected | `employee_manager_team_service`, `employee_request_service` |
| Routers affected | `employee_manager_team`, `employee_request_review` |
| Tests affected | manager team, review, mobile requests (regression) |
| Migration risk | Low — nullable column, no backfill |
| Frontend impact | Copy + empty/403 states; no assignment UI |

## Schema / migration

- Model: `backend/models/employees.py` — nullable `manager_employee_id` FK + index
- Alembic: `s51_employee_manager_employee_id.py` (revises `s50_employee_payment_records`)
- Dev/test: `Base.metadata.create_all` picks up column without running Alembic
- **No** department → manager backfill

## Source of truth

```text
manager team scope = employees where manager_employee_id = manager's employee id (active only)
admin scope = all
department = operational only (deprecated for team scope)
```

## Endpoints updated

| Endpoint | Change |
|----------|--------|
| `GET /api/v1/employee-mobile/manager/team-attendance` | Direct-report scope |
| `GET /api/v1/employee-mobile/manager/team-requests` | Direct-report scope |
| `GET /api/v1/employee-requests/review` | Manager: direct reports only |
| `GET /api/v1/employee-requests/review/{id}` | Scope check |
| `PATCH .../approve`, `PATCH .../reject` | Scope check |

## Review inbox

- Manager list/detail/approve/reject limited to direct reports (`team_scope_violation` → 403)
- Admin unchanged (all requests)
- Self-review forbidden unchanged
- Approval remains status-only (no effect generation/apply)

## Frontend

- `EmployeeManagerTeamWorkspace.tsx` — direct-report copy, empty/403 messages
- `EmployeeMobileHomeDashboard.tsx` — team card description
- `employeeManagerTeam.ts`, `employeeRequestErrors.ts` — comments + error copy

## Tests run

### Backend

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_employee_manager_team_workspace.py tests/test_employee_request_review.py tests/test_employee_mobile_requests.py tests/test_employee_attendance_events.py tests/test_employee_request_attendance_effects.py -v
```

**Result:** 158 passed

### Frontend (targeted)

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/pages/EmployeeManagerTeamWorkspace.test.tsx src/pages/EmployeeMobileApp.test.tsx src/pages/EmployeeAttendanceEffects.test.tsx src/App.test.tsx
```

**Result:** 48 passed

## Manual smoke

Not run in this session (stack not started). Verify locally:

1. `/employee-app/team` — „raportează direct” copy
2. Team attendance / requests tabs
3. `/employee-app/review` — manager sees direct reports only
4. `/employee-app/attendance` self unchanged
5. `/attendance/effects` admin/operator unchanged

## Migration notes

Production/staged DBs: run Alembic upgrade through `s51_employee_manager_employee_id`. Assign `manager_employee_id` via admin/data ops — no automatic assignment in this build.

## PASS/FAIL

**PASS** — formal reporting link implemented; tests green; scope aligned.

## Confirmations

- [x] Formal reporting link implemented (`manager_employee_id`)
- [x] Department no longer source of truth for team scope
- [x] Manager review inbox scoped to direct reports
- [x] Manager team attendance read-only
- [x] Manager cannot attendance write
- [x] Manager cannot generate/apply effects
- [x] No payroll/payment/cost changes
- [x] No auto-apply / no reversal-unapply
- [x] Self flows unchanged
- [x] Approval status-only
- [x] No auth rewrite
- [x] No CostEngine / Quote / Pricing / ProductSystem changes
