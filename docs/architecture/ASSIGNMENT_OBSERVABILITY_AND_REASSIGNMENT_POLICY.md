# Assignment Observability and Reassignment Policy

**Status:** Wave 8 audit **COMPLETE** — reassignment **NOT IMPLEMENTED**  
**Date:** 2026-08-04  
**Owner GO:** `FINALIZATION_WAVE_8_AUTH_FAIL_CLOSED_AND_ASSIGNMENT_OBSERVABILITY_POLICY`  
**Related:** `ASSIGNMENT_COMMAND_REMEDIATION_DECISIONS.md` (DEC-ASSIGN-01…08)  
**Worklog:** `docs/worklog/realignment/2026-08-04_finalization_wave8_assignment_auth_observability_reassignment_policy.md`

```text
REASSIGNMENT_IMPLEMENTED = NO
UNASSIGNMENT_IMPLEMENTED = NO
SCHEMA_CHANGE = NO
WAVE_9 = NOT_AUTHORIZED
```

---

## 1. Production authentication fail-closed (Wave 8)

| Case | Contract | Evidence |
| ---- | -------- | -------- |
| `APP_ENV=production` + missing Authorization | **401 denied** | `test_production_blocks_dev_bypass_without_credentials`, Wave 8 suite |
| production + invalid / expired / wrong-key JWT | **401 denied** | Wave 8 suite |
| production + `DEBUG=true` | **Startup BLOCKED** (`DEBUG_MODE_OFF`); bypass still impossible | `startup_safety` + Wave 8 tests |
| staging / production | `dev_auth_allowed() == False` | `core/environment.py` |
| unknown / typo `APP_ENV` | **bypass denied** (fail-closed) | Wave 8 `dev_auth_allowed` hardening |
| missing `APP_ENV` (local default) | defaults to `development`; bypass permitted for local DX | documented — not production |

`DEBUG` never enables missing-auth bypass. Synthetic `dev-admin-user-00000000` exists only when `dev_auth_allowed()` is true.

---

## 2. Observability inventory (current model)

### Persistent business audit (embedded in `tasks_json`)

| Field | Status |
| ----- | ------ |
| `assigned_employee_id` | `IMPLEMENTED_AND_PROVEN` |
| `assignment_updated_at` | `IMPLEMENTED_AND_PROVEN` |
| `assignment_source` | `IMPLEMENTED_AND_PROVEN` (`canonical_controlled_assign_v1`) |
| `assignment_actor_user_id` | `IMPLEMENTED_AND_PROVEN` |
| Previous employee history on reassignment | `MISSING` (reassignment forbidden) |
| Dedicated assignment event table | `NOT_APPLICABLE` / deferred (DEC-ASSIGN-04/06 — no schema) |
| Correlation / request ID in DB | `MISSING` |

**Limit:** Embedded audit is sufficient for “who holds the task now + last successful assign metadata”. It is **not** a full append-only event log. Idempotent same-employee retry does **not** rewrite audit fields (no duplicate stamp).

### Operational application log

| Signal | Status |
| ------ | ------ |
| Safe structured `assignment_command` log on success / idempotent retry | `IMPLEMENTED_AND_PROVEN` (Wave 8) |
| Conflict / eligibility / auth denial structured assignment log | `PARTIAL` (HTTP detail + permission warning; not unified event stream) |
| Correlation ID propagation | `MISSING` |

### Security / HTTP

| Signal | Status |
| ------ | ------ |
| Permission denied warning (`user_id` only) | `IMPLEMENTED_AND_PROVEN` (Wave 8 PII fix) |
| uvicorn access log | `IMPLEMENTED_NOT_PROVEN` as business audit |
| Exception body leaking JWT / secrets | `PARTIAL` — auth logs exception type only |

### Classification reminder

Console / access logs ≠ persistent business audit. Do not invent an event table without Owner GO `OBSERVABILITY_SCHEMA`.

---

## 3. Privacy boundary

**Allowed:** actor user id, role, order id, plan id, task key, employee id, outcome codes, eligibility status codes, timestamps, authorization scope codes.

**Forbidden in logs/audit exports:** salary, CNP, address, phone, private email, full employee object, JWT / Authorization header, passwords/secrets, commercial pricing / internal cost, complete `tasks_json`, DB dumps.

API responses may still return `assigned_employee_name` to authorized operators — that is product UI truth, not an operational log field.

---

## 4. Required conceptual events

| Event | Trigger | Persistent / operational | Required fields | Forbidden |
| ----- | ------- | ------------------------ | --------------- | --------- |
| `ASSIGNMENT_SUCCEEDED` | CAS unassigned→employee | both (embedded + app log) | actor, order, plan, task, employee id, eligibility status, timestamp, outcome | JWT, pricing, full tasks_json |
| `ASSIGNMENT_IDEMPOTENT_RETRY` | same employee already assigned | operational log; no audit rewrite | same + `already_assigned` | same |
| `ASSIGNMENT_CONFLICT` | different employee / stale completed / session active | HTTP 409 (+ future ops log) | error code, current employee id if any | secrets |
| `ASSIGNMENT_AUTH_DENIED` | missing/invalid auth or missing permission | security/ops log | user id (if any), permission, role | email (prefer id), JWT |
| `ASSIGNMENT_ELIGIBILITY_DENIED` | DEC-015 / inactive employee | HTTP error | reason codes | full employee dossier |
| `ASSIGNMENT_STALE_STATE` | completed task etc. | HTTP 409 | reason | — |
| `ASSIGNMENT_LEGACY_BYPASS_REJECTED` | `controlled=false` / `allow_reassign=true` | HTTP 422 | error code | — |
| `ASSIGNMENT_DIRECT_SERVICE_BLOCKED` | `assign_plan_task` | HTTP 403 | `direct_assign_blocked` | — |
| `ASSIGNMENT_INTERNAL_FAILURE` | persist/audit inconsistency | HTTP 500 + error log | error code | payload dumps |

Deduplication: same-employee retry returns current state without second audit stamp.

---

## 5. Reassignment / unassignment code inventory

| Piece | Classification |
| ----- | -------------- |
| Public `allow_reassign=true` on assign body | `BLOCKED_LEGACY` (422) |
| `controlled=false` | `BLOCKED_LEGACY` (422) |
| Direct `assign_plan_task` | `BLOCKED_LEGACY` (403) |
| `allow_reassign` param on controlled service | `SUPERSEDED` (accepted then discarded; silent reassignment forbidden) |
| `clear_plan_task_assignment` | `ACTIVE_LEGACY` for frozen Mobile rollback helpers only — **not** a public unassign API |
| Mobile `claim_my_task` / `start_available_task` | `BLOCKED_LEGACY` / frozen (`employee_mobile_assignment_frozen`) |
| Desktop Assign UI (Ops-Graph) | `ACTIVE_CANONICAL` caller of controlled assign; no Reassign/Unassign product controls authorized |
| Employee Mobile Claim UI | `ACTIVE_LEGACY` surface; backend frozen |

```text
Dead pieces discovered: allow_reassign flag, clear helper, Mobile claim UI, public bypass fields
Dead pieces touched: none removed
Dead pieces removed: NONE
```

---

## 6. Policy options (Owner decision required — not implemented)

### Option A — Strict pre-start reassignment (recommended first build)

```text
actors: manager + admin (execution.task_assign + future reassign permission if split)
when: task not started; no active session; no schedule/reservation; not completed/cancelled
reason: required (coded enum + optional text)
history: previous employee + new + actor + reason + timestamp retained (may need schema GO)
concurrency: CAS expected current employee_id; no last-write-wins
unassignment: manager/admin only, same pre-start gates, reason required
employee acknowledgement: notification only (Mobile remains frozen)
scheduling: reassignment ≠ availability; HOLD remains until separate scheduling GO
```

### Option B — Controlled operational transfer (future / higher risk)

```text
active work handoff, session closure, planner intervention, employee acknowledgement
class: FUTURE — not first build
```

**Default recommendation:** Option A only after Owner answers DEC-REASSIGN-01…08.

---

## 7. Owner decisions required

| ID | Question | Recommended (not decided) |
| -- | -------- | ------------------------- |
| DEC-REASSIGN-01 | Who may reassign? | manager + admin |
| DEC-REASSIGN-02 | When allowed? | unstarted only; block completed/cancelled/active session/scheduled/reserved |
| DEC-REASSIGN-03 | History retention? | previous + new + actor + reason + timestamp (+ eligibility ref) |
| DEC-REASSIGN-04 | Reason code mandatory? | yes — enum + optional text |
| DEC-REASSIGN-05 | Unassignment? | allowed only before start, manager/admin, no session/schedule/reservation |
| DEC-REASSIGN-06 | Employee acknowledgement? | notification only until Mobile unfrozen |
| DEC-REASSIGN-07 | Concurrency? | expected current employee + CAS; no LWW |
| DEC-REASSIGN-08 | Scheduling interaction? | reassignment does not imply availability/start; separate scheduling GO |

---

## 8. Next step

```text
OWNER DECISION ON CONTROLLED PRE-START REASSIGNMENT POLICY
```

Do not implement reassignment until those decisions are recorded.
