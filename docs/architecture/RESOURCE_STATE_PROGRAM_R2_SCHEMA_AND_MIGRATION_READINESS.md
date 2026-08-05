# Resource State Program R2 — Schema and Migration Readiness

**Task:** `RESOURCE_STATE_PROGRAM_R2 = SCHEMA_AND_MIGRATION_READINESS_AUDIT`  
**Owner GO:** `AUTHORIZE_RESOURCE_STATE_PROGRAM_R2_SCHEMA_AND_MIGRATION_READINESS`  
**Date:** 2026-08-05  
**Status:** **PASS** · Schema implementation **NOT AUTHORIZED** · Migration file **NOT CREATED**  
**R1 canonical:** `RESOURCE_STATE_PROGRAM_R1_OWNER_DECISIONS.md`  
**Worklog:** `docs/worklog/realignment/2026-08-05_resource_state_program_r2_schema_and_migration_readiness.md`

```text
RESOURCE_STATE_PROGRAM_R2 = PASS
SCHEMA_AND_MIGRATION_READINESS = COMPLETE
TABLE_PACKAGE = FINALIZED
DOMAIN_CONFIGURATION_HISTORY = INCLUDED
SCHEDULE_TABLES = FINALIZED
MACHINE_RESERVATION_TABLES = FINALIZED
CAPACITY_ALLOCATION_TABLES = FINALIZED
PRIMARY_KEYS = DEFINED
FOREIGN_KEYS = DEFINED
TASK_KEY_INTEGRITY = APPLICATION_GUARDED
UNIQUE_CONSTRAINTS = DEFINED
CHECK_CONSTRAINTS = DEFINED
INDEXES = DEFINED
CAS_AND_VERSIONING = DEFINED
IDEMPOTENCY = DEFINED
APPEND_ONLY_HISTORY = DEFINED
DELETE_POLICY = DEFINED
ALEMBIC_OWNERSHIP = DEFINED
MIGRATION_ANCESTRY = DEFINED
EXPAND_ONLY_POLICY = DEFINED
INITIAL_BACKFILL = NONE
INITIAL_CLEAR_BACKFILL = FORBIDDEN
FRESH_SQLITE_UPGRADE_PLAN = READY
S63_TO_RESOURCE_STATE_UPGRADE_PLAN = READY
DOWNGRADE_REUPGRADE_PLAN = READY
RUNTIME_CREATE_ALL_EXCLUSION_PLAN = READY
SCHEMA_IMPLEMENTATION = NOT_AUTHORIZED
MIGRATION_CREATION = NOT_AUTHORIZED
QA_SCHEMA_ROLLOUT = NOT_AUTHORIZED
PHASE_B_WIRING = NOT_AUTHORIZED
PHASE_C = BLOCKED
QA_MUTATIONS = 0
```

This document is the **technical schema/migration readiness** for R3. It does **not** create ORM models or Alembic files.

---

## 1. R1 decision preservation

R2 does **not** reopen:

```text
DEDICATED_PERSISTED_RESOURCE_STATE_MODEL
EXPLICIT_PERSISTED_DOMAIN_CONFIGURATION_REQUIRED
FOUR_STATE_FAIL_CLOSED_SEMANTICS
DOMAIN_SPECIFIC_GRANULARITY
PERSIST_DOMAIN_RECORDS_DERIVE_GUARD_STATE
CURRENT_STATE_PLUS_APPEND_ONLY_HISTORY
VERSIONED_CAS_AND_IDEMPOTENT_TRANSITIONS
IN_TRANSACTION_RESOURCE_STATE_REVALIDATION
EMPLOYEE_AVAILABILITY_OUTSIDE_INITIAL_TRIAD
MACHINE_ASSIGNMENT_DISTINCT_FROM_MACHINE_RESERVATION
AGGREGATE_STATE_DERIVED_ONLY
INITIAL_CLEAR_BACKFILL_FORBIDDEN
ALEMBIC_OWNS_NEW_TABLES
```

No Owner reconsideration required — R1 maps cleanly onto repo conventions below.

---

## 2. Repo / migration conventions (factual)

| Convention | Repo truth |
| ---------- | ---------- |
| Plan table | `execution_plan` · PK `id` INTEGER |
| Assignment transitions | `execution_task_assignment_transitions` · Integer PK + `transition_id` String(36) UNIQUE |
| UUID storage | `String(36)` everywhere; no SQLAlchemy `Uuid` type |
| Actor IDs | `String(255)` denormalized; **no FK** to `users` (Alembic excludes `users`) |
| Enum storage | String + CHECK (s63 pattern) |
| Partial unique | Supported (s58 `sqlite_where` / `postgresql_where`) |
| Revision naming | `sNN_snake_description` · current head `s63_execution_task_assignment_transitions` |
| `ALEMBIC_OWNED_TABLES` | Currently **only** assignment transitions — R3 must expand set |
| SQLite FK pragma | Runtime `DatabaseManager` does **not** set `PRAGMA foreign_keys=ON` (QA pragma=0). Tests enable FKs explicitly. |
| Machines | `machines.id` INTEGER PK · `machine_code` UNIQUE |
| Workcenters | **No** relational `workcenters` table in local SQLite ORM; use **string codes** for capacity scope |
| Plan hard-delete | No product delete service; transitions FK `ondelete=RESTRICT` |

---

## 3. Final table package

```text
OPTION_A_ALL_REQUIRED_TABLES_EXPAND_ONLY = SELECTED
```

Eight tables in **one** future expand-only migration (history from day one per R1):

| # | Table |
| - | ----- |
| 1 | `resource_domain_configurations` |
| 2 | `resource_domain_configuration_transitions` |
| 3 | `execution_task_schedules` |
| 4 | `execution_task_schedule_transitions` |
| 5 | `execution_task_machine_reservations` |
| 6 | `execution_task_machine_reservation_transitions` |
| 7 | `execution_task_capacity_allocations` |
| 8 | `execution_task_capacity_allocation_transitions` |

Option B (defer history) **rejected** — contradicts R1 “history from first write-capable implementation.”

Conceptual future revision id (not created):

```text
s64_resource_state_persistence
down_revision = s63_execution_task_assignment_transitions
```

---

## 4. PK / UUID / FK strategy

| Pattern | Choice | Rationale |
| ------- | ------ | --------- |
| Current-row PK | INTEGER autoincrement | Matches `execution_plan`, transitions, `machines` |
| Business / event identity | `String(36)` UUID | Matches `transition_id` |
| Actor | `String(255)` nullable | Matches assignment transitions; no `users` FK |
| Plan FK | `execution_plan_id` → `execution_plan.id` `ON DELETE RESTRICT` | Safety history |
| Machine FK | `machine_id` → `machines.id` `ON DELETE RESTRICT` | Integer PK |
| Self-supersede | `superseded_by_id` → same table, nullable, CHECK ≠ self | Soft lineage |
| Workcenter | **No FK** — `resource_scope_id` TEXT code when type=WORKCENTER | No SQLite workcenters table |
| Task | `task_key` TEXT — **no relational FK** | Embedded in `tasks_json` |

```text
TASK_KEY_REFERENTIAL_INTEGRITY = APPLICATION_AND_TRANSACTION_GUARD_REQUIRED
```

Service must verify `task_key` exists in plan `operational_tasks[]` under plan lock before write/eval.

---

## 5. Domain configuration

### `resource_domain_configurations`

| Column | Type | Notes |
| ------ | ---- | ----- |
| id | INTEGER PK | |
| domain | TEXT NOT NULL | CHECK ∈ SCHEDULING, MACHINE_RESERVATION, CAPACITY_ALLOCATION |
| application_scope_key | TEXT NOT NULL | Default `'application'` (single-org) |
| status | TEXT NOT NULL | CHECK ∈ ACTIVE, DISABLED |
| version | INTEGER NOT NULL DEFAULT 1 | CHECK ≥ 1 · CAS |
| configured_at | DateTime(tz) NULL | Required when ACTIVE (CHECK) |
| configured_by | String(255) NULL | |
| disabled_at | DateTime(tz) NULL | Required when DISABLED |
| disabled_by | String(255) NULL | |
| created_at / updated_at | DateTime(tz) NOT NULL | |

**Unique:** `(domain, application_scope_key)`  
**Does not store** CLEAR/ACTIVE/UNKNOWN/NOT_CONFIGURED evaluation results.

### `resource_domain_configuration_transitions`

Append-only: `transition_id` String(36) UNIQUE, `idempotency_key` String(36) UNIQUE, `configuration_id` FK RESTRICT, domain, operation, previous/new status, previous/new version, reason_code, reason_note nullable, actor_user_id, correlation_id nullable, created_at.  
No UPDATE/DELETE via repository.

---

## 6. Scheduling tables

### `execution_task_schedules`

| Column | Type |
| ------ | ---- |
| id | INTEGER PK |
| execution_plan_id | INTEGER NOT NULL FK → execution_plan RESTRICT |
| order_id | INTEGER NOT NULL | denormalized for query (matches transition pattern) |
| task_key | TEXT NOT NULL | CHECK length > 0 |
| scheduled_start / scheduled_end | DateTime(tz) NOT NULL | CHECK end > start |
| timezone | TEXT NOT NULL | IANA id; store instants as UTC-aware |
| status | TEXT NOT NULL | first-schema set below |
| workcenter_code | TEXT NULL | optional; not employee ownership |
| version | INTEGER NOT NULL DEFAULT 1 | CAS |
| created_by / updated_by | String(255) NULL | |
| created_at / updated_at | DateTime(tz) NOT NULL | |
| cancelled_at / cancelled_by | nullable | consistent with CANCELLED |
| superseded_by_id | INTEGER NULL FK self RESTRICT | CHECK ≠ id |
| idempotency_key | String(36) NOT NULL UNIQUE | |

**First-schema statuses (minimum):**

```text
DRAFT, PLANNED, CONFIRMED, CANCELLED, SUPERSEDED
```

Defer `DISPATCHED` / `IN_PROGRESS` / `EXPIRED` until write-flow Owner GO (may add via expand CHECK migration).

**Blocking for guard ACTIVE (when configured):** `PLANNED`, `CONFIRMED`  
**Non-blocking:** `DRAFT`, `CANCELLED`, `SUPERSEDED`

**Partial unique (SQLite/PG where):** at most one non-terminal current schedule per `(execution_plan_id, task_key)` where `status IN ('DRAFT','PLANNED','CONFIRMED')` — pattern like s58.

**Overlap same task:** service validation under plan lock (SQLite cannot exclusion-constrain).  
**Future PG:** optional exclusion constraint GO.

Do **not** include `assigned_employee_id` as schedule ownership (R1).

### `execution_task_schedule_transitions`

Append-only: transition_id UNIQUE, idempotency_key UNIQUE, schedule_id FK RESTRICT, plan_id, task_key, operation, previous/new status, previous/new start/end, previous/new version, reason_code, reason_note, actor_user_id, correlation_id, created_at.  
Enough columns to reconstruct change without full JSON blob.

---

## 7. Machine reservation tables

### `execution_task_machine_reservations`

Same structural pattern as schedules + `machine_id` INTEGER NOT NULL FK → `machines.id` RESTRICT.

**First-schema statuses:**

```text
HELD, RESERVED, CANCELLED, RELEASED, SUPERSEDED
```

Defer `CONFIRMED` / `IN_USE` / `EXPIRED` until write-flow GO.

**Blocking:** `HELD`, `RESERVED`  
**Non-blocking:** `CANCELLED`, `RELEASED`, `SUPERSEDED`

**Partial unique:** at most one open reservation per `(execution_plan_id, task_key, machine_id)` for status IN (`HELD`,`RESERVED`).

**Overlap same machine:** service transactional check (SQLite).  

```text
OWNER_DECISION_REQUIRED_BEFORE_WRITE_SERVICE =
  whether a task may hold multiple machines concurrently
  whether inactive machines may be reserved
```

(Schema allows multiple rows; policy is service-layer.)

### `execution_task_machine_reservation_transitions`

Mirror schedule transitions + machine_id snapshot fields.

---

## 8. Capacity allocation tables

### `execution_task_capacity_allocations`

| Column | Type |
| ------ | ---- |
| resource_scope_type | TEXT CHECK ∈ WORKCENTER, MACHINE |
| resource_scope_id | TEXT NOT NULL | workcenter_code or machines.id as decimal string / prefer machine_id column when MACHINE |
| bucket_start / bucket_end | DateTime(tz) | CHECK end > start |
| quantity | INTEGER NOT NULL | CHECK > 0 · **minutes** |
| unit | TEXT NOT NULL | CHECK = `'minutes'` initially |
| status | TEXT | first set below |
| (+ plan, task_key, version, actors, supersede, idempotency) | |

**First-schema statuses:**

```text
HELD, ALLOCATED, RELEASED, CANCELLED, SUPERSEDED
```

Defer `COMMITTED` / `CONSUMING` until write-flow GO.

**Blocking:** `HELD`, `ALLOCATED`  
**Non-blocking:** `RELEASED`, `CANCELLED`, `SUPERSEDED`

**EMPLOYEE / RESOURCE_POOL scope types:** **not** in first schema (availability out of triad; no pool table).

For `MACHINE` scope: store `machine_id` INTEGER FK in addition to or instead of opaque scope_id — **R3 preferred:** `machine_id` nullable FK + `workcenter_code` nullable with CHECK exactly one scope populated.

### Transitions

Mirror other history tables + quantity/bucket before/after + unit.

---

## 9. Status / enum storage

```text
string + CHECK constraint
```

Stable UPPER_SNAKE values. Expand via new expand-only migration altering CHECK (batch mode). No native PG enum required for freeze.

---

## 10. Unique / check / index package (summary)

| Table | Unique | Key checks | Indexes |
| ----- | ------ | ---------- | ------- |
| resource_domain_configurations | (domain, application_scope_key) | domain/status/version; ACTIVE⇒configured_at; DISABLED⇒disabled_at | domain+scope, status |
| *_configuration_transitions | transition_id; idempotency_key | — | configuration_id, created_at |
| execution_task_schedules | idempotency_key; partial open per plan+task | end>start; status; version; supersede≠self | (plan, task), (status), (scheduled_start, scheduled_end) |
| schedule_transitions | transition_id; idempotency_key | — | schedule_id, (plan, task, created_at) |
| machine_reservations | idempotency_key; partial open per plan+task+machine | end>start; machine FK | (plan, task), (machine_id, reservation_start, reservation_end), status |
| reservation_transitions | transition_id; idempotency_key | — | reservation_id, (plan, task, created_at) |
| capacity_allocations | idempotency_key | quantity>0; unit; end>start; scope xor | (plan, task), (workcenter_code, bucket_*), (machine_id, bucket_*), status |
| capacity_transitions | transition_id; idempotency_key | — | allocation_id, (plan, task, created_at) |

Avoid indexes redundant with UNIQUE.

---

## 11. Temporal overlap policy

| Layer | Ownership |
| ----- | --------- |
| SQLite DB | Partial unique for “one open current” rows; CHECK end>start |
| Service + plan lock + CAS | Overlap detection queries; capacity conflict rules |
| Future PostgreSQL | Optional EXCLUDE USING gist — separate GO |

```text
SQLITE_OVERLAP_ENFORCEMENT = TRANSACTIONAL_SERVICE
POSTGRESQL_EXCLUSION = FUTURE_CANDIDATE
```

---

## 12. CAS / versioning / idempotency

```text
version INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1)
```

`updated_at` = audit only; **version** = CAS authority.  
UPDATE … WHERE id=? AND version=expected → version+1.

Transitions record `previous_version` / `new_version`.

Idempotency: globally unique `idempotency_key` String(36) per write table + transition table; service payload conflict detection (assignment-transition style). Store fingerprint fields only (no unredacted full request).

---

## 13. Append-only and deletion

```text
NO_DB_TRIGGER_IN_FIRST_SQLITE_IMPLEMENTATION
APPEND_ONLY_ENFORCED_BY_SERVICE_REPOSITORY_TESTS
```

History: insert-only repositories; no update/delete methods; tests forbid mutators.

Current rows: terminal status / supersession preferred; hard delete forbidden in services.

Plan delete: `ON DELETE RESTRICT` if resource rows exist.

```text
OWNER_DECISION_REQUIRED =
EXECUTION_PLAN_DELETION_WITH_RESOURCE_HISTORY
```

(when product ever adds plan delete UI — fixture deletes must respect FK when pragma ON.)

---

## 14. Domain evaluation (schema sufficiency)

Derived only — no persisted aggregate CLEAR flag.

```text
not configured → NOT_CONFIGURED
configured + query fail/inconsistency → UNKNOWN
configured + blocking status rows → ACTIVE
configured + success + no blocking rows → CLEAR
```

Evaluation returns: state, configuration id/version, source row ids, evaluated_at, reason_code.

---

## 15. Initial migration state

```text
INITIAL_RESOURCE_STATE_BACKFILL = NONE
INITIAL_CLEAR_BACKFILL = FORBIDDEN
INITIAL_CONFIGURATION_ROWS = NONE
```

Post-upgrade evaluation: all three domains NOT_CONFIGURED.  
Do not import HOLD / not_reserved / NOT_STARTED / ORR Pregătit / zero sessions as truth.

---

## 16. Alembic design

| Item | Spec |
| ---- | ---- |
| down_revision | `s63_execution_task_assignment_transitions` |
| Conceptual revision | `s64_resource_state_persistence` |
| Order | configs → config transitions → schedules → schedule transitions → reservations → reservation transitions → allocations → allocation transitions |
| Mode | expand-only create tables/indexes/constraints |
| Ownership | Add all 8 names to `ALEMBIC_OWNED_TABLES` |
| Forbidden | alter tasks_json; rewrite plans; seed CLEAR; activate configs; drop placeholders |

**Runtime create_all:** empty DB + startup without Alembic → Resource State tables **absent**; upgrade head → present.

---

## 17. Proof plans (future R3 — not executed here)

### Fresh SQLite

```text
empty DB → alembic upgrade head → inspect schema fingerprint
→ zero rows → zero ACTIVE configs → downgrade → re-upgrade
```

### s63 → s64

```text
fresh DB → upgrade to s63 → minimal seed (plan/employees as needed)
→ upgrade s64 → verify old plan/tasks_json/transitions hashes unchanged
→ new tables empty → no configs
```

### Downgrade

| Kind | Policy |
| ---- | ------ |
| Technical Alembic downgrade | Drop only new Resource State tables — for isolated tests |
| Operational downgrade after data exists | **Forbidden** without separate Owner GO |

---

## 18. SQLite compatibility findings

| Topic | Finding |
| ----- | ------- |
| CHECK / partial unique | Supported; s58/s63 patterns exist |
| Self-FK | Supported |
| UUID | String(36) |
| Timestamps | `DateTime(timezone=True)` — store UTC; keep `timezone` column for window display |
| FK pragma | **Must address in R3:** enable `PRAGMA foreign_keys=ON` on app engines **or** document app-only enforcement (current freeze leaves pragma OFF) |
| DDL | batch mode already used in env |
| Integer minutes | Avoid float |

```text
R3_REQUIREMENT =
DOCUMENT_OR_ENABLE_SQLITE_FOREIGN_KEYS_FOR_RESOURCE_STATE_FKS
```

---

## 19. PostgreSQL future

```text
SUPPORTED_NOT_ACTIVE
```

Later: native UUID optional, exclusion constraints, timestamptz, stronger row locks. Schema strings/CHECKs remain portable.

---

## 20. Reason codes / privacy

Destructive/reversing ops require `reason_code`; `reason_note` optional except OTHER; length limit + safe charset (Phase B spirit); notes out of normal logs.

Never store JWT, Authorization, salary, rates, pricing, PII, full tasks_json, artwork.

---

## 21. Permissions readiness (conceptual)

| Permission | Admin | Manager | Operator | Viewer |
| ---------- | ----- | ------- | -------- | ------ |
| resource_state.read | yes | yes | no* | no* |
| resource_domain.configure | yes | no | no | no |
| schedule.manage | yes | yes | no | no |
| reservation.manage | yes | yes | no | no |
| capacity.manage | yes | yes | no | no |

\*Operator/viewer diagnostic read deferred to separate security GO. No `planner` role. **Not registered now.**

---

## 22. Phase B integration plan (not implemented)

```text
lock execution_plan
→ resolve task_key in tasks_json
→ read ACTIVE configs (same session/DB)
→ evaluate schedules / reservations / allocations
→ require CLEAR ×3
→ continue assignment transition dual-write
```

Same SQLite DB + SQLAlchemy session expected. TEST_ONLY env CLEAR remains until post-wiring test double.

---

## 23. Concurrency test plan (future)

Schedule/reservation/capacity create vs reassignment eval; config disable mid-command; cancel/release mid-command → one serialized outcome or conflict; **no stale CLEAR success**.

---

## 24. QA rollout stages

| Stage | Content | Owner GO |
| ----- | ------- | -------- |
| R3 | ORM + migration + isolated fresh/s63 proofs | separate |
| R4 | Downgrade/re-upgrade + create_all ownership + constraint matrix | separate |
| R5 | Controlled QA schema-only migrate (empty tables, NOT_CONFIGURED) | separate |
| R6 | Configure + write services | separate program |

R5 expected: new tables empty; guards still NOT_CONFIGURED; Phase C blocked.

---

## 25. Open items (non-blocking for R2 PASS)

| Item | Status |
| ---- | ------ |
| Multi-machine reservation policy | OWNER_DECISION_REQUIRED_BEFORE_WRITE_SERVICE |
| Inactive machine reservation | OWNER_DECISION_REQUIRED_BEFORE_WRITE_SERVICE |
| Plan deletion product behavior | OWNER_DECISION_REQUIRED when delete UI exists |
| SQLite FK pragma enablement | R3 technical requirement |
| Extra schedule statuses | expand later |

---

## 26. Next Owner gate

```text
FUTURE CANDIDATE:
RESOURCE_STATE_PROGRAM_R3_ISOLATED_SCHEMA_AND_MIGRATION_IMPLEMENTATION
```

R3 may authorize ORM + Alembic + isolated tests only. Still: QA mutation 0; no configs; no Phase B wiring; Phase C blocked.

---

## 27. Dead pieces

| Piece | Class |
| ----- | ----- |
| HOLD / not_reserved / NOT_STARTED | PLACEHOLDER |
| ORR Pregătit | ACTIVE_LEGACY |
| Phase B fail-closed guard | ACTIVE_CANONICAL |
| WORKOS_PHASE_B_RESOURCE_GUARDS | TEST_ONLY |
| create_all path | ACTIVE_CANONICAL (must exclude new tables) |

```text
Dead pieces removed: NONE
```
