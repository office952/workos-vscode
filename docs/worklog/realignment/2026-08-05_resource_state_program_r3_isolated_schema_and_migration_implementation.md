# Resource State Program R3 — Isolated Schema and Migration Implementation

**Task:** `RESOURCE_STATE_PROGRAM_R3 = ISOLATED_SCHEMA_AND_MIGRATION_IMPLEMENTATION`  
**Owner GO:** `AUTHORIZE_RESOURCE_STATE_PROGRAM_R3_ISOLATED_SCHEMA_AND_MIGRATION_IMPLEMENTATION`  
**Date:** 2026-08-05  
**Branch:** `feat/f7i-owner-rate-activation`  
**Starting HEAD:** `fb190aad`

---

## Verdict

```text
RESOURCE_STATE_PROGRAM_R3 = PASS
ISOLATED_SCHEMA_AND_MIGRATION_IMPLEMENTATION = VERIFIED
ORM_MODELS = IMPLEMENTED
TABLE_COUNT = 8
MIGRATION = s64_resource_state_persistence
DOWN_REVISION = s63_execution_task_assignment_transitions
EXPAND_ONLY = VERIFIED
INITIAL_BACKFILL = NONE
INITIAL_CONFIGURATION_ROWS = 0
INITIAL_RESOURCE_RECORDS = 0
INITIAL_CLEAR_BACKFILL = FORBIDDEN
SQLITE_FOREIGN_KEYS = VERIFIED_ON
CONSTRAINTS = VERIFIED
INDEXES = VERIFIED
CAS_VERSIONING = VERIFIED
IDEMPOTENCY_CONSTRAINTS = VERIFIED
APPEND_ONLY_BOUNDARY = VERIFIED_APPLICATION_LEVEL
RUNTIME_CREATE_ALL_EXCLUSION = VERIFIED
FRESH_SQLITE_UPGRADE = VERIFIED
S63_TO_S64_UPGRADE = VERIFIED
DOWNGRADE_REUPGRADE = VERIFIED
QA_SCHEMA_MUTATIONS = 0
QA_DATA_MUTATIONS = 0
QA_OPERATIONAL_STATE = UNCHANGED
RESOURCE_STATE_CONFIGURATIONS = 0
RESOURCE_STATE_RECORDS = 0
PHASE_B_WIRING = NOT_AUTHORIZED
PHASE_C = BLOCKED
FRONTEND_CHANGED = NO
EMPLOYEE_MOBILE = FROZEN_FINAL_FINAL
R4 = NOT_AUTHORIZED
QA_SCHEMA_ROLLOUT = NOT_AUTHORIZED
```

---

## Owner GO readback

```text
OWNER GO:
AUTHORIZE_RESOURCE_STATE_PROGRAM_R3_ISOLATED_SCHEMA_AND_MIGRATION_IMPLEMENTATION
```

Authorized: ORM, s64 migration, SQLite FK hardening, create_all exclusions, isolated tests/proofs, docs.  
Forbidden: QA alembic upgrade, resource seeds/configs, write services/APIs, Phase B/C, frontend/Mobile, push/PR.

---

## Repo identity / preflight

| Item | Value |
| ---- | ----- |
| Worktree | `C:\w\psiso` |
| Branch | `feat/f7i-owner-rate-activation` |
| Starting HEAD | `fb190aad` |
| Ancestry | `0baf8932` · `fb190aad` OK |
| Foreign tracked | none |
| Untracked leftovers | `docs/qa/**`, `backend/_qa_backups/**` — not staged |
| QA path | `C:\w\psiso\backend\dev.db` |
| QA alembic (unchanged) | `s63_execution_task_assignment_transitions` |

### Confirmed repo facts (before write)

| Fact | Value |
| ---- | ----- |
| Plan table/PK | `execution_plan.id` INTEGER |
| Machine table/PK | `machines.id` INTEGER |
| Transition UUID column | `transition_id` String(36) (s63 convention) |
| Workcenter relational PK | **none** — no `workcenters` table |
| Workcenter identity | string `workcenter_code` (also `workcenter_rates.code` for rates) |

Capacity scope therefore uses `workcenter_code` + `machine_id` FK + XOR CHECK — not an invented workcenter PK.

### Open-authoring uniqueness (locked)

```text
schedule open = status IN ('DRAFT','PLANNED','CONFIRMED')
reservation open = status IN ('HELD','RESERVED')
```

DRAFT is non-blocking for resource-guard ACTIVE, but still unique per plan+task for authoring.

---

## Implementation summary

### SQLite FK

Shared helper: `backend/core/sqlite_pragma.py`  
Wired via SQLAlchemy `connect` event on:

- `DatabaseManager.init_db`
- Alembic `env.py`
- `IsolatedDBFixture`
- R3 sync test engines (`register_sqlite_foreign_keys`)

Proofs: app / Alembic / fixture / helper engines report `foreign_keys = 1`.  
Raw `sqlite3.connect` to QA without helper still shows 0 (non-product path; classified BYPASS_RISK).

### ORM + ownership

Eight models registered; `ALEMBIC_OWNED_TABLES` expanded to include all eight Resource State tables (+ assignment transitions).

### Migration

`s64_resource_state_persistence` — expand-only, zero DML, create order matches R2, downgrade drops only s64 objects.

---

## Tests

| Suite | Result |
| ----- | ------ |
| `test_resource_state_r3_migration_closure.py` | PASS |
| `test_resource_state_r3_schema_constraints.py` | PASS |
| Wave10 canonical migration + assignment schema | PASS (head → s64) |
| Wave11 Phase B guard + reassignment | PASS |

R3 total: **25 passed** (closure + constraints).

---

## QA read-only proof

| Metric | Value |
| ------ | ----- |
| QA_DB_FILE_SHA | `0023d2fb98145587a13d1117f13dac39c3c648aec7484ea7122560e7d846d1c2` |
| schema_fingerprint | `77011cf97c5ce19a0c5695d056ec9bf968f4b0294a3726065f9aaee3fbf795c2` |
| plan 23 / LED→7 / 1+12 | unchanged |
| tasks_json SHA | `00ee947c0b5e2da587c0d0563f1051ca89379d66cfec434e75dbe3883ccfc1f2` |
| transitions | 7 |
| Resource State tables on QA | **none** |
| alembic | still `s63` |

```text
QA_ALEMBIC_UPGRADE_CALLS = 0
QA_ALEMBIC_DOWNGRADE_CALLS = 0
QA_SCHEMA_MUTATIONS = 0
QA_DATA_MUTATIONS = 0
QA_ASSIGNMENT_REQUESTS = 0
QA_REASSIGNMENT_REQUESTS = 0
QA_UNASSIGNMENT_REQUESTS = 0
```

Baselines: 880811/22 · 973019/21 · 88002 absent · F7I unchanged.

---

## Dead pieces

| Piece | Class |
| ----- | ----- |
| Runtime create_all path | ACTIVE_CANONICAL (excludes RS tables) |
| SQLite FK helper on product engines | ACTIVE_CANONICAL |
| Raw sqlite3 scripts without pragma | BYPASS_RISK (non-product) |
| HOLD / not_reserved / NOT_STARTED | PLACEHOLDER |
| WORKOS_PHASE_B_RESOURCE_GUARDS | TEST_ONLY |

```text
Dead pieces removed: NONE
```

---

## Method

```text
Cursor Plan Mode = COMPLETE (approved)
Cursor Agent Mode = ONE writer
READ_ONLY_SUBAGENTS = used for convention audit
PARALLEL_WRITERS = NO
```

Order: FK helper → ORM → ownership → s64 → constraint tests → migration proofs → regressions → QA RO → docs/commits.

---

## Scores

```text
Direction alignment score: 98/100
Operational completion score: 74/100
```

---

## Next step

```text
FUTURE CANDIDATE:
RESOURCE_STATE_PROGRAM_R4_CANONICAL_MIGRATION_CLOSURE
```

Do not begin R4. Do not migrate QA.
