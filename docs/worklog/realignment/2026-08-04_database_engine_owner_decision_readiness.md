# Database Engine Owner Decision — Readiness Pack

**Task:** `DATABASE_ENGINE_OWNER_DECISION_ONLY`  
**Date:** 2026-08-04  
**Branch:** `feat/f7i-owner-rate-activation`  
**HEAD at docs commit:** (see git)  
**Starting tip before this task:** `f51148fe`

---

## Verdict

```text
DATABASE_ENGINE_DECISION_READINESS = COMPLETE
RECOMMENDED_DATABASE_ENGINE_DECISION =
SQLITE_IS_CANONICAL_FOR_CURRENT_PRODUCT_FREEZE
OWNER_DECISION_RECORDED = NO
FINALIZATION_WAVE_10 = PARTIAL_BLOCKED
PHASE_B = NOT_AUTHORIZED
QA_MUTATIONS = 0
```

Owner ACCEPT of Wave 10 technical closure is retained. Remaining blocker is **deployment architecture decision**, not further migration implementation.

Scores (Owner-adjusted):

```text
Direction alignment score: 94/100
Operational completion score: 72/100
```

---

## Repo identity

| Item | Value |
| ---- | ----- |
| Repo root | `C:\w\psiso` |
| Worktree | linked gitdir `workos_app_vs/.git/worktrees/psiso` |
| Branch | `feat/f7i-owner-rate-activation` |
| Tip before docs | `f51148fe` |
| Prior Wave 10 closure | `22d6193b` / `8222f716` / `f51148fe` |

Tracked dirty at start: none for this task (docs-only). Untracked `docs/qa/**`, `_qa_backups/**` ignored (not staged).

---

## Sources inspected (read-only)

| Source | Finding |
| ------ | ------- |
| `backend/.env.example` | SQLite `./dev.db`; warns not for staging/production secrets |
| `.env.example` | SQLite `./backend/dev.db` |
| `ENVIRONMENT_NOTES.md` | Local = SQLite; table says production “PostgreSQL / managed DB (**typical**)” — aspirational, not a manifest |
| `INSTALL_LOCAL.md` | SQLite only |
| `AGENTS.md` | Dev/test helpers inject SQLite; freeze = reference laboratory |
| `scripts/dev.ps1`, `start-dev.ps1`, `dev-backend.ps1`, `dev-detached.ps1`, `test-backend.ps1`, `template-lifecycle.ps1` | Hardcode SQLite `DATABASE_URL` |
| `start_app.sh` | SQLite |
| `backend/core/database.py` | Supports sqlite+aiosqlite and postgresql+asyncpg rewrite; Lambda/Neon comments |
| `backend/core/config.py` | Requires `DATABASE_URL`; no engine default beyond env |
| `backend/requirements.txt` | `asyncpg>=0.29.0` present |
| Docker / compose | **None** found |
| `.github/workflows/ci.yml` | No PostgreSQL service; backend smoke pytest without PG |
| `backend/release.json` | Label `staging` / BUILD_25; **no database engine** |
| `docs/freeze/CURRENT_WORKOS_FROZEN_AS_REFERENCE.md` | Laboratory / reference freeze; no PG deploy |
| Alembic `env.py` | `render_as_batch=True`; URL from `DATABASE_URL` |
| Backup worklogs (2026-07-15) | SQLite file backup/restore proven |
| Architecture notes mentioning PG | Capability / “typical” language only |

No production credentials opened. No QA schema/data writes.

---

## Environment matrix (summary)

| Environment | Engine | Classification | Canonical? |
| ----------- | ------ | -------------- | ---------- |
| Development | SQLite | CONFIGURED + USED_AT_RUNTIME | yes (candidate) |
| Tests | SQLite isolated / helpers | CONFIGURED + USED_AT_RUNTIME | yes for current proofs |
| QA | SQLite `dev.db` | CONFIGURED + USED_AT_RUNTIME | yes (candidate) |
| Staging | unknown DB; label only | DOCUMENTED_ONLY / UNKNOWN | no |
| Production | no rollout in-repo | UNKNOWN as cloud; freeze NOT_AUTHORIZED | n/a |

PostgreSQL: `SUPPORTED_IN_CODE` only.

---

## Recommendation — Option A

```text
RECOMMENDED_DATABASE_ENGINE_DECISION =
SQLITE_IS_CANONICAL_FOR_CURRENT_PRODUCT_FREEZE
```

Satisfies decision rule:

- all **active** environments use SQLite;
- no **authoritative** production PostgreSQL configuration;
- current freeze is local/QA laboratory reference;
- SQLite backup/restore and concurrency limits are acknowledged in architecture boundary doc.

Does **not** invent production scale claims. Future PG remains a separate Owner program.

---

## Wave 10 / Phase B implications

| If Owner confirms… | Wave 10 | Phase B |
| ------------------ | ------- | ------- |
| SQLite freeze (A) | May become `PASS` with `CURRENT_DEPLOYMENT_DATABASE_MIGRATION_RUNTIME=VERIFIED_SQLITE` | Still **NOT_AUTHORIZED** |
| PostgreSQL target (B) | Remains `PARTIAL_BLOCKED`; need `WAVE_10_POSTGRESQL_MIGRATION_RUNTIME_PROOF` | **NOT_AUTHORIZED** |
| Undecided (C) | Remains `PARTIAL_BLOCKED`; `DATABASE_DEPLOYMENT_ARCHITECTURE_NOT_DECIDED` | **NOT_AUTHORIZED** |

Until Owner records a decision, keep:

```text
FINALIZATION_WAVE_10 = PARTIAL_BLOCKED
OWNER_DECISION_RECORDED = NO
PHASE_B = NOT_AUTHORIZED
```

---

## Zero mutation proof (QA RO)

| Metric | Value |
| ------ | ----- |
| order | 880750 |
| plan | 23 |
| LED employee | 7 |
| assigned / unassigned | 1 / 12 |
| tasks_json SHA | `00ee947c0b5e2da587c0d0563f1051ca89379d66cfec434e75dbe3883ccfc1f2` |
| updated_at | `2026-08-04 19:16:57.407320` |
| transition rows | 7 |
| QA_TRANSITION_ROW_FINGERPRINT | `bea29ac2e60690f78efa6d399972d0132145be05eae00a4c1a13d33c43f3ee4b` |
| QA_DB_FILE_SHA | `0023d2fb98145587a13d1117f13dac39c3c648aec7484ea7122560e7d846d1c2` |
| sessions | 0 (unchanged policy) |
| scheduling | HOLD |
| capacity | NOT_STARTED |

```text
ASSIGNMENT_REQUESTS = 0
REASSIGNMENT_REQUESTS = 0
UNASSIGNMENT_REQUESTS = 0
QA_DB_SCHEMA_MUTATIONS = 0
QA_DB_DATA_MUTATIONS = 0
```

---

## Protected baselines / F7I

| Baseline | Factual in QA `dev.db` |
| -------- | ---------------------- |
| 880811 | present (`ORD-F7B-880811`, plan 22) |
| 973019 | present (`ORD-IV6-V2-…`, plan 21) |
| 88002 | **ABSENT** in current QA DB (no `orders.id` / `orders.code` match) — not mutated by this task |
| 880750 | present (protected Wave fixture) |

F7I rates unchanged in `commercial_rules_volumetric_v2.py`:

```text
BACK_CNC = 15.0 EUR/m²
LED_MODULE = 1.5 EUR/buc
PSU = 35.0 EUR/buc
AMBALARE = 20.0 EUR/set
currency = EUR
4/4 identities retained
```

---

## Dead Pieces Check (nothing removed)

| Piece | Classification |
| ----- | -------------- |
| unused PostgreSQL configuration (none present) | N/A / UNKNOWN as deploy config |
| `asyncpg` dependency | `SUPPORTED_NOT_ACTIVE` |
| SQLite-specific helpers / scripts | `ACTIVE_CANONICAL` (candidate) |
| `create_all` runtime paths | `ACTIVE_LEGACY` for non-owned tables; Alembic-owned skip = `ACTIVE_CANONICAL` guard |
| legacy manual alembic_version SQL (Wave 10 QA history) | `SUPERSEDED` by Alembic CLI / stamp tool |
| duplicate QA indexes (ORM + migration names) | `ACTIVE_LEGACY` debt; Owner GO to normalize |
| ENVIRONMENT_NOTES “typical PostgreSQL” | `DOCUMENTED_ONLY` aspiration |
| Lambda / Neon code branches | `SUPPORTED_NOT_ACTIVE` |

---

## Files

- `docs/architecture/DATABASE_ENGINE_AND_MIGRATION_VALIDATION_BOUNDARY.md` (new)
- `docs/worklog/realignment/2026-08-04_database_engine_owner_decision_readiness.md` (this file)
- pointer update: `docs/architecture/realignment/21_WORKOS_IMPLEMENTATION_ROUTE.md`

---

## Next step (Owner only)

```text
OWNER DECISION:
SQLITE_CURRENT_FREEZE
```

Alternate if Owner rejects recommendation:

```text
OWNER DECISION:
POSTGRESQL_TARGET
```

or:

```text
OWNER DECISION:
DATABASE_ARCHITECTURE_REQUIRED
```

Do not start Phase B.
