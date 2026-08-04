# Finalization Wave 10 — Canonical Migration Closure

**Task:** `FINALIZATION_WAVE_10_CANONICAL_MIGRATION_CLOSURE`  
**Date:** 2026-08-04  
**Branch:** `feat/f7i-owner-rate-activation`  
**Starting HEAD:** `02dcab8f`  
**Closure commits:** `22d6193b` (code/tests), `8222f716` (evidence worklog)  
**Worktree:** `C:\w\psiso` (gitdir → `workos_app_vs/.git/worktrees/psiso`)

---

## Verdict

```text
FINALIZATION_WAVE_10 = PARTIAL_BLOCKED
PHASE_A_SCHEMA_OBJECTS = IMPLEMENTED
QA_BACKFILL = VERIFIED
CANONICAL_ALEMBIC_UPGRADE_CHAIN = VERIFIED_SQLITE_ISOLATED
ALEMBIC_SCHEMA_OWNERSHIP = VERIFIED
CREATE_ALL_PRODUCTION_BYPASS = CLOSED_FOR_ALEMBIC_OWNED_TABLES
MIGRATION_ANCESTRY = VERIFIED
FRESH_DATABASE_MIGRATION = VERIFIED_SQLITE
PRIOR_REVISION_TO_HEAD = VERIFIED_SQLITE
BACKFILL_IDEMPOTENCY = VERIFIED
DUPLICATE_INDEXES = RESOLVED_FOR_FRESH_PATH
DOWNGRADE_REUPGRADE = VERIFIED_ISOLATED_SQLITE
PRODUCTION_DATABASE_ENGINE = NOT_IDENTIFIED_IN_REPO
PRODUCTION_DATABASE_MIGRATION_RUNTIME = NOT_VERIFIED
BLOCKER = PRODUCTION_DATABASE_ENGINE_NOT_VERIFIED
QA_OPERATIONAL_STATE = UNCHANGED
PHASE_B = NOT_AUTHORIZED
```

Wave 10 Phase A operational proof (7 QA rows, consistency MATCH) remains valid.
This closure task proved the **canonical Alembic path on isolated SQLite** and closed
runtime `create_all` bypass for the transition table. Pass is blocked solely by
inability to identify / exercise a production database engine runtime (PostgreSQL
or otherwise) from repo configuration.

---

## Repo integrity incident

| Field | Evidence |
| ----- | -------- |
| Exact failure | During evidence-closure docs commit, branch ref file briefly contained **41 null bytes** instead of a SHA; subsequent git operations failed / staged mass accidental paths |
| Affected ref | `refs/heads/feat/f7i-owner-rate-activation` (main repo: `C:\Users\offic\workos_app_vs\.git\refs\heads\...`) |
| Timestamp | Same session as evidence-closure commits (2026-08-04), immediately before recovery to `a5394688` then tip `02dcab8f` |
| Reflog after recovery | Worktree HEAD reflog shows continuous chain `d393b27f` … `02dcab8f` |
| Recovered commit | Ref rewritten to `a53946881418c40b1a024b580c971b3430774583` |
| Recovery command | Write SHA + newline into branch ref file; verify `git rev-parse` / `git log` from worktree |
| Final branch target | `02dcab8f` at task start; tip advanced by this closure’s commits |
| `git fsck` | Reports preexisting invalid **main-worktree/HEAD** reflog entries (shared-repo noise). Branch tip objects for this worktree are reachable |
| Ancestry checkpoints | `d393b27f`, `bbb4c466`, `73ed6592`, `9eef4414`, `02dcab8f` all ancestors of HEAD at start |
| Lost commits | **NONE** |
| Lost files | **NONE** |

```text
REPO_COMMIT_CHAIN = VERIFIED
LOST_COMMITS = NONE
LOST_FILES = NONE
```

---

## Schema ownership inventory

### Decision

```text
ALEMBIC_OWNS_PRODUCTION_SCHEMA = YES
  (for ALEMBIC_OWNED_TABLES; currently execution_task_assignment_transitions)

RUNTIME_CREATE_ALL_MAY_CREATE_LEGACY_TABLES = YES
  (historical DatabaseManager path; not used for Alembic-owned tables)

ISOLATED_TEST_CREATE_ALL = ALLOWED
  (IsolatedDBFixture / direct Base.metadata.create_all)
```

### `create_all` callers

| Caller | Environment | Database | Models | When | Checks revision? | Can create prod tables? |
| ------ | ----------- | -------- | ------ | ---- | ---------------- | ----------------------- |
| `DatabaseManager.create_tables` → `_runtime_create_all` | all via `initialize_database` | configured `DATABASE_URL` | all registered except `ALEMBIC_OWNED_TABLES` | app/seed startup | no | **No** for Alembic-owned; yes for other ORM tables (legacy) |
| `DatabaseManager.check_and_repair_existing_tables` | development/local/dev/test | same | existing non-owned tables only | before create_all | no | ALTER only; **skips** Alembic-owned |
| `tests/_db_fixture.py` IsolatedDBFixture | test | isolated | full metadata | fixture setup | no | N/A (isolated) |
| Seeds (`seed_tpl_*`, backfill scripts) | script | target URL | via `create_tables` | script boot | no | same as DatabaseManager |
| Historical QA path | development uvicorn | `backend/dev.db` | previously included transition table | live boot after model import | no | **was yes** — closed by this task |

### Correction applied

- New module `backend/core/schema_ownership.py` lists `ALEMBIC_OWNED_TABLES`.
- Runtime `create_all` **excludes** those tables in every environment.
- Repair **skips** those tables.
- Explicit stamp tool: `backend/scripts/stamp_alembic_revision_after_parity.py` (never raw SQL stamp in app code).

---

## Alembic graph / s63

| Field | Value |
| ----- | ----- |
| revision | `s63_execution_task_assignment_transitions` |
| down_revision | `s62_material_actuals_closed_job_v1` |
| branch_labels | none |
| depends_on | none |
| current heads | single: `s63_...` |
| multiple heads | no |
| merge revisions | historical merges exist earlier (`s31`, `s61`); s63 is linear after s62 |

Manual `alembic_version` SQL is **not** treated as ancestry proof. Ancestry is from `ScriptDirectory` + isolated `alembic upgrade`.

---

## Fresh migration (Scenario A)

Isolated empty SQLite → `alembic upgrade head`:

- Full prior revision chain executed (including merges).
- s63 executed once; table created by migration.
- Canonical indexes only (`ix_exec_task_assign_tr_*`); **zero** legacy ORM auto-names.
- Backfill rows = 0 on empty data.
- `alembic_version` = s63.

Automated: `test_scenario_a_fresh_empty_database_upgrade_head`.

---

## Prior revision → head (Scenario B)

Isolated SQLite at s62 → seed one embedded assignment → `alembic upgrade head`:

- Table absent before; present after.
- Exactly 1 synthetic ASSIGN backfill row.
- `tasks_json` / `updated_at` unchanged.
- Revision advanced by Alembic to s63.

Automated: `test_scenario_b_prior_revision_to_head_backfill`.

---

## Collision recovery

Policy:

```text
_table_exists skip-create = legitimate recovery compatibility
  (not a mask for missing parity — column parity fail-closed)

Missing canonical indexes = created by s63 upgrade
Legacy ORM duplicate index names = retained if present; drop only with Owner GO + backup
Revision stamping = Alembic CLI / stamp tool only — not migration body, not app SQL
```

Isolated proof: s62 → ORM `create_all` of transition table → `alembic upgrade head` succeeds, backfills once, revision = s63.

QA DB already has duplicate index **names** (ORM + migration). **No destructive index drop on QA** in this task.

Normalization plan (future Owner GO):

1. Backup QA DB.
2. Confirm column equivalence of legacy `ix_execution_task_assignment_transitions_*` vs canonical `ix_exec_task_assign_tr_*`.
3. Drop legacy names only; keep canonical.
4. Re-fingerprint schema.

---

## Index inventory

| Name | Columns | Source | Fresh path | QA live |
| ---- | ------- | ------ | ---------- | ------- |
| `ix_exec_task_assign_tr_transition_id` | transition_id | Alembic + ORM Index | yes | yes |
| `ix_exec_task_assign_tr_plan_id` | execution_plan_id | Alembic + ORM Index | yes | yes |
| `ix_exec_task_assign_tr_order_id` | order_id | Alembic + ORM Index | yes | yes |
| `ix_exec_task_assign_tr_task_key` | task_key | Alembic + ORM Index | yes | yes |
| `ix_exec_task_assign_tr_source` | source | Alembic + ORM Index | yes | yes |
| `ix_exec_task_assign_tr_plan_task_id` | plan, task_key, id | Alembic + ORM Index | yes | yes |
| `ix_execution_task_assignment_transitions_*` (5) | same singles | historical ORM `index=True` | **no** (fixed) | **yes (duplicate)** |
| `uq_exec_task_assign_transition_id` / sqlite autoindex | transition_id unique | constraint | yes | yes |

Canonical source: Alembic s63 names; ORM mirrors via `CANONICAL_ASSIGNMENT_TRANSITION_INDEXES` (no `Column(index=True)`).

---

## Backfill

| Check | Result |
| ----- | ------ |
| First migration run | inserts expected rows |
| Second backfill | inserted=0, skipped_existing=N |
| Deterministic UUID5 identity | stable |
| No `tasks_json` / `updated_at` writes | verified in isolated + QA RO |

Conceptual separation: schema create → backfill → consistency verify → revision stamp (Alembic-owned).

---

## Downgrade / re-upgrade (isolated only)

s62 → seed → upgrade s63 → downgrade s62 → upgrade s63:

- Embedded plan unchanged across downgrade.
- Transition table removed on downgrade (**history destroyed** — pre-Phase B only).
- Re-upgrade recreates deterministic backfill row.

**Never executed on QA `dev.db`.**

---

## Production DB identification

| Source | Finding |
| ------ | ------- |
| `backend/.env.example` | `sqlite+aiosqlite:///./dev.db` |
| `core/config.py` / `DatabaseManager` | supports sqlite+aiosqlite and postgresql+asyncpg |
| Docker/compose in repo | no PostgreSQL service found |
| Deploy/service manifests | no production `DATABASE_URL` in-repo |
| Host tooling | `pg_isready` / `docker` / `psql` not available |

```text
PRODUCTION_DATABASE_ENGINE = NOT_IDENTIFIED_IN_REPO
CODE_SUPPORTS = sqlite | postgresql+asyncpg
LOCAL_CANONICAL_EVIDENCE = sqlite
POSTGRESQL_RUNTIME_MIGRATION = NOT_VERIFIED
```

Code review ≠ runtime parity. Test `test_postgresql_canonical_upgrade_if_available` skips unless `WORKOS_ISOLATED_POSTGRES_URL` is set.

---

## QA read-only verification (before = after)

| Metric | Value |
| ------ | ----- |
| order | 880750 |
| plan | 23 |
| operational tasks | 13 |
| LED employee | 7 |
| assigned / unassigned | 1 / 12 |
| tasks_json SHA | `00ee947c0b5e2da587c0d0563f1051ca89379d66cfec434e75dbe3883ccfc1f2` |
| updated_at | `2026-08-04 19:16:57.407320` |
| transition rows | 7 |
| consistency | MATCH (prior Wave 10 proof; RO recheck counts/fingerprint) |
| sessions | 0 |
| machine assignments | 0 |
| scheduling | HOLD |
| capacity | NOT_STARTED |

```text
QA_DB_FILE_SHA = 0023d2fb98145587a13d1117f13dac39c3c648aec7484ea7122560e7d846d1c2
QA_SCHEMA_FINGERPRINT = 465fe46fef4e67b0dbae04dc416c209f43b87bc56ee106738d970ce1cf72de49
QA_TRANSITION_ROW_FINGERPRINT = bea29ac2e60690f78efa6d399972d0132145be05eae00a4c1a13d33c43f3ee4b
```

No transition rows deleted; no new QA backfill; no `alembic_version` edit; no `dev.db` rebuild.

---

## Tests

```text
command:
  cd backend && python -m pytest -q \
    tests/test_finalization_wave10_canonical_migration_closure.py \
    tests/test_finalization_wave10_assignment_transition_schema.py

engine: sqlite (isolated tmp + programmatic)
passed: 19
failed: 0
skipped: 1 (PostgreSQL — WORKOS_ISOLATED_POSTGRES_URL unset)
classification: WAVE10_CANONICAL_MIGRATION_CLOSURE
```

Scenarios covered: graph, fresh head, s62→head backfill, create_all collision, downgrade/re-upgrade, backfill idempotency, ownership filter, ORM index names, PG skip.

---

## Files changed

- `backend/core/schema_ownership.py` (new)
- `backend/core/database.py` (exclude Alembic-owned from create_all/repair)
- `backend/models/execution_task_assignment_transition.py` (canonical Index names)
- `backend/alembic/versions/s63_execution_task_assignment_transitions.py` (parity fail-closed)
- `backend/scripts/stamp_alembic_revision_after_parity.py` (new explicit stamp tool)
- `backend/tests/test_finalization_wave10_canonical_migration_closure.py` (new)
- this worklog

---

## Remaining risks

1. Production engine unknown → cannot claim deploy migration runtime.
2. QA still has legacy ORM duplicate index names (non-destructive debt).
3. Runtime `create_all` still creates **non**-Alembic-owned tables (legacy bootstrap); only Alembic-owned set is closed.
4. Downgrade destroys transition history — must not run after Phase B / real usage.

---

## Scores

```text
Direction alignment score: 92/100
Operational completion score: 78/100
```

(Operational score capped by production-engine / PostgreSQL runtime blocker.)

---

## Next step

```text
Wave 10 remains PARTIAL_BLOCKED until Owner identifies production DB engine
and authorizes isolated runtime migration proof for that engine
(or formally declares SQLite-only for this reference freeze).

PHASE_B = NOT_AUTHORIZED

FUTURE CANDIDATE (only after genuine Wave 10 PASS):
PHASE_B_CONTROLLED_PRE_START_REASSIGNMENT_BACKEND_IMPLEMENTATION
```

Await Owner review.
