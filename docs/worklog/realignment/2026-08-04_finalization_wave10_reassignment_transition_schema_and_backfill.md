# Finalization Wave 10 / Phase A — Transition Schema and Backfill

| Field | Value |
| ----- | ----- |
| Date | 2026-08-04 |
| Task | `PHASE_A = REASSIGNMENT_TRANSITION_SCHEMA_AND_BACKFILL_IMPLEMENTATION` |
| Status | **`FINALIZATION_WAVE_10 = PASS`** |
| Starting HEAD | `d393b27f` |
| Impl commit | `bbb4c466` |
| Docs commit | (pending tip) |
| Repo / worktree | `C:\w\psiso` |
| Branch | `feat/f7i-owner-rate-activation` |
| Phase B | **NOT_AUTHORIZED** |

## Verdict

```text
FINALIZATION_WAVE_10 = PASS
PHASE_A_SCHEMA_AND_BACKFILL = VERIFIED
TRANSITION_TABLE = IMPLEMENTED
MIGRATION = VERIFIED
BACKFILL = VERIFIED
BACKFILLED_ASSIGNMENT_TRANSITIONS = 7
WAVE7_ASSIGNMENT_TRANSITION = VERIFIED
EMBEDDED_CURRENT_STATE = UNCHANGED
CONSISTENCY_CHECK = MATCH
OPERATIONAL_TASK_MUTATIONS = 0
ASSIGNMENT_REQUESTS = 0
REASSIGNMENT_IMPLEMENTED = NO
UNASSIGNMENT_IMPLEMENTED = NO
PHASE_B = NOT_AUTHORIZED
WAVE_11 = NOT_AUTHORIZED
```

## Scope

Authorized: ORM model, expand-only Alembic `s63`, indexes/constraints, deterministic legacy backfill, consistency verifier, append-only repository, isolated tests, controlled QA migration.

Unauthorized / not done: reassignment/unassignment routes or services, assignment mutation, frontend, Mobile, sessions, scheduling, push/PR.

## Owner decisions readback

`DEC-REASSIGN-SCHEMA-01…12` applied: separate append-only table; embedded current state remains canonical; expand-only migration; synthetic `ASSIGN` backfill; UUID5 transition identity; fail-closed consistency.

## Repo / preflight

| Item | Value |
| ---- | ----- |
| Root | `C:/w/psiso` |
| Branch | `feat/f7i-owner-rate-activation` |
| Start HEAD | `d393b27f` |
| Ancestry | Wave 6–9 · `3d0d40e6` · `d393b27f` OK |
| Tracked dirty at start | none |
| Untracked leftovers | preexisting `docs/qa/**`, `_qa_backups` — not staged |
| Migration framework | Alembic (`backend/alembic`) |
| Heads before | single `s62_material_actuals_closed_job_v1` |
| Heads after | single `s63_execution_task_assignment_transitions` |
| QA `alembic_version` before | **absent** (create_all era DB) |
| QA `alembic_version` after | `s63_execution_task_assignment_transitions` |

## Database engines

| Environment | Engine |
| ----------- | ------ |
| Development | SQLite (`sqlite+aiosqlite:///./dev.db`) |
| Test | SQLite isolated (`IsolatedDBFixture` / tmp files) |
| Production URL in repo | **not present** |
| Production dialect support in code | `postgresql+asyncpg` via `DatabaseManager` |
| Migration portability | VARCHAR / INTEGER / CHECK / UNIQUE / RESTRICT FKs; no Postgres-only ENUM |

Production deploy URL is outside this frozen reference repo; Phase A types follow existing dual-dialect Alembic patterns.

## Schema design

Table: `execution_task_assignment_transitions`

| Column | Type | Null | Notes |
| ------ | ---- | ---- | ----- |
| id | INTEGER PK AI | NO | Canonical order |
| transition_id | VARCHAR(36) UNIQUE | NO | UUID5 for backfill |
| execution_plan_id | INTEGER FK → execution_plan.id RESTRICT | NO | |
| order_id | INTEGER | NO | Denormalized |
| task_key | VARCHAR(512) | NO | Embedded task id |
| transition_type | VARCHAR(16) | NO | CHECK ASSIGN/REASSIGN/UNASSIGN |
| previous_employee_id | INTEGER FK employees RESTRICT | YES | |
| new_employee_id | INTEGER FK employees RESTRICT | YES | NULL only for UNASSIGN |
| actor_user_id | VARCHAR(255) | YES | **No FK** (users excluded from Alembic) |
| actor_role | VARCHAR(50) | YES | |
| reason_code | VARCHAR(64) | YES | Backfill uses `INITIAL_ASSIGNMENT_BACKFILL` |
| reason_note | VARCHAR(500) | YES | |
| task_state_at_transition | VARCHAR(64) | YES | |
| eligibility_* | VARCHAR | YES | |
| request_id / correlation_id | VARCHAR(64) | YES | |
| expected_current_employee_id | INTEGER | YES | Phase B CAS echo |
| source | VARCHAR(64) | YES | `LEGACY_EMBEDDED_BACKFILL` |
| command_version | VARCHAR(32) | YES | |
| metadata_json | TEXT | YES | Only `embedded_assignment_source` when present |
| created_at | DateTime(tz) | NO | Preserved from assignment_updated_at when available |

Indexes (migration): `ix_exec_task_assign_tr_*` including composite `(execution_plan_id, task_key, id)`.

QA note: brief create_all (empty table, 0 rows) appeared before controlled upgrade while writers were still up; upgrade skipped recreate, added migration indexes, then backfilled. Documented; no operational task mutation.

## Transition ID strategy

```text
UUID5(
  namespace=6b0f3e2a-8c1d-4f5a-9e7b-2d4c8a1f0b3e,
  name=workos:execution_task_assignment_transition:legacy_embedded_backfill:v1
        :{plan_id}:{task_key}:{employee_id}:{assignment_updated_at or ''}
)
```

Re-run → same ID → skip insert.

## Backfill inventory (pre-migration)

| Metric | Value |
| ------ | ----- |
| Plans scanned | 21 |
| Operational tasks | 177 |
| Current assignments | **7** |
| Malformed | 0 |
| Expected rows | 7 |

Known documented fixtures (not unexpected unknowns):

1. 880750/23 Wave 7 LED→7 `canonical_controlled_assign_v1`
2. 973019/21 golden-pilot `controlled_ops_graph_assign_v1` (Wave 3 noted)
3. 23099/4 ×3 and 23150/5 ×2 historical Mobile/operator lab assignments

## Backfill execution

| Metric | Value |
| ------ | ----- |
| Rows inserted | 7 |
| Idempotent re-run | 7 → 7 |
| Wave 7 row | ASSIGN, previous=null, new=7, actor preserved, source=LEGACY_EMBEDDED_BACKFILL, reason=INITIAL_ASSIGNMENT_BACKFILL |
| tasks_json SHA | unchanged `00ee947c…c1f2` |
| plan updated_at | unchanged `2026-08-04 19:16:57.407320` |

## Consistency

```text
fail_closed = False
match_count = 177 (incl. unassigned NO_HISTORY)
mismatch_count = 0
Wave 7 = CURRENT_ASSIGNMENT_WITH_BACKFILLED_HISTORY
```

## Isolated tests

```text
command: pytest -q tests/test_finalization_wave10_assignment_transition_schema.py
suite: Wave 10 Phase A
passed: 11
failed: 0
skipped: 0
DB engine: sqlite (tmp + IsolatedDBFixture)
classification: ISOLATED_ONLY
```

## QA migration proof

| Step | Result |
| ---- | ------ |
| Stop writers | stop-dev + stop :8002 (Owner-authorized for this GO) |
| Backup | `backend/_qa_backups/wave10_phase_a/dev.db.before_s63_*` (gitignored/untracked) |
| Upgrade | `s63` upgrade() + stamp alembic_version |
| Rows | 7 |
| Consistency | MATCH |
| Retry | no duplicates |

### Mutation budget

```text
AUTHORIZED_TABLES_CREATED = 1
AUTHORIZED_INDEXES_CREATED = 6 migration-named (+ ORM auto indexes from incidental create_all)
AUTHORIZED_CONSTRAINTS_CREATED = UNIQUE transition_id + 2 CHECK + 3 FK RESTRICT
AUTHORIZED_TRANSITION_ROWS_BACKFILLED = 7
OPERATIONAL_TASK_MUTATIONS = 0
ASSIGNED_EMPLOYEE_CHANGES = 0
ASSIGNMENT_REQUESTS = 0
REASSIGNMENT_REQUESTS = 0
UNASSIGNMENT_REQUESTS = 0
SESSION_MUTATIONS = 0
```

## Protected state

| Field | Before | After |
| ----- | ------ | ----- |
| order/plan | 880750 / 23 | same |
| ops / assigned / unassigned | 13 / 1 / 12 | same |
| LED employee | 7 | 7 |
| tasks_json SHA | `00ee947c…c1f2` | same |
| updated_at | `2026-08-04 19:16:57.407320` | same |
| sessions / machines | 0 | 0 |
| scheduling / capacity | HOLD / NOT_STARTED | same |
| latest transition | n/a | new_employee_id=7 MATCH |

```text
PROTECTED_ROW_STATE = UNCHANGED
GLOBAL_DB_FILE_SHA_PRE_CONTROLLED_MIG = 231f3d1e09099372aa2c94ea1a661d28ff5857fe43417c308c0c06a3b6cc4c4c
GLOBAL_DB_FILE_SHA_CHANGE_ATTRIBUTION =
  pre-mig drift from live uvicorn create_all of empty transition table;
  controlled mig = 7 backfill rows + alembic_version + migration indexes
GLOBAL_ZERO_MUTATION = NOT_CLAIMED_FOR_FILE
```

## Protected baselines / F7I

880811 plan 22 · 973019 plan 21 · 88002 absent — plan identities/timestamps unchanged.  
F7I 15 / 1.5 / 35 / 20 EUR untouched.

## Runtime / UI

`FRONTEND_CHANGED = NO`. No reassignment/unassignment controls. Stack restarted detached after migration for read-only continuity only.

## Dead Pieces Check

Classified unchanged; **removed: NONE**.

## Remaining risks

- QA DB had create_all empty table before stamp (documented).
- Production URL not in repo — dialect support is code-level only.
- Dual index naming (ORM + migration) on QA — harmless.
- Phase B dual-write not present — history can drift if assign path mutates without transitions until Phase B.

## Scores

```text
Direction alignment score: 94/100
Operational completion score: 55/100
```

(Schema+backfill done; reassignment/unassignment still absent.)

## Next step

```text
FUTURE CANDIDATE:
PHASE_B_CONTROLLED_PRE_START_REASSIGNMENT_BACKEND_IMPLEMENTATION
```

Do not start Phase B without Owner GO.
