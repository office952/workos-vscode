# BUILD — Employee Request Attendance Effects Foundation

## Purpose

Implement **`attendance_request_effects`** model and generation service for approved employee requests that may affect pontaj — idempotent, auditable, conflict-aware. **No auto-apply** to `employee_attendance_events` in this build.

## Context

- Branch: `local/integration-pr4-plus-svg-path`
- Base: `70a1228` — `docs(employee): define request attendance integration decision`
- Decision doc: `docs/architecture/EMPLOYEE_REQUEST_ATTENDANCE_INTEGRATION_DECISION.md`

## Files changed

| Path | Change |
|------|--------|
| `backend/models/attendance_request_effect.py` | New model |
| `backend/models/__init__.py` | Import for `create_all` |
| `backend/services/attendance_request_effect_service.py` | Generation + conflict + cancel |
| `backend/tests/test_employee_request_attendance_effects.py` | Foundation tests |
| `docs/architecture/EMPLOYEE_REQUEST_ATTENDANCE_INTEGRATION_DECISION.md` | §20 implemented foundation |
| `docs/qa/BUILD_EMPLOYEE_REQUEST_ATTENDANCE_EFFECTS_FOUNDATION.md` | This doc |

## Model fields

Table: `attendance_request_effects`

- Unique: `employee_request_id` (`uq_attendance_request_effects_request_id`)
- Statuses: `pending`, `applied`, `conflict`, `cancelled`
- Effect types: `leave_range`, `day_off`, `partial_time_off`, `attendance_correction`

## Service functions

| Function | Role |
|----------|------|
| `generate_attendance_effect_for_request` | Create pending/conflict effect; idempotent |
| `get_attendance_effect_for_request` | Fetch by request id |
| `detect_attendance_effect_conflict` | Evaluate conflict reason |
| `cancel_attendance_effect_for_request` | Cancel non-applied effect |

## Idempotency

One row per `employee_request_id`. Repeated `generate_*` returns existing row.

## Conflict rules

| Condition | Result |
|-----------|--------|
| Overlapping non-cancelled attendance event | `conflict` + `attendance_event_overlap:...` |
| `time_off` without hours on request | `conflict` + `time_off_requires_structured_hours` |
| `attendance_correction` without structured payload | `conflict` + `attendance_correction_requires_structured_payload` |
| Clean leave/day_off range | `pending` |

No deletion or modification of `employee_attendance_events`.

## Request type behavior

| Type | Effect |
|------|--------|
| `leave` | pending or conflict |
| `day_off` | pending or conflict |
| `time_off` | conflict (deferred) |
| `attendance_correction` | conflict (deferred) |
| `advance`, `equipment`, `issue_report`, `other` | skip (no row) |

## Endpoint

**None** — service-only; invoked from tests (and future worker/apply build).

## Tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_employee_request_attendance_effects.py -v
.\.venv\Scripts\python.exe -m pytest tests/test_employee_mobile_requests.py tests/test_employee_request_review.py tests/test_employee_attendance_events.py -v
```

## Boundaries (confirmed)

| Boundary | OK |
|----------|-----|
| No frontend | ✓ |
| No auto-apply to attendance events | ✓ |
| No payment / balance / payroll | ✓ |
| No CostEngine / Quote / Pricing | ✓ |
| No review endpoint change | ✓ |
| No migration (create_all in dev/test) | ✓ |

## Next build

**`Employee Request Attendance Effects Apply Step`** — apply pending effects to `employee_attendance_events` with conflict re-check.

Alternative: **`Employee Request Attendance Effects Admin Review UI`**.

## Recommended commit message

```
feat(employee): add attendance request effects foundation
```
