# BUILD — Employee Request Attendance Effects Apply Step Decision

## Purpose

Document **apply-step guards and contracts** for moving `attendance_request_effects` → `employee_attendance_events`. **Decision only** — no runtime, no frontend, no DB.

## Preflight

| Check | Result |
|-------|--------|
| Branch | `local/integration-pr4-plus-svg-path` |
| HEAD (start) | `ae23b2b` — `feat(employee): add attendance request effects foundation` |
| Working tree (start) | clean |
| Co-authored-by on HEAD | absent |

## Files inspected (read-only)

| Path |
|------|
| `backend/models/attendance_request_effect.py` |
| `backend/services/attendance_request_effect_service.py` |
| `backend/tests/test_employee_request_attendance_effects.py` |
| `backend/models/employee_attendance_event.py` |
| `backend/services/employee_attendance_service.py` |
| `backend/routers/employee_attendance.py` |
| `backend/tests/test_employee_attendance_events.py` |
| `backend/models/employee_request.py` |
| `backend/services/employee_request_service.py` |
| `backend/tests/test_employee_mobile_requests.py` |
| `backend/tests/test_employee_request_review.py` |
| `docs/architecture/EMPLOYEE_REQUEST_ATTENDANCE_INTEGRATION_DECISION.md` |
| `docs/qa/BUILD_EMPLOYEE_REQUEST_ATTENDANCE_EFFECTS_FOUNDATION.md` |

## Files changed

| Path | Change |
|------|--------|
| `docs/architecture/EMPLOYEE_REQUEST_ATTENDANCE_EFFECTS_APPLY_STEP_DECISION.md` | New apply-step decision |
| `docs/qa/BUILD_EMPLOYEE_REQUEST_ATTENDANCE_EFFECTS_APPLY_STEP_DECISION.md` | This QA doc |
| `docs/architecture/EMPLOYEE_REQUEST_ATTENDANCE_INTEGRATION_DECISION.md` | Short pointer to apply-step doc |

## Impact summary

| Area | Impact |
|------|--------|
| Runtime | **none** |
| Frontend | **none** |
| DB / migrations | **none** |
| Payroll / payment | **none** |
| Auto-apply to attendance | **none** |

## Decision summary

1. Apply is **separate** from approve — manual admin/operator in MVP.
2. Only `pending` effects with passing re-validation may apply.
3. Conflict → apply **refused**; no delete/overwrite of existing events.
4. Idempotent apply — no duplicate attendance events per request/effect.
5. `time_off` and structured `attendance_correction` apply **deferred**.
6. Proposed future endpoints under `/api/v1/employee-attendance/effects/*` — not implemented.
7. Proposed future field `applied_attendance_event_id` — documented only.

## Deferred items

See decision doc §13: auto-apply, scheduled job, reversal, frontend UI, manager apply, schema FK, day_off policy.

## Commands run

```powershell
# Preflight (read-only)
git branch --show-current
git rev-parse --short HEAD
git status -sb
git log -1 --oneline

# Backend regression (unchanged runtime)
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_employee_request_attendance_effects.py tests/test_employee_mobile_requests.py tests/test_employee_request_review.py tests/test_employee_attendance_events.py -v
```

## Test results

| Suite | Result |
|-------|--------|
| `test_employee_request_attendance_effects.py` | pass |
| `test_employee_mobile_requests.py` | pass |
| `test_employee_request_review.py` | pass |
| `test_employee_attendance_events.py` | pass |
| **Total** | **72 passed** |

## Git guard (end of build)

Expected:

- `git diff --cached --name-only` → empty (no staging)
- `git log -1 --oneline` → still `ae23b2b` (no new commit)
- `git diff --name-only` → only the 3 docs files listed above

## Boundaries (confirmed)

| Boundary | OK |
|----------|-----|
| No backend runtime | ✓ |
| No frontend | ✓ |
| No DB / migrations | ✓ |
| No auto-apply | ✓ |
| No payment / payroll / CostEngine | ✓ |
| No staging / commit | ✓ |

## Next build

**`Employee Request Attendance Effects Apply Step`** — implement `apply_attendance_effect` service + admin endpoints + tests from decision doc §12.

## Recommended commit message (when user requests)

```
docs(employee): define attendance effects apply step decision
```

## Final verdict

**PASS** — decision docs only; runtime unchanged; tests green.
