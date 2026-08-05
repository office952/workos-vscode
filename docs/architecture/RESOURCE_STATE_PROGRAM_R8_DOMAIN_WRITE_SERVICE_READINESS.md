# Resource State Program R8 — Domain Write Service Readiness

**Task:** `RESOURCE_STATE_PROGRAM_R8 = DOMAIN_WRITE_SERVICE_READINESS`  
**Owner GO:** `AUTHORIZE_RESOURCE_STATE_PROGRAM_R8_DOMAIN_WRITE_SERVICE_READINESS`  
**Date:** 2026-08-05  
**Status:** **PASS** · Contracts **FINALIZED** · R9 implemented schedule+reservation writers (capacity still blocked)  
**Branch tip at authoring:** `eb40308c` (R7 accepted)  
**Worklog:** `docs/worklog/realignment/2026-08-05_resource_state_program_r8_domain_write_service_readiness.md`  
**R9 implementation:** `docs/worklog/realignment/2026-08-05_resource_state_program_r9_scheduling_and_reservation_writer_implementation.md`

```text
RESOURCE_STATE_PROGRAM_R8 = PASS
DOMAIN_WRITE_SERVICE_READINESS = COMPLETE
SCHEDULING_WRITER_CONTRACT = FINALIZED
MACHINE_RESERVATION_WRITER_CONTRACT = FINALIZED
CAPACITY_ALLOCATION_WRITER_CONTRACT = FINALIZED_WITH_EXACT_BLOCKER
CAS = DEFINED
IDEMPOTENCY = DEFINED
TRANSACTION_BOUNDARY = DEFINED
TRANSITION_HISTORY = DEFINED
CONCURRENCY_TESTS = DEFINED
OVER_ALLOCATION_VALIDATION = BLOCKED_UNTIL_CAPACITY_SOURCE_EXISTS
DOMAIN_ACTIVATION = NOT_AUTHORIZED
QA_RESOURCE_STATE_ROWS = 0
PHASE_B_WIRING = NOT_AUTHORIZED
PHASE_C = BLOCKED
R9 = PASS  # scheduling + reservation writers implemented; QA not activated
```

This document remains the **canonical write-service contract**. R9 implements scheduling + reservation writers against these contracts; capacity writer and QA activation stay separate.

---

## 0. Sources preserved

| Source | Use in R8 |
| ------ | --------- |
| R1 Owner decisions | Architecture, CAS, history, machine≠assignment, capacity minutes, fail-closed |
| R2 schema readiness | Table package, statuses, partial uniques, overlap = service |
| R3–R5 | Schema `s64` live on QA empty |
| R6 read evaluators | Blocking statuses; DISABLED → NOT_CONFIGURED |
| R7 configuration command | CAS/idempotency/txn pattern; `DOMAIN_WRITER_READY`; activation gate |
| Assignment dual-write | Plan lock + `WITH FOR UPDATE` + task_key in `tasks_json` + transition idempotency |

R8 does **not** reopen R1–R7 semantics. It freezes **command contracts** against the **first-schema** status vocabularies already in ORM CHECK constraints.

---

## 1. Non-goals (explicit)

```text
NO scheduling engine / auto-planning
NO optimizer
NO Phase B wiring
NO Phase C
NO QA activation / QA Resource State rows
NO new Alembic migration in R8
NO frontend / Employee Mobile
NO hard delete of current or history rows
NO synthetic CLEAR backfill
```

---

## 2. Shared writer platform (all three domains)

### 2.1 Preconditions (every command)

1. Domain configuration row exists and `status=ACTIVE` for the domain (else reject `domain_not_active` / treat as write forbidden).  
2. `execution_plan_id` exists.  
3. `task_key` resolves inside plan `tasks_json.operational_tasks[].task_id` under plan lock.  
4. Actor has domain manage permission.  
5. Schema + transition tables present (Alembic-owned).  
6. No hard delete; terminal states only via status transitions / supersession.

### 2.2 CAS

```text
expected_version INTEGER
create → expected_version MUST be 0 (no prior current open row for that grain, or create-new after supersede)
update → expected_version MUST equal current row.version
success → version = version + 1
stale → 409 cas_stale
```

`updated_at` is audit only; **version** is CAS authority (R2/R7).

### 2.3 Idempotency

```text
idempotency_key String(36) UNIQUE on current-row create keys AND on transition rows
```

Fingerprint (minimum):

```text
operation, domain entity id (or create grain), execution_plan_id, task_key,
expected_version, target fields (window/machine/quantity/status),
reason_code, reason_note, actor_user_id
```

| Retry | Result |
| ----- | ------ |
| same key + same fingerprint | `already_applied=true`, no second transition |
| same key + different fingerprint | `409 idempotency_payload_conflict` |

Convention mirrors R7 config command + assignment `transition_id` payload compare.

### 2.4 Transaction boundary

```text
BEGIN (same AsyncSession / SQLite connection)
→ acquire plan lock (process lock by order_id + SELECT plan FOR UPDATE)
→ re-read domain configuration (must still be ACTIVE)
→ validate task_key / machine / windows
→ conflict / overlap queries
→ INSERT or CAS-UPDATE current row
→ INSERT append-only transition (same txn)
→ FLUSH
→ COMMIT
```

```text
current_row_mutation + transition_insert = SAME_SQLITE_TRANSACTION
NO_SILENT_OVERWRITE
ROLLBACK on any validation/CAS/overlap failure after mutation attempt
```

Service may commit (assignment style) or flush+router commit (R7 style). **R9 recommendation:** service owns commit inside plan lock (assignment pattern), because writers are plan-scoped and race-sensitive.

### 2.5 History

Append-only transition tables already exist:

- `execution_task_schedule_transitions`
- `execution_task_machine_reservation_transitions`
- `execution_task_capacity_allocation_transitions`

Repository: insert/read only; tests forbid update/delete mutators (R7 config pattern).

### 2.6 Error convention

| Condition | HTTP / code |
| --------- | ----------- |
| Stale CAS | 409 `cas_stale` |
| Idempotency payload conflict | 409 `idempotency_payload_conflict` |
| Invalid status transition | 409 `invalid_transition` |
| Overlap / open-row uniqueness | 409 `overlap_conflict` or `open_row_conflict` |
| Domain not ACTIVE | 409 `domain_not_active` |
| Domain DISABLED mid-write | 409 `domain_disabled` (re-read config in txn) |
| Plan missing | 404 `execution_plan_not_found` |
| Task missing in plan | 404 `task_key_not_found` |
| Machine missing | 404 `machine_not_found` |
| Machine not reservable | 422 `machine_not_reservable` |
| Invalid time window | 422 `invalid_time_window` |
| Permission denied | 403 |
| Over-allocation (capacity) | 409 `over_allocation` **only after** capacity source exists; until then see §5 |

### 2.7 Permissions (register in R9 — not in R8 code)

| Permission | Roles | Notes |
| ---------- | ----- | ----- |
| `execution.schedule.manage` | admin, manager | R1 proposed; **not registered yet** |
| `execution.machine_reservation.manage` | admin, manager | same |
| `execution.capacity_allocation.manage` | admin, manager | same |
| `execution.resource_state.read` | admin, manager | optional; R6 currently uses `execution.plan_generate` |
| `execution.resource_domain.configure` | admin, manager | **already registered** (R7) |

Operator / viewer: denied for all manage writes.

### 2.8 Common command envelope fields

Every write command body includes:

```text
execution_plan_id
task_key
expected_version
idempotency_key
reason_code          # required for cancel/release/supersede; required-or-default for create
reason_note?         # max 500, safe charset
correlation_id?
actor                # from auth, not client-spoofable
```

---

## 3. Scheduling writer contract

**Table:** `execution_task_schedules`  
**Statuses (schema-frozen):** `DRAFT | PLANNED | CONFIRMED | CANCELLED | SUPERSEDED`  
**Open authoring uniqueness:** at most one of `DRAFT|PLANNED|CONFIRMED` per `(execution_plan_id, task_key)`  
**Guard blocking (R6):** `PLANNED`, `CONFIRMED`  
**Non-blocking:** `DRAFT`, `CANCELLED`, `SUPERSEDED`

```text
DRAFT     = authoring state (not guard-blocking)
PLANNED   = blocking scheduled intent
CONFIRMED = blocking confirmed schedule
CANCELLED = terminal
SUPERSEDED = terminal (replaced by newer schedule row)
```

### 3.1 Commands

#### CREATE_SCHEDULE

| Item | Spec |
| ---- | ---- |
| Purpose | Create first open schedule for plan+task |
| Required inputs | plan, task_key, scheduled_start/end, timezone, `initial_status` ∈ {DRAFT, PLANNED}, workcenter_code?, expected_version=0, idempotency_key, reason_code |
| Allowed prior | no open row for plan+task |
| Target status | DRAFT or PLANNED |
| Conflicts | open_row_conflict if open exists; invalid_time_window if end≤start; overlap_conflict if another blocking window for same task overlaps (should not happen if partial unique holds — still check) |
| History | operation=`CREATE_SCHEDULE`, previous_*=null, new_*=created |

Creating directly as `CONFIRMED` is **forbidden** in first writer (must CREATE then CONFIRM) — keeps audit trail clear.

#### RESCHEDULE

| Item | Spec |
| ---- | ---- |
| Purpose | Change window (and optional workcenter) on open schedule |
| Required inputs | schedule_id, new start/end, timezone?, workcenter_code?, expected_version, idempotency_key, reason_code |
| Allowed current | DRAFT, PLANNED, CONFIRMED |
| Target status | **unchanged** (status preserved) |
| Conflicts | cas_stale; invalid_time_window; overlap vs other open rows (N/A under partial unique of one open); domain_disabled |
| History | operation=`RESCHEDULE`, previous/new start/end, version+1 |

#### CONFIRM_SCHEDULE

| Item | Spec |
| ---- | ---- |
| Allowed current | DRAFT → CONFIRMED, or PLANNED → CONFIRMED |
| Target | CONFIRMED |
| Forbidden | CONFIRM from CANCELLED/SUPERSEDED; CONFIRM when already CONFIRMED unless idempotent retry |
| History | `CONFIRM_SCHEDULE` |

#### CANCEL_SCHEDULE

| Item | Spec |
| ---- | ---- |
| Allowed current | DRAFT, PLANNED, CONFIRMED |
| Target | CANCELLED |
| Side effects | set `cancelled_at` / `cancelled_by` (CHECK requires cancelled_at when CANCELLED) |
| Reason | reason_code **required** |
| History | `CANCEL_SCHEDULE` |

#### SUPERSEDE_SCHEDULE

| Item | Spec |
| ---- | ---- |
| Purpose | Atomically terminalize current open row and create replacement |
| Allowed current | DRAFT, PLANNED, CONFIRMED |
| Effect (same txn) | (1) old.status→SUPERSEDED, old.superseded_by_id→new.id, version+1 + transition `SUPERSEDE_SCHEDULE`; (2) insert new open row (DRAFT or PLANNED) version=1 + transition `CREATE_SCHEDULE` (or single compound op recorded on both) |
| Recommendation | Record **two** transitions (supersede on old, create on new) with shared `correlation_id`; distinct idempotency keys or one compound key with documented sub-ops — **R9 must pick one and test**. Preferred: **two transitions, one correlation_id, client supplies supersede_key + create_key**. |
| Reason | required on supersede |

### 3.2 Scheduling status matrix

| From \ To | DRAFT | PLANNED | CONFIRMED | CANCELLED | SUPERSEDED |
| --------- | ----- | ------- | --------- | --------- | ---------- |
| (create) | CREATE | CREATE | — | — | — |
| DRAFT | RESCHEDULE | *(optional promote — not in min command set; use CONFIRM or recreate)* | CONFIRM | CANCEL | SUPERSEDE |
| PLANNED | — | RESCHEDULE | CONFIRM | CANCEL | SUPERSEDE |
| CONFIRMED | — | — | RESCHEDULE | CANCEL | SUPERSEDE |
| CANCELLED | — | — | — | — | — |
| SUPERSEDED | — | — | — | — | — |

Optional `PROMOTE_DRAFT_TO_PLANNED` deferred — not required for R9 minimum if CREATE may start as PLANNED.

### 3.3 Scheduling overlap / conflict

- Partial unique enforces one open row per plan+task.  
- Service still validates `end > start` and rejects concurrent create races with `open_row_conflict` / unique integrity → mapped 409.  
- No cross-task schedule optimizer.  
- Employee assignment is **out of scope** (must not write `assigned_employee_id`).

---

## 4. Machine reservation writer contract

**Table:** `execution_task_machine_reservations`  
**Statuses:** `HELD | RESERVED | CANCELLED | RELEASED | SUPERSEDED`  
**Open uniqueness:** one of `HELD|RESERVED` per `(plan, task_key, machine_id)`  
**Guard blocking:** `HELD`, `RESERVED`  
**Non-blocking:** `CANCELLED`, `RELEASED`, `SUPERSEDED`

### 4.1 Concept separation (R1 DEC-09)

```text
machine assignment  ≠  machine reservation  ≠  machine usage
```

- Assignment = ops task machine identity (write still NOT_IMPLEMENTED).  
- Reservation = time-bound claim in this table.  
- Usage = session/reality (out of triad writers).

Assignment alone must never imply reservation CLEAR/ACTIVE.

### 4.2 Commands

#### CREATE_RESERVATION

| Item | Spec |
| ---- | ---- |
| Inputs | plan, task_key, machine_id, reservation_start/end, timezone, `initial_status` ∈ {HELD, RESERVED}, expected_version=0, idempotency_key, reason_code |
| Machine validation | row exists; for first writer: require `MachinesReadService.machine_available` semantics (`is_active` ∧ `is_available` ∧ `operational_status==active`) unless Owner later allows inactive holds |
| Task validation | task_key in plan |
| Window | end > start |
| Overlap | no overlapping open reservation on **same machine_id** with status in {HELD,RESERVED} (any plan/task) — transactional query |
| Multi-machine per task | **Allowed by schema** (different machine_id). Policy: **ALLOW** concurrent open reservations for different machines on same task (R2 open decision → R8 default ALLOW; Owner may tighten later) |
| History | `CREATE_RESERVATION` |

#### CONFIRM_RESERVATION

Schema has **no** `CONFIRMED` status (deferred in R2). Map Owner command name to schema:

```text
CONFIRM_RESERVATION = HELD → RESERVED
```

| Allowed | HELD |
| Target | RESERVED |
| Idempotent | already RESERVED + same key → already_applied |
| History | `CONFIRM_RESERVATION` |

Do **not** add CONFIRMED without expand-only migration GO.

#### RELEASE_RESERVATION

| Allowed | HELD, RESERVED |
| Target | RELEASED |
| Side effects | `released_at` / `released_by` |
| Reason | required |
| Semantics | orderly end of claim (resource freed) — distinct from CANCEL |

#### CANCEL_RESERVATION

| Allowed | HELD, RESERVED |
| Target | CANCELLED |
| Side effects | `cancelled_at` / `cancelled_by` |
| Reason | required |
| Semantics | abort / void — distinct from RELEASE |

#### SUPERSEDE_RESERVATION

Same atomic pattern as schedule supersede: terminalize old → SUPERSEDED + create new open reservation; two transitions + correlation_id preferred.

### 4.3 Reservation status matrix

| From \ To | HELD | RESERVED | RELEASED | CANCELLED | SUPERSEDED |
| --------- | ---- | -------- | -------- | --------- | ---------- |
| (create) | CREATE | CREATE | — | — | — |
| HELD | *(window adjust via SUPERSEDE or future ADJUST — not min)* | CONFIRM | RELEASE | CANCEL | SUPERSEDE |
| RESERVED | — | *(no-op / idempotent)* | RELEASE | CANCEL | SUPERSEDE |
| RELEASED / CANCELLED / SUPERSEDED | — | — | — | — | — |

Window change on open reservation: **prefer SUPERSEDE** (clear audit) rather than silent UPDATE of times without history of old window — if R9 adds `ADJUST_RESERVATION_WINDOW`, it must CAS + transition with previous/new start/end (columns already exist on transition model).

**R8 minimum:** no ADJUST command; use SUPERSEDE for window changes.

### 4.4 Inactive machine policy (R2 open → R8 default)

```text
INACTIVE_MACHINE_RESERVATION = FORBIDDEN_IN_FIRST_WRITER
```

Must pass `machine_available` (or equivalent). Owner GO may later allow HELD-only on inactive machines.

---

## 5. Capacity allocation writer contract

**Table:** `execution_task_capacity_allocations`  
**Statuses:** `HELD | ALLOCATED | RELEASED | CANCELLED | SUPERSEDED`  
**Unit:** `minutes` only  
**Scope:** `WORKCENTER` (workcenter_code string) XOR `MACHINE` (machine_id FK)  
**Guard blocking:** `HELD`, `ALLOCATED`

### 5.1 Commands

#### CREATE_ALLOCATION

| Inputs | plan, task_key, resource_scope_type, workcenter_code **or** machine_id, bucket_start/end, timezone, quantity (>0 minutes), initial_status ∈ {HELD, ALLOCATED}, expected_version=0, idempotency_key, reason_code |
| Validation | scope XOR; machine exists if MACHINE; workcenter_code non-blank if WORKCENTER (no relational workcenters table — string identity only); bucket end>start; unit forced `minutes` |
| Over-allocation | see §5.3 |
| History | `CREATE_ALLOCATION` |

#### ADJUST_ALLOCATION

| Allowed | HELD, ALLOCATED |
| Effect | change quantity and/or bucket window; status unchanged; version+1 |
| History | `ADJUST_ALLOCATION` with previous/new quantity and buckets |
| Over-allocation | re-check §5.3 |

#### RELEASE_ALLOCATION

| Allowed | HELD, ALLOCATED → RELEASED |
| Reason | required |
| History | `RELEASE_ALLOCATION` |

#### CANCEL_ALLOCATION

| Allowed | HELD, ALLOCATED → CANCELLED |
| Reason | required |
| History | `CANCEL_ALLOCATION` |

#### SUPERSEDE_ALLOCATION

Atomic terminalize + create replacement (same pattern as schedule/reservation).

### 5.2 Capacity status matrix

| From \ To | HELD | ALLOCATED | RELEASED | CANCELLED | SUPERSEDED |
| --------- | ---- | --------- | -------- | --------- | ---------- |
| (create) | CREATE | CREATE | — | — | — |
| HELD | ADJUST | *(optional promote — deferred; CREATE may start ALLOCATED)* | RELEASE | CANCEL | SUPERSEDE |
| ALLOCATED | — | ADJUST | RELEASE | CANCEL | SUPERSEDE |
| terminal | — | — | — | — | — |

### 5.3 Over-allocation boundary (exact blocker)

Repo evidence: **no canonical available-capacity / minutes-pool source**.

| Candidate | Classification |
| --------- | -------------- |
| `execution_task_capacity_allocations` | demand/allocation side only |
| `workcenter_rates` | commercial rates — **not** capacity |
| HR productive hours / CostEngine labor | **out of** Resource State triad (R1) |
| `machines.capacity_metadata` | ad-hoc JSON — **not** minutes pool |
| Relational workcenters / pools | **absent** |

```text
OVER_ALLOCATION_VALIDATION =
BLOCKED_UNTIL_CAPACITY_SOURCE_EXISTS
```

**R9 capacity writer may implement:**

1. Schema/write correctness (create/adjust/release/cancel/supersede, CAS, history, permissions) **without** ceiling checks; **or**  
2. Stay blocked entirely until a Capacity Source GO lands.

**R8 recommendation for sequencing:** do **not** activate `CAPACITY_ALLOCATION` domain until both writer **and** capacity source exist. Schema-correct writes on isolated DBs may precede activation, but **QA activation remains forbidden**.

```text
CAPACITY_DOMAIN_ACTIVATION_PREREQUISITE =
  writer_exists
  AND capacity_source_canonical_exists
  AND over_allocation_rules_implemented
  AND isolated+runtime proofs
```

---

## 6. Concurrency design

Under SQLite single-writer + plan lock + CAS:

| Scenario | Expected outcome |
| -------- | ---------------- |
| Two overlapping CREATE_SCHEDULE same task | one success; other 409 open_row_conflict / unique |
| Two overlapping CREATE_RESERVATION same machine window | one success; other 409 overlap_conflict |
| Two ADJUST/CAS on same allocation | one success; other 409 cas_stale |
| CANCEL racing RESCHEDULE same schedule | one serialized success; other cas_stale or invalid_transition |
| RELEASE racing Phase B reassignment | **out of R9 scope** until Phase B wiring; design note: reassignment must re-read derived CLEAR in same txn (R1 DEC-07) — release then reassignment → CLEAR may pass; reservation ACTIVE blocks |
| Domain DISABLE racing domain write | writer re-reads config in txn → 409 domain_disabled; disable CAS on config separate |
| Idempotent retry during race | second sees transition by key → already_applied |

```text
RESULT ∈ { serialized_success, explicit_conflict }
NO_SILENT_LOST_UPDATE
```

---

## 7. Activation readiness (per domain)

Flip `DOMAIN_WRITER_READY[domain]=True` in R7 gate **only after** prerequisites below. Env bypass remains test-only.

### Minimum checklist (all domains)

```text
schema exists (s64 tables)
read evaluator exists (R6)
writer service exists
transition history writing proven
permissions registered + enforced
isolated tests pass
runtime test on temporary DB passes
no inconsistent source status rows
domain configuration command available (R7)
Owner GO authorizing activation (separate from writer GO)
```

### Per-domain extras

| Domain | Extra |
| ------ | ----- |
| SCHEDULING | scheduling writer implemented + overlap/CAS proofs |
| MACHINE_RESERVATION | reservation writer + machine validation + machine overlap proofs |
| CAPACITY_ALLOCATION | allocation writer **and** `CAPACITY_SOURCE` **and** over-allocation rules |

```text
SCHEDULING activation blocked until scheduling writer exists
MACHINE_RESERVATION activation blocked until reservation writer exists
CAPACITY activation blocked until allocation writer AND capacity source exist
QA activation = NOT_AUTHORIZED in R8/R9 unless separate Owner GO
```

---

## 8. Implementation sequencing

### Option A — all three writers in one build

| + | Resource State “complete” faster |
| - | Large scope; capacity blocked on missing source; review risk |

### Option B — scheduling + reservation together; capacity separate (**SELECTED**)

| + | Same temporal/overlap nature; shared plan-lock platform; capacity waits on source GO |
| - | Capacity domain stays NOT_CONFIGURED longer |

**Repo confirmation:** no capacity source → Option A would ship a third writer that cannot safely activate. **OPTION_B confirmed.**

```text
R9  = SCHEDULING_AND_RESERVATION_WRITER_IMPLEMENTATION
R10 = CAPACITY_ALLOCATION_WRITER (+ depends on CAPACITY_SOURCE GO)  # naming reserved; not authorized
```

Do not micro-split R9 further unless implementation proves too large mid-build.

---

## 9. Future test matrix (R9 / capacity build)

### Common

```text
create success
CAS conflict (stale expected_version)
idempotent retry (already_applied)
payload mismatch conflict
invalid transition
history exactly once
atomic rollback (transition absent if current fails)
task missing → 404
permission denial (operator/viewer)
domain disabled / not active → 409
```

### Scheduling-specific

```text
time window invalid
open_row_conflict second create
confirm DRAFT→CONFIRMED and PLANNED→CONFIRMED
cancel sets cancelled_at
supersede creates new + terminals old
RESCHEDULE preserves status
evaluator: PLANNED/CONFIRMED → ACTIVE; DRAFT → CLEAR when configured
```

### Reservation-specific

```text
machine missing / not reservable
overlap same machine
CONFIRM HELD→RESERVED
RELEASE vs CANCEL semantics
multi-machine same task allowed
evaluator HELD/RESERVED → ACTIVE
```

### Capacity-specific (split)

```text
A. schema/write correctness:
   create/adjust/release/cancel/supersede, CAS, history, scope XOR, unit=minutes
B. available-capacity business validation:
   BLOCKED_UNTIL_CAPACITY_SOURCE_EXISTS
   (no fake ceiling from rates/HR)
```

---

## 10. Internal API sketch (future — not implemented in R8)

Bounded under `/api/v1/execution/resource-state/…` (same family as R6/R7):

```text
POST .../schedules
POST .../schedules/{id}/reschedule
POST .../schedules/{id}/confirm
POST .../schedules/{id}/cancel
POST .../schedules/{id}/supersede

POST .../machine-reservations
POST .../machine-reservations/{id}/confirm
POST .../machine-reservations/{id}/release
POST .../machine-reservations/{id}/cancel
POST .../machine-reservations/{id}/supersede

POST .../capacity-allocations          # after capacity writer GO
...
```

Exact paths may follow router conventions; permissions per §2.7.

---

## 11. Open Owner decisions (non-blocking for R8 PASS)

| ID | Topic | R8 default for R9 |
| -- | ----- | ----------------- |
| OD-R8-01 | Multi-machine open reservations per task | **ALLOW** |
| OD-R8-02 | Inactive machine reservation | **FORBIDDEN** |
| OD-R8-03 | Supersede idempotency key shape | two keys + shared correlation_id |
| OD-R8-04 | Capacity source model | **OWNER_GO_REQUIRED** before activation |
| OD-R8-05 | Plan deletion with resource history | still OWNER_DECISION when delete UI exists (R2) |

---

## 12. Dead pieces

| Piece | Class |
| ----- | ----- |
| HOLD / not_reserved / NOT_STARTED | PLACEHOLDER — not writer inputs |
| ORR Pregătit | ACTIVE_LEGACY — not capacity/schedule truth |
| Phase B env CLEAR | TEST_ONLY — not removed here |
| workcenter_rates as capacity | REJECTED as available-capacity source |

```text
Dead pieces removed: NONE
```

---

## 13. Next Owner gate

```text
FUTURE CANDIDATE:
RESOURCE_STATE_PROGRAM_R10_CONTROLLED_DOMAIN_ACTIVATION_READINESS
```

R9 delivered scheduling + reservation writers. Capacity writer remains separate until capacity source exists. R10 decides activation readiness (including whether schedule+reservation may activate while capacity stays NOT_CONFIGURED) — **without** auto-activating QA.

```text
SCHEDULING_WRITER = IMPLEMENTED
MACHINE_RESERVATION_WRITER = IMPLEMENTED
CAPACITY_WRITER = NOT_IMPLEMENTED
PHASE_B_WIRING = NOT_AUTHORIZED
PHASE_C = BLOCKED
```
