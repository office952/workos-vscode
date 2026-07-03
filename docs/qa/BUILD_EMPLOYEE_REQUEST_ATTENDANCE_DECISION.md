# BUILD — Employee Request Approved Leave Attendance Decision Doc

## Purpose

Document architecture decision for linking **approved employee requests** to **internal attendance (pontaj)** — **docs / decision only**. No runtime, DB, or migration changes in this build.

## Context

- Branch: `local/integration-pr4-plus-svg-path`
- Base HEAD: `3e3377a` — `feat(employee): harden request review UX`
- Prior chain: mobile shell → self requests → manager review → review UI → UX hardening
- **Backend / frontend / DB unchanged in this build**

## Files changed

| Path | Change |
|------|--------|
| `docs/architecture/EMPLOYEE_REQUEST_ATTENDANCE_INTEGRATION_DECISION.md` | Decision document (new) |
| `docs/qa/BUILD_EMPLOYEE_REQUEST_ATTENDANCE_DECISION.md` | This QA doc (new) |

## Scope

- Audit attendance model and employee request types
- Classify request types vs pontaj impact
- Define MVP `attendance_request_effects` architecture (conceptual)
- Conflict matrix, idempotency, audit rules
- Future test plan

## Out of scope (confirmed)

- No backend runtime changes
- No frontend runtime changes
- No DB / migrations
- No attendance side effects on approve today
- No payment / balance / payroll fiscal integration
- No CostEngine / Quote / Pricing / Margins
- No team lead scope
- No notifications

---

## Audit — attendance findings

### Model

| Item | Finding |
|------|---------|
| Table | `employee_attendance_events` |
| Paradigm | **Event-based exceptions** on default-present schedule (Mon–Fri, 8h) |
| Punch clock | **No** check-in/check-out |
| Event types | `absent`, `leave`, `sick`, `partial`, `overtime`, `correction` |
| Statuses | `planned`, `approved`, `confirmed`, `cancelled` |
| Partial day | `partial` + `hours_override`; `overtime`/`correction` use delta/override |
| Conflicts | Service validation → HTTP 409 |
| Request link | **None** today (`source` default `manual`) |

### Endpoints

- `GET/POST /api/v1/employee-attendance/events`
- `PUT/DELETE /api/v1/employee-attendance/events/{id}`
- `GET /api/v1/employee-attendance/summary`

### Tests

- `backend/tests/test_employee_attendance_events.py` — ranges, partial, correction, conflicts, summary
- `backend/tests/test_employee_request_review.py` — **`test_approve_does_not_create_attendance_event`** (explicit no side effect)

### Risks if approve auto-writes attendance

1. Overwrites/conflicts with manually entered events (409 today if done naively).
2. No idempotency key → duplicate events on retry.
3. `day_off` / `time_off` have no 1:1 attendance type; wrong mapping.
4. `attendance_correction` needs structured old/new — request lacks fields.
5. Blurs workflow approval with operational pontaj truth.
6. Manager self-approval path must remain blocked.

---

## Request type classification (summary)

| Type | Attendance? | MVP effect |
|------|-------------|------------|
| `leave` | yes | pending → apply as `leave` range |
| `day_off` | yes | pending (mapping TBD: leave vs absent) |
| `time_off` | yes | **deferred** (no hours on request) |
| `attendance_correction` | yes | pending → apply as `correction` with validation |
| `advance` | no | forbidden |
| `equipment` | no | forbidden |
| `issue_report` | no | forbidden |
| `other` | no | forbidden (default) |

Full table: `docs/architecture/EMPLOYEE_REQUEST_ATTENDANCE_INTEGRATION_DECISION.md` §4.

---

## Decision summary

1. **Approve stays status-only** — no change to current approve/reject handlers.
2. **Dedicated `attendance_request_effects` layer** (future build) between approved request and `employee_attendance_events`.
3. **Idempotent** — one effect per approved request; `employee_request_id` as key.
4. **No auto-delete** of existing pontaj; conflicts → `conflict` or manual review.
5. **Audit** — request_id, approver, generator, applier, timestamps, correction snapshots.
6. **Partial day / time_off** deferred until request schema supports hours.
7. **Payroll fiscal** explicitly out of scope.

---

## Recommended MVP architecture

See decision doc §16 — **`attendance_request_effects`** table (conceptual) with statuses `pending`, `applied`, `conflict`, `cancelled`.

Flow: approve → generate pending effect → conflict check → apply creates attendance event(s).

---

## Conflict matrix summary

- Clean date + `leave` → eligible for apply (MVP may still start as pending).
- Existing leave/sick/absent → **CONFLICT**.
- `time_off` / incomplete correction → **DEFERRED** or **PENDING**.
- Rejected / non-attendance types → **FORBIDDEN**.
- Full matrix: decision doc Appendix A.

---

## Tests

| Gate | Result |
|------|--------|
| Backend pytest | **N/A** — docs-only build |
| Frontend vitest | **N/A** — docs-only build |
| Runtime smoke | **N/A** — docs-only build |

Future mandatory tests listed in decision doc Appendix C (10 cases).

---

## Commands run (audit)

```powershell
# Preflight
git branch --show-current   # local/integration-pr4-plus-svg-path
git rev-parse --short HEAD  # 3e3377a
git status --short          # clean before doc add

# Code inspection (read-only)
# backend/models/employee_attendance_event.py
# backend/services/employee_attendance_service.py
# backend/routers/employee_attendance.py
# backend/services/employee_request_service.py
# backend/tests/test_employee_attendance_events.py
# backend/tests/test_employee_request_review.py
```

---

## Boundaries (confirmed)

| Boundary | OK |
|----------|-----|
| No backend runtime | ✓ |
| No frontend runtime | ✓ |
| No DB / migrations | ✓ |
| No attendance side effects (runtime) | ✓ |
| No payment side effects | ✓ |
| No payroll fiscal | ✓ |
| No CostEngine / Quote / Pricing | ✓ |
| No sensitive data in new docs | ✓ |

---

## Next recommended build

**`Employee Request Attendance Effects Foundation`**

- Migration + service for `attendance_request_effects`
- Generator + apply + conflict integration with existing attendance service
- Tests from Appendix C
- Still no payroll/payment/CostEngine

---

## Recommended commit message

```
docs(employee): define request attendance integration decision
```
