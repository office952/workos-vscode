# BUILD — Employee Request Manager Review (dual context)

## Purpose

Add **manager/admin review** endpoints for employee requests while preserving **employee self app** for managers/admins with a valid `employees.user_id` link. Approve/reject updates request status only — no attendance/payment side effects.

## Owner correction

Managers are not only approvers. A manager linked as an employee must use the **self app** for own leave/requests. Review and self are **separate contexts**:

| Context | Routes | Who |
|---------|--------|-----|
| Employee self app | `/api/v1/employee-mobile/requests` | `employee_mobile`, `manager`, `admin` with active employee link |
| Manager review | `/api/v1/employee-requests/review` | `admin`, `manager` only |

## Self access role decision

`EMPLOYEE_SELF_ACCESS_ROLES = {employee_mobile, manager, admin}`

- Role grants **zone** access; `employees.user_id` grants **identity**
- Unlinked manager/admin → 403 `employee_link_missing`
- Linked `viewer` / `operator` / `sales` → 403 `employee_self_role_required`
- Self routes never grant review rights

## Review endpoints

Prefix: `/api/v1/employee-requests`

| Method | Path | Action |
|--------|------|--------|
| GET | `/review` | List `submitted` requests |
| GET | `/review/{request_id}` | Detail + safe employee display |
| PATCH | `/review/{request_id}/approve` | Approve submitted |
| PATCH | `/review/{request_id}/reject` | Reject submitted |

Body: `{ "review_note": "optional" }` — `extra=forbid`

## Roles allowed / denied

**Review:** `admin`, `manager` — denied: `employee_mobile`, `viewer`, `operator`, `sales`

**Self app:** `employee_mobile`, `manager`, `admin` (with link) — denied: others without role or link

## Self-approval prevention

If reviewer has active `employees.user_id` link and `request.employee_id` matches → 403 `self_review_forbidden`

Unlinked reviewer can still review others.

## Status transition rules

| From | Approve | Reject |
|------|---------|--------|
| `submitted` | → `approved` | → `rejected` |
| `draft` | 422 | 422 |
| `approved` / `rejected` / `cancelled` | 409 | 409 |

Server sets: `reviewed_at`, `reviewed_by_user_id`, `review_note`

## No side effects (confirmed)

- No `employee_attendance_events` writes
- No `employee_payment_records` writes
- No balances / advance ledger
- No payroll fiscal exposure
- No CostEngine / quote / pricing changes
- Review response excludes `cost_lunar_firma`, salary fields

## Files changed

| Path | Change |
|------|--------|
| `backend/dependencies/employee_mobile.py` | `EMPLOYEE_SELF_ACCESS_ROLES`, `require_employee_self_user` |
| `backend/dependencies/employee_request_review.py` | `require_employee_request_reviewer` |
| `backend/services/employee_request_service.py` | Review list/get/approve/reject |
| `backend/routers/employee_mobile_requests.py` | Use `require_employee_self_user` |
| `backend/routers/employee_request_review.py` | Review router |
| `backend/tests/test_employee_mobile_requests.py` | Dual-context self tests |
| `backend/tests/test_employee_request_review.py` | Review security tests |
| `docs/architecture/EMPLOYEE_MOBILE_IDENTITY_BOUNDARY.md` | Dual context section |

## Tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_employee_mobile_requests.py -v
.\.venv\Scripts\python.exe -m pytest tests/test_employee_request_review.py -v
```

## Boundaries

- No manager UI in this build
- No notifications
- No attendance integration on approve
- No payment/advance ledger on approve
- No team lead scope
- No frontend changes

## Deferred

- Manager review UI
- Notifications
- Attendance/payment hooks after approval
- Team lead roster scope

## Recommended commit message

```
feat(employee): add request manager review
```

## Status

READY for manual `git commit-tree` after review.
