# Capacity Source and Writer Decision

**Task:** `CAPACITY_SOURCE_AND_WRITER_DECISION`  
**Owner GO:** `AUTHORIZE_CAPACITY_SOURCE_AND_WRITER_DECISION`  
**Date:** 2026-08-05  
**Status:** **PASS** · Decision complete · Stage 1 writer **IMPLEMENTED** · s65 migration closure **VERIFIED** · QA schema **s65** (empty Capacity tables) · QA Capacity **NOT_CONFIGURED**  
**Starting HEAD:** `efc3b190`  
**Worklog:** `docs/worklog/realignment/2026-08-05_capacity_source_and_writer_decision.md`  
**Stage 1 implementation:** `docs/worklog/realignment/2026-08-05_capacity_stage_1_workcenter_source_and_writer_implementation.md`  
**Migration readiness:** `docs/worklog/realignment/2026-08-05_capacity_stage_1_canonical_migration_and_qa_rollout_readiness.md`  
**QA schema rollout:** `docs/worklog/realignment/2026-08-05_capacity_stage_1_controlled_qa_schema_rollout.md`  
**Prerequisites:** Resource State R1–R11 PASS · Scheduling + Machine Reservation ACTIVE in QA · Capacity rows = 0

```text
CAPACITY_SOURCE_AND_WRITER_DECISION = PASS
CAPACITY_SOURCE = WORKCENTER_CONFIGURED_CAPACITY
RESOURCE_SCOPE = WORKCENTER_PRIMARY | MACHINE_DEFERRED_STAGE_2
CAPACITY_UNIT = minutes
PLANNING_BUCKET = DAY
TASK_WORKLOAD_SOURCE = LABELED_MINUTES_WITH_NULL_PRESERVED
AI_ESTIMATE_POLICY = PREVIEW_PLANNING_ONLY_NEVER_SILENT_EXECUTION_TRUTH
OVER_ALLOCATION_POLICY = CONFIGURABLE_PER_WORKCENTER_DEFAULT_WARN_ONLY
CAPACITY_WRITER_CONTRACT = FINALIZED
CAPACITY_EVALUATOR_SEMANTICS = FINALIZED
PHASE_B_CAPACITY_POLICY = FINALIZED
IMPLEMENTATION_STRATEGY = OPTION_D_STAGED
CAPACITY_STAGE_1 = PASS
CAPACITY_WRITER = IMPLEMENTED
CAPACITY_STAGE_1_MIGRATION_READINESS = PASS
CAPACITY_STAGE_1_QA_SCHEMA_ROLLOUT = PASS
CANONICAL_MIGRATION_CLOSURE = VERIFIED
code Alembic = s65_workcenter_capacity_source
QA Alembic = s65_workcenter_capacity_source
QA_CAPACITY_CONFIGURATION = 0
QA_CAPACITY_SOURCE_ROWS = 0
QA_CAPACITY_ROWS = 0
CAPACITY_ACTIVATION = NOT_AUTHORIZED
PHASE_B_WIRING = NOT_AUTHORIZED
PHASE_C = BLOCKED
```

Stage 1 implements the workcenter/day source + WORKCENTER allocation writer. Canonical `s64 → s65` is verified; QA now has the s65 schema with empty Capacity source tables. Capacity remains NOT_CONFIGURED — schema ≠ activation.

---

## 0. Repo evidence (decisive)

| Fact | Evidence |
| ---- | -------- |
| Demand table exists | `execution_task_capacity_allocations` (s64) — `quantity` + `unit=minutes` |
| Supply / available pool **absent** | No Owner available-minutes table; R8 rejected all current candidates |
| Scopes in schema | `WORKCENTER` \| `MACHINE` only (no EMPLOYEE, no RESOURCE_POOL) |
| Workcenters relational table | **Absent** — identity = string `workcenter_code` |
| Calendar shift util | `capacity_shift_model.py` — dashboard/lab denominator; **not** Resource State SoT |
| Planning minutes | May be null; `PLANNING_MINUTES_SOURCE_REQUIRED`; TE2E-028A forbids inventing `0.0` |
| Writer readiness | `DOMAIN_WRITER_READY["CAPACITY_ALLOCATION"] = False` |
| Activation | `ACTIVATION_BLOCKED_MISSING_WRITER_AND_SOURCE` |
| QA (post-R11) | Scheduling+Reservation ACTIVE; Capacity config = 0; capacity rows = 0 |

Rejected as available-capacity source (R8, reconfirmed):

```text
execution_task_capacity_allocations   → demand only
workcenter_rates                      → commercial rates
HR / CostEngine productive hours      → out of Resource State triad
machines.capacity_metadata            → ad-hoc JSON, not minutes pool
company calendar shift util           → dashboard KPI denominator only
```

---

## 1. What Capacity is (five values — never conflated)

| Term | Meaning | Persist? |
| ---- | ------- | -------- |
| **capacity available** | How many minutes a resource can process in a planning bucket | **Yes — new Owner-configured supply** (Stage 1) |
| **capacity requested** | Minutes the task asks for (workload input to an allocate command) | Input / labeled; may copy into allocation |
| **capacity allocated** | Minutes reserved for a task in a bucket (`execution_task_capacity_allocations.quantity` while open) | **Yes — demand table (exists)** |
| **capacity consumed** | Minutes actually executed (Execution Reality sessions / actuals) | Reality domain — **not** Resource State allocation |
| **capacity remaining** | `available − sum(open allocated in bucket)` (computed) | Derived at check time |

```text
Capacity Allocation ≠ real worked time
Machine Reservation ≠ Capacity Allocation
Schedule window ≠ Capacity Allocation
```

Conceptual formulas:

```text
available_capacity  = Owner-configured minutes for (scope, bucket)
requested_capacity  = task workload minutes for this allocate intent
allocated_capacity  = sum(quantity) of open HELD|ALLOCATED rows overlapping bucket+scope
consumed_capacity   = Execution Reality actual minutes (out of triad)
remaining_capacity  = available_capacity − allocated_capacity
```

---

## 2. Answers to the fifteen Owner questions

| # | Question | Decision |
| - | -------- | -------- |
| 1 | What is capacity in WorkOS? | Planned **minutes claim** against a resource scope in a time bucket — separate from schedule windows, machine claims, and actual work sessions. |
| 2 | Source of available capacity? | **WORKCENTER_CONFIGURED_CAPACITY** (Owner-configured supply). Stage 2 may refine from machines/maintenance. |
| 3 | Which resources may have capacity? | Stage 1 available pool: **WORKCENTER**. Allocation row scopes remain schema `WORKCENTER` \| `MACHINE`; MACHINE available pool = Stage 2. EMPLOYEE stays outside triad. |
| 4 | Unit? | **`minutes`** (schema-frozen `CAPACITY_UNIT`). |
| 5 | Relation to tasks? | One or more allocations keyed by `(execution_plan_id, task_key)` + scope + bucket; task identity = operational `task_id`. |
| 6 | How is consumption calculated? | **Allocated** = sum open allocation quantities. **Consumed** = Reality actuals (informational / profitability; not Stage-1 guard input). |
| 7 | Overlap? | Bucket overlap for the **same scope**: open allocations contribute to allocated minutes in overlapping windows. Machine Reservation handles exclusive machine time separately. |
| 8 | Over-allocation? | Configurable per workcenter; **default WARN_ONLY** in Stage 1. Hard reject only when policy = HARD_BLOCK. |
| 9 | Estimated vs real? | Allocated/requested = planning. Consumed = Reality. Never silently promote AI/preview into execution truth. |
| 10 | Owner-configured data? | Available minutes per workcenter per day (and over-allocation policy). Later: exceptions, maintenance deductions. |
| 11 | From ExecutionPlan? | `workcenter`, `estimated_time_minutes`, `planning_minutes_source` — workload candidates; null preserved. |
| 12 | From Execution Reality? | Actual/session minutes = **consumed** only; not available pool; not Stage-1 over-allocation ceiling. |
| 13 | What must block Phase B? | Any **open** capacity allocation (`HELD`/`ALLOCATED`) on the task (until controlled transfer exists). Also existing fail-closed: NOT_CONFIGURED / UNKNOWN / ACTIVE domain states. |
| 14 | What remains warning? | Soft over-allocation under WARN_ONLY; missing planning minutes (no invent); AI preview estimates. |
| 15 | Writer + evaluator needed? | Capacity **supply** config path + allocation writer (R8 commands) + R6 reader already present; activate only after Stage-1 prerequisites. |

---

## 3. Resource scopes

```text
RESOURCE_SCOPE = WORKCENTER_PRIMARY | MACHINE_DEFERRED_STAGE_2
```

| Scope | Stage 1 available pool | Stage 1 allocation rows | Notes |
| ----- | ---------------------- | ----------------------- | ----- |
| WORKCENTER | **Yes** — Owner-configured | **Yes** — primary | Matches R2/R3; string `workcenter_code` |
| MACHINE | No (deferred) | Schema allows; Stage 2 for ceiling checks | Exclusive time stays on Machine Reservation |
| EMPLOYEE | **Out of triad** | Forbidden | Availability / skills / sessions stay separate |
| RESOURCE_POOL | **Do not invent** | N/A | No real model in repo |

**Rule preserved:** employee availability is outside the Resource State triad (R1).

---

## 4. Capacity source decision

```text
CAPACITY_SOURCE = WORKCENTER_CONFIGURED_CAPACITY
IMPLEMENTATION_STRATEGY = OPTION_D_STAGED
```

### Option comparison (repo-confirmed)

| Option | Fit | Verdict |
| ------ | --- | ------- |
| A — WC configured minutes/day | Matches missing supply; simple; admin-owned | **Stage 1 core** |
| B — Machine-derived | Needs program/availability/maintenance truth | **Stage 2** |
| C — Remain blocked forever | Correct until source exists; not a product end-state | Rejected as strategy |
| D — Hybrid staged | A now; B later | **SELECTED** |

### Stage 1 supply (to be implemented in next GO — not this task)

Minimum conceptual configuration grain:

```text
workcenter_code
bucket_kind = DAY
bucket_start / bucket_end   # calendar day bounds in timezone
timezone
available_minutes           # Owner-configured
over_allocation_policy      # HARD_BLOCK | WARN_ONLY | ALLOW_WITH_REASON
source_label = OWNER_CONFIGURED
version + history (CAS/idempotency pattern like R7)
```

Do **not** reuse `workcenter_rates`, HR hours, or dashboard shift util as this supply.

### Stage 2 refinements (future)

```text
machine-derived contributions / caps
shift models if Owner makes shifts canonical
maintenance windows deducted from available
historical calibration
```

---

## 5. Planning bucket

```text
PLANNING_BUCKET = DAY
```

| Candidate | Decision |
| --------- | -------- |
| DAY | **Selected** for Stage 1 |
| SHIFT | Not canonical Resource State SoT today (company calendar is dashboard-only) — **do not invent** |
| CUSTOM_TIME_WINDOW | Allocation rows already store arbitrary `bucket_start`/`bucket_end`; Stage 1 available pool still keyed by DAY |

Computed/check fields:

```text
bucket_start
bucket_end
timezone
available_minutes
allocated_minutes   # sum open overlapping allocations
remaining_minutes   # available − allocated
```

---

## 6. Task workload source

```text
TASK_WORKLOAD_SOURCE = LABELED_MINUTES_WITH_NULL_PRESERVED
```

| Source class | Use |
| ------------ | --- |
| `OWNER_CONFIGURED` | Owner/manager explicit minutes on allocate / WC config |
| `SYSTEM_DERIVED` | From ProductAggregate / EP `estimated_time_minutes` when `planning_minutes_source` is authorized |
| `AI_DECISION` | Preview/planning assistance only — must record explanation; replaceable |
| `MANUAL_MANAGER` | Manager override on allocate command |
| `UNKNOWN` | Must not silently become zero or execution truth |

Rules:

1. Null planning minutes → **preserve null**; never invent `0`.  
2. Capacity allocation `quantity` is always explicit on the write command.  
3. If EP minutes are used as default request, persist `workload_source` + provenance on the transition/command.  
4. Missing canonical workload does **not** by itself activate Capacity; Stage 1 may allocate only when quantity is explicitly provided with a label.

---

## 7. AI estimate policy

```text
AI_ESTIMATE_POLICY = PREVIEW_PLANNING_ONLY_NEVER_SILENT_EXECUTION_TRUTH
```

| Allowed | Forbidden |
| ------- | --------- |
| AI estimated workload in preview / planning UI | Silent write into Product Truth / EP minutes as confirmed |
| Labeled `AI_DECISION` on a manager-accepted allocate (audit trail) | Using AI estimate as available-capacity ceiling |
| Replaceable later without rewriting history (supersede) | Treating AI as CostEngine / commercial authority |

Capacity Stage 1 may **start** with labeled non-AI workload (Owner/system/manual). AI may assist requested minutes for planning, but must not silently become execution truth.

---

## 8. Over-allocation policy

```text
OVER_ALLOCATION_POLICY = CONFIGURABLE_PER_WORKCENTER_DEFAULT_WARN_ONLY
```

| Situation | Meaning |
| --------- | ------- |
| Within capacity | `allocated + requested ≤ available` |
| Soft over-allocation | Exceeds available under WARN_ONLY → write allowed + warning / reason detail |
| Hard over-allocation | Exceeds available under HARD_BLOCK → `409 over_allocation` |
| Unknown capacity | No supply config for scope/bucket → treat as **unknown ceiling** — Stage 1 writer must not invent a pool; prefer reject `capacity_source_missing` or allow only if policy explicitly ALLOW_WITH_REASON **and** reason recorded |

Policy enum (per workcenter):

```text
HARD_BLOCK
WARN_ONLY          # Stage 1 default
ALLOW_WITH_REASON  # requires reason_code
```

Phase B / aggregate remain fail-closed on `NOT_CONFIGURED` / `UNKNOWN` / open `ACTIVE` allocations — warnings do not make aggregate CLEAR.

---

## 9. Allocation versus reservation

| Domain | Claim |
| ------ | ----- |
| Machine Reservation | Temporal claim on a **concrete machine** |
| Capacity Allocation | Planned **minutes** inside a capacity bucket for a scope |
| Scheduling | Temporal intent window on a **task** |

A task may hold reservation **and** capacity allocation as **separate rows**. Do not dual-write the same truth into both tables.

---

## 10. Writer contract (finalized — not implemented)

Extends R8 §5. Permission to register later: `execution.capacity_allocation.manage`.

### Commands

| Command | From → To | Notes |
| ------- | --------- | ----- |
| `CREATE_ALLOCATION` | → HELD or ALLOCATED | `expected_version=0`; quantity>0; unit=minutes; scope XOR; bucket valid |
| `ADJUST_ALLOCATION` | HELD/ALLOCATED → same | CAS; may change quantity/bucket; capacity check per policy |
| `RELEASE_ALLOCATION` | HELD/ALLOCATED → RELEASED | reason required |
| `CANCEL_ALLOCATION` | HELD/ALLOCATED → CANCELLED | reason required |
| `SUPERSEDE_ALLOCATION` | open → SUPERSEDED + new row | atomic same txn |

### Shared platform (same as schedule/reservation)

```text
domain ACTIVE
plan lock + task_key in operational_tasks
CAS expected_version
idempotency_key + fingerprint
append-only transition in same SQLite transaction
no hard delete
```

### Capacity check (Stage 1)

```text
ON CREATE / ADJUST / SUPERSEDE (new quantity):
  resolve WORKCENTER available_minutes for DAY bucket covering allocation
  compute allocated_minutes of open overlapping rows (exclude self on adjust)
  apply over_allocation_policy
```

MACHINE-scope ceiling checks wait for Stage 2 supply (or reject MACHINE create until then with explicit code).

---

## 11. Evaluator semantics (finalized)

R6 states unchanged: `NOT_CONFIGURED` | `UNKNOWN` | `ACTIVE` | `CLEAR`.

| State | Meaning for Capacity |
| ----- | -------------------- |
| `NOT_CONFIGURED` | Domain configuration not ACTIVE |
| `UNKNOWN` | Query failure / inconsistent status |
| `ACTIVE` | ≥1 open allocation in `HELD` \| `ALLOCATED` for the task |
| `CLEAR` | Domain ACTIVE and no open blocking allocations |

```text
ACTIVE = open capacity allocation exists
over-allocation / conflict = reason_code + details (not a fifth aggregate state)
```

Blocking statuses remain schema-aligned: `HELD`, `ALLOCATED`.  
Non-blocking: `RELEASED`, `CANCELLED`, `SUPERSEDED`.

---

## 12. Phase B capacity policy (finalized — not wired)

```text
PHASE_B_CAPACITY_POLICY =
  any open task capacity allocation (HELD|ALLOCATED)
  → blocks pre-start reassignment
  until controlled allocation transfer exists
```

Also retain existing fail-closed:

```text
NOT_CONFIGURED | UNKNOWN | ACTIVE (domain/task) → block
CLEAR → may continue (subject to schedule/reservation CLEAR)
```

Do **not** require capacity allocation tied to employee in Stage 1 (employee out of triad). Workcenter/machine commitment is expressed by the allocation row scope.

**This GO does not wire Phase B.**

---

## 13. Activation prerequisites

```text
CAPACITY_ACTIVATION_READINESS = BLOCKED
```

until **all** of:

```text
capacity source (WORKCENTER_CONFIGURED_CAPACITY) implemented
planning bucket DAY model + timezone rules
available capacity configuration path (CAS/history)
task workload labeling rules enforced on writer
capacity allocation writer (R8 commands)
R6 reader (exists)
allocation transition history (schema exists)
execution.capacity_allocation.manage registered
CAS/idempotency proofs
over-allocation policy implemented
isolated + temporary-DB tests
separate Owner GO for QA activation
```

---

## 14. Scale review (many products)

Model is already generic — no per-product logic:

```text
execution_plan_id + task_key + resource_scope + time bucket + minutes
```

| Concern | Stage-1 note |
| ------- | ------------ |
| Indexes | plan+task, status, WC bucket, machine bucket (s64) — adequate for bucket sums |
| Aggregate queries | Sum open quantities by `workcenter_code` + overlapping `[bucket_start, bucket_end)` |
| Contention | Plan lock + CAS (same platform as R9) |
| Batch evaluation | R6 per-task; future plan-batch read may page by task_key |
| Pagination | List APIs (future) must page; do not load all plans into writer path |

50 products / thousands of tasks are supported **if** writers stay plan-scoped and bucket queries use WC/machine indexes. No product-specific capacity code.

---

## 15. Recommended implementation stages

```text
OPTION_D_STAGED
```

### Stage 1 — next candidate GO

```text
CAPACITY_STAGE_1_WORKCENTER_SOURCE_AND_WRITER_IMPLEMENTATION
```

1. Persist Owner workcenter available minutes (DAY).  
2. Implement capacity allocation writer + over-allocation policy (default WARN_ONLY).  
3. Register manage permission.  
4. Isolated tests (schema write + ceiling policy).  
5. **No** QA activation without separate Owner GO.

### Stage 2 — later

```text
machine-derived refinements
shifts (only if Owner canonizes)
maintenance deductions
historical calibration
MACHINE available pool
HARD_BLOCK defaults where truth is mature
```

---

## 16. QA boundary (this GO)

```text
QA_SCHEMA_MUTATIONS = 0
QA_DATA_MUTATIONS = 0
QA_CAPACITY_CONFIGURATIONS = 0
QA_CAPACITY_ALLOCATIONS = 0
Scheduling config = ACTIVE
Reservation config = ACTIVE
schedule/reservation/capacity rows = 0
assignment transitions = 7
```

No Capacity configuration endpoint calls. No schedule/reservation writers on QA.

---

## 17. Impact

### `/modules`

```text
Capacity source and ownership decision
no Capacity runtime active
Scheduling + Reservation remain ACTIVE (empty operational rows)
```

### `/governance`

```text
Owner configures workcenter available minutes + over-allocation policy
source labels mandatory on workload provenance
AI decision policy = preview/planning only
Capacity activation remains Owner-gated
Phase B wiring still NOT_AUTHORIZED
```

---

## 18. Next Owner gate

```text
CAPACITY_STAGE_1 = PASS (writer + source in code; QA inactive)
FUTURE CANDIDATE:
CAPACITY_STAGE_1_CANONICAL_MIGRATION_AND_QA_ROLLOUT_READINESS
```

QA Alembic upgrade / Capacity activation remain separate Owner GOs.
