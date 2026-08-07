# MACHINE_RUN — Minimal Reservation Lifecycle Readiness

**Task:** `MACHINE_RUN_MINIMAL_RESERVATION_LIFECYCLE_READINESS`  
**Owner GO:** `AUTHORIZE_MACHINE_RUN_MINIMAL_RESERVATION_LIFECYCLE_READINESS`  
**Date:** 2026-08-07  
**Status:** **PASS** · docs-only · **no runtime · no QA writes**  
**Starting HEAD:** `db056724`  
**Prerequisites:** CREATE_MACHINE_RUN runtime PASS · s66 QA schema · R9 reservation lifecycle  
**Worklog:** `docs/worklog/realignment/2026-08-07_machine_run_minimal_reservation_lifecycle_readiness.md`

```text
MACHINE_RUN_MINIMAL_RESERVATION_LIFECYCLE_READINESS = PASS
CONFIRM_MACHINE_RUN = FINALIZED
RELEASE_MACHINE_RUN = FINALIZED
CANCEL_MACHINE_RUN = FINALIZED
CONFIRM_TRANSITION = HELD→RESERVED
RELEASE_TRANSITION = RESERVED→RELEASED
CANCEL_TRANSITIONS = HELD|RESERVED→CANCELLED
RUN_RESERVATION_STATE_COUPLING = ATOMIC
TERMINAL_STATES = RELEASED,CANCELLED
CAS = FINALIZED
IDEMPOTENCY = FINALIZED
R9_REUSE = FINALIZED
OVERLAP_OPEN_STATES = HELD,RESERVED
R6_STATE_BEHAVIOR = FINALIZED
PERMISSION = execution.machine_run.manage
DOMAIN_GATE = MACHINE_RESERVATION_ACTIVE
MACHINE_RUN_CONFIRM_RELEASE_CANCEL_RUNTIME_IMPLEMENTATION = PASS
MACHINE_RUN_RESCHEDULE_RUNTIME_READINESS = PASS
RESCHEDULE_MACHINE_RUN_RUNTIME_IMPLEMENTATION = PASS
RESCHEDULE_MACHINE_RUN = VERIFIED
MACHINE_RUN_PARTICIPANT_MUTATION_RUNTIME_READINESS = PASS
MACHINE_RUN_ADD_REMOVE_PARTICIPANT_RUNTIME_IMPLEMENTATION = PASS
RUNTIME_IMPLEMENTATION = VERIFIED
MACHINE_RUN_EXECUTION_LIFECYCLE = NOT_IMPLEMENTED
AUTO_BATCH = NOT_IMPLEMENTED
QA_MUTATIONS = 0
CAPACITY_STAGE_1 = IMPLEMENTED_INACTIVE
PHASE_B = NOT_AUTHORIZED
PHASE_C = BLOCKED
NEXT_TASK = NOT_AUTHORIZED
```

Implementation worklog: `docs/worklog/realignment/2026-08-07_machine_run_confirm_release_cancel_runtime_implementation.md`  
Reschedule readiness: `docs/architecture/MACHINE_RUN_RESCHEDULE_RUNTIME_READINESS.md`  
Reschedule implementation: `docs/worklog/realignment/2026-08-07_reschedule_machine_run_runtime_implementation.md`  
Participant mutation readiness: `docs/architecture/MACHINE_RUN_PARTICIPANT_MUTATION_RUNTIME_READINESS.md`  
Participant mutation implementation: `docs/worklog/realignment/2026-08-07_machine_run_add_remove_participant_runtime_implementation.md`

---

## 1. Why reservation lifecycle before RUNNING/COMPLETED

```text
CREATE_MACHINE_RUN → HELD / HELD
= grouping + provisional machine commitment
```

Next coherent step is to **confirm or dispose** that commitment:

```text
HELD → RESERVED → RELEASED
HELD|RESERVED → CANCELLED
```

That is machine-clock governance, not shop-floor execution.

```text
RESERVED ≠ RUNNING
RELEASED ≠ COMPLETED
```

`RUNNING` / `COMPLETED`, task start/stop, sessions, employee work remain a later GO.

---

## 2. Baseline (CREATE runtime — frozen for this readiness)

```text
POST /api/v1/execution/resource-state/machine-runs
→ machine_run HELD v1
→ run-owned reservation HELD v1
→ N participants ACTIVE (N ≥ 2)
→ CREATE_MACHINE_RUN + CREATE_RESERVATION histories
```

Permission: `execution.machine_run.manage`  
Domain: `MACHINE_RESERVATION` ACTIVE  
No CONFIRM/RELEASE/CANCEL MACHINE_RUN writers exist yet.

---

## 3. R9 lifecycle source (facts)

Task-owned reservation (`execution_task_machine_reservation_command_service.py`):

| Command | Allowed sources | Target |
| ------- | --------------- | ------ |
| CONFIRM_RESERVATION | HELD only | RESERVED |
| RELEASE_RESERVATION | HELD, RESERVED | RELEASED |
| CANCEL_RESERVATION | HELD, RESERVED | CANCELLED |

Open for overlap / R6 blocking: `{HELD, RESERVED}`  
Terminal: `{CANCELLED, RELEASED, SUPERSEDED}`  
CAS: `cas_stale` on reservation.version  
Idempotency: transition key + match on operation / previous_version / new_status / reason_code / actor

**MACHINE_RUN intentional divergence:**  
R9 allows `HELD → RELEASED`. MACHINE_RUN MVP uses **RELEASE only from RESERVED**; dispose of unconfirmed HELD via **CANCEL**. Clearer operator semantics for shared runs.

---

## 4. State transition matrix (finalized)

| Command | Run from → to | Reservation from → to |
| ------- | ------------- | --------------------- |
| CONFIRM_MACHINE_RUN | HELD → RESERVED | HELD → RESERVED |
| RELEASE_MACHINE_RUN | RESERVED → RELEASED | RESERVED → RELEASED |
| CANCEL_MACHINE_RUN | HELD → CANCELLED | HELD → CANCELLED |
| CANCEL_MACHINE_RUN | RESERVED → CANCELLED | RESERVED → CANCELLED |

Forbidden (reject `invalid_transition`):

```text
CONFIRM from RESERVED|RELEASED|CANCELLED|SUPERSEDED
RELEASE from HELD|RELEASED|CANCELLED|SUPERSEDED
CANCEL from RELEASED|CANCELLED|SUPERSEDED
any reopen (RELEASED/CANCELLED → HELD|RESERVED)
```

```text
TERMINAL_STATES = RELEASED, CANCELLED
```

`SUPERSEDED` remains schema vocabulary only — not in this command set.

---

## 5. Run / reservation coupling (atomic)

```text
run.status == reservation.status
```

must hold **before** and **after** every lifecycle command (for the run-owned reservation).

On load:

```text
if run.status != reservation.status
→ reject run_reservation_state_mismatch
```

No auto-heal.

Each command updates **both** rows + both histories in **one DB transaction**.  
Forbidden outcomes: half-confirmed / half-released / half-cancelled.

---

## 6. CONFIRM_MACHINE_RUN (finalized)

### Request

```text
ConfirmMachineRunCommand
  expected_version: int (≥ 1)   # machine_runs.version
  idempotency_key: str
  reason_code: str (default machine_run_confirm)
  reason_note: optional
  correlation_id: optional
```

Path id: `machine_run_id`  
Not accepted: machine_id, participants, window, capability (immutable after CREATE).

### Semantics

```text
allowed from = HELD / HELD
target       = RESERVED / RESERVED
```

- Window unchanged  
- Participants unchanged  
- Overlap still open (RESERVED remains blocking)

### CAS

```text
require run.version == expected_version
require reservation.version == expected_version   # lockstep defense
→ run.version += 1
→ reservation.version += 1
```

Versions remain independent columns; CREATE + lifecycle keep them equal when coupling holds.

---

## 7. RELEASE_MACHINE_RUN (finalized)

### Request

Same shape as CONFIRM (`expected_version`, idempotency, reason).  
Default reason: `machine_run_release`.

### Semantics

```text
allowed from = RESERVED / RESERVED
target       = RELEASED / RELEASED
```

```text
HELD → RELEASED = FORBIDDEN
use CANCEL_MACHINE_RUN for unconfirmed disposal
```

Sets `released_at` / `released_by` on both run and reservation (mirror R9 release columns).  
Historical window retained (no rewrite).  
Frees machine for future overlap (status leaves OPEN).

---

## 8. CANCEL_MACHINE_RUN (finalized)

### Request

Same shape. Default reason: `machine_run_cancel`.

### Semantics

```text
allowed from = HELD / HELD  or  RESERVED / RESERVED
target       = CANCELLED / CANCELLED
```

Sets `cancelled_at` / `cancelled_by` on both.  
Does **not** delete participants or histories.  
Frees machine for future overlap.

---

## 9. CAS (finalized)

```text
CAS = FINALIZED
caller expected_version = machine_runs.version
```

| Step | Run version | Reservation version |
| ---- | ----------- | ------------------- |
| CREATE | 1 | 1 |
| CONFIRM (expect 1) | 2 | 2 |
| RELEASE (expect 2) | 3 | 3 |
| or CANCEL from HELD (expect 1) | 2 | 2 |

Mismatch codes:

```text
cas_stale                      # expected_version ≠ run.version
run_reservation_state_mismatch # statuses or versions diverge before mutate
```

No shared single version column.

---

## 10. Idempotency (finalized)

Per command, transition idempotency on `machine_run_transitions.idempotency_key` (+ matching reservation transition key, R9 dual-key style).

Canonical fingerprint includes:

```text
operation ∈ {CONFIRM_MACHINE_RUN, RELEASE_MACHINE_RUN, CANCEL_MACHINE_RUN}
machine_run_id
expected_version
reason_code
reason_note          # include in match for MACHINE_RUN (stricter than R9 mutate)
actor_user_id
```

```text
same key + same fingerprint → already_applied=true, no new rows
same key + different fingerprint → idempotency_payload_conflict
```

---

## 11. R9 primitive reuse (finalized)

Reuse:

- status vocabulary OPEN/TERMINAL  
- window immutability on confirm/release/cancel  
- CAS +1 version pattern  
- history column shape  
- domain gate `require_active_domain_config(MACHINE_RESERVATION)`  
- overlap OPEN set (no mutate-time overlap check needed)  
- `released_*` / `cancelled_*` audit columns  

**Do not** call public `confirm_reservation` / `release_reservation` / `cancel_reservation` as-is:

| Blocker | Why |
| ------- | --- |
| TASK owner assumptions | fingerprints / transitions set `owner_form=TASK`, `machine_run_id=None` |
| `plan_order_lock` + `require_task_in_plan` | run-owned reservation has NULL plan/task |
| Result type | `ReservationCommandResult` requires non-null plan/task |

Implementation GO should add **internal** run-owned mutate helpers (or generalize `_mutate_reservation` with owner_form MACHINE_RUN + machine_lock), orchestrated by MACHINE_RUN commands in one transaction. Public reservation HTTP remains task-owned only.

```text
R9_REUSE = SEMANTICS_AND_HELPERS_NOT_PUBLIC_HTTP
```

---

## 12. Atomic transaction order (recommended)

```text
1. Idempotency precheck (run transition key)
2. machine_lock(run.machine_id)
3. load run FOR UPDATE
4. load run-owned reservation FOR UPDATE (by machine_run_id)
5. require domain ACTIVE
6. reject if reservation missing
7. reject if status/version mismatch (coupling)
8. validate expected_version + allowed source status
9. apply status + version + audit stamps on both
10. INSERT machine_run_transitions
11. INSERT reservation transition (owner_form=MACHINE_RUN)
12. COMMIT
```

Any failure → ROLLBACK ALL.

---

## 13. Participant invariance

```text
participant count unchanged
(execution_plan_id, task_key, order_id) unchanged
status remains ACTIVE (no REMOVE in this slice)
```

Lifecycle does not touch `machine_run_participants`.

---

## 14. Overlap behavior (finalized)

```text
OVERLAP_OPEN_STATES = HELD, RESERVED
```

| Status | In `find_overlapping_open` | Blocks new claim |
| ------ | -------------------------- | ---------------- |
| HELD | yes | yes |
| RESERVED | yes | yes |
| RELEASED | no | no |
| CANCELLED | no | no |

Same engine for task-owned and run-owned rows.

---

## 15. R6 behavior (finalized)

Vocabulary unchanged (`ACTIVE` / `CLEAR` / …). Path: participant ACTIVE → run → run-owned reservation.

| Run+Res status | Participant R6 machine_reservation.state |
| -------------- | ---------------------------------------- |
| HELD | ACTIVE |
| RESERVED | ACTIVE |
| RELEASED | CLEAR (if no other open commitment) |
| CANCELLED | CLEAR (if no other open commitment) |

Proof required in implementation GO on isolated DB for all four.

---

## 16. Permission (finalized)

```text
PERMISSION = execution.machine_run.manage
```

Reuse for CONFIRM / RELEASE / CANCEL. No three separate permissions for MVP.

---

## 17. Domain gate (finalized)

```text
DOMAIN_GATE = MACHINE_RESERVATION must be ACTIVE
```

No new MACHINE_RUN domain. DISABLED / NOT_CONFIGURED → write reject; reads remain possible per current R6 governance.

---

## 18. API contract (finalized)

Mount under existing resource-state style:

```text
POST /api/v1/execution/resource-state/machine-runs/{machine_run_id}/confirm
POST /api/v1/execution/resource-state/machine-runs/{machine_run_id}/release
POST /api/v1/execution/resource-state/machine-runs/{machine_run_id}/cancel
```

Explicit command endpoints (same pattern as reservations). No generic PATCH lifecycle.

---

## 19. Response contract (finalized)

Extend / mirror `CreateMachineRunResult` shape:

```text
machine_run_id
status                 # run
version                # run
reservation_id
reservation_status
reservation_version
machine_id
reservation_start / reservation_end / timezone
participants[]         # unchanged identities
operation              # CONFIRM_|RELEASE_|CANCEL_MACHINE_RUN
transition_id
reservation_transition_id
already_applied
previous_status / previous_version   # optional, R9-aligned
```

No commercial / Aggregate payloads.

---

## 20. Error contract (finalized)

Map to existing Resource State codes where possible:

| Situation | Code | HTTP |
| --------- | ---- | ---- |
| Unknown run | `machine_run_not_found` | 404 |
| Missing run-owned reservation | `reservation_not_found` | 404 |
| Wrong source status | `invalid_transition` | 409 |
| Run vs reservation status/version diverge | `run_reservation_state_mismatch` | 409 |
| CAS | `cas_stale` | 409 |
| Idempotency clash | `idempotency_payload_conflict` | 409 |
| Domain inactive | `domain_not_active` / `domain_disabled` | 409 |
| Permission | 403 | 403 |

Do not invent parallel `VERSION_CONFLICT` if `cas_stale` is canonical.

---

## 21. History (finalized)

Each successful command writes:

```text
1 machine_run_transitions row
1 execution_task_machine_reservation_transitions row
```

with previous/new status + version, actor, reason, timestamps.  
Reservation transition: `owner_form=MACHINE_RUN`, `machine_run_id` set, plan/task NULL.

---

## 22. CREATE regression boundary

CREATE remains:

```text
CREATE_MACHINE_RUN → HELD / HELD v1
```

No change to request/response/idempotency of create. Lifecycle tests must keep create suite green.

---

## 23. Capacity / Phase / execution boundaries

```text
CONFIRM/RELEASE/CANCEL
≠ Capacity allocate/deallocate
≠ employee assignment change
≠ task start/stop
≠ sessions
≠ Phase B / Phase C
≠ RUNNING / COMPLETED
```

```text
CAPACITY_STAGE_1 = IMPLEMENTED_INACTIVE
PHASE_B = NOT_AUTHORIZED
PHASE_C = BLOCKED
```

---

## 24. Next implementation GO (bounded)

**In:**

```text
Confirm/Release/CancelMachineRunCommand + Result
orchestrator service methods
internal run-owned reservation mutate (MACHINE_RUN owner_form)
atomic coupling + CAS + idempotency
API routes confirm/release/cancel
isolated tests: happy paths, negatives, R6 CLEAR after release/cancel
CREATE regression suite
R9 task-owned reservation regressions
```

**Out:**

```text
ADD/REMOVE participant
RESCHEDULE
SUPERSEDE
START/COMPLETE / RUNNING
auto-batch / nesting / UI
Capacity / Phase B
QA operational writes
```

```text
MACHINE_RUN_CONFIRM_RELEASE_CANCEL_RUNTIME_IMPLEMENTATION = PASS
RUNTIME_IMPLEMENTATION = VERIFIED
MACHINE_RUN_EXECUTION_LIFECYCLE = NOT_IMPLEMENTED
```

---

## 25. Overengineering check

| Candidate | Needed for HELD↔RESERVED↔RELEASED/CANCELLED? | Verdict |
| --------- | --------------------------------------------- | ------- |
| RUNNING/COMPLETED | no | defer |
| ADD/REMOVE participants | no | defer |
| RESCHEDULE window | deferred here; later VERIFIED in RESCHEDULE runtime GO | closed elsewhere |
| New permission per command | no | reject |
| New MACHINE_RUN domain | no | reject |
| Auto-heal mismatched statuses | no | reject |
| Call public R9 HTTP internally | no | reject |

---

## 26. QA proof (read-only this GO)

```text
QA Alembic = s66_machine_run_reservation_grain
QA SHA = b7950463b2956e779275e14fa81ee742a681ccee2e9f338a9db1310e1b740fb1
machine_runs / participants / transitions / reservations = 0
assignment transitions = 7
foreign_key_check = 0
QA_MUTATIONS = 0
```

---

## 27. `/modules` · `/governance`

```text
NO_UI_CHANGE
```

Docs: CREATE + CONFIRM/RELEASE/CANCEL + RESCHEDULE runtime VERIFIED in code · QA operational usage not activated · RESERVED ≠ RUNNING.
