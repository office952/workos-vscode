# BUILD: Employee Effects Generation Operational Closure

## Meta

| Field | Value |
|-------|--------|
| **Branch** | `local/integration-pr4-plus-svg-path` |
| **HEAD before** | `412f0db` — `chore(employee): harden mobile attendance integration` |
| **HEAD after** | _(post-commit)_ |
| **Status** | PASS |

## Backend endpoints added

| Method | Path | Guard | Purpose |
|--------|------|-------|---------|
| GET | `/api/v1/employee-attendance/effects/generation-candidates` | admin/operator | Approved requests needing effect |
| POST | `/api/v1/employee-attendance/effects/generate` | admin/operator | Idempotent effect row creation |

Payload generate: `{ "employee_request_id": number }` only.

Status codes:
- **201** — new effect
- **200** — existing effect (`already_exists: true`)
- **403** — insufficient role
- **404** — request missing
- **422** — not approved, skipped type, unsupported

## Frontend UI changes

- `/attendance/effects` tabs: **De generat** | **Efecte**
- Candidates list with **Generează efect** per row
- Copy: „Generarea pregătește efectul de pontaj. Aplicarea se face separat.”
- After generate → switch to Efecte tab (pending/conflict filter)
- API: `listAttendanceEffectGenerationCandidates`, `generateAttendanceEffect`

## Operational flow

### Before
Approve (status-only) → manual service call / no HTTP → apply in console.

### After
Approve → operator opens **De generat** → **Generează efect** → effect in **Efecte** → **Aplică în pontaj** → employee sees read-only attendance.

## Permission matrix

| Action | admin | operator | manager | employee_mobile |
|--------|-------|----------|---------|-----------------|
| List candidates | Yes | Yes | No | No |
| POST generate | Yes | Yes | No | No |
| List/apply effects | Yes | Yes | No | No |

## Idempotency

- Service: unique on `employee_request_id`; IntegrityError race refetch
- HTTP: second POST → 200 + `already_exists: true`

## Conflict / unsupported

- **leave/day_off**: pending or conflict (overlap) at generate
- **time_off/attendance_correction**: effect row with `status=conflict` (deferred apply)
- **advance/equipment/other**: HTTP 422 skipped
- Generate never writes `employee_attendance_events`

## Tests added

Backend (`test_employee_request_attendance_effects.py`): +14 HTTP generate/candidates tests.

Frontend (`EmployeeAttendanceEffects.test.tsx`): candidates section, generate API, no apply on generate, 403/422 UX.

## Tests run + results

```text
test_employee_request_attendance_effects.py → 54 passed
test_employee_attendance_events.py → (regression) PASS
test_employee_mobile_requests.py + test_employee_request_review.py → PASS
EmployeeAttendanceEffects.test.tsx → 7 passed
EmployeeMobileApp.test.tsx → 27 passed
```

## Manual smoke

Not run (stack local not started).

## Confirmations

- [x] No auto-generate on approve
- [x] No auto-apply
- [x] Approval status-only
- [x] Generate admin/operator only
- [x] Candidates admin/operator only
- [x] No attendance event on generate
- [x] Attendance event only on apply
- [x] No payroll/payment/cost
- [x] No DB/migration
- [x] No reversal/unapply
- [x] No manager team attendance
- [x] No client employee_id on self flows
