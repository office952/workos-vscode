# MACHINE_RUN — Minimal Command Runtime Readiness

**Task:** `MACHINE_RUN_MINIMAL_COMMAND_RUNTIME_READINESS`  
**Owner GO:** `AUTHORIZE_MACHINE_RUN_MINIMAL_COMMAND_RUNTIME_READINESS`  
**Date:** 2026-08-07  
**Status:** **PASS** · docs-only · **no runtime · no ORM · no QA writes**  
**Starting HEAD:** `1468e2d3`  
**Prerequisites:** QA s66 schema rollout PASS · Reservation grain OPTION_B · face_cnc_cut demand E2E PASS  
**Worklog:** `docs/worklog/realignment/2026-08-07_machine_run_minimal_command_runtime_readiness.md`

```text
MACHINE_RUN_MINIMAL_COMMAND_RUNTIME_READINESS = PASS
COMMAND = CREATE_MACHINE_RUN
REQUEST_CONTRACT = FINALIZED
RESPONSE_CONTRACT = FINALIZED
ERROR_CONTRACT = FINALIZED
PARTICIPANT_IDENTITY = EXECUTION_PLAN_ID_PLUS_TASK_KEY
MIN_PARTICIPANTS = 2
MACHINE_SELECTION = CLIENT_PROVIDES_MACHINE_ID
CAPABILITY_VALIDATION = FINALIZED
BATCH_ELIGIBILITY_VALIDATION = FINALIZED
FULL_BATCH_COMPATIBILITY = DEFERRED_EXPLICIT_CALLER_SELECTION
INITIAL_RUN_STATUS = HELD
INITIAL_RESERVATION_STATUS = HELD
ATOMIC_TRANSACTION = FINALIZED
IDEMPOTENCY = FINALIZED
OVERLAP_ENGINE = SINGLE_SHARED
ACTIVE_MEMBERSHIP_GUARD = FINALIZED
PERMISSION = execution.machine_run.manage
DOMAIN_GATE = MACHINE_RESERVATION_ACTIVE
R6_POST_CREATE_BEHAVIOR = FINALIZED
CREATE_MACHINE_RUN_MINIMAL_RUNTIME_IMPLEMENTATION = PASS
RUNTIME_IMPLEMENTATION = VERIFIED
MACHINE_RUN_LIFECYCLE = CREATE_ONLY
AUTO_BATCH = NOT_IMPLEMENTED
QA_MUTATIONS = 0
CAPACITY_STAGE_1 = IMPLEMENTED_INACTIVE
PHASE_B = NOT_AUTHORIZED
PHASE_C = BLOCKED
NEXT_TASK = NOT_AUTHORIZED
```

Implementation worklog: `docs/worklog/realignment/2026-08-07_create_machine_run_minimal_runtime_implementation.md`  
API: `POST /api/v1/execution/resource-state/machine-runs` (create-only; QA operational usage not activated).

---

## 1. Why this comes after s66 QA rollout

```text
schema + grain in code and QA
→ command contract can target the same tables
→ implementation will not invent a parallel schema
```

Still **no** CREATE API until a separate Owner GO.

---

## 2. Central principle

```text
CREATE_MACHINE_RUN
= explicit participant list
→ validate demand stamps
→ create run + participants + one run-owned reservation
→ write histories
→ commit atomically
```

```text
≠ auto-batching
≠ nesting
≠ machine auto-selection
≠ full lifecycle (confirm/release/cancel/start/complete)
```

```text
task / Operation Contract = demand
caller                    = selected tasks + machine + window
CREATE_MACHINE_RUN        = validates + commits grouping + reservation
Machine Reservation       = exclusive machine clock (run-owned)
```

---

## 3. Request contract (finalized)

```text
CreateMachineRunCommand
```

| Field | Required | Source / rule |
| ----- | -------- | ------------- |
| `machine_id` | yes | Client-selected; server validates reservable |
| `reservation_start` | yes | Window start |
| `reservation_end` | yes | Window end (> start) |
| `timezone` | yes | Same pattern as R9 |
| `participants` | yes | List of `{execution_plan_id, task_key}` · **min length 2** · dedupe after sort |
| `idempotency_key` | yes | 8–36 chars (R9 pattern) |
| `expected_version` | yes | Must be `0` on create |
| `reason_code` | yes | Default e.g. `machine_run_create` |
| `reason_note` | no | max 500 |
| `correlation_id` | no | max 64 |

### Not accepted from client (server reads from EP snapshot)

```text
operation_code
machine_capability_code
resource_mode
batch_eligible
order_id
commercial / product payloads
```

```text
client sends identity
server reads technical truth
```

Suggested future mount (implementation GO):  
`POST /api/v1/execution/resource-state/machine-runs`

---

## 4. Participant identity

```text
PARTICIPANT_IDENTITY = (execution_plan_id, task_key)
```

- `task_key` must exist in that plan’s `tasks_json.operational_tasks[]` (canonical EP V2 truth).
- `order_id` derived from `execution_plan.order_id` and stored on participant row.
- Duplicate identities in one request → collapse after canonical sort (or reject as invalid — prefer **collapse** after sort for idempotency stability).

---

## 5. Minimum participants (finalized)

```text
MIN_PARTICIPANTS = 2
```

| Option | Verdict |
| ------ | ------- |
| 1 | Rejected for MVP — redundant with task-owned `CREATE_RESERVATION` |
| **2+** | **Selected** — MACHINE_RUN reserved for shared grouping |

Single CNC jobs continue to use **task-owned** Reservation. MACHINE_RUN is for multi-task shared machine time.

---

## 6. Machine selection (finalized)

```text
MACHINE_SELECTION = CLIENT_PROVIDES_MACHINE_ID
```

Server validates (reuse R9 helpers):

- machine exists  
- reservable (`is_active`, `is_available`, `operational_status==active`)  
- window valid  

**No** auto-selection in this command.

---

## 7. Capability validation (finalized)

### Minimal runtime eligibility (participants)

For **each** participant, read from operational task / stamped fields:

```text
resource_mode = MACHINE_BOUND          (authoritative stamp)
machine_capability_code IS NOT NULL
batch_eligible = true
```

Across participants:

```text
all resolve to the same machine_capability_code
else → PARTICIPANT_CAPABILITY_MISMATCH
```

Reject:

```text
UNKNOWN / missing capability
batch_eligible false or null
resource_mode ≠ MACHINE_BOUND (incl. HYBRID soft-hint only)
```

### Machine inventory capability join

```text
MACHINE_CAPABILITY_INVENTORY_MATCH = DEFERRED_HARDENING
```

Repo fact: CNC seed may lack populated `machines.capabilities` (face CNC Owner decisions).  
**MVP CREATE** therefore:

1. Enforces participant demand stamps + shared capability code.  
2. Enforces R9 reservable machine gates.  
3. Does **not** hard-block on empty `machines.capabilities` until a separate inventory-binding GO.  
4. When `machines.capabilities` is non-empty, implementation **must** require intersection with the shared participant capability.

This is an honest MVP bound, not silent inventing of capability from workcenter.

---

## 8. Batch eligibility vs full compatibility

| Layer | Status |
| ----- | ------ |
| `MINIMAL_RUNTIME_ELIGIBILITY` | batch_eligible + MACHINE_BOUND + shared capability + explicit list |
| `FULL_OPERATIONAL_BATCH_COMPATIBILITY` | **DEFERRED** — material/thickness/nest/tooling/setup |

```text
FULL_BATCH_COMPATIBILITY = DEFERRED_EXPLICIT_CALLER_SELECTION
```

**No blocker:** Owner accepts explicit caller selection as MVP gate. Compatibility engines are separate Owner GOs. Risk is operational (bad grouping) — mitigated by human/controlled caller, not by inventing nest rules now.

---

## 9. Initial statuses (finalized)

Lockstep with R9 CREATE:

| Entity | Status | Version |
| ------ | ------ | ------- |
| `machine_runs` | **HELD** | 1 |
| run-owned reservation | **HELD** | 1 |

| Transition | Operation | new_status |
| ---------- | --------- | ---------- |
| machine_run_transitions | `CREATE_MACHINE_RUN` | HELD |
| reservation transitions | `CREATE_RESERVATION` | HELD · `owner_form=MACHINE_RUN` |

CONFIRM (HELD→RESERVED) for run+reservation is **out of this command** (future lifecycle GO). Writers must keep run↔reservation status aligned in the same txn when that arrives.

---

## 10. Reservation create boundary

```text
exactly one run-owned reservation
execution_plan_id = NULL
task_key = NULL
order_id = NULL
machine_run_id = <new run id>
XOR satisfied
```

### Reuse vs refactor

Reuse from R9:

- window validation  
- `_require_reservable_machine`  
- `find_overlapping_open` (single engine)  
- domain gate `MACHINE_RESERVATION` ACTIVE  
- transition insert + idempotency helper pattern  
- CAS version start at 1  

Bounded refactor required (implementation GO):

- Internal run-owned create path (skip `require_task_in_plan`)  
- `ReservationCommandResult.execution_plan_id` / `task_key` nullable **or** dedicated run-create result  
- Lock key: not single `plan.order_id` — use **machine_id** serialization (and/or ordered multi-plan locks) so overlap stays race-safe across orders  

Public `POST …/reservations` remains **task-owned only**. Orchestrator owns run-level reservation create.

---

## 11. Atomic transaction order (finalized)

Single DB transaction, FK-safe (one-direction `reservation.machine_run_id`):

```text
1. Validate request + load/validate all participants (EP tasks + stamps)
2. Validate machine + window + overlap (read)
3. INSERT machine_runs (HELD, v1, idempotency_key)
4. INSERT execution_task_machine_reservations (run-owned, HELD, v1)
5. INSERT machine_run_participants[] (ACTIVE; order_id derived)
6. INSERT machine_run_transitions (CREATE_MACHINE_RUN)
7. INSERT reservation transition (CREATE_RESERVATION, owner_form=MACHINE_RUN)
8. COMMIT
```

On any failure → **ROLLBACK ALL**.

Forbidden outcomes: run without reservation · reservation without run · partial participants · missing history.

---

## 12. Idempotency (finalized)

Same `idempotency_key` + same **canonical fingerprint** → replay with `already_applied=true`.  
Same key + different fingerprint → `idempotency_payload_conflict` (409).

Canonical fingerprint includes:

```text
operation = CREATE_MACHINE_RUN
owner_form = MACHINE_RUN
machine_id
reservation_start / reservation_end (dt_key)
timezone
expected_version = 0
participants = sorted([(execution_plan_id, task_key), ...])  # order-independent
reason_code / reason_note
actor_user_id
```

```text
[A,B] ≡ [B,A]
```

Prefer storing command idempotency on `machine_runs.idempotency_key` (UNIQUE) + matching run transition key (R9 dual-key style).

---

## 13. Active membership guard (finalized)

Schema: partial unique ACTIVE `(execution_plan_id, task_key)` on participants.

Behavior:

```text
TASK_ALREADY_IN_ACTIVE_MACHINE_RUN
```

if any participant already has `status=ACTIVE` in another run.  
No auto-move · no auto-supersede.

---

## 14. Overlap (finalized)

```text
OVERLAP_ENGINE = SINGLE_SHARED
→ find_overlapping_open(machine_id, window)
→ overlap_conflict (existing R9 code)
```

Owner form irrelevant.

---

## 15. ExecutionPlan task validation

For each participant:

1. Plan exists.  
2. `task_key` in `operational_tasks[]` (`task_id` / aliased key — same helper as R9 `require_task_in_plan`).  
3. Demand stamps read from that operational task (and/or projection-equivalent fields frozen on snapshot).

No legacy task-table fallback.

---

## 16. Multi-plan / multi-order

```text
ALLOWED
```

- Provenance per participant: `execution_plan_id`, `task_key`, derived `order_id`.  
- Do not bind run identity to a single Order.  
- Concurrency: machine-scoped lock recommended for create.

---

## 17. Permission (finalized)

```text
PERMISSION = execution.machine_run.manage  (NEW)
roles = admin, manager
```

**Why not reuse** `execution.machine_reservation.manage` alone: CREATE_MACHINE_RUN is orchestration (run + N participants + reservation), not a single-task reservation write. Parallel naming matches schedule/reservation/capacity splits.

Implementation GO adds the permission string; this readiness does not mutate ACL tables.

---

## 18. Domain gate (finalized)

```text
DOMAIN_GATE = MACHINE_RESERVATION must be ACTIVE
```

```text
no new MACHINE_RUN resource domain for MVP
```

Rationale: exclusive clock remains Machine Reservation; MACHINE_RUN is grouping orchestration above it. Future dedicated domain only if governance requires independent activation.

---

## 19. Response contract (finalized)

```text
CreateMachineRunResult
```

| Field | Notes |
| ----- | ----- |
| `machine_run_id` | |
| `status` | HELD |
| `version` | 1 |
| `reservation_id` | |
| `reservation_status` | HELD |
| `reservation_version` | 1 |
| `machine_id` | |
| `reservation_start` / `reservation_end` / `timezone` | |
| `participants[]` | `{execution_plan_id, task_key, order_id, status}` |
| `operation` | `CREATE_MACHINE_RUN` |
| `transition_id` | run transition |
| `reservation_transition_id` | reservation history |
| `already_applied` | R9 boolean convention |

No commercial / Aggregate blobs.

---

## 20. Error contract (finalized)

Map to existing R9 codes where possible; new codes only where needed:

| Situation | Code | HTTP |
| --------- | ---- | ---- |
| Plan missing | `execution_plan_not_found` | 404 |
| Task missing | `task_key_not_found` | 404 |
| Blank identity | `invalid_task_identity` | 422 |
| Not MACHINE_BOUND | `task_not_machine_bound` | 422 |
| Not batch eligible | `task_not_batch_eligible` | 422 |
| Missing capability | `task_capability_unknown` | 422 |
| Capability mismatch across participants | `participant_capability_mismatch` | 422 |
| `< 2` participants after dedupe | `invalid_participant_set` | 422 |
| Machine missing | `machine_not_found` | 404 |
| Machine not reservable | `machine_not_reservable` | 422 |
| Bad window | `invalid_time_window` | 422 |
| Overlap | `overlap_conflict` | 409 |
| Already ACTIVE in a run | `task_already_in_active_machine_run` | 409 |
| Idempotency clash | `idempotency_payload_conflict` | 409 |
| Domain inactive | `domain_not_active` / `domain_disabled` | 409 |
| Permission | standard 403 | 403 |
| expected_version ≠ 0 | `cas_stale_or_missing` | 409 |

API body shape (R9): `detail.error` + `detail.message`.

---

## 21. R6 post-create behavior (future proof)

After successful CREATE (implementation GO must verify on isolated DB):

```text
each ACTIVE participant task
→ list_reservations_visible_to_task
→ sees run-owned HELD reservation
→ machine_reservation.state = ACTIVE
→ aggregate may be BLOCKED_ACTIVE (if other domains CLEAR)
```

QA smoke remains empty until runtime GO.

---

## 22. face_cnc_cut canonical example

```text
Plan X / face_cnc_cut A
Plan Y / face_cnc_cut B
resource_mode = MACHINE_BOUND
machine_capability_code = CNC_ROUTER_CUTTING
batch_eligible = true
machine_id = compatible CNC (client-selected)
window = explicit
→ 1 MACHINE_RUN (HELD)
→ 2 participants ACTIVE
→ 1 run-owned Reservation (HELD)
→ machine time once
≠ Reservation(A) + Reservation(B)
```

---

## 23. Next implementation GO scope (bounded)

**In:**

```text
CreateMachineRunCommand / Result schemas
CREATE_MACHINE_RUN orchestrator service
participant validation (stamps + shared capability)
machine reservable + overlap reuse
run-owned reservation internal create
atomic histories
idempotency (sorted participants)
permission execution.machine_run.manage
isolated runtime tests (incl. R6 union ACTIVE)
face_cnc_cut two-plan fixture
```

**Out:**

```text
ADD/REMOVE participant after create
CONFIRM/RELEASE/CANCEL/SUPERSEDE run
START/COMPLETE
auto-batch / nesting
UI / Mobile
Capacity / Phase B
machines.capabilities hard inventory GO (unless paired)
```

```text
NEXT_IMPLEMENTATION_SCOPE = CREATE_MACHINE_RUN_ONLY
RUNTIME_IMPLEMENTATION = NOT_STARTED
```

---

## 24. Overengineering check

| Candidate | Needed for atomic create? | Verdict |
| --------- | ------------------------- | ------- |
| Auto-batcher | no | defer |
| Lifecycle beyond HELD create | no | defer |
| New ResourceDomain MACHINE_RUN | no | defer |
| Full material compatibility | no | defer |
| UI | no | defer |
| MIN_PARTICIPANTS=1 | no — duplicates task reservation | reject |

---

## 25. QA proof (read-only this GO)

```text
QA Alembic = s66_machine_run_reservation_grain
QA SHA = b7950463b2956e779275e14fa81ee742a681ccee2e9f338a9db1310e1b740fb1
machine_runs / participants / transitions / reservations = 0
Scheduling = ACTIVE
Reservation = ACTIVE
Capacity = NOT_CONFIGURED
assignment transitions = 7
foreign_key_check = 0
plans 21/22/23 SHA unchanged
QA_MUTATIONS = 0
```

---

## 26. `/modules` · `/governance`

```text
NO_UI_CHANGE
```

Docs only: schema available · command readiness · runtime not active · do not list CREATE_MACHINE_RUN as live.
