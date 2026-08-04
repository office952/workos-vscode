# Resource State Program R1 — Owner Decisions and Domain Contract

**Task:** `RESOURCE_STATE_PROGRAM_R1 = OWNER_DECISIONS_AND_DOMAIN_CONTRACT`  
**Owner GO:** `AUTHORIZE_RESOURCE_STATE_PROGRAM_R1_OWNER_DECISIONS`  
**Date:** 2026-08-05  
**Status:** **PASS** · Decisions **RECORDED** · Implementation **NOT AUTHORIZED**  
**Prior:** readiness audit COMPLETE · `DEC-PHASE-C-RESOURCE-01 = KEEP_PHASE_C_BLOCKED`  
**Worklog:** `docs/worklog/realignment/2026-08-05_resource_state_program_r1_owner_decisions.md`

```text
RESOURCE_STATE_PROGRAM_R1 = PASS
OWNER_DECISIONS = RECORDED
ARCHITECTURE = DEDICATED_PERSISTED_RESOURCE_STATE_MODEL
DOMAIN_CONFIGURATION = EXPLICIT_PERSISTED_CONFIGURATION_REQUIRED
STATE_SEMANTICS = CLEAR_ACTIVE_UNKNOWN_NOT_CONFIGURED_DEFINED
DOMAIN_GRANULARITY = DEFINED
PERSISTENCE_AND_DERIVATION = DEFINED
CAS_AND_VERSIONING = DEFINED
AUDIT_AND_PROVENANCE = DEFINED
LOCK_AND_REVALIDATION = DEFINED
FAIL_CLOSED_POLICY = DEFINED
SCHEMA_CHANGE_REQUIRED = YES
CONCEPTUAL_SCHEMA = READY_FOR_R2_READINESS
INITIAL_CLEAR_BACKFILL = FORBIDDEN
RESOURCE_STATE_IMPLEMENTATION = NOT_AUTHORIZED
MIGRATION = NOT_AUTHORIZED
R2 = NOT_AUTHORIZED
PHASE_C = BLOCKED
QA_MUTATIONS = 0
```

This document is the **canonical Owner decision register** for Resource State R1.  
Readiness audit remains historical evidence: `RESOURCE_STATE_CONTRACT_AND_SCHEDULING_BOUNDARY_READINESS.md`.

---

## 0. Decision register (summary)

| ID | Decision |
| -- | -------- |
| DEC-RESOURCE-STATE-01 | Dedicated persisted Resource State model = **CANONICAL_CURRENT_STATE_MODEL** with future Scheduling Domain as write-owner of schedule/reservation/allocation **source records** |
| DEC-RESOURCE-STATE-02 | Explicit persisted domain configuration required per domain |
| DEC-RESOURCE-STATE-03 | Four-state fail-closed semantics: CLEAR / ACTIVE / UNKNOWN / NOT_CONFIGURED |
| DEC-RESOURCE-STATE-04 | Domain-specific granularity (not plan/task boolean SoT) |
| DEC-RESOURCE-STATE-05 | Persist domain records; derive guard state |
| DEC-RESOURCE-STATE-06 | Versioned CAS + idempotent transitions |
| DEC-RESOURCE-STATE-07 | In-transaction Resource State revalidation (same SQLite DB) |
| DEC-RESOURCE-STATE-08 | Employee availability = separate future domain (not initial triad) |
| DEC-RESOURCE-STATE-09 | Machine assignment ≠ machine reservation |
| DEC-RESOURCE-STATE-10 | Capacity = explicit persisted allocations first; unit = minutes |
| DEC-RESOURCE-STATE-11 | Configuration scope = application-global (single-org) until multi-site exists |
| DEC-RESOURCE-STATE-12 | Internal service first; no public/admin/FE endpoint in first implementation GO |
| DEC-RESOURCE-STATE-13 | Aggregate derived only; precedence ACTIVE > UNKNOWN > NOT_CONFIGURED > CLEAR |
| DEC-RESOURCE-STATE-14 | Fail-closed; no placeholder/env fallback outside tests |
| DEC-RESOURCE-STATE-15 | Placeholders / ORR “Pregătit” = non-canonical |
| DEC-RESOURCE-STATE-16 | Phase B future integration contract |
| DEC-RESOURCE-STATE-17 | Phase C reconsideration criteria (blocked until all met) |
| DEC-RESOURCE-STATE-18 | Conceptual schema package + Alembic ownership |
| DEC-RESOURCE-STATE-19 | Initial backfill = NONE; synthetic CLEAR forbidden |
| DEC-RESOURCE-STATE-20 | Conceptual permission families (not registered yet) |
| DEC-RESOURCE-STATE-21 | UI honesty boundary (no UI change in R1) |
| DEC-RESOURCE-STATE-22 | SQLite freeze + future PostgreSQL parity notes |
| DEC-RESOURCE-STATE-23 | Current rows + append-only history from first write-capable GO |
| DEC-RESOURCE-STATE-24 | Race prevention under SQLite single-writer |

Unresolved decisions requiring a later Owner GO (non-blocking for R1 PASS): none material for semantics. Capacity unit subtypes beyond minutes deferred to a future GO if needed.

---

## 1. Domain separation (non-negotiable)

```text
SCHEDULING
MACHINE_RESERVATION
CAPACITY_ALLOCATION
EMPLOYEE_AVAILABILITY          # out of initial triad
EMPLOYEE_ASSIGNMENT            # existing CANONICAL_ACTIVE
MACHINE_ASSIGNMENT             # distinct; write NOT_IMPLEMENTED today
EXECUTION_SESSION
EXECUTION_REALITY
```

```text
employee assignment ≠ scheduling ≠ availability
machine requirement ≠ machine assignment ≠ machine reservation
task readiness / ORR capability ≠ scheduling CLEAR
no session ≠ resource CLEAR
```

---

## 2. DEC-RESOURCE-STATE-01 — Program architecture

```text
DEC-RESOURCE-STATE-01 =
DEDICATED_PERSISTED_RESOURCE_STATE_MODEL
=
CANONICAL_CURRENT_STATE_MODEL
WITH_FUTURE_SCHEDULING_DOMAIN_AS_WRITE_OWNER
```

Meaning:

1. Resource State is **not** owned solely by `ExecutionPlan.tasks_json`.  
2. Resource State is **not** derived from HOLD / not_reserved / NOT_STARTED.  
3. Resource State is **not** a QA-only fixture.  
4. Dedicated persisted **domain records** (schedule / reservation / allocation) are the evidence.  
5. Guard evaluation is a **derived read** over those records + configuration.  
6. Precedes, but stays compatible with, a full Scheduling Domain / optimizer.  
7. Must not become a hidden optimizer.  
8. Must support fail-closed reads for Phase B.

**Avoiding two sources of truth:**

- **Write ownership of source facts** belongs to the Scheduling / Reservation / Capacity write flows (future domain GO).  
- **Guard state** is never independently writable; it is computed from source records + configuration.  
- No parallel “resource_clear=true” flag on tasks or plans as SoT.  
- Optional denormalized cache on plan/task may exist later only as **derived**, versioned projection with invalidation rules — never authoritative.

---

## 3. DEC-RESOURCE-STATE-02 — Domain configuration

```text
DEC-RESOURCE-STATE-02 =
EXPLICIT_PERSISTED_DOMAIN_CONFIGURATION_REQUIRED
```

Conceptual: `resource_domain_configurations` — one active configuration row per `(domain, scope)`.

| Domain | Configured when |
| ------ | --------------- |
| Scheduling | Persistent row `domain=SCHEDULING`, `status=ACTIVE`, version ≥ 1 |
| Machine reservation | Same for `MACHINE_RESERVATION` |
| Capacity allocation | Same for `CAPACITY_ALLOCATION` |

Properties: persistent, auditable, not environment-only, not inferred from missing rows, not hardcoded to order/task, queryable inside transaction.

Rules:

```text
no configuration record          → NOT_CONFIGURED
configuration disabled           → NOT_CONFIGURED
configuration ACTIVE + query fail → UNKNOWN
configuration ACTIVE + successful eval + no active conflicts → CLEAR (domain-specific)
```

Scope for initial product (repo is effectively single-org; no plant/site tenant on execution plans):

```text
DEC-RESOURCE-STATE-11 =
APPLICATION_GLOBAL_CONFIGURATION_SCOPE
```

`execution_plan_id` + `task_key` remain **evaluation scope**, not configuration scope. Future site/plant narrowing requires a separate Owner GO when those identities exist.

---

## 4. DEC-RESOURCE-STATE-03 — Enum semantics

```text
DEC-RESOURCE-STATE-03 = FOUR_STATE_FAIL_CLOSED_SEMANTICS
```

| State | Meaning | Guard |
| ----- | ------- | ----- |
| `NOT_CONFIGURED` | No active persisted configuration for domain/scope | **blocks** |
| `UNKNOWN` | Configured but evaluation unsafe (query fail, inconsistent, stale version, missing provenance, lock/txn failure) | **blocks** |
| `ACTIVE` | ≥1 canonical active conflicting record for evaluation grain | **blocks** |
| `CLEAR` | Configured; evaluation succeeded; no active conflict; provenance + versions present | may continue |

```text
NOT_CONFIGURED ≠ UNKNOWN ≠ ACTIVE ≠ CLEAR
no rows ≠ CLEAR unless domain CONFIGURED and empty-set semantics apply
```

---

## 5. DEC-RESOURCE-STATE-04 / domain ACTIVE semantics

```text
DEC-RESOURCE-STATE-04 = DOMAIN_SPECIFIC_GRANULARITY
```

Rejected as sole SoT: plan-level `resource_clear`, task-level `all_resources_clear`, status string in `tasks_json`.

### Scheduling grain

```text
operational_task + scheduled_time_window
identity: execution_plan_id, task_key, scheduled_start, scheduled_end
(+ optional workcenter_code)
```

**ACTIVE (blocks)** conceptual statuses: `PLANNED`, `CONFIRMED`, `DISPATCHED`, `IN_PROGRESS`, `LOCKED`  
**Non-blocking:** `DRAFT`, `CANCELLED`, `SUPERSEDED`, `EXPIRED`  
(Names are conceptual until write-flow GO freezes vocabulary.)

### Machine reservation grain

```text
machine + operational_task + reservation_time_window
identity: execution_plan_id, task_key, machine_id, reservation_start, reservation_end
```

**ACTIVE:** `HELD`, `RESERVED`, `CONFIRMED`, `IN_USE`  
**Non-blocking:** `RELEASED`, `CANCELLED`, `EXPIRED`, `SUPERSEDED`

### Capacity allocation grain

```text
workcenter/resource_pool + operational_task + capacity_bucket
identity: execution_plan_id, task_key, resource_scope, bucket_start, bucket_end, quantity, unit
```

**ACTIVE:** `HELD`, `ALLOCATED`, `COMMITTED`, `CONSUMING` (any positive quantity in these statuses for the task scope blocks)  
**Non-blocking:** `RELEASED`, `CANCELLED`, `EXPIRED`, `SUPERSEDED`, quantity=0 terminal rows

---

## 6. DEC-RESOURCE-STATE-05 — Persistence vs derivation

```text
DEC-RESOURCE-STATE-05 = PERSIST_DOMAIN_RECORDS_DERIVE_GUARD_STATE
```

| Layer | Policy |
| ----- | ------ |
| Schedule / reservation / allocation | **Persisted** source records |
| Guard component states | **Derived** |
| Aggregate | **Derived only** — never independently writable |

---

## 7. DEC-RESOURCE-STATE-23 — Current state + history

```text
DEC-RESOURCE-STATE-23 =
CURRENT_CANONICAL_RECORDS_PLUS_APPEND_ONLY_HISTORY
FROM_FIRST_WRITE_CAPABLE_IMPLEMENTATION
```

- Current rows for fast guard evaluation.  
- Append-only transition/event history from first write-capable GO (safety-affecting).  
- R2 schema readiness must include history design; expand-only current tables may land first only if history ships in the **same** write-capable GO before any production write.

---

## 8. DEC-RESOURCE-STATE-06 — Versioning / CAS / idempotency

```text
DEC-RESOURCE-STATE-06 = VERSIONED_CAS_AND_IDEMPOTENT_TRANSITIONS
```

| Entity | Mechanism |
| ------ | --------- |
| Domain configuration | `version` integer; expected-version on update |
| Domain records | `version` + `updated_at` + `updated_by` |
| Events | `event_id` UUID + `idempotency_key` UNIQUE |

Stale writers → conflict; no silent overwrite.

---

## 9. Audit and provenance

Evaluation report (conceptual): domain, configuration id/version, source table/model, source record IDs, evaluation scope, `evaluated_at`, result, reason code, optional request correlation id.

Write audit: actor, operation, previous/new state, reason code, timestamp, idempotency key.

**Forbidden in payloads/logs:** salary, employee rate, pricing, CNP, address, phone, private email, JWT, Authorization header, complete `tasks_json`.

Notes: optional on write commands; max length + safe charset (same spirit as Phase B reason_note); redact from public logs.

---

## 10. DEC-RESOURCE-STATE-07 / 24 — Lock, transaction, races

```text
DEC-RESOURCE-STATE-07 = IN_TRANSACTION_RESOURCE_STATE_REVALIDATION
DEC-RESOURCE-STATE-24 = SQLITE_SINGLE_WRITER_RACE_BOUNDARY
```

Conceptual flow:

```text
begin transaction
→ lock/re-read execution plan
→ resolve task
→ read active domain configurations
→ query scheduling / reservation / capacity states
→ verify each = CLEAR
→ continue reassignment/unassignment dual-write
→ commit
```

```text
SAME_DATABASE = REQUIRED (SQLite freeze)
SAME_TRANSACTION = REQUIRED where possible
SQLITE_SINGLE_WRITER_BOUNDARY = ACKNOWLEDGED
MULTI_NODE_ATOMICITY = NOT_PROVEN
```

Race mitigation (minimum under freeze): plan lock + in-txn re-read of config versions + domain record versions; configuration change during command → UNKNOWN or explicit conflict. Future PostgreSQL: row locks / serializable as separate design GO.

---

## 11. DEC-RESOURCE-STATE-08 — Availability

```text
DEC-RESOURCE-STATE-08 =
EMPLOYEE_AVAILABILITY_SEPARATE_FUTURE_DOMAIN
NOT_PART_OF_INITIAL_RESOURCE_GUARD_TRIAD
```

DEC-015 remains eligibility authority. Availability is time-dependent and out of Phase B’s current Owner triad (scheduling / reservation / capacity).

---

## 12. DEC-RESOURCE-STATE-09 — Machine assignment vs reservation

```text
DEC-RESOURCE-STATE-09 =
MACHINE_ASSIGNMENT_DISTINCT_FROM_RESERVATION
```

- **Assignment** = selected/associated machine identity (`machine_code` on ops task — write not implemented).  
- **Reservation** = time-bound controlled claim.  

Assignment alone must **not** imply reservation ACTIVE or CLEAR. Future reservations may reference `machine_id` (+ optional assignment linkage) without collapsing concepts.

---

## 13. DEC-RESOURCE-STATE-10 — Capacity

```text
DEC-RESOURCE-STATE-10 =
EXPLICIT_PERSISTED_CAPACITY_ALLOCATIONS_FIRST
UNIT_MINUTES
```

Repo evidence: operational tasks / capacity util speak in **estimated minutes**. Initial unit = `minutes` (machine-time or labor-time expressed as minutes; subtype field optional later).

Future derivation from schedules allowed after Scheduling Domain write-owner exists. HR productive hours / dashboard util remain **out of** this guard triad.

---

## 14. DEC-RESOURCE-STATE-12 / 13 — API and aggregate

```text
DEC-RESOURCE-STATE-12 =
INTERNAL_SERVICE_FIRST
PUBLIC_ADMIN_ENDPOINT_NOW = NO
FRONTEND_ENDPOINT_NOW = NO
```

Conceptual: `get_task_resource_state(execution_plan_id, task_key, evaluated_at=None)` returning per-domain state + provenance + derived aggregate.

```text
DEC-RESOURCE-STATE-13 = DERIVED_AGGREGATE_ONLY
```

| Aggregate | When |
| --------- | ---- |
| CLEAR | all three CLEAR |
| BLOCKED_ACTIVE | any ACTIVE |
| BLOCKED_UNKNOWN | any UNKNOWN (if no ACTIVE) |
| BLOCKED_NOT_CONFIGURED | any NOT_CONFIGURED (if no ACTIVE/UNKNOWN) |

Reporting precedence: `ACTIVE` > `UNKNOWN` > `NOT_CONFIGURED` > `CLEAR`. Preserve component states always.

---

## 15. DEC-RESOURCE-STATE-14 — Failure policy

```text
query failure → UNKNOWN
configuration read failure → UNKNOWN
invalid source record → UNKNOWN
version mismatch → UNKNOWN or explicit conflict
domain / config absent or disabled → NOT_CONFIGURED
active conflict → ACTIVE
configured + success + no conflicts → CLEAR
```

Any non-CLEAR component blocks Phase B reassignment/unassignment.  
No fallback to placeholders.  
No env CLEAR outside `APP_ENV=test` automated isolated tests (`WORKOS_PHASE_B_RESOURCE_GUARDS` remains TEST_ONLY until removed after integration).

---

## 16. DEC-RESOURCE-STATE-15 — Placeholders

```text
DEC-RESOURCE-STATE-15 =
PLACEHOLDERS_AND_CAPABILITY_STATUS_ONLY
NOT_RESOURCE_STATE_SOURCE_OF_TRUTH
```

| Token | Class |
| ----- | ----- |
| scheduling HOLD | PLACEHOLDER inventory |
| not_reserved | PLACEHOLDER |
| NOT_STARTED | PLACEHOLDER |
| ORR “Pregătit” | capability readiness — not resource CLEAR |

Future UI must rename/qualify these (separate UI GO).

---

## 17. DEC-RESOURCE-STATE-16 — Phase B integration (future)

```text
DEC-RESOURCE-STATE-16 = PHASE_B_USES_CANONICAL_RESOURCE_STATE_SERVICE
```

- Before domains configured → NOT_CONFIGURED → commands blocked (same as today).  
- Partial configuration → non-configured domains block.  
- After all three ACTIVE configs + service → canonical evaluation; no placeholder fallback.  
- TEST_ONLY env override retained **only** for automated isolated tests until a dedicated test double exists.  
- **No Phase B code change in R1.**

---

## 18. DEC-RESOURCE-STATE-17 — Phase C reconsideration

```text
PHASE_C = BLOCKED
UNTIL_ALL_RECONSIDERATION_CRITERIA_ARE_MET
```

1. R1 Owner decisions recorded  
2. Separate schema Owner GO  
3. Migration implemented and verified  
4. Canonical configuration exists  
5. Domain records evaluable  
6. Internal Resource State service implemented  
7. Phase B integration verified  
8. Isolated runtime proof  
9. Concurrency/rollback proof  
10. QA read-only resource-state proof  
11. All three domains factual CLEAR for selected QA task  
12. Separate Owner GO for one controlled QA transition  

---

## 19. DEC-RESOURCE-STATE-18 — Conceptual schema package

**Not implemented. No migration file.**

Alembic owns all new tables; runtime `create_all` must skip them (`ALEMBIC_OWNED_TABLES`).

### A. `resource_domain_configurations`

| Aspect | Spec |
| ------ | ---- |
| Purpose | Prove domain CONFIGURED |
| Owner | admin configure permission (future) |
| PK | `id` INTEGER/UUID |
| Unique | `(domain, scope_key)` where scope_key = `application` initially |
| Fields | domain, scope_key, status, version, configured_at/by, disabled_at, created_at, updated_at |
| Checks | domain ∈ {SCHEDULING, MACHINE_RESERVATION, CAPACITY_ALLOCATION}; status ∈ {ACTIVE, DISABLED} |
| Indexes | (domain, scope_key), (status) |

### B. `execution_task_schedules`

| Aspect | Spec |
| ------ | ---- |
| Purpose | Persisted schedule windows |
| PK | id |
| Unique | active window uniqueness TBD in R2 (e.g. no overlapping ACTIVE for same task) |
| Fields | execution_plan_id, order_id, task_key, scheduled_start/end, status, workcenter_code nullable, version, actor fields, timestamps |
| Soft cancel | status → CANCELLED/SUPERSEDED; no hard delete of history |

### C. `execution_task_machine_reservations`

| Aspect | Spec |
| ------ | ---- |
| Purpose | Time-bound machine claims |
| Fields | execution_plan_id, order_id, task_key, machine_id, reservation_start/end, status, version, … |
| FK | machine_id → machines (logical; SQLite FK ON if enabled) |

### D. `execution_task_capacity_allocations`

| Aspect | Spec |
| ------ | ---- |
| Purpose | Explicit capacity holds |
| Fields | execution_plan_id, order_id, task_key, resource_scope, bucket_start/end, quantity, unit=`minutes`, status, version, … |

### E. History

**Decision:** separate typed append-only tables preferred over one polymorphic mega-table for SQLite clarity and FK safety:

```text
execution_task_schedule_events
execution_task_machine_reservation_events
execution_task_capacity_allocation_events
resource_domain_configuration_events
```

Each: event_id UUID UNIQUE, idempotency_key UNIQUE, parent record id, op, before/after JSON **redacted**, actor, reason_code, created_at.

SQLite: TEXT ISO timestamps or numeric epoch; UUID as TEXT(36); CHECK constraints; indexes on (execution_plan_id, task_key), (status), time ranges as needed.  
PostgreSQL later: same logical schema; native UUID/timestamptz optional.

---

## 20. DEC-RESOURCE-STATE-19 — Migration / backfill

```text
INITIAL_RESOURCE_STATE_BACKFILL = NONE
SYNTHETIC_CLEAR_BACKFILL = FORBIDDEN
```

Forbidden: backfill HOLD→schedule, not_reserved→CLEAR, NOT_STARTED→CLEAR, ORR ready→CLEAR.  
After migration: domains **absent/NOT_CONFIGURED** until explicit configure GO.  
Expand-only; no destructive cleanup; downgrade policy deferred to R2 readiness.

---

## 21. DEC-RESOURCE-STATE-20 — Permissions (conceptual)

Repo roles today: `admin`, `manager`, `sales`, `operator`, `viewer`, `employee_mobile`. **No `planner` role.**

| Permission (future) | Roles (proposed) |
| ------------------- | ---------------- |
| `execution.resource_state.read` | admin, manager |
| `execution.resource_domain.configure` | admin |
| `execution.schedule.manage` | admin, manager |
| `execution.machine_reservation.manage` | admin, manager |
| `execution.capacity_allocation.manage` | admin, manager |

Operator/viewer: no manage; read only if separately authorized later.  
**Not registered in PERMISSION_MATRIX in R1.**

---

## 22. DEC-RESOURCE-STATE-21 — UI honesty

Future UI GO must:

- qualify HOLD / not_reserved / NOT_STARTED as inventory/placeholders;  
- separate ORR “Pregătit” from operational resource clearance;  
- show provenance/evaluated_at where useful;  
- keep operator-first, day/light, compact warnings.  

No UI change in R1.

---

## 23. DEC-RESOURCE-STATE-22 — SQLite / PostgreSQL

```text
CURRENT_PRODUCT_FREEZE_DATABASE = SQLITE
POSTGRESQL = SUPPORTED_NOT_ACTIVE
```

Design for SQLite FK/index/CHECK/single-writer; avoid JSON as sole SoT for relational facts.  
Future PG: parity of constraints + stronger row locking — verify in a dedicated GO.

---

## 24. Roadmap gates

| Gate | Status |
| ---- | ------ |
| R1 Owner decisions | **COMPLETE** |
| R2 schema & migration readiness | **NOT_AUTHORIZED** |
| Schema implementation / migration file | **NOT_AUTHORIZED** |
| Resource State service / Phase B wire-up | **NOT_AUTHORIZED** |
| Phase C | **BLOCKED** |

Next candidate after Owner review:

```text
RESOURCE_STATE_PROGRAM_R2_SCHEMA_AND_MIGRATION_READINESS
```

---

## 25. Dead pieces (classify only)

| Piece | Class |
| ----- | ----- |
| HOLD / not_reserved / NOT_STARTED | PLACEHOLDER |
| ORR Pregătit | ACTIVE_LEGACY (capability) |
| Phase B fail-closed guard | ACTIVE_CANONICAL |
| `WORKOS_PHASE_B_RESOURCE_GUARDS` | TEST_ONLY |
| QA CLEAR fixture | BYPASS_RISK / REJECTED |

```text
Dead pieces removed: NONE
```
