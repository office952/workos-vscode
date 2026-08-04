# Database Engine and Migration Validation Boundary

**Status:** DECISION READINESS — Owner confirmation required  
**Date:** 2026-08-04  
**Task:** `DATABASE_ENGINE_OWNER_DECISION_ONLY`  
**Owner decision recorded:** `NO`

---

## 1. Purpose

Establish the factual deployment database truth for the current WorkOS product freeze and the migration validation boundary before Phase B.

This document does **not** authorize Phase B, reassignment, unassignment, schema changes, or production connection.

---

## 2. Recommended decision (evidence-based; not Owner GO)

```text
RECOMMENDED_DATABASE_ENGINE_DECISION =
SQLITE_IS_CANONICAL_FOR_CURRENT_PRODUCT_FREEZE

OWNER_DECISION_RECORDED = NO
```

### Why not PostgreSQL as confirmed target

- No Docker Compose / Dockerfile PostgreSQL service in this repo.
- No production/staging `DATABASE_URL` template with a real host.
- CI (`.github/workflows/ci.yml`) does not provision or test PostgreSQL.
- `asyncpg` in `requirements.txt` and `DatabaseManager` URL normalization prove **code capability only**.
- `ENVIRONMENT_NOTES.md` row “Production → PostgreSQL / managed DB (typical)” is **aspirational export guidance**, not an authoritative deployment manifest for this freeze.

### Why not “not yet decided”

Active, scripted, documented, and QA-used environments all resolve to SQLite file URLs. Absence of a future multi-node production architecture is not the same as absence of a current deployment engine.

---

## 3. Canonical statements (pending Owner confirm of Option A)

If Owner confirms SQLite freeze:

```text
DATABASE_ENGINE_DECISION =
SQLITE_IS_CANONICAL_FOR_CURRENT_PRODUCT_FREEZE

CURRENT_PRODUCT_DATABASE = SQLite
DATABASE_SCOPE = current product freeze only
CURRENT_DEPLOYMENT_DATABASE =
SQLITE_FOR_CURRENT_PRODUCT_FREEZE

CURRENT_DEPLOYMENT_DATABASE_MIGRATION_RUNTIME =
VERIFIED_SQLITE

MIGRATION_OWNER = Alembic
CREATE_ALL_PRODUCTION_SCHEMA_OWNERSHIP = forbidden
  (for ALEMBIC_OWNED_TABLES; see core/schema_ownership.py)

MULTI_NODE_DATABASE_WRITES = NOT_SUPPORTED_OR_NOT_PROVEN
SELECT_FOR_UPDATE_SEMANTICS = LIMITED_BY_SQLITE
PROCESS_CONCURRENCY = single-writer SQLite file; app uses async SQLAlchemy;
  multi-process writers NOT_PROVEN for this freeze
BACKUP_POLICY = file-level copy of backend/dev.db (and forensic/backup copies);
  proven in BACKUP-BASELINE worklogs; not HA replication
RECOVERY_POLICY = restore SQLite file to isolated path + start stack with
  DATABASE_URL pointing at restored file
DATABASE_FILE_LOCATION = configuration-driven via DATABASE_URL
  (scripts default to <backend>/dev.db)

POSTGRESQL_SUPPORT_IN_CODE = SUPPORTED_NOT_ACTIVE
FUTURE_POSTGRESQL_MIGRATION = requires separate Owner program + runtime proof
```

If Owner instead confirms PostgreSQL target:

```text
FINALIZATION_WAVE_10 = PARTIAL_BLOCKED
BLOCKER = POSTGRESQL_MIGRATION_RUNTIME_NOT_VERIFIED
Required next task: WAVE_10_POSTGRESQL_MIGRATION_RUNTIME_PROOF
PHASE_B = NOT_AUTHORIZED
```

If Owner leaves architecture undecided:

```text
FINALIZATION_WAVE_10 = PARTIAL_BLOCKED
BLOCKER = DATABASE_DEPLOYMENT_ARCHITECTURE_NOT_DECIDED
PHASE_B = NOT_AUTHORIZED
```

---

## 4. Environment matrix

| Environment | Engine configured | Source | Classification | Runtime proof | Canonical for freeze? |
| ----------- | ----------------- | ------ | -------------- | ------------- | --------------------- |
| Development | SQLite `sqlite+aiosqlite://…/dev.db` | `scripts/dev.ps1`, `start-dev.ps1`, `dev-backend.ps1`, `dev-detached.ps1`, `start_app.sh`, `.env.example`, `backend/.env.example`, `INSTALL_LOCAL.md`, `ENVIRONMENT_NOTES.md` | `CONFIGURED` + `USED_AT_RUNTIME` | Live Owner stack / detached scripts use SQLite file | **yes** (candidate) |
| Tests | SQLite (isolated tmp or fixture DB); CI backend job sets `APP_ENV=test` without PG service | `scripts/test-backend.ps1`, `_db_fixture.py`, Wave 10 isolated tests, `.github/workflows/ci.yml` | `CONFIGURED` (local helpers) / CI tests often self-scoped | Wave 10 canonical migration tests on isolated SQLite | **yes** for migration proof of current engine |
| QA | SQLite `backend/dev.db` | Same launch scripts; Wave audits | `CONFIGURED` + `USED_AT_RUNTIME` | Protected fixture 880750 / plan 23 / 7 transitions | **yes** (candidate) |
| Staging | Label `staging` in `backend/release.json`; **no DB URL** | `release.json` environment field only | `DOCUMENTED_ONLY` (label) / DB engine `UNKNOWN` | No in-repo staging DB proof | **no** |
| Production | No production `DATABASE_URL`; freeze = laboratory/reference | `docs/freeze/CURRENT_WORKOS_FROZEN_AS_REFERENCE.md`; AGENTS.md freeze note | Production rollout `NOT_AUTHORIZED` / engine `UNKNOWN` as cloud deploy; **not** proven PostgreSQL | None in-repo | **n/a — no production rollout** |

### Code support (not deployment truth)

| Capability | Classification |
| ---------- | -------------- |
| `sqlite` / `aiosqlite` | `ACTIVE_CANONICAL` for current freeze (pending Owner confirm) |
| `postgresql+asyncpg` URL rewrite in `DatabaseManager` | `SUPPORTED_NOT_ACTIVE` |
| `asyncpg` dependency | `SUPPORTED_NOT_ACTIVE` |
| Neon `channel_binding` sanitize comment | `SUPPORTED_NOT_ACTIVE` (provider hint only) |
| Lambda NullPool branch | `SUPPORTED_NOT_ACTIVE` (runtime path exists; no deploy manifest) |
| Alembic `render_as_batch=True` | Compatible with SQLite; also used for portable migrations |

---

## 5. Answers to required questions

| # | Question | Answer |
| - | -------- | ------ |
| 1 | Real production deployment in this repo? | **No** authoritative deploy pipeline with DB. Freeze declares laboratory/reference. Production rollout **NOT_AUTHORIZED**. |
| 2 | Server configuration source? | **UNKNOWN** / absent for cloud servers. Local scripts are the active config source. |
| 3 | Production `DATABASE_URL` documented? | **No** real URL. Examples are SQLite. Placeholder PG strings appear only in secret-scan tests. |
| 4 | Backup/restore policy for SQLite? | **Yes (file-level)** — BACKUP-BASELINE worklogs; copy `dev.db`; integrity via SQLite APIs. Not HA. |
| 5 | PostgreSQL service/configuration? | **No** in-repo service. |
| 6 | Is `asyncpg` used at runtime or only available? | **Available / supported in code.** Active Owner/QA/dev paths use SQLite. No evidence of live PG runtime in this freeze. |
| 7 | CI tests PostgreSQL? | **No.** |
| 8 | Migration runbook for PostgreSQL? | **No** dedicated PG runbook. Alembic is dialect-portable in principle; runtime PG proof absent. |
| 9 | WorkOS local/development/QA only now? | **Yes** for active use — local stack + QA SQLite. |
| 10 | Can freeze declare SQLite official without contradicting authoritative source? | **Yes.** Only non-authoritative “typical production = PostgreSQL” language exists; it does not configure a PG target. |

---

## 6. Wave 10 implication

Current (until Owner records decision):

```text
FINALIZATION_WAVE_10 = PARTIAL_BLOCKED
BLOCKER = PRODUCTION_DATABASE_ENGINE_NOT_IDENTIFIED_IN_REPO
  (more precisely: CURRENT_DEPLOYMENT_DATABASE not Owner-recorded)
PHASE_B = NOT_AUTHORIZED
```

After Owner confirms Option A (SQLite freeze):

```text
FINALIZATION_WAVE_10 = PASS
CURRENT_DEPLOYMENT_DATABASE = SQLITE_FOR_CURRENT_PRODUCT_FREEZE
CURRENT_DEPLOYMENT_DATABASE_MIGRATION_RUNTIME = VERIFIED_SQLITE
PHASE_B = NOT_AUTHORIZED
```

Prefer “current deployment” over “production” unless a production rollout exists.

---

## 7. Phase B gate

```text
PHASE_B = NOT_AUTHORIZED
```

Even after Wave 10 PASS under SQLite freeze, Phase B requires a separate Owner GO.  
SQLite freeze acknowledges concurrency limits (`SELECT FOR UPDATE` / multi-writer) for any future reassignment design.

---

## 8. Future PostgreSQL program (only if Owner chooses Option B later)

Required proof task (not started here):

```text
WAVE_10_POSTGRESQL_MIGRATION_RUNTIME_PROOF
```

Minimum isolated proof: baseline/prior → s63 table, constraints, UUID, FK, indexes, backfill, idempotency, downgrade/re-upgrade — no production credentials.

---

## 9. Related

- Wave 10 closure: `docs/worklog/realignment/2026-08-04_finalization_wave10_canonical_migration_closure.md`
- Schema ownership: `backend/core/schema_ownership.py`
- Implementation route pointer: `docs/architecture/realignment/21_WORKOS_IMPLEMENTATION_ROUTE.md`
- Worklog: `docs/worklog/realignment/2026-08-04_database_engine_owner_decision_readiness.md`
