# Reassignment Transition Persistence Schema — Owner Decisions

**Status:** Owner decisions **RECORDED** (2026-08-04)  
**Task:** `REASSIGNMENT_TRANSITION_PERSISTENCE_SCHEMA_OWNER_DECISION_ONLY`  
**Schema implementation:** **NOT AUTHORIZED**  
**Migration:** **NOT AUTHORIZED**  
**Table creation:** **NOT AUTHORIZED**  
**Wave 9 retained:** `PARTIAL_BLOCKED` (readiness)  
**Related:** `CONTROLLED_PRE_START_REASSIGNMENT_DECISIONS.md` · `CONTROLLED_PRE_START_REASSIGNMENT_IMPLEMENTATION_READINESS.md`  
**Worklog:** `docs/worklog/realignment/2026-08-04_reassignment_transition_persistence_schema_owner_decisions.md`

```text
REASSIGNMENT_TRANSITION_SCHEMA_OWNER_DECISIONS = RECORDED
FINALIZATION_WAVE_9 = PARTIAL_BLOCKED
FINALIZATION_WAVE_10 = PASS
SCHEMA_CHANGE_REQUIRED = YES
PERSISTENCE_STRATEGY = SEPARATE_APPEND_ONLY_ASSIGNMENT_TRANSITION_TABLE
SCHEMA_IMPLEMENTED = YES
MIGRATION_EXECUTED = YES
BACKFILLED_ASSIGNMENT_TRANSITIONS = 7
REASSIGNMENT_IMPLEMENTED = NO
UNASSIGNMENT_IMPLEMENTED = NO
PHASE_A = VERIFIED
PHASE_B = NOT_AUTHORIZED
WAVE_11 = NOT_AUTHORIZED
```

Phase A proof: `docs/worklog/realignment/2026-08-04_finalization_wave10_reassignment_transition_schema_and_backfill.md`
Evidence closure: worklog "Evidence closure addendum"; programmatic s63.upgrade() + post-body stamp; UUID5=backfill identity only; Wave10 tip before closure 9eef4414.
Migration: `backend/alembic/versions/s63_execution_task_assignment_transitions.py`

---

## Owner gate

```text
SCHEMA_DECISION_AUTHORIZED = YES
SCHEMA_IMPLEMENTATION_AUTHORIZED = YES   # Phase A completed
MIGRATION_AUTHORIZED = YES               # Phase A completed (expand-only)
TABLE_CREATION_AUTHORIZED = YES          # Phase A completed
REASSIGNMENT_IMPLEMENTATION_AUTHORIZED = FALSE
UNASSIGNMENT_IMPLEMENTATION_AUTHORIZED = FALSE
REASSIGNMENT_EXECUTION_AUTHORIZED = FALSE
UNASSIGNMENT_EXECUTION_AUTHORIZED = FALSE
PHASE_B = NOT_AUTHORIZED
```

---

## Factual schema context (read-only inspection)

| Fact | Value |
| ---- | ----- |
| Local QA DB | SQLite `backend/dev.db` (`journal_mode=delete`) |
| Production dialect | Not assumed SQLite — Alembic + SQLAlchemy async; tests mention `postgresql`/`asyncpg`; design must be dialect-portable |
| Current assignee store | `execution_plan.tasks_json` → `operational_tasks[].assigned_employee_id` |
| Plan PK | `execution_plan.id` INTEGER |
| Plan `order_id` | INTEGER NOT NULL — **no FK** to orders in live pragma (denormalized identity, same pattern as `execution_task_participants.order_id`) |
| Employees PK | `employees.id` INTEGER |
| Users PK | `users.id` VARCHAR(255) — matches embedded `assignment_actor_user_id` shape |
| Existing idempotency pattern | `stock_movements.idempotency_key` UNIQUE |
| Existing assignment transition table | **NONE** |
| Session / reality | `execution_reality` (order-scoped JSON tasks); no assignment-transition linkage today |
| Permission matrix | Declarative Python `PERMISSION_MATRIX` in `dependencies/permissions.py` — `execution.task_assign` includes operator; reassign/unassign keys **absent** |

Protected fixture (must remain unchanged by this docs task):

```text
order_id = 880750
execution_plan_id = 23
task_key = node:root_product:TPL-VOLUMETRIC-LETTERS_v2:led_install_letters
assigned_employee_id = 7
assignment_source = canonical_controlled_assign_v1
assignment_actor_user_id = dev-admin-user-00000000
assignment_updated_at = 2026-08-04T16:16:57.406324+00:00
```

---

## DEC-REASSIGN-SCHEMA-01 — Persistence model

| Field | Value |
| ----- | ----- |
| Decision | **`SEPARATE_APPEND_ONLY_ASSIGNMENT_TRANSITION_TABLE`** |
| Current operational state | `operational_tasks[].assigned_employee_id` (and existing embedded audit fields) |
| Historical truth | `execution_task_assignment_transitions` (conceptual name) |
| Forbidden now | Moving current state exclusively into the table; removing embedded fields; inventing JSON `assignment_history[]` as primary store |

---

## DEC-REASSIGN-SCHEMA-02 — Backfill

| Field | Value |
| ----- | ----- |
| Decision | **`BACKFILL_EXISTING_ASSIGNMENTS_WITH_SYNTHETIC_INITIAL_TRANSITION`** |
| Rule | One synthetic `ASSIGN` per task with `assigned_employee_id != null` |
| Source | `LEGACY_EMBEDDED_BACKFILL` |
| Preserve when present | `assignment_actor_user_id` → `actor_user_id`; `assignment_updated_at` → `created_at`; `assignment_source` → optional `source` / provenance note |
| Missing metadata | `actor_user_id = null`; use exact available timestamp only; never invent actor/time |
| Fixture expectation | Exactly one backfill row for LED→7 on plan 23 |

---

## DEC-REASSIGN-SCHEMA-03 — Transition identity

| Field | Value |
| ----- | ----- |
| Decision | **`CLIENT_OR_SERVER_TRANSITION_ID_REQUIRED`** |
| Preferred type | UUID string |
| Purpose | Deterministic retry, duplicate detection, same-transition idempotency, conflict on same ID + different payload, log/response correlation |

---

## DEC-REASSIGN-SCHEMA-04 — Uniqueness

| Field | Value |
| ----- | ----- |
| Decision | **`UNIQUE_TRANSITION_ID`** |
| Required | `UNIQUE(transition_id)` global |
| Evaluated optional | `UNIQUE(execution_plan_id, task_key, transition_id)` — redundant if `transition_id` is globally unique UUID; optional defense-in-depth only |
| Forbidden | Unique on `task_key` alone; unique on employee alone |

---

## DEC-REASSIGN-SCHEMA-05 — Current-state authority

| Field | Value |
| ----- | ----- |
| Decision | **`EMBEDDED_CURRENT_STATE_REMAINS_CANONICAL_FOR_EXECUTION`** |
| First build | Do not rebuild live plan assignee solely from event history |
| Consistency | Latest transition `new_employee_id` must match embedded assignee; mismatch → fail-closed `ASSIGNMENT_TRANSITION_STATE_MISMATCH` — **no auto-heal** |

---

## DEC-REASSIGN-SCHEMA-06 — Foreign keys

| Field | Value |
| ----- | ----- |
| Decision | **`FOREIGN_KEYS_WHERE_REAL_SCHEMA_SUPPORTS_STABLE_IDENTITIES`** |

### Evaluated variants (choose at Phase A implementation, not now)

| Reference | Recommended conceptual policy | Rationale |
| --------- | ----------------------------- | --------- |
| `execution_plan_id` → `execution_plan.id` | FK `ON DELETE RESTRICT` | Plan deletion must not orphan transitions silently |
| `order_id` | **Denormalized** INTEGER (no FK) unless a stable orders FK already exists in target dialect migration set | Matches `execution_task_participants` / plan row pattern; plan FK already anchors identity |
| `previous_employee_id` / `new_employee_id` → `employees.id` | Prefer **FK `ON DELETE RESTRICT`** for active integrity; alternative **nullable columns without FK** if hard-delete of employees is operationally required | History must survive inactive/deleted employees — soft-delete/`status`/`end_date` preferred over hard delete |
| `actor_user_id` → `users.id` | FK optional; if present use `ON DELETE SET NULL` (VARCHAR identity) | Actor may be removed; retain transition with null actor rather than delete row |
| `task_key` | String, **no task table FK** | Tasks live in embedded JSON |

Contrast: `execution_task_participants.employee_id` uses `ON DELETE CASCADE` — **must not** be copied for transition history.

---

## DEC-REASSIGN-SCHEMA-07 — Append-only

| Field | Value |
| ----- | ----- |
| Decision | **`APPEND_ONLY_NO_UPDATE_NO_DELETE`** |
| Enforcement (conceptual) | No operational UPDATE/DELETE API; DB role/app layer deny; corrections = new transition |
| Retention cleanup | Future Owner policy only |

---

## DEC-REASSIGN-SCHEMA-08 — Reason and note

| Field | Value |
| ----- | ----- |
| Decision | **`CONTROLLED_REASON_ENUM_PLUS_OPTIONAL_SAFE_NOTE`** |
| Codes | `EMPLOYEE_UNAVAILABLE` · `EMPLOYEE_INACTIVE` · `ELIGIBILITY_CHANGED` · `INCORRECT_INITIAL_ASSIGNMENT` · `MANAGER_CORRECTION` · `PLANNING_CHANGE` · `OPERATIONAL_REBALANCE_PRE_START` · `OTHER` |
| `OTHER` | Safe note **required** |
| Others | Note optional |
| Constraints | Length limit; redaction; no HR-sensitive / pricing / secrets |

Storage strategy: VARCHAR + application/OpenAPI enum validation (portable across SQLite/Postgres). Optional CHECK constraint listing codes when dialect supports it.

---

## DEC-REASSIGN-SCHEMA-09 — Ordering

| Field | Value |
| ----- | ----- |
| Decision | **`DATABASE_SEQUENCE_PLUS_CREATED_AT`** |
| Canonical order | Monotonic primary key `id` ASC, then `created_at` |
| Note | `created_at` alone insufficient under equal timestamps |

---

## DEC-REASSIGN-SCHEMA-10 — Retry semantics

| Field | Value |
| ----- | ----- |
| Decision | **`TRANSITION_ID_IDEMPOTENCY`** |

| Case | Result |
| ---- | ------ |
| Same `transition_id`, same payload | Return prior canonical result; no new row; no second current-state mutation |
| Same `transition_id`, different payload | Conflict; no mutation |
| Different `transition_id`, stale expected employee | Conflict |
| Success lost response | Retry same `transition_id` → prior success |

Payload fingerprint for “same payload” (conceptual): `transition_type`, `execution_plan_id`, `task_key`, `expected_current_employee_id`, `previous_employee_id`/`new_employee_id` as applicable, `reason_code`, normalized `reason_note`.

---

## DEC-REASSIGN-SCHEMA-11 — Consistency check

| Field | Value |
| ----- | ----- |
| Decision | **`LATEST_TRANSITION_MUST_MATCH_EMBEDDED_CURRENT_STATE`** |
| Assign/reassign | `latest.new_employee_id == embedded.assigned_employee_id` |
| Unassign | both null |
| Failure | `STATE=INCONSISTENT`; reassignment/unassignment **BLOCKED**; Owner/admin repair required; no auto-heal |

---

## DEC-REASSIGN-SCHEMA-12 — Migration safety

| Field | Value |
| ----- | ----- |
| Decision | **`EXPAND_ONLY_MIGRATION_FIRST`** |
| Phase A only | Create table + indexes/constraints + backfill + verify; leave embedded state intact; **no** assignment route change in same migration |
| Phases | A schema/backfill · B commands · C QA proof — each needs separate Owner GO |

---

## Dual-write atomic contract (future Phase B)

```text
BEGIN
  lock execution_plan row (SELECT FOR UPDATE + existing process lock pattern)
  re-read tasks_json / task
  validate expected_current_employee_id
  validate guards (session history, scheduling/reservation/capacity CLEAR only)
  validate new employee + DEC-015 (reassign) OR null target (unassign)
  INSERT transition row (append-only)
  UPDATE tasks_json current assignee + embedded audit fields
COMMIT
```

Failure of either write → **ROLLBACK BOTH**.  
Forbidden: current state without history; history without current state.

Application ops logs remain best-effort (must not alone gate commit), consistent with Wave 6 assign observability.

---

## Proposed table (conceptual — not created)

### Name

```text
execution_task_assignment_transitions
```

### Columns

| Column | Type (conceptual) | Null | Notes |
| ------ | ----------------- | ---- | ----- |
| `id` | INTEGER / BIGSERIAL PK autoincrement | NO | Monotonic order authority |
| `transition_id` | CHAR/UUID string (36) | NO | Client or server UUID |
| `execution_plan_id` | INTEGER | NO | FK → `execution_plan.id` |
| `order_id` | INTEGER | NO | Denormalized audit identity |
| `task_key` | VARCHAR(512) | NO | Embedded operational task id string |
| `transition_type` | VARCHAR(16) | NO | `ASSIGN` \| `REASSIGN` \| `UNASSIGN` |
| `previous_employee_id` | INTEGER | YES | Null on first ASSIGN / after unassign→assign |
| `new_employee_id` | INTEGER | YES | Null on UNASSIGN |
| `actor_user_id` | VARCHAR(255) | YES | Matches `users.id`; null on incomplete backfill |
| `actor_role` | VARCHAR(50) | YES | Safe role string at transition time |
| `reason_code` | VARCHAR(64) | YES* | Required for REASSIGN/UNASSIGN; backfill ASSIGN may use synthetic code or null + source |
| `reason_note` | VARCHAR(500) | YES | Required when reason=`OTHER` |
| `task_state_at_transition` | VARCHAR(64) | YES | Safe compact state token |
| `eligibility_decision_code` | VARCHAR(64) | YES | DEC-015 outcome code |
| `eligibility_provenance` | VARCHAR(128) | YES | Short provenance, not full RM dump |
| `request_id` | VARCHAR(64) | YES | Optional HTTP/request id |
| `correlation_id` | VARCHAR(64) | YES | Optional correlation |
| `expected_current_employee_id` | INTEGER | YES | Optional CAS echo |
| `source` | VARCHAR(64) | YES | e.g. `LEGACY_EMBEDDED_BACKFILL`, `canonical_controlled_reassign_v1` |
| `command_version` | VARCHAR(32) | YES | Optional |
| `metadata_json` | TEXT/JSON | YES | Optional compact non-PII bag — never full `tasks_json` / employee / JWT |
| `created_at` | TIMESTAMP WITH TIME ZONE | NO | From request time or preserved backfill timestamp |

\*Backfill `ASSIGN` rows: reason may be null or a dedicated synthetic code such as `LEGACY_BACKFILL_INITIAL_ASSIGN` — **must be decided in Phase A** without inventing fake operational reasons. Prefer explicit synthetic code over pretending `MANAGER_CORRECTION`.

### Forbidden column content

Salary, hourly rate, CNP, address, phone, private email, JWT, Authorization, commercial price, internal cost, complete `tasks_json`, full employee object.

### Indexes / constraints (conceptual)

```text
PK (id)
UNIQUE (transition_id)  -- uq_exec_task_assign_transition_id
INDEX (execution_plan_id, task_key, id)  -- latest-per-task / ordering
INDEX (order_id, task_key)
INDEX (created_at)
CHECK (transition_type IN ('ASSIGN','REASSIGN','UNASSIGN'))
CHECK (
  (transition_type = 'UNASSIGN' AND new_employee_id IS NULL)
  OR (transition_type IN ('ASSIGN','REASSIGN') AND new_employee_id IS NOT NULL)
)
-- optional CHECK on reason_code enum list
```

### Append-only enforcement strategy

1. No repository methods for update/delete of transitions.  
2. DB grants: INSERT + SELECT only for app role where possible.  
3. Consistency verifier read-only.  
4. Corrections = new transition under Phase B rules.

---

## Enum / type strategy

Prefer application-level string enums (OpenAPI + Python) for SQLite/Postgres portability. Optional native Postgres ENUM only if production dialect is confirmed Postgres **and** Owner accepts Alembic complexity — default recommendation: **VARCHAR + CHECK**.

---

## Backfill algorithm (conceptual, Phase A)

1. Count operational tasks with `assigned_employee_id != null` across plans in scope (or all plans).  
2. Expected transition rows = that count (for initial backfill).  
3. For each assigned task: INSERT one `ASSIGN` with `previous_employee_id=null`, `new_employee_id=current`, `source=LEGACY_EMBEDDED_BACKFILL`, preserve actor/timestamp/source when present.  
4. Generate `transition_id` server-side UUID per backfill row (stable algorithm: optional deterministic UUID5 from `(execution_plan_id, task_key, 'LEGACY_EMBEDDED_BACKFILL')` for idempotent re-run).  
5. Verify latest transition per task matches embedded assignee.  
6. Re-run backfill → zero new rows (idempotent).  
7. Verify `tasks_json` SHA / `updated_at` / embedded assignee **unchanged**.  
8. Verify protected fixtures (880750 LED→7; baselines).  
9. On inconsistency → **STOP**; no silent repair.  
10. Emit evidence report (counts, mismatches) without PII dumps.

Wave 7 fixture expected after backfill:

```text
transition_type = ASSIGN
previous_employee_id = null
new_employee_id = 7
actor_user_id = dev-admin-user-00000000
created_at = 2026-08-04T16:16:57.406324+00:00 (preserved)
source = LEGACY_EMBEDDED_BACKFILL
```

---

## Consistency query (conceptual)

For each plan/task with transitions or embedded assignee:

```text
latest = max(id) transition for (execution_plan_id, task_key)
assert latest.new_employee_id == embedded.assigned_employee_id  -- both null OK
```

Mismatch → `ASSIGNMENT_TRANSITION_STATE_MISMATCH`.

---

## Rollback policy (conceptual)

| Condition | Allowed |
| --------- | ------- |
| Phase A only, no Phase B commands, no real REASSIGN/UNASSIGN rows | Drop table / reverse expand migration **with** backup + evidence; embedded assignees untouched |
| Real operational transitions exist | Destructive rollback **forbidden** without separate Owner decision |

Rollback must never unassign or mutate embedded current state.

---

## Permissions (retained targets — not implemented)

```text
execution.task_reassign  → admin, manager
execution.task_unassign  → admin, manager
```

Must appear in `PERMISSION_MATRIX`, route dependencies, and service-level checks. Not UI-only. Must not reuse `execution.task_assign` (includes operator).

---

## Guards (schema-era policy bindings)

### Scheduling / reservation / capacity

Explicit guard states for future Phase B:

```text
NOT_CONFIGURED | UNKNOWN | ACTIVE | CLEAR
```

Only **`CLEAR`** allows reassign/unassign. Unknown/not configured → **blocked** (fail-closed). Absence of a scheduling system ≠ CLEAR.

### Session history

```text
NO_SESSION_HISTORY_REQUIRED_FOR_FIRST_REASSIGNMENT_BUILD
```

Any session/execution history for the task → reassign and unassign **blocked**. Active-only check is insufficient. Post-start operational transfer = future Phase E architecture.

---

## Implementation phases (all NOT AUTHORIZED)

| Phase | Scope | Auth |
| ----- | ----- | ---- |
| **A** | Table + constraints + indexes + backfill + consistency verification; no command behavior change | **`VERIFIED` (Wave 10 PASS)** |
| **B** | Permissions, routes, schemas, CAS, DEC-015, guards, atomic dual-write, observability | `NOT_AUTHORIZED` |
| **C** | Controlled QA: **one** reassignment **or** one unassignment; Owner fixture; exact mutation budget | `NOT_AUTHORIZED` |
| **D** | UI after backend proof | `NOT_AUTHORIZED` |
| **E** | Post-start operational transfer (sessions/scheduling integrated) | `NOT_AUTHORIZED` |

```text
FUTURE CANDIDATE (not started):
PHASE_B_CONTROLLED_PRE_START_REASSIGNMENT_BACKEND_IMPLEMENTATION
```

---

## SQLite vs production DB

| Concern | Guidance |
| ------- | -------- |
| Local QA | SQLite — INTEGER PK, CHECK, UNIQUE supported |
| Production | Do not assume SQLite; use Alembic portable types (`sa.Integer`, `sa.String`, `DateTime(timezone=True)`) |
| FOR UPDATE | Wave 6 already uses dialect-aware locking; Phase B must retain that pattern around dual-write |
| UUID | Store as string (36) for portability |

---

## Test strategy (future — not executed here)

Isolated test DB only for Phase A/B: table create; unique transition_id; backfill idempotency; consistency pass/fail; dual-write rollback; same-ID retry; payload conflict; FK restrict behavior; append-only denial; permission matrix keys; session-history block; scheduling CLEAR-only. **Never** mutate protected QA `dev.db` without Phase C Owner GO.

---

## Dead pieces (record only — nothing removed)

| Piece | Class |
| ----- | ----- |
| `allow_reassign` | `BLOCKED_LEGACY` |
| `clear_plan_task_assignment` | `ACTIVE_LEGACY` (unsafe for policy unassign) |
| Direct overwrite helpers | `BLOCKED_LEGACY` / `SUPERSEDED` |
| Mobile claim / `start_from_available` | `BLOCKED_LEGACY` |
| Embedded current-only audit | `ACTIVE_CANONICAL` for current state; `INSUFFICIENT` for history |
| Legacy reassignment tests | `ACTIVE_LEGACY` |
| Old UI actions | `UNKNOWN` / absent as product controls |

```text
Dead pieces removed: NONE
```

---

## Next step

```text
FUTURE CANDIDATE:
REASSIGNMENT_TRANSITION_SCHEMA_AND_BACKFILL_IMPLEMENTATION
```

Phase A is **not** authorized by this document. Await Owner review / separate GO.
