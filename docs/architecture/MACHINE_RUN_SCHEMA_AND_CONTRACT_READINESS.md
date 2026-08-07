# MACHINE_RUN — Schema and Contract Readiness

**Task:** `MACHINE_RUN_SCHEMA_AND_CONTRACT_READINESS`  
**Owner GO:** `AUTHORIZE_MACHINE_RUN_SCHEMA_AND_CONTRACT_READINESS`  
**Date:** 2026-08-07  
**Status:** **PASS** · docs-only · **no runtime · no ORM · no migration**  
**Starting HEAD:** `2e7e4310`  
**Prerequisites:** Owner D4 MACHINE_RUN owns Reservation · `face_cnc_cut` machine demand E2E PASS · TRR contract + projection PASS  
**Worklog:** `docs/worklog/realignment/2026-08-07_machine_run_schema_and_contract_readiness.md`

```text
MACHINE_RUN_SCHEMA_AND_CONTRACT_READINESS = PASS
MACHINE_RUN_OWNERSHIP = FINALIZED
RESERVATION_RELATION = FINALIZED
PARTICIPANT_MODEL = FINALIZED
MULTI_PLAN_PARTICIPATION = SUPPORTED
BATCH_ELIGIBILITY_BOUNDARY = FINALIZED
NESTING_BOUNDARY = FINALIZED
MACHINE_TIME_COUNTING = ONCE_PER_RUN
STATUS_MODEL = BOUNDED_FOR_READINESS
CAS_IDEMPOTENCY_HISTORY = FINALIZED
SCHEMA_GAP = FINALIZED
RESERVATION_GRAIN_REALIGNMENT_READINESS = PASS
MACHINE_RUN_SCHEMA_FOUNDATION = PASS
QA_S66_SCHEMA_ROLLOUT = PASS
MACHINE_RUN_MINIMAL_COMMAND_RUNTIME_READINESS = PASS
CREATE_MACHINE_RUN_MINIMAL_RUNTIME_IMPLEMENTATION = PASS
MACHINE_RUN_MINIMAL_RESERVATION_LIFECYCLE_READINESS = PASS
MACHINE_RUN_CONFIRM_RELEASE_CANCEL_RUNTIME_IMPLEMENTATION = PASS
RESCHEDULE_MACHINE_RUN_RUNTIME_IMPLEMENTATION = PASS
MACHINE_RUN_PARTICIPANT_MUTATION_RUNTIME_READINESS = PASS
MACHINE_RUN_ADD_REMOVE_PARTICIPANT_RUNTIME_IMPLEMENTATION = PASS
CODE_ALEMBIC_HEAD = s66_machine_run_reservation_grain
QA_ALEMBIC = s66_machine_run_reservation_grain
RUNTIME_IMPLEMENTATION = VERIFIED
MACHINE_RUN_RUNTIME = CREATE_LIFECYCLE_RESCHEDULE_PARTICIPANT_MUTATION_IMPLEMENTED_IN_CODE
MACHINE_RUN_LIFECYCLE = CREATE_PLUS_RESERVATION_LIFECYCLE_PLUS_RESCHEDULE_PLUS_PARTICIPANT_MUTATION
AUTO_BATCH = NOT_IMPLEMENTED
CONFIRM_RELEASE_CANCEL = VERIFIED
RESCHEDULE_MACHINE_RUN = VERIFIED
PARTICIPANT_MUTATION = VERIFIED
MACHINE_RUN_EXECUTION_LIFECYCLE_READINESS = PASS
MACHINE_RUN_EXECUTION_LIFECYCLE = NOT_IMPLEMENTED
QA_MUTATIONS = 0
CAPACITY_STAGE_1 = IMPLEMENTED_INACTIVE
PHASE_B = NOT_AUTHORIZED
PHASE_C = BLOCKED
NEXT_TASK = NOT_AUTHORIZED
```

---

## 1. Central principle

```text
MACHINE_RUN
≠ task
≠ Machine Reservation
≠ product / order
≠ commercial nesting sheet
≠ Intake nesting preview
```

Role:

```text
MACHINE_RUN
= planned / real shared machine execution
  for one or more compatible MACHINE_BOUND tasks
  under exactly one exclusive Machine Reservation
```

Example (conceptual):

```text
MACHINE_RUN R-001
machine        = CNC_01          (via owned reservation)
reservation    = RES-77
participants:
  - plan 31 / task_key …:cnc_face_cut (face_cnc_cut)
  - plan 32 / task_key …:cnc_face_cut
  - plan 35 / task_key …:cnc_face_cut
machine time   = 70 minutes once
≠ 70 + 70 + 70
```

---

## 2. Ownership (finalized)

| Layer | Owns | Does not own |
| ----- | ---- | ------------ |
| **Task** (EP snapshot) | Technical demand: capability, `resource_mode`, `batch_eligible`, WC, operation | Concrete `machine_id`, exclusive interval, run membership as SoT |
| **Machine Reservation** | Concrete `machine_id` + exclusive interval + open exclusivity enforcement | Task demand fields; participant list; commercial identity merge |
| **MACHINE_RUN** (future) | Shared execution grouping; participant identities; one runtime context; provenance links; **reference** to exactly one Reservation | Capability/demand SoT; commercial totals; Capacity truth |
| **Commercial / Intake nesting** | Sheet/roll consumption, waste, tariff batch hints, preview layouts | Reservation; MACHINE_RUN; EP task identity mutation |

```text
demand     = Operation Contract → Aggregate → EP task
commitment = Machine Reservation (exclusive machine clock)
grouping   = MACHINE_RUN (participants under one reservation)
```

**Forbidden:** MACHINE_RUN inventing or mutating technical demand (`machine_capability_code`, `resource_mode`, `batch_eligible`).

---

## 3. Reservation relationship (finalized)

### Decision

```text
MACHINE_RUN owns reservation reference
machine_runs.reservation_id → execution_task_machine_reservations.id
cardinality = exactly one Reservation per MACHINE_RUN
```

Inverse `reservation.machine_run_id` is **not** the ownership authority. An optional denormalized back-pointer may be added later for indexing only.

**CREATE policy (readiness):** a run reaches open `HELD` only with an owned reservation already attached (create reservation in the same command txn, or attach one open reservation). There is no long-lived run without `reservation_id`. Temporary in-memory draft before first persist is an API concern, not a null-FK schema state.

**SUPERSEDE (future):** `reservation_id UNIQUE` applies to the **current** run row that owns the open claim. Supersede terminals the old run (`SUPERSEDED`) and creates a **new** run row with a **new** reservation (same pattern as reservation supersede). Historical runs keep their original `reservation_id` pointing at terminal reservation rows.

### Why (repo + Owner)

1. Owner D4 already states MACHINE_RUN owns exactly one Machine Reservation (`MACHINE_BATCH_AND_MANUAL_WORKSPACE_OWNER_DECISIONS.md`).
2. Reservation is today’s exclusive-interval grain (`machine_id` + window + open overlap / partial unique). Run must sit **above** that grain, not invent a second exclusive clock.
3. Today’s reservation row is **task-keyed** (`execution_plan_id`, `task_key`, `machine_id`). Multi-participant runs cannot honestly treat each participant as the reservation owner.

### Known schema tension — resolved at readiness (implementation still deferred)

Grain realignment readiness (docs-only):  
`docs/architecture/MACHINE_RUN_RESERVATION_GRAIN_REALIGNMENT_READINESS.md`

| Today | Target |
| ----- | ------ |
| Reservation requires one `task_key` | **OPTION_B:** TASK owner XOR RUN owner (`machine_run_id`) |
| Open unique `(plan, task_key, machine_id)` | Keep for TASK; run-owned uses `machine_run_id` + shared machine overlap |
| CREATE API is single-task | Keep task POST; MACHINE_RUN orchestration owns run-level create |

**Reuse as-is:** overlap checks, CAS/`expected_version`, transition idempotency, status vocabulary for the claim, machine reservability gates.  
**Do not** create a parallel exclusive-time system on the run row.  
**Do not** implement MACHINE_RUN runtime until reservation grain schema lands (same atomic migration slice).

---

## 4. Participant model (finalized)

Participants **reference** tasks; they do not clone `tasks_json`.

### Minimal participant identity

| Field | Required | Role |
| ----- | -------- | ---- |
| `machine_run_id` | yes | Parent run |
| `execution_plan_id` | yes | Plan scope |
| `task_key` | yes | Stable within plan (`FrozenTaskIdentity.deterministic_task_key`) |
| `order_id` | yes (denormalized) | Cross-plan / commercial provenance (same pattern as reservation) |

### Optional denormalized join aids (not SoT)

| Field | Role |
| ----- | ---- |
| `source_operation_code` | e.g. `face_cnc_cut` — join aid |
| `workcenter_code` | routing display / filter |
| `machine_capability_code` | match filter at attach time (still owned by task snapshot) |

### Explicit non-fields on participant (v1)

```text
full frozen_identity blob
commercial payload
material geometry
per-participant reservation_id
cost share / commercial allocation
batch_grouping_key as auto-stamp authority
```

Unique membership (design): one ACTIVE row per `(machine_run_id, execution_plan_id, task_key)`. Soft-remove (`REMOVED`) preferred over hard delete.

**Note:** `execution_task_participants` (employee HELPER membership) is a different domain — do not reuse as MACHINE_RUN participants.

---

## 5. Eligibility boundary (finalized)

A task **may join a future MACHINE_RUN** only when all hold:

```text
batch_eligible = true
resource_mode = MACHINE_BOUND
machine_capability_code compatible with the run machine
```

### face_cnc_cut proof of concept (already stamped)

```text
operation_code           = face_cnc_cut
workcenter               = WC_CNC_ROUTING
machine_capability_code  = CNC_ROUTER_CUTTING
resource_mode            = MACHINE_BOUND
batch_eligible           = true
→ MAY_JOIN_FUTURE_MACHINE_RUN
→ NOT sufficient for auto-grouping
```

### Insufficient alone

```text
batch_eligible = true
≠ MACHINE_RUN exists
≠ reservation exists
≠ tasks grouped
≠ nesting performed
≠ machine time shared
```

Future grouping service (separate Owner GO) must still check material / process / setup / nesting / timing / production rules. Those rules are **not** defined in this readiness package.

### Legacy / unknown

Tasks without authoritative capability / mode / `batch_eligible` remain:

```text
NOT_ELIGIBLE_OR_UNKNOWN
```

No backfill of plans 21 / 22 / 23.

---

## 6. Status model (bounded for readiness)

Prefer **lockstep vocabulary with Machine Reservation** for the planning claim lifecycle:

| Status | Needed for readiness? | Role | Terminal? | Who changes (future) |
| ------ | --------------------- | ---- | --------- | -------------------- |
| `HELD` | **Yes** | Authoring / held intent | no | planner/manager CREATE / edit |
| `RESERVED` | **Yes** | Confirmed open run; owned reservation open | no | CONFIRM |
| `CANCELLED` | **Yes** | Aborted | **yes** | CANCEL |
| `RELEASED` | **Yes** | Normal release of machine claim | **yes** | RELEASE |
| `SUPERSEDED` | Later (optional first slice) | Replaced by another run | **yes** | SUPERSEDE |
| `RUNNING` | **Readiness PASS** (not in s66 yet) | Shop-floor started | no | START (future impl) |
| `COMPLETED` | **Readiness PASS** (not in s66 yet) | Shop-floor finished | **yes** (future) | COMPLETE then RELEASE |

```text
one MACHINE_RUN lifecycle (recommended)
planned (HELD → RESERVED) → [future RUNNING] → RELEASED / CANCELLED / [future COMPLETED]
```

**Why not adopt DRAFT/READY/RUNNING now as the readiness set:** Reservation already uses HELD/RESERVED; dual vocabularies without shop-floor consumers is overengineering. `RUNNING`/`COMPLETED` wait until actual timestamps exist.

**Lockstep meaning:** status **names** align with Reservation for cognitive reuse. Run status is **not** automatically derived from reservation status — writers must keep them consistent in the same command txn. A future GO may tighten sync rules; readiness does not invent a second independent open/terminal matrix.

---

## 7. Runtime versus planning

| Concept | Home | Notes |
| ------- | ---- | ----- |
| Planned machine run | MACHINE_RUN status `HELD`/`RESERVED` | Same entity lifecycle |
| Exclusive interval | **Owned Machine Reservation** | Sole exclusive clock |
| Estimated run minutes | Planning hint on run or derived from demand | ≠ reserved window ≠ actual |
| Actual runtime | Future `actual_started_at` / `actual_ended_at` on run | Defer measurement |

```text
estimated_run_minutes  ≠ reserved_interval ≠ actual_runtime_minutes
example: estimate 60 · reservation 08:00–09:15 · actual 68
```

Do **not** store a second exclusive window on the run as SoT.

---

## 8. Cost and allocation (boundary only)

```text
machine runtime counted once per MACHINE_RUN
```

Later cost/commercial allocation among participants is allowed as a **separate** concern. MACHINE_RUN must not double machine minutes per participant task. No cost/material/commercial allocation schema in this GO.

---

## 9. Nesting boundary (finalized)

### What exists today

| Artifact | Role | MACHINE_RUN? |
| -------- | ---- | ------------ |
| Flat / plexi / forex / vinyl nesting services | Commercial / material qty, waste, preview | **No** |
| Intake V4/V6 nesting preview / `nesting_group_key` | Diagnostic / preview consolidation | **No** |
| Pricing nest batch labels (e.g. plexi face batch) | Tariff / cost trace | **No** |

Owner truth (unchanged): Intake material nesting does **not** satisfy `batch_eligible` and is **not** MACHINE_RUN.

### Decision

```text
nesting artifact (commercial / material / preview)
  → may INFORM future grouping
  → may later ATTACH as manufacturing payload to a MACHINE_RUN
  → MUST NOT own MACHINE_RUN
  → MUST NOT create Reservation by itself

MACHINE_RUN
  → does not become the commercial nesting SoT
```

No new nesting entity is required for readiness.

---

## 10. Multi-plan / multi-product (finalized)

```text
MACHINE_RUN may span multiple execution plans and products
when operationally valid — not automatic
```

- Provenance per participant: `(execution_plan_id, task_key, order_id)`.
- No repo rule found that legally forbids cross-order shop batching; also **no** executable compatibility engine yet.
- Do **not** bind run identity to a single Order as a hard schema rule.
- Current reservation writer locks by the reservation plan’s `order_id` — multi-order concurrency is a **future implementation gap**, documented only.

---

## 11. Concurrency / CAS / idempotency / history (finalized)

Mirror Resource State R8/R9 (reservation pattern):

```text
current row.version + expected_version CAS
transition.idempotency_key UNIQUE + payload fingerprint
append-only transitions
same transaction: mutate current + insert history
```

### Minimal command set for a future first slice

| Command | Readiness-needed? |
| ------- | ----------------- |
| `CREATE_RUN` | **Yes** |
| `ADD_PARTICIPANT` | **Yes** |
| `REMOVE_PARTICIPANT` | **Yes** (soft) |
| `ASSIGN_RESERVATION` / create-owned reservation as part of CREATE | **Yes** (relation) |
| `CONFIRM_RUN` | **Yes** |
| `CANCEL_RUN` | **Yes** |
| `RELEASE_RUN` | **Yes** (or fold into complete later) |
| `SUPERSEDE_RUN` | Future |
| `START_RUN` / `COMPLETE_RUN` | Future (shop-floor) |
| Auto-group / nest builder | Future — separate Owner GO |

---

## 12. Schema gap analysis (design only — not created)

### Recommended tables

| Table | Why now (for future GO) | Consumer | Derivable? |
| ----- | ----------------------- | -------- | ---------- |
| `machine_runs` | Run identity, status, version, `reservation_id` UNIQUE, `machine_id`, idempotency | writers, UI, accounting once | no |
| `machine_run_participants` | Multi-plan provenance without cloning tasks | grouping, ORR, audit | no |
| `machine_run_transitions` | Same audit/CAS replay as Reservation | writers, compliance | no |

### `machine_runs` — core fields

| Field | Why | Derivable? |
| ----- | --- | ---------- |
| `id` | PK | no |
| `reservation_id` UNIQUE FK | D4 ownership; required on persist (see §3 CREATE policy) | no |
| `machine_id` FK | Match owned reservation; query aid | must equal reservation’s machine |
| `status` | Lifecycle | no |
| `version` | CAS | no |
| `timezone` | Audit with windows | copy-ok from reservation |
| `estimated_run_minutes` | Optional planning hint | often from demand/window |
| `idempotency_key` | Create replay | no |
| `actual_*` | **Defer** | — |

Reserved interval SoT remains on the Reservation row.

### Smaller model rejected

A single JSON blob on reservation or EP cannot provide CAS, multi-plan participants, or append-only history without forking Resource State patterns.

### Migration readiness (future GO only)

- New Alembic revision after s65 (or current tip).
- Register in schema ownership / Resource State domain config (new domain key e.g. `MACHINE_RUN` — **not** present today).
- Adapt reservation create path for run-owned (nullable or sentinel `task_key` policy — **Owner decision required at implementation GO**).
- **This GO creates zero tables.**

---

## 13. Relation to existing tasks and protected plans

| Item | Disposition |
| ---- | ----------- |
| Plans 21 / 22 / 23 | Unchanged; no backfill |
| Tasks without stamps | `NOT_ELIGIBLE_OR_UNKNOWN` |
| `vector_prep` duration E2E | Orthogonal; remains PASS |
| `face_cnc_cut` three fields | Sufficient for `MAY_JOIN_FUTURE_MACHINE_RUN` only |

---

## 14. Product System boundary

```text
Operation Contract     = machine capability / resource demand truth
Component Contract     = geometry / material / process truth
Product Template       = composition
ExecutionPlan task     = frozen concrete task demand
Machine Reservation    = concrete machine commitment (exclusive clock)
MACHINE_RUN (future)   = shared execution grouping under one reservation
```

No per-product logic in Resource State for inventing demand.

---

## 15. QA proof (read-only)

```text
QA Alembic = s65_workcenter_capacity_source
Scheduling = ACTIVE
Machine Reservation = ACTIVE
Capacity = NOT_CONFIGURED
MACHINE_RUN tables = absent
MACHINE_RUN rows = 0
capacity source rows = 0
capacity allocation rows = 0
assignment transitions = 7
foreign_key_check = 0
QA SHA = b54d223f0f8929268319ff1589203d9999711908974cd60029395929ab9d28b4
plan 21 tasks_json SHA = 75933211c1c180d421648bd3c54a96493716ba4c92262f42032c522486b9ff59
plan 22 tasks_json SHA = 0ec2dce6f1daea4509808b876f58c9ee7326fb7059e64d057cd81fbbd35ecb97
plan 23 tasks_json SHA = 00ee947c0b5e2da587c0d0563f1051ca89379d66cfec434e75dbe3883ccfc1f2
QA_MUTATIONS = 0
RUNTIME_IMPLEMENTATION = NOT_STARTED
```

---

## 16. Overengineering check

| Candidate | Why now? | Verdict |
| --------- | -------- | ------- |
| ORM / migration | No consumer yet | **No** |
| `RUNNING`/`COMPLETED` | No shop-floor actuals | **Defer** |
| Cost share columns | No allocator | **Defer** |
| New nesting entity | Commercial nesting already exists | **No** |
| Auto-grouper | Explicitly forbidden until Owner GO | **No** |
| `reservation.machine_run_id` as authority | Conflicts with D4 | **No** |
| Three-table Resource State mirror | Needed for CAS/history/participants | **Yes (design)** |

---

## 17. Implementation gap list (for a future Owner GO)

1. ~~Atomic schema slice + OPTION_B grain~~ → s66 PASS.
2. ~~CREATE_RUN orchestration + R6 union~~ → runtime PASS.
3. ~~CONFIRM / RELEASE / CANCEL / RESCHEDULE~~ → runtime PASS.
4. ~~ADD/REMOVE_PARTICIPANT~~ → runtime PASS (HELD-only, soft REMOVED).
5. Phase B (later): consume union path — not authorized now.
6. Grouping service (eligibility beyond the three stamps) — separate GO.
7. Optional attach of nesting/program payload — separate decision.
8. ~~START/COMPLETE readiness~~ → PASS (runtime not started).
9. Machine reassignment / PAUSE / Phase B wiring — separate GO.

```text
RESERVATION_GRAIN_REALIGNMENT_READINESS = PASS
MACHINE_RUN_MINIMAL_COMMAND_RUNTIME_READINESS = PASS
CREATE_MACHINE_RUN_MINIMAL_RUNTIME_IMPLEMENTATION = PASS
MACHINE_RUN_MINIMAL_RESERVATION_LIFECYCLE_READINESS = PASS
MACHINE_RUN_CONFIRM_RELEASE_CANCEL_RUNTIME_IMPLEMENTATION = PASS
RESCHEDULE_MACHINE_RUN_RUNTIME_IMPLEMENTATION = PASS
MACHINE_RUN_PARTICIPANT_MUTATION_RUNTIME_READINESS = PASS
MACHINE_RUN_ADD_REMOVE_PARTICIPANT_RUNTIME_IMPLEMENTATION = PASS
MACHINE_RUN_EXECUTION_LIFECYCLE_READINESS = PASS
RUNTIME_IMPLEMENTATION = VERIFIED
PARTICIPANT_MUTATION = VERIFIED
MACHINE_RUN_EXECUTION_LIFECYCLE = NOT_IMPLEMENTED
NEXT_TASK = NOT_AUTHORIZED
```

Command readiness: `docs/architecture/MACHINE_RUN_MINIMAL_COMMAND_RUNTIME_READINESS.md`  
CREATE implementation worklog: `docs/worklog/realignment/2026-08-07_create_machine_run_minimal_runtime_implementation.md`  
Lifecycle readiness: `docs/architecture/MACHINE_RUN_MINIMAL_RESERVATION_LIFECYCLE_READINESS.md`  
Lifecycle implementation worklog: `docs/worklog/realignment/2026-08-07_machine_run_confirm_release_cancel_runtime_implementation.md`  
Participant mutation readiness: `docs/architecture/MACHINE_RUN_PARTICIPANT_MUTATION_RUNTIME_READINESS.md`  
Participant mutation implementation: `docs/worklog/realignment/2026-08-07_machine_run_add_remove_participant_runtime_implementation.md`  
Execution lifecycle readiness: `docs/architecture/MACHINE_RUN_EXECUTION_LIFECYCLE_READINESS.md`
