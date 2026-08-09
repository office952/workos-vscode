# WorkOS — V1 Production Readiness Smoke Pack

**Date:** 2026-08-09  
**Starting HEAD:** `a113e89d`  
**Owner GO:** `AUTHORIZE_WORKOS_V1_PRODUCTION_READINESS_SMOKE_PACK`

## Verdict

```text
WORKOS_V1_PRODUCTION_READINESS_SMOKE_PACK = PASS
PRODUCTION_READINESS_V1 = DONE_FOR_V1
DEPLOYMENT_MODEL = single-workstation / internal laboratory (Windows)
CANONICAL_STARTUP = .\scripts\dev-detached.ps1
FRONTEND_PRODUCTION_BUILD = PASS
BACKEND_RUNTIME = PASS
DB_ENGINE = SQLite (aiosqlite)
SQLITE_V1_STATUS = ACCEPTED (DEC-DATABASE-01 + V1 single-tenant; cloud rollout NOT_AUTHORIZED)
ALEMBIC_READINESS = PASS (head s67_machine_run_execution_status)
FRESH_DB_BOOTSTRAP = PASS
EXISTING_DB_UPGRADE = PASS (full chain empty→head on disposable DB)
BACKUP_PROCEDURE = DOCUMENTED
RESTORE_SMOKE = PASS
AUTH_READINESS = PASS (dev stack auth; secrets env-driven)
V1_ROUTE_SMOKE = PASS (/modules live after restart)
LETTERS_E2E_SMOKE = PASS (profitability + CI subset + Policy A tests)
MATERIAL_ACTUAL_SMOKE = PASS (covered by material/profitability tests)
PROFITABILITY_POLICY_A_SMOKE = PASS
RESTART_DURABILITY = PASS (stop-dev → detach start; health + UI)
PRODUCTION_DESTRUCTIVE_STARTUP_RISK = NONE
FRESH_MACHINE_SETUP_READINESS = PARTIAL (docs + scripts; physical new machine not provisioned)
KNOWN_V1_LIMITATIONS = machine/other N/A; Capacity inactive; Phase E/PAUSE deferred; Postgres LATER
DB_SCHEMA_CHANGES = 0
QA_MUTATIONS = 0
WORKOS_V1_COMPLETION_ESTIMATE ≈ 95%
NEXT_RECOMMENDED_BUILD = WORKOS_V1_EXIT_VERIFICATION
NEXT_TASK = NOT_AUTHORIZED
```

## Bounded fixes

1. `scripts/_workos-python.ps1` — pip stderr no longer aborts detached start under `$ErrorActionPreference=Stop`.  
2. `scripts/canonical_startup_contract.test.mjs` — sync with current OpenAPI manifest + detached-first `dev.ps1` contract.

## Evidence

`docs/qa/workos-v1-production-readiness-smoke-pack/`  
Runbook: `docs/operations/WORKOS_V1_PRODUCTION_RUNBOOK.md`

## Remaining exit prerequisites (≤5)

1. Owner formal acknowledgment of V1 exit checklist (roadmap §14).  
2. Confirm no open Owner commercial product-set decisions blocking Letters-only V1.  
3. Secrets posture for any non-lab host (strong JWT; disable DEV bypass).  
4. Optional: one Owner-supervised Letters live walk on their data.  
5. Declare `WORKOS_V1_EXIT_VERIFICATION` PASS — no further feature domains.
