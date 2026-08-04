# DEC-DATABASE-01 — SQLite Canonical for Current Product Freeze

**Decision ID:** `DEC-DATABASE-01`  
**Decision:** `SQLITE_IS_CANONICAL_FOR_CURRENT_PRODUCT_FREEZE`  
**Owner GO:** `SQLITE_CURRENT_FREEZE = GO`  
**Status:** `RECORDED`  
**Date:** 2026-08-04  
**Task that recorded:** `FINALIZATION_WAVE_10_SQLITE_CURRENT_FREEZE_CLOSURE`

This is the **canonical Owner decision** for the database engine of the current WorkOS freeze.  
Evidence matrix and migration validation detail live in  
[`DATABASE_ENGINE_AND_MIGRATION_VALIDATION_BOUNDARY.md`](./DATABASE_ENGINE_AND_MIGRATION_VALIDATION_BOUNDARY.md)  
(updated to recorded status; historical readiness narrative retained).

---

## 1. Decision text

```text
OWNER DECISION: SQLITE_CURRENT_FREEZE = GO

DEC-DATABASE-01 =
SQLITE_IS_CANONICAL_FOR_CURRENT_PRODUCT_FREEZE

CURRENT_PRODUCT_FREEZE_DATABASE = SQLITE
CURRENT_ACTIVE_ENVIRONMENTS = development + tests + QA
PRODUCTION_ROLLOUT = NOT_AUTHORIZED
POSTGRESQL = SUPPORTED_NOT_ACTIVE
MULTI_NODE_DATABASE_WRITES = NOT_PROVEN
FUTURE_DATABASE_MIGRATION = SEPARATE_OWNER_PROGRAM
PHASE_B = NOT_AUTHORIZED
```

Do **not** write `PRODUCTION_DATABASE = SQLITE`. Production rollout does not exist and is not authorized.

---

## 2. Meaning (eight points)

1. SQLite is the active and canonical engine for the **current** WorkOS freeze.
2. The decision applies to demonstrated **development**, **tests**, and **QA** environments.
3. It does **not** declare SQLite a permanent solution for a future production rollout.
4. It does **not** prove multi-node concurrency.
5. It does **not** prove high availability.
6. It does **not** authorize production deployment.
7. PostgreSQL remains available in code (`SUPPORTED_NOT_ACTIVE`).
8. Any PostgreSQL activation requires a separate Owner decision plus: isolated migration proof, deployment configuration, backup/restore policy, concurrency review, and rollout plan.

---

## 3. SQLite operational boundaries

```text
SQLITE_SCOPE = CURRENT_FREEZE_ONLY
SINGLE_WRITER_LIMIT = ACKNOWLEDGED
MULTI_PROCESS_WRITE_SAFETY = LIMITED_AND_DOCUMENTED
MULTI_NODE_WRITE_SAFETY = NOT_PROVEN
DATABASE_FILE_BACKUP_REQUIRED = YES
ALEMBIC_MIGRATION_REQUIRED = YES
CREATE_ALL_SCHEMA_BYPASS = FORBIDDEN_FOR_OWNED_TABLES
MIGRATION_OWNER = Alembic
```

---

## 4. PostgreSQL boundary

```text
POSTGRESQL_DRIVER_SUPPORT = PRESENT
POSTGRESQL_ACTIVE_DEPLOYMENT = NO
POSTGRESQL_CANONICAL_RUNTIME = NO
POSTGRESQL_MIGRATION_RUNTIME_PROOF = DEFERRED
POSTGRESQL_MIGRATION_RUNTIME = NOT_REQUIRED_FOR_CURRENT_FREEZE
```

Future activation gate (not started):

1. authoritative PostgreSQL deployment configuration  
2. isolated migration runtime proof  
3. s63 upgrade/downgrade proof  
4. UUID / FK / index / check parity  
5. backfill idempotency  
6. concurrency model review  
7. backup and restore policy  
8. production rollout Owner GO  

---

## 5. Schema / migration boundary (unchanged truth)

```text
Alembic owns Alembic-managed tables.
Runtime create_all must not create Alembic-owned tables.
SQLite canonical migration path is verified.
QA legacy duplicate indexes = ACTIVE_LEGACY
  NON_BLOCKING_FOR_CURRENT_FREEZE
  FUTURE_NORMALIZATION_REQUIRES_OWNER_GO
```

No destructive QA index cleanup is authorized by this decision.

---

## 6. Wave 10 status enabled by this decision

```text
FINALIZATION_WAVE_10 = PASS
PHASE_A_SCHEMA_AND_BACKFILL = VERIFIED
CURRENT_PRODUCT_FREEZE_DATABASE = SQLITE
CURRENT_ACTIVE_DATABASE_RUNTIME = VERIFIED_SQLITE
CURRENT_DEPLOYMENT_DATABASE_MIGRATION_RUNTIME = VERIFIED_SQLITE
CANONICAL_ALEMBIC_UPGRADE_CHAIN = VERIFIED_SQLITE_ISOLATED
ALEMBIC_SCHEMA_OWNERSHIP = VERIFIED
POSTGRESQL_MIGRATION_RUNTIME_PROOF = DEFERRED_UNTIL_ACTIVATION
PHASE_B = NOT_AUTHORIZED
WAVE_11 = NOT_AUTHORIZED
```

This decision closes Wave 10. It does **not** authorize Phase B.

---

## 7. Related

- Boundary / matrix: `docs/architecture/DATABASE_ENGINE_AND_MIGRATION_VALIDATION_BOUNDARY.md`
- Closure worklog: `docs/worklog/realignment/2026-08-04_sqlite_current_freeze_owner_decision_and_wave10_closure.md`
- Route: `docs/architecture/realignment/21_WORKOS_IMPLEMENTATION_ROUTE.md`
