# Reassignment Transition Persistence Schema — Owner Decisions

| Field | Value |
| ----- | ----- |
| Date | 2026-08-04 |
| Task | `REASSIGNMENT_TRANSITION_PERSISTENCE_SCHEMA_OWNER_DECISION_ONLY` |
| Status | **`REASSIGNMENT_TRANSITION_SCHEMA_OWNER_DECISIONS = RECORDED`** |
| Starting HEAD | `55bcd619` |
| Content commit | `3d0d40e6` |
| Repo / worktree | `C:\w\psiso` |
| Branch | `feat/f7i-owner-rate-activation` |
| Schema / migration / table | **NONE** (decision docs only) |
| Production code | **unchanged** |
| QA mutations | **0** |

## Verdict

```text
REASSIGNMENT_TRANSITION_SCHEMA_OWNER_DECISIONS = RECORDED
FINALIZATION_WAVE_9 = PARTIAL_BLOCKED
SCHEMA_CHANGE_REQUIRED = YES
PERSISTENCE_STRATEGY = SEPARATE_APPEND_ONLY_ASSIGNMENT_TRANSITION_TABLE
SCHEMA_IMPLEMENTED = NO
MIGRATION_EXECUTED = NO
REASSIGNMENT_IMPLEMENTED = NO
UNASSIGNMENT_IMPLEMENTED = NO
QA_MUTATIONS = 0
PHASE_A = NOT_AUTHORIZED
WAVE_10 = NOT_AUTHORIZED
```

Canonical: `docs/architecture/REASSIGNMENT_TRANSITION_PERSISTENCE_SCHEMA_DECISIONS.md`

## Decisions recorded

| ID | Decision |
| -- | -------- |
| DEC-REASSIGN-SCHEMA-01 | `SEPARATE_APPEND_ONLY_ASSIGNMENT_TRANSITION_TABLE` |
| DEC-REASSIGN-SCHEMA-02 | `BACKFILL_EXISTING_ASSIGNMENTS_WITH_SYNTHETIC_INITIAL_TRANSITION` |
| DEC-REASSIGN-SCHEMA-03 | `CLIENT_OR_SERVER_TRANSITION_ID_REQUIRED` |
| DEC-REASSIGN-SCHEMA-04 | `UNIQUE_TRANSITION_ID` |
| DEC-REASSIGN-SCHEMA-05 | `EMBEDDED_CURRENT_STATE_REMAINS_CANONICAL_FOR_EXECUTION` |
| DEC-REASSIGN-SCHEMA-06 | `FOREIGN_KEYS_WHERE_REAL_SCHEMA_SUPPORTS_STABLE_IDENTITIES` |
| DEC-REASSIGN-SCHEMA-07 | `APPEND_ONLY_NO_UPDATE_NO_DELETE` |
| DEC-REASSIGN-SCHEMA-08 | `CONTROLLED_REASON_ENUM_PLUS_OPTIONAL_SAFE_NOTE` |
| DEC-REASSIGN-SCHEMA-09 | `DATABASE_SEQUENCE_PLUS_CREATED_AT` |
| DEC-REASSIGN-SCHEMA-10 | `TRANSITION_ID_IDEMPOTENCY` |
| DEC-REASSIGN-SCHEMA-11 | `LATEST_TRANSITION_MUST_MATCH_EMBEDDED_CURRENT_STATE` |
| DEC-REASSIGN-SCHEMA-12 | `EXPAND_ONLY_MIGRATION_FIRST` |

Plus bindings: dual-write atomicity; permissions `execution.task_reassign` / `execution.task_unassign` manager+admin; fail-closed scheduling/reservation/capacity (`CLEAR` only); `NO_SESSION_HISTORY_REQUIRED_FOR_FIRST_REASSIGNMENT_BUILD`.

## Schema inspection (RO)

| Item | Fact |
| ---- | ---- |
| Plan | `execution_plan.id` INTEGER; `order_id` denormalized; `tasks_json` VARCHAR |
| Employees | `employees.id` INTEGER |
| Users | `users.id` VARCHAR(255) |
| Idempotency precedent | `stock_movements.idempotency_key` UNIQUE |
| Transition table today | absent |
| Dialect | Local SQLite; design portable (do not assume prod = SQLite) |

## Zero mutation

```text
PROTECTED_ROW_STATE = UNCHANGED
order 880750 / plan 23 / ops 13 / assigned 1 (LED→7) / unassigned 12
tasks_json SHA = 00ee947c0b5e2da587c0d0563f1051ca89379d66cfec434e75dbe3883ccfc1f2
updated_at = 2026-08-04 19:16:57.407320
sessions 0 / machines 0 / scheduling HOLD / capacity NOT_STARTED

GLOBAL_DB_FILE_SHA_BEFORE = 0f6a03322e4a68d6fdb6f575815ae1ea84124a870373e7e2789241f8819f8a2a
GLOBAL_DB_FILE_SHA_AFTER  = 0f6a03322e4a68d6fdb6f575815ae1ea84124a870373e7e2789241f8819f8a2a
GLOBAL_DB_FILE_SHA_CHANGE_ATTRIBUTION = UNCHANGED_DURING_DECISION_WINDOW
transition_table_created = NO
```

```text
QA_ASSIGNMENT_REQUESTS = 0
QA_REASSIGNMENT_REQUESTS = 0
QA_UNASSIGNMENT_REQUESTS = 0
QA_SUCCESSFUL_MUTATIONS = 0
```

## Protected baselines / F7I

880811 plan 22 · 973019 plan 21 · 88002 absent — unchanged.  
F7I: 15 / 1.5 / 35 / 20 EUR — untouched.

## Dead Pieces Check

Classified; **removed: NONE**.

## Phases

A–E documented; **all NOT_AUTHORIZED**. Phase A not started.

## Scores

```text
Direction alignment score: 95/100
Operational completion score: 35/100
```

(Decision recording only — schema not implemented.)

## Next step

```text
FUTURE CANDIDATE:
REASSIGNMENT_TRANSITION_SCHEMA_AND_BACKFILL_IMPLEMENTATION
```

Do not start Phase A without Owner GO.
