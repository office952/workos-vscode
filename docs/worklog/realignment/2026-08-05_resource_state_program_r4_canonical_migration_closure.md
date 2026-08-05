# Resource State Program R4 — Canonical Migration Closure

**Task:** `RESOURCE_STATE_PROGRAM_R4 = CANONICAL_MIGRATION_CLOSURE`  
**Owner GO:** `AUTHORIZE_RESOURCE_STATE_PROGRAM_R4_CANONICAL_MIGRATION_CLOSURE`  
**Date:** 2026-08-05  
**Branch:** `feat/f7i-owner-rate-activation`  
**Starting HEAD:** `964d10d0`  
**Final HEAD:** `02d3e51b`

---

## Verdict

```text
RESOURCE_STATE_PROGRAM_R4 = PASS
CANONICAL_MIGRATION_CLOSURE = VERIFIED
R3_IMPLEMENTATION = RETAINED
TABLE_COUNT = 8
ORM_MIGRATION_PARITY = VERIFIED
SCHEMA_DRIFT = NONE
CONSTRAINTS = VERIFIED
INDEXES = VERIFIED
PARTIAL_INDEX_PREDICATES = VERIFIED
FOREIGN_KEYS = VERIFIED
SQLITE_FOREIGN_KEYS = VERIFIED_ON
ALEMBIC_HEAD_COUNT = 1
ALEMBIC_HEAD = s64_resource_state_persistence
MIGRATION_ANCESTRY = VERIFIED
RUNTIME_CREATE_ALL_OWNERSHIP = VERIFIED
FRESH_FULL_CHAIN = VERIFIED
S63_TO_S64 = VERIFIED
DOWNGRADE_REUPGRADE = VERIFIED
SCHEMA_FINGERPRINT = MATCH
INITIAL_CONFIGURATION_ROWS = 0
INITIAL_RESOURCE_STATE_ROWS = 0
INITIAL_CLEAR_BACKFILL = FORBIDDEN
QA_ALEMBIC_REVISION = s63
QA_RESOURCE_STATE_TABLES = 0
QA_FOREIGN_KEY_INTEGRITY = DEBT_PRESENT
QA_SCHEMA_MUTATIONS = 0
QA_DATA_MUTATIONS = 0
QA_OPERATIONAL_STATE = UNCHANGED
PHASE_B_WIRING = NOT_AUTHORIZED
PHASE_C = BLOCKED
R5 = NOT_AUTHORIZED
QA_SCHEMA_ROLLOUT = NOT_AUTHORIZED
```

---

## Owner GO readback

```text
OWNER GO:
AUTHORIZE_RESOURCE_STATE_PROGRAM_R4_CANONICAL_MIGRATION_CLOSURE
```

Authorized: read-only audits, isolated migration proofs, test hardening, FK path fixes if required, docs.  
Forbidden: QA migrate, resource seeds/configs/services, Phase B/C, frontend/Mobile, push/PR.

---

## Repo identity / preflight

| Item | Value |
| ---- | ----- |
| Worktree | `C:\w\psiso` |
| Branch | `feat/f7i-owner-rate-activation` |
| Starting HEAD | `964d10d0` |
| Ancestry | `fb190aad` … `964d10d0` OK |
| Foreign tracked | none |
| Untracked leftovers | `docs/qa/**`, `backend/_qa_backups/**` — not staged |
| Code Alembic head | `s64_resource_state_persistence` (single) |
| QA Alembic | `s63_execution_task_assignment_transitions` |

---

## ORM ↔ migration parity

| Table | Match |
| ----- | ----- |
| resource_domain_configurations | yes |
| resource_domain_configuration_transitions | yes |
| execution_task_schedules | yes |
| execution_task_schedule_transitions | yes |
| execution_task_machine_reservations | yes |
| execution_task_machine_reservation_transitions | yes |
| execution_task_capacity_allocations | yes |
| execution_task_capacity_allocation_transitions | yes |

```text
SCHEMA_DRIFT = NONE
```

Only `EXPECTED_SERVER_DEFAULT_NORMALIZATION` (ORM Python `default=` vs migration `server_default=`).

### Status / unit / open predicates

| Domain | Values |
| ------ | ------ |
| Configuration | ACTIVE, DISABLED |
| Schedule | DRAFT, PLANNED, CONFIRMED, CANCELLED, SUPERSEDED |
| Reservation | HELD, RESERVED, CANCELLED, RELEASED, SUPERSEDED |
| Capacity | HELD, ALLOCATED, RELEASED, CANCELLED, SUPERSEDED |
| Capacity unit | `minutes` (R3 retained; CHECK `unit = 'minutes'`) |
| Open schedule unique | DRAFT+PLANNED+CONFIRMED (authoring uniqueness) |
| Open reservation unique | HELD+RESERVED |

---

## FK closure

Product/migration/test paths ON via `register_sqlite_foreign_keys`:

- DatabaseManager
- Alembic env
- IsolatedDBFixture
- R3/R4 sync engines
- Wave10 sync engines (**R4 hardening**)

Scripts without helper = SCRIPT_ONLY / BYPASS_RISK (listed; not product runtime).

### QA foreign_key_check (read-only, non-mutating)

```text
QA_FOREIGN_KEY_INTEGRITY = DEBT_PRESENT
foreign_key_check_count = 11
```

Affected (preexisting legacy, **not** Resource State — RS tables absent on QA):

| table | parent (sample) |
| ----- | --------------- |
| execution_plan | quote_snapshots_v2 |
| orders | quote_snapshots_v2 |
| employee_*_authorizations | employees |

No repair. No Alembic on QA. Does **not** block R4 PASS (debt reported only).

---

## Proofs (isolated)

| Proof | Result |
| ----- | ------ |
| Fresh full-chain → s64 | VERIFIED · RS rows 0 · FK ON |
| ORM vs migrated drift | NONE |
| s63→s64 preserve prior | VERIFIED |
| Downgrade s63 / re-upgrade fingerprint MATCH | VERIFIED |
| create_all dual (runtime-owned present; RS absent / Alembic present) | VERIFIED |
| Downgrade after sample config+schedule | **DESTRUCTIVE** (tables dropped) |

```text
TECHNICAL_DOWNGRADE = AVAILABLE
DOWNGRADE_AFTER_RESOURCE_DATA = DESTRUCTIVE
OPERATIONAL_DOWNGRADE_REQUIRES_OWNER_GO = YES
```

---

## Append-only boundary

```text
WRITE_SERVICE_NOT_IMPLEMENTED
MODEL_HISTORY_STRUCTURE_READY
APPEND_ONLY = APPLICATION_REPOSITORY_AND_SERVICE_BOUNDARY
```

No Resource State repositories yet.

---

## Regression suites

| Suite | Result |
| ----- | ------ |
| R3 migration + constraints | PASS |
| R4 canonical closure | PASS (8) |
| Wave10 migration + assignment | PASS |
| Wave11 Phase B | PASS |
| Combined | **81 passed**, 1 skipped |

No INTRODUCED_BY_R4 failures.

---

## QA read-only proof

| Metric | Value |
| ------ | ----- |
| QA_DB_FILE_SHA | `0023d2fb98145587a13d1117f13dac39c3c648aec7484ea7122560e7d846d1c2` |
| schema_fingerprint | `77011cf97c5ce19a0c5695d056ec9bf968f4b0294a3726065f9aaee3fbf795c2` |
| Alembic | s63 |
| RS tables | 0 |
| plan 23 / LED→7 / 1+12 | unchanged |
| tasks_json SHA | `00ee947c0b5e2da587c0d0563f1051ca89379d66cfec434e75dbe3883ccfc1f2` |
| transitions 7 · fp | `27c68a532996d2fca9761f38932d9b058ef76f3a720d4209f9b2e43926657236` |

```text
QA_ALEMBIC_UPGRADE_CALLS = 0
QA_ALEMBIC_DOWNGRADE_CALLS = 0
QA_SCHEMA_MUTATIONS = 0
QA_DATA_MUTATIONS = 0
QA_ASSIGNMENT_REQUESTS = 0
QA_REASSIGNMENT_REQUESTS = 0
QA_UNASSIGNMENT_REQUESTS = 0
```

Baselines 880811/22 · 973019/21 · 88002 absent · F7I unchanged.

---

## Dead pieces

| Piece | Class |
| ----- | ----- |
| FK helper on product engines | ACTIVE_CANONICAL |
| create_all exclusions | ACTIVE_CANONICAL |
| Raw sqlite3 / proof scripts without helper | BYPASS_RISK / SCRIPT_ONLY |
| stamp_alembic_revision_after_parity | ACTIVE_LEGACY |
| HOLD / not_reserved / NOT_STARTED | PLACEHOLDER |
| WORKOS_PHASE_B_RESOURCE_GUARDS | TEST_ONLY |

```text
Dead pieces removed: NONE
```

---

## Corrections made in R4

| Change | Why |
| ------ | --- |
| Wave10 sync engines register FK helper | Close TEST path gap (canonical connect event) |
| New R4 closure tests | Drift, fingerprint, downgrade-after-data, dual create_all |

No ORM/migration DDL changes required (parity already clean).

---

## Method

```text
read-only subagents = ORM parity + FK inventory
write owner = one (tests + Wave10 FK wiring + docs)
PARALLEL_WRITERS = NO
Plan Mode corrections = not required for schema (tests only)
```

---

## Scores

```text
Direction alignment score: 98/100
Operational completion score: 76/100
```

---

## Next step

```text
FUTURE CANDIDATE:
RESOURCE_STATE_PROGRAM_R5_CONTROLLED_QA_SCHEMA_ONLY_ROLLOUT
```

Do not begin R5. Do not migrate QA.
