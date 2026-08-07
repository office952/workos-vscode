# MACHINE_RUN — Participant Mutation Runtime Readiness

**Task:** `MACHINE_RUN_PARTICIPANT_MUTATION_RUNTIME_READINESS`  
**Owner GO:** `AUTHORIZE_MACHINE_RUN_PARTICIPANT_MUTATION_RUNTIME_READINESS`  
**Date:** 2026-08-07  
**Status:** **PASS** · readiness finalized · **runtime VERIFIED** · **no QA writes**  
**Starting HEAD:** `484c7a8c`  
**Prerequisites:** CREATE + CONFIRM/RELEASE/CANCEL + RESCHEDULE runtime PASS · s66 schema  
**Readiness worklog:** `docs/worklog/realignment/2026-08-07_machine_run_participant_mutation_runtime_readiness.md`  
**Implementation worklog:** `docs/worklog/realignment/2026-08-07_machine_run_add_remove_participant_runtime_implementation.md`

```text
MACHINE_RUN_PARTICIPANT_MUTATION_RUNTIME_READINESS = PASS
MACHINE_RUN_ADD_REMOVE_PARTICIPANT_RUNTIME_IMPLEMENTATION = PASS
ADD_MACHINE_RUN_PARTICIPANT = VERIFIED
REMOVE_MACHINE_RUN_PARTICIPANT = VERIFIED
ALLOWED_FROM = HELD
MIN_PARTICIPANTS_AFTER_MUTATION = 2
MACHINE_ID_UNCHANGED = VERIFIED
RESERVATION_WINDOW_UNCHANGED = VERIFIED
RESERVATION_STATUS_UNCHANGED = VERIFIED
RUN_VERSION_BEHAVIOR = INCREMENT
RESERVATION_VERSION_BEHAVIOR = INCREMENT_LOCKSTEP
PARTICIPANT_HISTORY_MODEL = SOFT_REMOVED_ROW_PLUS_COMMAND_TRANSITION
SCHEMA_SUFFICIENCY = VERIFIED
CAS = VERIFIED
IDEMPOTENCY = VERIFIED
R6_ADD_BEHAVIOR = VERIFIED
R6_REMOVE_BEHAVIOR = VERIFIED
MULTI_PLAN_ADD = VERIFIED
PERMISSION = execution.machine_run.manage
DOMAIN_GATE = MACHINE_RESERVATION_ACTIVE
RUNTIME_IMPLEMENTATION = VERIFIED
QA_MUTATIONS = 0
MACHINE_RUN_EXECUTION_LIFECYCLE_READINESS = PASS
MACHINE_RUN_EXECUTION_LIFECYCLE = NOT_IMPLEMENTED
AUTO_BATCH = NOT_IMPLEMENTED
CAPACITY_STAGE_1 = IMPLEMENTED_INACTIVE
PHASE_B = NOT_AUTHORIZED
PHASE_C = BLOCKED
NEXT_TASK = NOT_AUTHORIZED
```

---

## 1. Why participant mutation before RUNNING

```text
CREATE / CONFIRM / RESCHEDULE / RELEASE / CANCEL
= commitment lifecycle (machine clock + grouping seal)
```

Real operations need to **correct the batch membership** while the run is still provisional:

```text
remove a task that no longer belongs in the CNC batch
add a compatible task from another plan/order
```

```text
participant mutation
≠ machine reassignment
≠ window move
≠ shop-floor RUNNING / COMPLETED
≠ auto-batch discovery
```

---

## 2. Baseline (frozen)

```text
CREATE_MACHINE_RUN      → HELD / HELD
CONFIRM_MACHINE_RUN     → RESERVED / RESERVED
RESCHEDULE_MACHINE_RUN  → same status + new window
RELEASE_MACHINE_RUN     → RELEASED / RELEASED
CANCEL_MACHINE_RUN      → CANCELLED / CANCELLED
```

```text
RESERVED ≠ RUNNING
MIN_PARTICIPANTS = 2 (CREATE)
Alembic = s66_machine_run_reservation_grain
```

QA: MACHINE_RUN tables empty · Capacity NOT_CONFIGURED · Phase B/C blocked.

---

## 3. Owner decisions (closed)

| ID | Decision | Verdict |
| -- | -------- | ------- |
| **D1** | Mutations allowed only from **HELD** (not RESERVED) | **FINALIZED** |
| **D2** | REMOVE cannot leave fewer than **2 ACTIVE** participants | **FINALIZED** → `minimum_participants_violation` |
| **D3** | Reservation `id` / `machine_id` / window / timezone / status unchanged; run status unchanged | **FINALIZED** |
| **D4** | Versioning: **OPTION B** — `run.version += 1` **and** `reservation.version += 1` | **FINALIZED** |
| **D5** | Removal model: **B** — soft `REMOVED` + `removed_at` / `removed_by` (no physical delete) | **FINALIZED** |
| **D6** | Current s66 schema sufficient for model B + command journal | **VERIFIED** |
| **D7** | ADD from another ExecutionPlan / Order remains **allowed** | **FINALIZED** |

### D1 rationale (repo-specific)

| Option | Verdict |
| ------ | ------- |
| A. HELD only | **Adopt** — grouping still provisional; CONFIRM seals commitment object |
| B. HELD + RESERVED | Reject for MVP — changes confirmed operational object |
| C. all open | Reject — RELEASED/CANCELLED are terminal |

For RESERVED correction:

```text
CANCEL or RELEASE
→ CREATE new MACHINE_RUN
```

(or a future `SUPERSEDE_MACHINE_RUN` — not this slice).

### D4 rationale (critical)

Runtime `_assert_coupled` requires:

```text
run.status == reservation.status
AND
run.version == reservation.version
```

Every CREATE / CONFIRM / RELEASE / CANCEL / RESCHEDULE keeps lockstep.

**OPTION A** (run only) after ADD/REMOVE → next CONFIRM/RESCHEDULE/CANCEL hits `run_reservation_state_mismatch`.  
**OPTION B** preserves CAS (`expected_version = machine_run.version`), coupling defense, and post-mutation lifecycle.

Reservation commitment fields (window/machine/status) do **not** change; version still advances as **coupling metadata**, same structural pattern as RESCHEDULE’s dual bump with a different semantic payload.

### D5 / D6 rationale (critical)

s66 already provides:

```text
machine_run_participants.status ∈ {ACTIVE, REMOVED}
added_at / added_by
removed_at / removed_by
uq_machine_run_participant_membership (run, plan, task)  — one row forever per identity
uq_machine_run_participant_active_plan_task WHERE ACTIVE — cross-run exclusivity
```

`machine_run_transitions` has **no** `execution_plan_id` / `task_key` columns.

That is **not** a schema blocker for MVP because:

1. Membership provenance lives on the **participant row** (designed soft-remove in schema readiness).
2. Each ADD/REMOVE command mutates **exactly one** participant identity.
3. Run transition is the **command journal** (operation, actor, reason, CAS/idempotency, same-status HELD→HELD).
4. Physical DELETE would destroy audit — **forbidden**.
5. Identity is **not** stuffed into `reason_*`.

Optional future migration to denormalize participant identity onto transitions is deferred — not required for readiness PASS.

---

## 4. Participant persistence model (as-built)

```text
ACTIVE  = counts toward MIN_PARTICIPANTS and R6 union
REMOVED = excluded from active membership + R6 union; row retained
```

Re-ADD of the same `(execution_plan_id, task_key)` to the **same** run after REMOVE:

```text
reactivate existing row
(status ACTIVE; clear removed_*; set added_* / actor)
≠ second INSERT (membership unique forbids it)
```

---

## 5. Allowed source states

```text
HELD      → ADD / REMOVE allowed
RESERVED  → invalid_transition
RELEASED  → invalid_transition
CANCELLED → invalid_transition
```

Run and reservation statuses remain **HELD** on success.

---

## 6. ADD_MACHINE_RUN_PARTICIPANT

### Request (minimum)

```text
execution_plan_id
task_key
expected_version          # = machine_run.version
idempotency_key
reason_code / reason_note*
correlation_id*
```

Client does **not** send: `machine_id`, capability, batch flags, window.

### Server reads from ExecutionPlan task stamps

```text
resource_mode
machine_capability_code
batch_eligible
order_id provenance
```

### Eligibility (reuse CREATE rules)

```text
canonical task exists
resource_mode = MACHINE_BOUND
batch_eligible = true
machine_capability_code known
capability == capability of existing ACTIVE participants
machine compatibility with reservation.machine_id (same CREATE rules)
not ACTIVE in another open MACHINE_RUN
```

Full batch compatibility (material/thickness/tooling/nesting/setup) remains **operator responsibility** — no auto-compatibility engine.

### Duplicate in same run

| Case | Result |
| ---- | ------ |
| Same idempotency key + same payload | `already_applied` replay |
| New command; participant already ACTIVE | `participant_already_exists` |
| Row REMOVED; new ADD | reactivate (success path) |

### Invariants on success

```text
machine_id unchanged
reservation.id / window / timezone / status unchanged
run.status = HELD
ACTIVE participant set grows by one
run.version += 1
reservation.version += 1
```

No new overlap check (window unchanged).

---

## 7. REMOVE_MACHINE_RUN_PARTICIPANT

### Request (minimum)

```text
execution_plan_id
task_key
expected_version
idempotency_key
reason*
```

### Behavior

```text
locate ACTIVE membership on this run
→ status = REMOVED
→ removed_at / removed_by stamped
```

Does **not**: delete task, mutate ExecutionPlan, change reservation identity/window/machine/status, change run status.

### Not found

```text
no ACTIVE membership for (plan, task) on this run
→ participant_not_found
```

### Minimum participants

```text
ACTIVE count after REMOVE must be ≥ 2
else → minimum_participants_violation
zero mutations
```

Teardown of a 2-participant run:

```text
CANCEL_MACHINE_RUN
```

No automatic conversion to task-owned Reservation. No auto-teardown.

---

## 8. Active membership guard

Reuse `_find_active_membership` / partial unique ACTIVE index:

```text
task already ACTIVE on another MACHINE_RUN
→ task_already_in_active_machine_run
```

No automatic move. No automatic REMOVE from the other run.

---

## 9. CAS

```text
expected_version = machine_run.version
stale → cas_stale · zero mutations
```

After OPTION B success, both versions equal the new value.  
`_assert_coupled` remains unchanged for subsequent CONFIRM / RESCHEDULE / CANCEL.

---

## 10. Idempotency

### ADD fingerprint

```text
ADD_MACHINE_RUN_PARTICIPANT
machine_run_id
execution_plan_id
task_key
expected_version
reason_code (+ reason_note if canonical)
actor
```

### REMOVE fingerprint

Analogous with `REMOVE_MACHINE_RUN_PARTICIPANT`.

```text
same key + same payload → already_applied
same key + different participant/payload → idempotency_payload_conflict
```

Store `idempotency_key` on the run transition (and reservation companion transition), matching RESCHEDULE dual-key pattern.

---

## 11. History model

### Run transition (command journal)

```text
operation ∈ {ADD_MACHINE_RUN_PARTICIPANT, REMOVE_MACHINE_RUN_PARTICIPANT}
previous_status = new_status = HELD
previous_version / new_version
actor / reason / idempotency_key
```

### Participant row (membership provenance)

```text
ADD new:     ACTIVE + added_at/by
ADD revive:  REMOVED → ACTIVE; clear removed_*; refresh added_*
REMOVE:      ACTIVE → REMOVED + removed_at/by
```

### Reservation companion transition (lockstep)

```text
same status (HELD)
window unchanged (previous_start/end == new_start/end)
reservation.version += 1
operation = MACHINE_RUN_PARTICIPANT_MUTATION_LOCKSTEP
```

Documents version bump without implying window/machine change.  
`operation` is unconstrained String(64) today — no migration required.

---

## 12. R6 behavior

R6 union already filters `machine_run_participants.status = 'ACTIVE'` onto the run-owned reservation.

### ADD

```text
new/reactivated ACTIVE participant
→ machine_reservation.state = ACTIVE
(same reservation_id as other ACTIVE members; run HELD)
```

### REMOVE

```text
REMOVED participant
→ CLEAR if no other open commitment
other ACTIVE members → remain ACTIVE
```

---

## 13. Multi-plan

```text
ADD may reference another execution_plan_id / order_id
store execution_plan_id + task_key + derived order_id
no same-plan restriction
```

---

## 14. Permission / domain

```text
permission = execution.machine_run.manage
domain gate = MACHINE_RESERVATION ACTIVE
```

No new permission. No new domain.

---

## 15. API contract (conceptual)

Command-style POST (consistent with confirm/release/cancel/reschedule):

```text
POST /api/v1/execution/resource-state/machine-runs/{machine_run_id}/add-participant
POST /api/v1/execution/resource-state/machine-runs/{machine_run_id}/remove-participant
```

Prefer command POST over bare `DELETE` so body can carry idempotency/CAS/reason.

### Response (minimum)

```text
machine_run_id
status                    # HELD
version
reservation_id
reservation_status
reservation_version
machine_id
reservation_start / end / timezone
participants[]            # ACTIVE (+ optionally include REMOVED for audit reads — impl choice)
affected_participant      # {execution_plan_id, task_key, status}
operation
transition_id
reservation_transition_id
already_applied
previous_version
```

---

## 16. Error contract

Reuse CREATE/lifecycle codes where they already exist; finalize REMOVE-specific minimum:

| Code | When |
| ---- | ---- |
| `machine_run_not_found` | missing run |
| `invalid_transition` | not HELD |
| `task_key_not_found` / `execution_plan_not_found` | missing identity |
| `task_not_machine_bound` | mode |
| `task_capability_unknown` | blank/missing capability |
| `task_not_batch_eligible` | batch flag |
| `participant_capability_mismatch` | vs existing ACTIVE set |
| `machine_capability_mismatch` | vs run machine |
| `participant_already_exists` | ACTIVE duplicate on same run |
| `task_already_in_active_machine_run` | ACTIVE elsewhere |
| `participant_not_found` | REMOVE miss |
| `minimum_participants_violation` | ACTIVE would drop below 2 |
| `cas_stale` | version |
| `idempotency_payload_conflict` | key reuse |
| `run_reservation_state_mismatch` | coupling precheck |
| `domain_not_active` / `domain_disabled` | domain gate |
| `permission_denied` | authz |

---

## 17. Boundaries

### Existing lifecycle

ADD/REMOVE must not change CREATE / CONFIRM / RESCHEDULE / RELEASE / CANCEL semantics.

### Execution

```text
MACHINE_RUN_EXECUTION_LIFECYCLE = NOT_IMPLEMENTED
```

No RUNNING/COMPLETED, sessions, task start/stop, actual machine runtime.

### Capacity / Phase

```text
CAPACITY_STAGE_1 = IMPLEMENTED_INACTIVE
PHASE_B = NOT_AUTHORIZED
PHASE_C = BLOCKED
```

No Capacity allocation, assignment mutation, or Phase calls.

### UI

```text
FRONTEND_CHANGED = NO
EMPLOYEE_MOBILE_CHANGED = NO
```

---

## 18. Runtime implementation (closed)

```text
MACHINE_RUN_ADD_REMOVE_PARTICIPANT_RUNTIME_IMPLEMENTATION = PASS
API = POST …/add-participant | …/remove-participant
```

**Still out of participant mutation (separate Owner GOs):**

```text
machine_id change
window change / RESCHEDULE redesign
RESERVED participant mutation
RUNNING / COMPLETED (execution readiness PASS elsewhere; runtime not started)
auto-batch / nesting / UI
QA operational writes
SUPERSEDE_MACHINE_RUN
```

```text
RUNTIME_IMPLEMENTATION = VERIFIED
MACHINE_RUN_EXECUTION_LIFECYCLE = NOT_IMPLEMENTED
```

Execution lifecycle readiness: `docs/architecture/MACHINE_RUN_EXECUTION_LIFECYCLE_READINESS.md`

---

## 19. Overengineering check

| Candidate | Needed for HELD membership edit? | Verdict |
| --------- | -------------------------------- | ------- |
| Transition columns for plan/task | nice; not required with row provenance + 1 mutation/command | defer |
| RESERVED mutation | no | reject |
| Auto-teardown at 1 participant | no | reject |
| Physical delete | destroys audit | reject |
| Capability-set engine | no | reject |
| Machine reassignment | no | defer |
| Auto-batch discovery | no | defer |

---

## 20. QA proof (read-only)

```text
QA Alembic = s66_machine_run_reservation_grain
QA SHA = b7950463b2956e779275e14fa81ee742a681ccee2e9f338a9db1310e1b740fb1
machine_runs / participants / transitions / reservations = 0
assignment transitions = 7
foreign_key_check = 0
QA_MUTATIONS = 0
```

---

## 21. `/modules` · `/governance`

```text
NO_UI_CHANGE
```

Docs: ADD/REMOVE runtime VERIFIED in code · QA operational usage not activated · grouping edit ≠ production execution.
