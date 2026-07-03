# BUILD — Employee Request Foundation (self-only)

## Purpose

Backend foundation for employee self-service **requests** under `/api/v1/employee-mobile/requests` — resolver-bound identity, role gate, generic request model, security tests. **No** attendance/payment/task integration in this build.

## Context

- Branch: `local/integration-pr4-plus-svg-path`
- Base HEAD: `d78e561` — `docs(employee): define mobile identity boundary`
- Architectural rule: client `employee_id` is never access authority; resolve via `employees.user_id`.

## Files changed

| Path | Change |
|------|--------|
| `backend/services/employee_mobile_identity.py` | `resolve_employee_for_user` + `ResolvedEmployee` |
| `backend/dependencies/employee_mobile.py` | `require_employee_mobile_self` dependency |
| `backend/models/employee_request.py` | `employee_requests` table model |
| `backend/services/employee_request_service.py` | create/list/get/cancel (no side effects) |
| `backend/routers/employee_mobile_requests.py` | self-only HTTP routes |
| `backend/models/__init__.py` | register model for `create_all` |
| `backend/dependencies/permissions.py` | add `employee_mobile` to `VALID_ROLES` |
| `backend/tests/test_employee_mobile_requests.py` | security + behavior tests |
| `docs/architecture/EMPLOYEE_MOBILE_IDENTITY_BOUNDARY.md` | implemented foundation section |
| `frontend/src/pages/EmployeeMobileApp.tsx` | Cereri card status placeholder only |

## Schema / migration behavior

- **No Alembic migration** in this build.
- Table `employee_requests` appears via existing dev/test `Base.metadata.create_all` after model import in `models/__init__.py`.
- Production staged migration (unique index on `employees.user_id`) remains **deferred**.

### `employee_requests` fields

`id`, `employee_id` (FK), `request_type`, `status` (default `submitted` on create), `title`, `description`, `start_date`, `end_date`, `amount`, `currency`, `reason`, `created_at`, `updated_at`, `submitted_at`, `reviewed_at`, `reviewed_by_user_id`, `review_note`.

**Request types:** `leave`, `day_off`, `time_off`, `advance`, `attendance_correction`, `equipment`, `issue_report`, `other`.

**Statuses:** `draft`, `submitted`, `approved`, `rejected`, `cancelled` — MVP create sets `submitted`.

## Resolver behavior

`resolve_employee_for_user(db, current_user)`:

| Condition | HTTP | error code |
|-----------|------|------------|
| No `employees.user_id` match | 403 | `employee_link_missing` |
| Multiple matches | 409 | `employee_link_ambiguous` |
| `status != active` | 403 | `employee_not_active` |
| Exactly one active link | OK | returns minimal `ResolvedEmployee` |

Never reads client `employee_id`.

## Role boundary

`require_employee_mobile_self`:

- Requires JWT role `employee_mobile` (via `resolve_effective_role`).
- Then calls resolver.
- **Denied:** `admin`, `manager`, `viewer`, `operator`, `sales` even if linked to an employee row.
- **Not** using dev bypass as security model in tests — explicit `get_current_user` overrides.

## Endpoints

Prefix: `/api/v1/employee-mobile`

| Method | Path | Behavior |
|--------|------|----------|
| GET | `/requests` | List own requests only |
| POST | `/requests` | Create for resolved employee; body `extra=forbid` (no `employee_id`) |
| GET | `/requests/{request_id}` | Detail own only → 404 for others |
| PATCH | `/requests/{request_id}/cancel` | Cancel own `draft`/`submitted` only |

No manager approval endpoints in this build.

## Tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_employee_mobile_requests.py -v
```

Coverage includes: resolver unit cases, create/list/detail/cancel, cross-employee deny, role deny, client `employee_id` 422, no attendance events, no payment records.

## Boundaries (confirmed)

- No attendance integration / no `employee_attendance_events` writes
- No payment integration / no `employee_payment_records` writes
- No payroll fiscal exposure
- No CostEngine / quote / pricing / margins changes
- No sensitive employee cost fields in responses
- No client `employee_id` authority
- No frontend live API wiring (shell placeholder only)
- No manager approval workflow

## Known debt

- Unique DB constraint on `employees.user_id` not enforced at DB level
- `draft` save flow deferred (UI)
- Manager/admin approval router deferred
- Attendance/payment ledger hooks on approve deferred
- `employee_mobile.*` permission keys not added to global matrix (local dependency only)

## Next build

**Employee Request UI — self-only create/list placeholder** — wire `/employee-app/requests` read-only to GET endpoints after auth persona exists.

## Recommended commit message

```
feat(employee): add self-only request foundation
```

## Status

READY for manual `git commit-tree` after review (not committed in agent session).
