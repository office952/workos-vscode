# BUILD — Employee Request Attendance Effects Apply Step

## Purpose

First **runtime** apply step: manual admin/operator application of `attendance_request_effects` → `employee_attendance_events`. Separate from approval; no auto-apply; no frontend; no payroll.

## Context

| Item | Value |
|------|--------|
| Branch | `local/integration-pr4-plus-svg-path` |
| HEAD before | `63dffb7` — `docs(employee): define attendance effects apply step decision` |
| Decision doc | `docs/architecture/EMPLOYEE_REQUEST_ATTENDANCE_EFFECTS_APPLY_STEP_DECISION.md` |

## Files inspected

- `docs/architecture/EMPLOYEE_REQUEST_ATTENDANCE_EFFECTS_APPLY_STEP_DECISION.md`
- `docs/architecture/EMPLOYEE_REQUEST_ATTENDANCE_INTEGRATION_DECISION.md`
- `backend/models/attendance_request_effect.py`
- `backend/services/attendance_request_effect_service.py`
- `backend/tests/test_employee_request_attendance_effects.py`
- `backend/models/employee_attendance_event.py`
- `backend/services/employee_attendance_service.py`
- `backend/routers/employee_attendance.py`
- `backend/models/employee_request.py`
- `backend/services/employee_request_service.py`
- `backend/tests/test_employee_mobile_requests.py`
- `backend/tests/test_employee_request_review.py`
- `backend/tests/test_employee_attendance_events.py`

## Files changed

| Path | Change |
|------|--------|
| `backend/services/attendance_request_effect_service.py` | `apply_attendance_request_effect`, idempotency via `source` |
| `backend/routers/employee_attendance.py` | `POST /effects/{effect_id}/apply`, admin/operator guard |
| `backend/tests/test_employee_request_attendance_effects.py` | Apply service + endpoint tests |
| `docs/qa/BUILD_EMPLOYEE_REQUEST_ATTENDANCE_EFFECTS_APPLY_STEP.md` | This doc |

## Model / service / endpoint decisions

### Model

No schema change. Existing fields used:

- Effect: `applied_at`, `applied_by_user_id`, `status`
- Attendance event linkage: `source = employee_request_effect:{effect_id}` (no `applied_attendance_event_id` FK)

### Service

`apply_attendance_request_effect(db, effect_id, applied_by_user_id)`:

1. Load effect + request
2. Refuse deferred types (`time_off`, `attendance_correction`) → `apply_unsupported`
3. Idempotent when `status == applied` (lookup by `source`)
4. Refuse `cancelled`, `conflict`, non-`pending`
5. Require request `approved`
6. Re-run `detect_attendance_effect_conflict`; on conflict set effect `conflict` and raise
7. Create attendance event via `create_attendance_event`
8. Mark effect `applied` with audit fields

### Endpoint

`POST /api/v1/employee-attendance/effects/{effect_id}/apply`

- Roles: **admin**, **operator** (`resolve_effective_role`)
- Responses: 200 apply, 403 forbidden role, 404 not found, 409 conflict, 422 unsupported

### Supported apply types

| Request | Effect type | Attendance event |
|---------|-------------|------------------|
| `leave` | `leave_range` | `event_type=leave`, range from effect dates |
| `day_off` | `day_off` | `event_type=leave` (interim policy — paid day off as leave) |

### Deferred apply types

- `time_off` / `partial_time_off` — no structured hours on request
- `attendance_correction` — no structured old/new payload
- Reversal / unapply
- Auto-apply on approve
- Frontend admin panel
- `applied_attendance_event_id` schema FK

## Permission decision

MVP apply roles: **`admin`** and **`operator`** only.

- `employee_mobile` (self): **403**
- `manager`: **403**
- No new `attendance_operator` role invented

## Conflict behavior

- Re-validates overlap before create
- On conflict: no attendance write; effect → `conflict` + reason; HTTP **409**
- Never deletes/overwrites existing events

## Idempotency behavior

- `source=employee_request_effect:{id}` on created event
- Retry on `applied` effect returns same `attendance_event_id`, `already_applied=true`
- No duplicate events per effect

## Audit behavior

- Effect: `applied_by_user_id`, `applied_at`
- Attendance: `source`, `notes` with request/effect ids
- Router: `logger.info` with effect/request/employee/event/actor
- **Gap:** no centralized audit logger in employee domain — deferred

## Tests run

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_employee_request_attendance_effects.py -v
.\.venv\Scripts\python.exe -m pytest tests/test_employee_mobile_requests.py tests/test_employee_request_review.py tests/test_employee_attendance_events.py -v
```

## Confirmations

| Guard | Status |
|-------|--------|
| Approval remains status-only | ✓ (no approve hook; review tests regression) |
| No auto-apply | ✓ |
| No frontend | ✓ |
| No DB/migration | ✓ |
| No payroll/payment/cost | ✓ |
| No reversal/unapply | ✓ |

## Recommended commit message

```
feat(employee): add attendance request effects apply step
```

## Verdict

**PASS** — 31 apply/foundation tests + 55 regression = **86 passed**.
