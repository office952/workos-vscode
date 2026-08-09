# MACHINE_RUN — Execution Lifecycle Readiness

**Task:** `MACHINE_RUN_EXECUTION_LIFECYCLE_READINESS`  
**Owner GO:** `AUTHORIZE_MACHINE_RUN_EXECUTION_LIFECYCLE_READINESS`  
**Date:** 2026-08-07  
**Status:** **PASS** · docs-only · **no runtime · no QA writes**  
**Starting HEAD:** `836964d9`  
**Prerequisites:** CREATE + ADD/REMOVE + CONFIRM + RESCHEDULE + RELEASE/CANCEL runtime PASS · s66  
**Worklog:** `docs/worklog/realignment/2026-08-07_machine_run_execution_lifecycle_readiness.md`

```text
MACHINE_RUN_EXECUTION_LIFECYCLE_READINESS = PASS
EXECUTION_STATUS_SCHEMA_FOUNDATION = ACCEPTED_FINAL
MACHINE_RUN_EXECUTION_STATUS_QA_S67_ROLLOUT = PASS
START_COMPLETE_MACHINE_RUN_RUNTIME_IMPLEMENTATION = PASS
CODE_ALEMBIC_HEAD = s67_machine_run_execution_status
QA_ALEMBIC = s67_machine_run_execution_status
QA_BASELINE_ACCEPTED =
  7586819bb20087cd3df71a221ea0f2332bcb062952991a92afced287368d35b4
QA_SHA_AFTER_S67 =
  bee5f5f74c428fd03cf30ffd7377db00be3fa64716a29ce2652ae9f93b161322
MACHINE_RUN_STATUS_RUNNING = SUPPORTED
MACHINE_RUN_STATUS_COMPLETED = SUPPORTED
STARTED_AT = IMPLEMENTED_NULLABLE
COMPLETED_AT = IMPLEMENTED_NULLABLE
RESERVATION_STATUS_MODEL = UNCHANGED
START_MACHINE_RUN = PASS
COMPLETE_MACHINE_RUN = PASS
RELEASE_AFTER_COMPLETED = PASS
START_ALLOWED_FROM = RESERVED
COMPLETE_ALLOWED_FROM = RUNNING
RUNNING_RESERVATION_STATE = RESERVED
COMPLETED_RESERVATION_STATE = RESERVED
RUN_RESERVATION_COUPLING_MODEL = PHASE_AWARE_MATRIX
ACTUAL_RUNTIME_OWNER = MACHINE_RUN
ACTUAL_RUNTIME_MINUTES_PERSISTED = NO
PARTICIPANT_TASK_STATE_MUTATION = FORBIDDEN_IN_FIRST_SLICE
EMPLOYEE_SESSION_MUTATION = FORBIDDEN_IN_FIRST_SLICE
COMPLETE_RESERVATION_BEHAVIOR = SEPARATE_RELEASE
PAUSE_RESUME = DEFERRED
CANCEL_WHILE_RUNNING = FORBIDDEN
RESCHEDULE_WHILE_RUNNING = FORBIDDEN
PARTICIPANT_MUTATION_WHILE_RUNNING = FORBIDDEN
VERSION_MODEL = DUAL_BUMP_VERIFIED
HISTORY_MODEL = VERIFIED
R6_RUNNING = ACTIVE
R6_COMPLETED = ACTIVE_UNTIL_RELEASE
PERMISSION_START_COMPLETE = execution.machine_run.execute
RELEASE_PERMISSION = execution.machine_run.manage
DOMAIN_GATE = MACHINE_RESERVATION_ACTIVE
PHASE_B_IMPACT = DOCUMENTED_NOT_IMPLEMENTED
SCHEMA_STATUS_EXPANSION_REQUIRED = NO
START_COMPLETE_RUNTIME = PASS
QA_SCHEMA_ROLLOUT = PASS
QA_RUNTIME_MUTATIONS = 0
CAPACITY_STAGE_1 = IMPLEMENTED_INACTIVE
PHASE_B = NOT_AUTHORIZED
PHASE_C = BLOCKED
FRONTEND_CHANGED = NO
EMPLOYEE_MOBILE_CHANGED = NO
NEXT_TASK = NOT_AUTHORIZED
```

---

## 1. What RUNNING means in the workshop (plain language)

Today the system can already:

```text
group CNC tasks into one MACHINE_RUN
correct who is in the group (HELD)
confirm the machine is committed (RESERVED)
move the booked window
release or cancel the booking
```

None of that means the spindle is turning.

```text
RESERVED  = “this CNC interval is ours — do not give the machine to someone else”
RUNNING   = “the shop floor has started this machine run for real”
COMPLETED = “the shop floor finished the machine work for this run”
RELEASED  = “the booking is over — the machine clock is free again”
```

Critical separations (non-negotiable):

```text
machine reservation commitment
≠
machine execution (this readiness)
≠
employee work session (ExecutionReality)
≠
participant task “in progress/done” (session-derived)
```

A CNC run can be **RUNNING** while:

- reservation stays **RESERVED** (machine still booked),
- employees may or may not have open labor sessions,
- individual tasks may still show assigned/pending until someone starts a session.

First execution slice must **not** pretend one button starts all four worlds.

---

## 2. Baseline (frozen)

```text
CREATE / ADD|REMOVE / CONFIRM / RESCHEDULE / RELEASE / CANCEL = PASS
MACHINE_RUN statuses today = HELD|RESERVED|CANCELLED|RELEASED|SUPERSEDED
Reservation statuses today = same five (no RUNNING/COMPLETED)
_assert_coupled today = run.status == reservation.status AND versions equal
R6 blocking = HELD|RESERVED on reservation rows
Labor actuals SoT = execution_reality sessions
Machine actual runtime = absent (gap)
PHASE_B = NOT_AUTHORIZED (stub guards)
```

QA: MACHINE_RUN tables empty · Capacity NOT_CONFIGURED · Phase B/C blocked.

---

## 3. Owner decisions (closed)

| ID | Decision | Verdict |
| -- | -------- | ------- |
| **D1** | START allowed only from **RESERVED** | **FINALIZED** |
| **D2** | Reservation stays **RESERVED** while run is **RUNNING** | **FINALIZED** |
| **D3** | Status lockstep **ends at START**; replace with phase-aware matrix; keep dual version bumps | **FINALIZED** |
| **D4** | **MACHINE_RUN** owns machine actual runtime (`started_at` / `completed_at` / derived minutes) | **FINALIZED** |
| **D5** | START does **not** mutate participant task / plan operational states | **FINALIZED** |
| **D6** | START does **not** create employee sessions | **FINALIZED** |
| **D7** | COMPLETE does **not** auto-RELEASE — separate **RELEASE** after COMPLETED | **FINALIZED** (Option A) |
| **D8** | PAUSE / RESUME **deferred** | **FINALIZED** |
| **D9** | CANCEL while RUNNING **forbidden** | **FINALIZED** |
| **D10** | Prefer new **`execution.machine_run.execute`** for START/COMPLETE; keep `manage` for orchestration | **FINALIZED** · wired in runtime GO |

### D1 — START from RESERVED only

HELD is still grouping. CONFIRM seals the commitment. Starting shop-floor work from HELD would skip the commitment gate already implemented.

```text
HELD → RUNNING     FORBIDDEN
RESERVED → RUNNING ALLOWED (implemented)
```

### D2 — Reservation during RUNNING

Reservation vocabulary has no RUNNING and must not invent one. Exclusive machine clock remains RESERVED so:

- R6 stays **ACTIVE**
- overlap OPEN set still blocks new claims
- workshop meaning stays “machine is still booked while we cut”

### D3 — Coupling redesign (critical)

Today:

```text
run.status == reservation.status
AND
run.version == reservation.version
```

After START under D2, status equality **cannot** hold. Readiness finalizes:

```text
Commitment phase (unchanged writers):
  HELD/HELD
  RESERVED/RESERVED
  RELEASED/RELEASED
  CANCELLED/CANCELLED

Execution phase (new matrix):
  RUNNING/RESERVED
  COMPLETED/RESERVED

Then back to commitment dispose:
  RELEASED/RELEASED   via RELEASE from COMPLETED+RESERVED
```

**Terminal membership (2026-08-09 hardening):** RELEASE/CANCEL (and SUPERSEDED) set ACTIVE participants → `REMOVED` so tasks can re-enter a future MachineRun. Blocking eligibility = ACTIVE ∩ non-terminal run (`HELD|RESERVED|RUNNING|COMPLETED`). Historical rows retained; no schema change. Worklog: `docs/worklog/realignment/2026-08-09_machine_run_terminal_membership_reeligibility_hardening_fix.md`.

**Version model (V1):** START and COMPLETE still bump **both** `run.version` and `reservation.version` (lockstep metadata), even if reservation status/window unchanged — same structural pattern as participant mutation / reschedule.  
`_assert_coupled` becomes **phase-aware** (allowed pairs + version equality), not blind status equality.

CAS remains:

```text
expected_version = machine_run.version
```

### D4 — Actual runtime owner

```text
MACHINE_RUN owns:
  started_at
  completed_at
  actual_runtime_minutes (derived)
```

Not Reservation (planned window only). Not each participant (would multiply machine minutes).  
Aligns with Owner batch rule: **machine time counted once per run**.

Labor minutes remain in `execution_reality` sessions — different concept.

### D5 — Participant task states

Repo fact: plan `operational_status` is not shop-floor SoT; task “in_progress/done” is session-derived; MACHINE_RUN never touches ExecutionReality today.

```text
START_MACHINE_RUN → NO automatic task start
COMPLETE_MACHINE_RUN → NO automatic task complete
```

If Owner later wants linkage, that is a **separate coupling GO**.

### D6 — Employee / sessions

Repo fact: sessions live in `execution_reality.tasks_json`; controlled start needs assigned employee; multi-plan runs make “which employee?” ambiguous.

```text
START_MACHINE_RUN → NO session create/end
```

Operators may still start labor sessions independently via existing task session APIs.

### D7 — COMPLETE vs RELEASE (Option A)

```text
RUNNING → COMPLETED          (run only; reservation stays RESERVED)
COMPLETED+RESERVED → RELEASED/RELEASED   (existing RELEASE semantics, extended source)
```

Why not Option B (auto-RELEASE on COMPLETE):

- Docs already teach `RELEASED ≠ COMPLETED`
- Workshop may need a brief post-complete window (cleanup, QA) while machine remains booked
- Keeps CANCEL / RELEASE / COMPLETE as distinct verbs

### D8 — PAUSE / RESUME

```text
PAUSE_RESUME = DEFERRED
```

Not required for first real lifecycle. Avoids exploding the coupling matrix.

### D9 — CANCEL while RUNNING

```text
CANCEL_MACHINE_RUN sources remain HELD|RESERVED only
RUNNING → CANCEL FORBIDDEN
```

Aborting live machine work needs a future explicit STOP/ABORT design — not silent CANCEL reuse.

### D10 — Permission

```text
manage  = admin/manager orchestration (create, membership, confirm, reschedule, release, cancel)
execute = recommended for START/COMPLETE (align roles with task_start/task_complete → include operator)
```

Runtime GO wired `execution.machine_run.execute` for START/COMPLETE (`admin`/`manager`/`operator`); RELEASE stays on `execution.machine_run.manage`.

---

## 4. Commands (contracts only)

### START_MACHINE_RUN

```text
from: RESERVED (+ reservation RESERVED, coupled versions)
to:   run RUNNING / reservation RESERVED
sets: run.started_at = now (server)
bumps: run.version += 1, reservation.version += 1
history: START_MACHINE_RUN on run; reservation lockstep companion (same-status RESERVED)
forbids: task mutation, session mutation, window change, participant change
```

### COMPLETE_MACHINE_RUN

```text
from: RUNNING (+ reservation RESERVED)
to:   run COMPLETED / reservation RESERVED
sets: run.completed_at = now; actual_runtime from started_at→completed_at
bumps: both versions += 1
history: COMPLETE_MACHINE_RUN + reservation lockstep companion
then: separate RELEASE_MACHINE_RUN → RELEASED/RELEASED
```

### Forbidden while RUNNING or COMPLETED

```text
ADD/REMOVE participant
RESCHEDULE
CANCEL (RUNNING)
START from non-RESERVED
```

RELEASE from COMPLETED+RESERVED: **allowed** (extends today’s RELEASE source set in implementation).

---

## 5. Schema sufficiency

**s67 (`s67_machine_run_execution_status`) — code schema foundation PASS.**

```text
machine_runs.status CHECK includes RUNNING|COMPLETED
machine_runs.started_at  nullable (no backfill)
machine_runs.completed_at nullable (no backfill)
Reservation status vocabulary UNCHANGED (no RUNNING/COMPLETED)
machine_run_transitions can store RESERVED→RUNNING / RUNNING→COMPLETED structurally
actual_runtime_minutes NOT persisted (derive later from completed_at - started_at)
```

```text
SCHEMA_STATUS_EXPANSION_REQUIRED = NO
SCHEMA_ACTUAL_RUNTIME_COLUMNS_REQUIRED = NO
EXECUTION_STATUS_SCHEMA_FOUNDATION = ACCEPTED_FINAL
START_COMPLETE_RUNTIME = NOT_IMPLEMENTED
QA_SCHEMA_ROLLOUT = PASS
S67_QA_ROLLOUT = PASS
```

Phase-aware `_assert_coupled` and START/COMPLETE writers remain **not implemented**.  
Current commitment runtime still uses status equality (HELD/RESERVED/RELEASED/CANCELLED only).

Structural coupling matrix (future runtime):

```text
run HELD       ↔ reservation HELD
run RESERVED   ↔ reservation RESERVED
run RUNNING    ↔ reservation RESERVED
run COMPLETED  ↔ reservation RESERVED
run RELEASED   ↔ reservation RELEASED
run CANCELLED  ↔ reservation CANCELLED
```

`RELEASE_AFTER_COMPLETED = FUTURE_RUNTIME_ADJUSTMENT_REQUIRED`  
(today RELEASE accepts run RESERVED only).

---

## 6. R6 behavior

| Run state | Reservation state | R6 machine_reservation |
| --------- | ----------------- | ---------------------- |
| RUNNING | RESERVED | **ACTIVE** |
| COMPLETED | RESERVED | **ACTIVE** (still booked) |
| any | RELEASED / CANCELLED | **CLEAR** (if no other open commitment) |

No R6 vocabulary change. Evaluator continues to read **reservation** OPEN statuses via the participant union.

---

## 7. Phase B impact (documented only)

```text
PHASE_B = NOT_AUTHORIZED
```

When later authorized, Phase B must:

1. Stop using stub CLEAR; consume R6 union (ACTIVE participants → run-owned reservation).
2. Treat reservation `HELD|RESERVED` as blocking for reassignment/unassignment.
3. While run is RUNNING/COMPLETED with reservation still RESERVED, keep machine commitment blocking (do not false-CLEAR).
4. Ignore REMOVED participants.
5. Keep existing ExecutionReality session-history guards; MACHINE_RUN RUNNING is an **additional** signal, not a substitute.

No Phase B code in the first START/COMPLETE implementation GO unless Owner expands that GO.

---

## 8. Domain gate

```text
MACHINE_RESERVATION = ACTIVE
```

No new domain. Reuse existing `require_active_domain_config`.

---

## 9. Idempotency / CAS / history (finalized shape)

```text
CAS: expected_version = machine_run.version
idempotency: unique key on run transition + fingerprint (command, run id, expected_version, reason, actor)
dual history: run transition + reservation lockstep companion (status unchanged on reservation for START/COMPLETE)
```

Run history must carry factual `started_at` / `completed_at` via run row columns (not stuffed into free-text reason).

---

## 10. API (conceptual)

```text
POST /api/v1/execution/resource-state/machine-runs/{id}/start
POST /api/v1/execution/resource-state/machine-runs/{id}/complete
```

Permission: `execution.machine_run.execute` for START/COMPLETE.  
Release remains on existing `/release` with `execution.machine_run.manage`.

---

## 11. Error contract (minimum)

```text
machine_run_not_found
invalid_transition
run_reservation_state_mismatch
cas_stale
idempotency_payload_conflict
domain_not_active / domain_disabled
permission_denied
```

---

## 12. Boundaries

```text
START_COMPLETE_RUNTIME = PASS
AUTO_BATCH = NOT_IMPLEMENTED
CAPACITY_STAGE_1 = IMPLEMENTED_INACTIVE
PHASE_B = NOT_AUTHORIZED
PHASE_C = BLOCKED
FRONTEND_CHANGED = NO
EMPLOYEE_MOBILE_CHANGED = NO
QA_RUNTIME_MUTATIONS = 0
```

---

## 13. Next implementation GO (bounded)

**Done (this arc):** START/COMPLETE writers · phase-aware coupling · RELEASE-after-COMPLETED · `execution.machine_run.execute` · isolated + regression proofs.

**Still out (require separate Owner GO):**

```text
PAUSE/RESUME
auto task start/complete
auto employee sessions
CANCEL-while-RUNNING / ABORT
Phase B wiring
Capacity activation
UI / Mobile START/COMPLETE buttons
auto-batch
machine reassignment
QA operational MACHINE_RUN usage
```

```text
NEXT_TASK = NOT_AUTHORIZED
```

---

## 14. Overengineering check

| Candidate | Needed for first real START/COMPLETE? | Verdict |
| --------- | ------------------------------------- | ------- |
| PAUSE/RESUME | no | defer |
| Auto-start all participant tasks | no | reject |
| Auto-create N employee sessions | no | reject |
| Auto-RELEASE on COMPLETE | optional UX; weaker audit | reject for MVP |
| Reservation status RUNNING | conflicts R6/OPEN model | reject |
| Generic shop-floor state machine | no | defer |

---

## 15. QA proof (read-only)

```text
QA Alembic = s67_machine_run_execution_status
CODE Alembic head = s67_machine_run_execution_status
QA baseline accepted =
  7586819bb20087cd3df71a221ea0f2332bcb062952991a92afced287368d35b4
QA SHA after s67 =
  bee5f5f74c428fd03cf30ffd7377db00be3fa64716a29ce2652ae9f93b161322
machine_runs / participants / transitions / reservations = 0
assignment transitions = 7
foreign_key_check = 0
started_at/completed_at = present nullable
RUNNING/COMPLETED on MachineRun CHECK = present
Reservation RUNNING/COMPLETED = absent
```

Known accepted intake baseline drift (pre-s67, not reversed):

```text
intake_requests.id=50 delivery_type=delivery_standard
updated_at=2026-08-07 22:10:46.650895
```

Worklogs:
- `docs/worklog/realignment/2026-08-07_qa_sqlite_byte_drift_closure_before_s67_rollout.md`
- `docs/worklog/realignment/2026-08-07_machine_run_execution_status_controlled_qa_s67_rollout.md`

---

## 16. `/modules` · `/governance`

```text
NO_UI_CHANGE
```

MachineRun execution lifecycle: START + COMPLETE implemented backend · UI = not implemented · employee/session coupling = not implemented · Phase B coupling = not implemented.
