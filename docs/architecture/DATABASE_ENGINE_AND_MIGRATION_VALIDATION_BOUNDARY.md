# Database Engine and Migration Validation Boundary

**Status:** OWNER DECISION RECORDED  
**Date:** 2026-08-04  
**Owner decision status:** `RECORDED`  
**Decision:** `SQLITE_CURRENT_FREEZE`  
**Decision ID:** `DEC-DATABASE-01`  
**Canonical decision document:** [`SQLITE_CURRENT_PRODUCT_FREEZE_OWNER_DECISION.md`](./SQLITE_CURRENT_PRODUCT_FREEZE_OWNER_DECISION.md)

```text
Scope = current WorkOS development/test/QA freeze
Permanent production decision = NO
PostgreSQL support = SUPPORTED_NOT_ACTIVE
PostgreSQL runtime proof required now = NO
Future PostgreSQL activation gate = separate Owner program
PHASE_B = NOT_AUTHORIZED
```

This document retains the evidence matrix. The Owner GO text lives in the decision document above (single decision source — do not duplicate conflicting GO text elsewhere).

---

## 1. Purpose

Establish the factual deployment database truth for the current WorkOS product freeze and the migration validation boundary before Phase B.

This document does **not** authorize Phase B, reassignment, unassignment, schema changes, or production connection.

---

## 2. Recorded Owner decision (not a recommendation)

```text
OWNER DECISION: SQLITE_CURRENT_FREEZE = GO

DEC-DATABASE-01 =
SQLITE_IS_CANONICAL_FOR_CURRENT_PRODUCT_FREEZE

DATABASE_ENGINE_OWNER_DECISION = RECORDED
CURRENT_PRODUCT_FREEZE_DATABASE = SQLITE
CURRENT_ACTIVE_ENVIRONMENTS = development + tests + QA
PRODUCTION_ROLLOUT = NOT_AUTHORIZED
POSTGRESQL = SUPPORTED_NOT_ACTIVE
MULTI_NODE_DATABASE_WRITES = NOT_PROVEN
FUTURE_DATABASE_MIGRATION = SEPARATE_OWNER_PROGRAM
```

Do **not** use `PRODUCTION_DATABASE = SQLITE`.

### Evidence that supported the GO (historical readiness)

- No Docker Compose / Dockerfile PostgreSQL service in this repo.
- No production/staging `DATABASE_URL` template with a real host.
- CI does not provision or test PostgreSQL.
- `asyncpg` / `DatabaseManager` PG rewrite = **code capability only**.
- `ENVIRONMENT_NOTES.md` “typical PostgreSQL” = aspirational, not a deploy manifest.
- All active scripted environments resolve to SQLite file URLs.

---

## 3. Canonical statements (in force)

```text
CURRENT_PRODUCT_FREEZE_DATABASE = SQLITE
DATABASE_SCOPE = current product freeze only
CURRENT_DEPLOYMENT_DATABASE_MIGRATION_RUNTIME = VERIFIED_SQLITE
CURRENT_ACTIVE_DATABASE_RUNTIME = VERIFIED_SQLITE

MIGRATION_OWNER = Alembic
CREATE_ALL_SCHEMA_BYPASS = FORBIDDEN_FOR_OWNED_TABLES
  (ALEMBIC_OWNED_TABLES; see core/schema_ownership.py)

SQLITE_SCOPE = CURRENT_FREEZE_ONLY
SINGLE_WRITER_LIMIT = ACKNOWLEDGED
MULTI_PROCESS_WRITE_SAFETY = LIMITED_AND_DOCUMENTED
MULTI_NODE_WRITE_SAFETY = NOT_PROVEN
SELECT_FOR_UPDATE_SEMANTICS = LIMITED_BY_SQLITE
DATABASE_FILE_BACKUP_REQUIRED = YES
ALEMBIC_MIGRATION_REQUIRED = YES
BACKUP_POLICY = file-level copy of backend/dev.db (BACKUP-BASELINE); not HA
RECOVERY_POLICY = restore SQLite file + DATABASE_URL to restored path
DATABASE_FILE_LOCATION = configuration-driven via DATABASE_URL
  (scripts default to <backend>/dev.db)

POSTGRESQL_DRIVER_SUPPORT = PRESENT
POSTGRESQL_ACTIVE_DEPLOYMENT = NO
POSTGRESQL_CANONICAL_RUNTIME = NO
POSTGRESQL_MIGRATION_RUNTIME_PROOF = DEFERRED
POSTGRESQL_MIGRATION_RUNTIME = NOT_REQUIRED_FOR_CURRENT_FREEZE
```

QA legacy duplicate indexes:

```text
ACTIVE_LEGACY
NON_BLOCKING_FOR_CURRENT_FREEZE
FUTURE_NORMALIZATION_REQUIRES_OWNER_GO
```

---

## 4. Environment matrix

| Environment | Engine configured | Source | Classification | Runtime proof | Canonical for freeze? |
| ----------- | ----------------- | ------ | -------------- | ------------- | --------------------- |
| Development | SQLite `sqlite+aiosqlite://…/dev.db` | launch scripts, `.env.example`, `INSTALL_LOCAL.md`, `ENVIRONMENT_NOTES.md` | `CONFIGURED` + `USED_AT_RUNTIME` | Live Owner stack | **yes** |
| Tests | SQLite isolated / helpers | `test-backend.ps1`, fixtures, Wave 10 tests, CI | `CONFIGURED` + `USED_AT_RUNTIME` | Isolated Alembic proofs | **yes** |
| QA | SQLite `backend/dev.db` | Same launch scripts; Wave audits | `CONFIGURED` + `USED_AT_RUNTIME` | 880750 / plan 23 / 7 transitions | **yes** |
| Staging | Label only in `release.json` | no DB URL | `DOCUMENTED_ONLY` / DB `UNKNOWN` | none | **no** |
| Production | no rollout | freeze = laboratory/reference | `NOT_AUTHORIZED` | none | **n/a** |

### Code support (not deployment truth)

| Capability | Classification |
| ---------- | -------------- |
| `sqlite` / `aiosqlite` | `ACTIVE_CANONICAL` for current freeze |
| `postgresql+asyncpg` URL rewrite | `SUPPORTED_NOT_ACTIVE` |
| `asyncpg` dependency | `SUPPORTED_NOT_ACTIVE` |
| Neon `channel_binding` sanitize | `SUPPORTED_NOT_ACTIVE` |
| Lambda NullPool branch | `SUPPORTED_NOT_ACTIVE` |
| Alembic `render_as_batch=True` | portable migrations; SQLite verified |

---

## 5. Wave 10 final status (after DEC-DATABASE-01)

```text
FINALIZATION_WAVE_10 = PASS
PHASE_A_SCHEMA_AND_BACKFILL = VERIFIED
CURRENT_PRODUCT_FREEZE_DATABASE = SQLITE
CURRENT_ACTIVE_DATABASE_RUNTIME = VERIFIED_SQLITE
CURRENT_DEPLOYMENT_DATABASE_MIGRATION_RUNTIME = VERIFIED_SQLITE
CANONICAL_ALEMBIC_UPGRADE_CHAIN = VERIFIED_SQLITE_ISOLATED
ALEMBIC_SCHEMA_OWNERSHIP = VERIFIED
CREATE_ALL_PRODUCTION_BYPASS = CLOSED_FOR_ALEMBIC_OWNED_TABLES
MIGRATION_ANCESTRY = VERIFIED
FRESH_DATABASE_MIGRATION = VERIFIED_SQLITE
PRIOR_REVISION_TO_HEAD = VERIFIED_SQLITE
BACKFILL_IDEMPOTENCY = VERIFIED
DOWNGRADE_REUPGRADE = VERIFIED_ISOLATED_SQLITE
POSTGRESQL = SUPPORTED_NOT_ACTIVE
POSTGRESQL_MIGRATION_RUNTIME = NOT_REQUIRED_FOR_CURRENT_FREEZE
MULTI_NODE_CONCURRENCY = NOT_PROVEN
QA_OPERATIONAL_STATE = UNCHANGED
PHASE_B = NOT_AUTHORIZED
WAVE_11 = NOT_AUTHORIZED
```

---

## 6. Phase B gate

```text
PHASE_B = NOT_AUTHORIZED
```

Wave 10 PASS under SQLite freeze does **not** authorize Phase B. Separate Owner GO required.

---

## 7. Future PostgreSQL activation (deferred)

Not required for current freeze. When Owner later activates PostgreSQL:

```text
WAVE_10_POSTGRESQL_MIGRATION_RUNTIME_PROOF
  (or successor task name under that Owner program)
```

Minimum: authoritative deploy config + isolated upgrade/downgrade + constraint/UUID/FK/index parity + backfill idempotency + concurrency review + backup/restore + production rollout GO. No production credentials in lab proofs.

---

## 8. Related

- Owner decision (canonical): `docs/architecture/SQLITE_CURRENT_PRODUCT_FREEZE_OWNER_DECISION.md`
- Closure worklog: `docs/worklog/realignment/2026-08-04_sqlite_current_freeze_owner_decision_and_wave10_closure.md`
- Prior readiness (historical): `docs/worklog/realignment/2026-08-04_database_engine_owner_decision_readiness.md`
- Wave 10 migration closure (historical PARTIAL then superseded by this PASS): `docs/worklog/realignment/2026-08-04_finalization_wave10_canonical_migration_closure.md`
- Schema ownership: `backend/core/schema_ownership.py`
- Route: `docs/architecture/realignment/21_WORKOS_IMPLEMENTATION_ROUTE.md`
