# BUILD — Employee Attendance Access Control Hardening

## Purpose

Close gap: attendance CRUD was available to any authenticated user. Align CRUD with apply endpoint — **admin/operator only**.

## Context

| Item | Value |
|------|--------|
| Branch | `local/integration-pr4-plus-svg-path` |
| HEAD before | `8f0ce07` — `feat(employee): add attendance request effects apply step` |
| Decision doc | `docs/architecture/EMPLOYEE_ATTENDANCE_ACCESS_CONTROL_DECISION.md` |

## Audit summary — endpoints before

| Method | Path | Op | Permission before | Risk |
|--------|------|-----|-------------------|------|
| GET | `/summary` | list | any authenticated | high |
| GET | `/events` | list/read | any authenticated | high |
| POST | `/events` | create | any authenticated | critical |
| PUT | `/events/{id}` | update | any authenticated | critical |
| DELETE | `/events/{id}` | delete | any authenticated | critical |
| POST | `/effects/{id}/apply` | apply | admin/operator | OK |

## Endpoint matrix after

All attendance routes (including summary, CRUD, apply) require `require_attendance_operator` → roles **admin**, **operator** via `resolve_effective_role`.

## Files changed

| Path | Change |
|------|--------|
| `backend/routers/employee_attendance.py` | Unified `require_attendance_operator` on all routes |
| `backend/tests/test_employee_attendance_events.py` | +19 permission tests |
| `backend/tests/test_employee_request_attendance_effects.py` | Relative event count assertion (isolation) |
| `docs/architecture/EMPLOYEE_ATTENDANCE_ACCESS_CONTROL_DECISION.md` | New |
| `docs/qa/BUILD_EMPLOYEE_ATTENDANCE_ACCESS_CONTROL_HARDENING.md` | This doc |

## Permission decision

- **admin / operator:** full attendance CRUD + apply
- **manager / employee_mobile / viewer / sales:** forbidden (403)
- **Self-read:** deferred (no general CRUD self access)
- **No new roles** — reuses `resolve_effective_role`

## Tests added

19 HTTP permission tests in `test_employee_attendance_events.py` covering list/create/update/delete for forbidden and allowed roles.

Apply regression: existing tests in `test_employee_request_attendance_effects.py` unchanged behavior.

## Tests run

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_employee_attendance_events.py tests/test_employee_request_attendance_effects.py tests/test_employee_mobile_requests.py tests/test_employee_request_review.py -v
```

**Result: 105 passed**

Breakdown: attendance 33, effects 31, mobile 23, review 18.

## Confirmations

| Guard | Status |
|-------|--------|
| No frontend | ✓ |
| No DB/migration | ✓ |
| No payroll/payment/cost | ✓ |
| No auto-apply | ✓ |
| Approval status-only | ✓ (review tests pass) |
| Apply admin/operator only | ✓ |
| CRUD no longer any authenticated user | ✓ |
| No self-read on general CRUD | ✓ |
| No manager write | ✓ |
| No employee_mobile write | ✓ |

## Recommended commit message

```
fix(employee): harden attendance access control
```

## Verdict

**PASS**
