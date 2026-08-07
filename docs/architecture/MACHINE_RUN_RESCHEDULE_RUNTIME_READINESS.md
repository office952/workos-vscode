# MACHINE_RUN — Reschedule Runtime Readiness

**Task:** `MACHINE_RUN_RESCHEDULE_RUNTIME_READINESS`  
**Owner GO:** `AUTHORIZE_MACHINE_RUN_RESCHEDULE_RUNTIME_READINESS`  
**Date:** 2026-08-07  
**Status:** **PASS** · readiness finalized · **runtime VERIFIED** · **no QA writes**  
**Starting HEAD:** `a36e7de3`  
**Prerequisites:** CREATE + CONFIRM/RELEASE/CANCEL runtime PASS · s66 schema  
**Readiness worklog:** `docs/worklog/realignment/2026-08-07_machine_run_reschedule_runtime_readiness.md`  
**Implementation worklog:** `docs/worklog/realignment/2026-08-07_reschedule_machine_run_runtime_implementation.md`

```text
MACHINE_RUN_RESCHEDULE_RUNTIME_READINESS = PASS
RESCHEDULE_MACHINE_RUN = VERIFIED
ALLOWED_FROM = HELD,RESERVED
MACHINE_ID_CHANGE = FORBIDDEN
STATUS_CHANGE = FORBIDDEN
WINDOW_MUTATION = VERIFIED
OVERLAP_ENGINE = SINGLE_SHARED
CAS = VERIFIED
IDEMPOTENCY = VERIFIED
HISTORY_MODEL = VERIFIED
SCHEMA_SUFFICIENCY = VERIFIED
PARTICIPANTS_UNCHANGED = VERIFIED
R6_BEHAVIOR = ACTIVE_UNCHANGED
PERMISSION = execution.machine_run.manage
DOMAIN_GATE = MACHINE_RESERVATION_ACTIVE
RUNTIME_IMPLEMENTATION = VERIFIED
QA_MUTATIONS = 0
CREATE_MACHINE_RUN = PASS
CONFIRM_RELEASE_CANCEL = PASS
MACHINE_RUN_PARTICIPANT_MUTATION_RUNTIME_READINESS = PASS
MACHINE_RUN_ADD_REMOVE_PARTICIPANT_RUNTIME_IMPLEMENTATION = PASS
MACHINE_RUN_EXECUTION_LIFECYCLE = NOT_IMPLEMENTED
AUTO_BATCH = NOT_IMPLEMENTED
CAPACITY_STAGE_1 = IMPLEMENTED_INACTIVE
PHASE_B = NOT_AUTHORIZED
PHASE_C = BLOCKED
NEXT_TASK = NOT_AUTHORIZED
```

---

## 1. Why reschedule before RUNNING/COMPLETED

```text
CREATE / CONFIRM / RELEASE / CANCEL
= commitment lifecycle (machine clock)
```

Real operations need to **move the window** without destroying the run, participants, or confirmed commitment status.

```text
reschedule machine commitment
≠ shop-floor execution
≠ RUNNING / COMPLETED
≠ ADD/REMOVE participants
```

---

## 2. Baseline (frozen)

```text
CREATE_MACHINE_RUN → HELD / HELD
CONFIRM_MACHINE_RUN → RESERVED / RESERVED
RELEASE_MACHINE_RUN → RELEASED / RELEASED
CANCEL_MACHINE_RUN → CANCELLED / CANCELLED
```

```text
RESERVED ≠ RUNNING
```

QA: s66 · MACHINE_RUN tables empty · Capacity NOT_CONFIGURED · Phase B/C blocked.

---

## 3. R9 / schedule sources (facts)

| Domain | Window-move command | Behavior |
| ------ | ------------------- | -------- |
| Scheduling | `RESCHEDULE` | In-place; **status preserved**; old/new window on schedule transition |
| Reservation (R9) | **No `RESCHEDULE_RESERVATION`** | Window move via **`SUPERSEDE_RESERVATION`** → old SUPERSEDED + new HELD; optional `machine_id` change; TASK-owned only |
| MACHINE_RUN | none yet | — |

**MACHINE_RUN must not reuse public SUPERSEDE:**

| Blocker | Why |
| ------- | --- |
| TASK owner hardcoding | plan/task required; run-owned has NULL |
| Status reset | replacement always HELD — would demote RESERVED→HELD |
| 1:1 UNIQUE `machine_run_id` | second reservation row forbidden while first exists |
| Semantic mismatch | supersede = replace claim; reschedule = move window |

**Reuse instead:**

- schedule-style **same-status** event  
- `_validate_window`  
- `find_overlapping_open(..., exclude_id=current_reservation.id)`  
- CAS +1 version pattern  
- domain gate `MACHINE_RESERVATION`  
- reservation transition window columns (`previous_start/end`, `new_start/end`)

```text
R9_REUSE = WINDOW_OVERLAP_CAS_DOMAIN_NOT_PUBLIC_SUPERSEDE
```

---

## 4. Owner decisions (finalized)

| ID | Question | Decision |
| -- | -------- | -------- |
| **D1** | Reschedule from HELD? | **YES** |
| **D2** | Reschedule from RESERVED? | **YES** |
| **D3** | `machine_id` change? | **NO** (same machine; new window only) |
| **D4** | Status change? | **NO** (HELD stays HELD; RESERVED stays RESERVED) |
| **D5** | History stores old+new window? | **YES** on reservation transition |
| **D6** | Existing schema supports this? | **YES** — see §10 |

```text
ALLOWED_FROM = HELD, RESERVED
MACHINE_ID_CHANGE = FORBIDDEN
STATUS_CHANGE = FORBIDDEN
```

Forbidden:

```text
RELEASED → RESCHEDULE
CANCELLED → RESCHEDULE
SUPERSEDED → RESCHEDULE
any reopen
RESERVED → HELD (status demotion)
```

Changing machine → future separate command / supersede-style replace (not this slice).

---

## 5. Request contract (finalized)

```text
RescheduleMachineRunCommand
```

| Field | Required | Rule |
| ----- | -------- | ---- |
| `reservation_start` | yes | new window start |
| `reservation_end` | yes | new window end (> start) |
| `timezone` | yes | same pattern as CREATE |
| `expected_version` | yes | `machine_runs.version` ≥ 1 |
| `idempotency_key` | yes | 8–36 chars |
| `reason_code` | yes | default e.g. `machine_run_reschedule` |
| `reason_note` | no | max 500 |
| `correlation_id` | no | max 64 |

Path: `machine_run_id`  
**Not accepted:** `machine_id`, participants, capability, batch_eligible, commercial payloads.

```text
client sends new window
server keeps machine + participants + status
```

---

## 6. Semantics (finalized)

```text
load run + run-owned reservation
assert coupled (status + version lockstep)
assert status ∈ {HELD, RESERVED}
assert machine_id unchanged (implicit)
validate new window
overlap check with exclude_id = reservation.id
update reservation.reservation_start/end (+ timezone if policy allows rewrite)
bump run.version and reservation.version
status unchanged on both
append histories
COMMIT
```

Timezone: accept request timezone; store on reservation/run consistently with CREATE (both currently hold timezone). Prefer updating both timezone fields to the request value when provided (same string as CREATE).

---

## 7. Overlap (finalized)

```text
OVERLAP_ENGINE = SINGLE_SHARED
→ find_overlapping_open(machine_id, new_start, new_end, exclude_id=reservation.id)
→ overlap_conflict
```

Open blockers remain `{HELD, RESERVED}` for other claims. Self excluded.

---

## 8. CAS (finalized)

```text
expected_version = machine_runs.version
require reservation.version == run.version   # coupling defense
→ run.version += 1
→ reservation.version += 1
status unchanged
```

Stale → `cas_stale` · zero mutations.

---

## 9. Idempotency (finalized)

Fingerprint:

```text
operation = RESCHEDULE_MACHINE_RUN
machine_run_id
reservation_start / reservation_end (dt_key)
timezone
expected_version
reason_code / reason_note
actor_user_id
```

```text
same key + same fingerprint → already_applied=true
same key + different window/payload → idempotency_payload_conflict
```

---

## 10. History model + schema sufficiency (finalized)

### Authoritative window audit — reservation transition

`execution_task_machine_reservation_transitions` already has:

```text
previous_start / previous_end
new_start / new_end
previous_status / new_status   # equal (same-status event)
previous_version / new_version
owner_form = MACHINE_RUN
machine_run_id set; plan/task NULL
operation = RESCHEDULE_RESERVATION   # or RESCHEDULE_MACHINE_RUN on res side — prefer RESCHEDULE_RESERVATION for R9 vocabulary symmetry with CONFIRM_RESERVATION
```

### Run transition — same-status event (no window columns)

`machine_run_transitions` has **no** window columns (s66). That matches CREATE today (window only on reservation history).

```text
operation = RESCHEDULE_MACHINE_RUN
previous_status = new_status ∈ {HELD, RESERVED}
previous_version / new_version
actor / reason / idempotency_key
```

```text
HISTORY_MODEL = RESERVATION_HOLDS_WINDOW_DELTA + RUN_SAME_STATUS_EVENT
SCHEMA_SUFFICIENCY = VERIFIED
SCHEMA_GAP_FOR_MVP = NONE
```

**Not required for MVP:** migration to add window columns on `machine_run_transitions`.  
If a future Owner wants run-history window mirrors, that is a separate schema GO — not a blocker for RESCHEDULE_MACHINE_RUN.

---

## 11. Atomic transaction order (recommended)

```text
1. idempotency precheck
2. machine_lock(run.machine_id)
3. load run + reservation FOR UPDATE
4. domain ACTIVE
5. coupling check
6. allowed status + CAS
7. validate window
8. overlap (exclude self)
9. write new window on reservation (+ timezone)
10. bump versions; status unchanged
11. INSERT run transition (RESCHEDULE_MACHINE_RUN)
12. INSERT reservation transition (window delta)
13. COMMIT
```

Failure → ROLLBACK ALL.

---

## 12. Participant + machine invariance

```text
participant count / identities / order_id unchanged
machine_id unchanged
capability re-validation not required when machine unchanged
```

---

## 13. R6 behavior (finalized)

| Before | After reschedule |
| ------ | ---------------- |
| HELD → ACTIVE | HELD → ACTIVE |
| RESERVED → ACTIVE | RESERVED → ACTIVE |

Interval moves; commitment state vocabulary unchanged. Participants unchanged.

---

## 14. Permission · domain

```text
PERMISSION = execution.machine_run.manage
DOMAIN_GATE = MACHINE_RESERVATION ACTIVE
```

No new permission / domain.

---

## 15. API · response · errors

```text
POST /api/v1/execution/resource-state/machine-runs/{machine_run_id}/reschedule
```

Response: same shape as other MACHINE_RUN commands (`CreateMachineRunResult` / shared result) with updated window + versions + `already_applied` + `operation=RESCHEDULE_MACHINE_RUN`.

| Situation | Code |
| --------- | ---- |
| Unknown run | `machine_run_not_found` |
| Missing reservation | `reservation_not_found` |
| Terminal / wrong status | `invalid_transition` |
| Coupling break | `run_reservation_state_mismatch` |
| Bad window | `invalid_time_window` |
| Overlap | `overlap_conflict` |
| CAS | `cas_stale` |
| Idempotency | `idempotency_payload_conflict` |
| Domain | `domain_not_active` / `domain_disabled` |
| Permission | 403 |

---

## 16. Regression boundary

Existing contracts unchanged:

```text
CREATE = HELD/HELD
CONFIRM = HELD→RESERVED
RELEASE = RESERVED→RELEASED
CANCEL = HELD|RESERVED→CANCELLED
```

RESCHEDULE does not allocate Capacity, change assignments, create sessions, or start tasks.

```text
MACHINE_RUN_EXECUTION_LIFECYCLE = NOT_IMPLEMENTED
CAPACITY_STAGE_1 = IMPLEMENTED_INACTIVE
PHASE_B = NOT_AUTHORIZED
PHASE_C = BLOCKED
```

---

## 17. Runtime implementation (closed)

```text
RESCHEDULE_MACHINE_RUN_RUNTIME_IMPLEMENTATION = PASS
API = POST …/machine-runs/{id}/reschedule
```

**Still out of RESCHEDULE (separate Owner GOs):**

```text
machine_id change
ADD/REMOVE participants (runtime PASS elsewhere; HELD-only)
SUPERSEDE run
RUNNING/COMPLETED
auto-batch / nesting / UI
QA operational writes
```

Participant mutation readiness: `docs/architecture/MACHINE_RUN_PARTICIPANT_MUTATION_RUNTIME_READINESS.md`

```text
RUNTIME_IMPLEMENTATION = VERIFIED
MACHINE_RUN_EXECUTION_LIFECYCLE = NOT_IMPLEMENTED
```

---

## 18. Overengineering check

| Candidate | Needed? | Verdict |
| --------- | ------- | ------- |
| SUPERSEDE-style replace | no — breaks 1:1 + status | reject |
| machine_id change | no | defer |
| Run transition window columns | no for MVP | defer |
| RUNNING/COMPLETED | no | defer |
| New permission | no | reject |

---

## 19. QA proof (read-only)

```text
QA Alembic = s66_machine_run_reservation_grain
QA SHA = b7950463b2956e779275e14fa81ee742a681ccee2e9f338a9db1310e1b740fb1
machine_runs / participants / transitions / reservations = 0
assignment transitions = 7
foreign_key_check = 0
QA_MUTATIONS = 0
```

---

## 20. `/modules` · `/governance`

```text
NO_UI_CHANGE
```

Docs: RESCHEDULE runtime VERIFIED in code · QA operational usage not activated · commitment move ≠ production execution.
