# Worklog — WorkOS Atoms reproducible demo environment V1

**Date:** 2026-08-10  
**Owner GO:** `AUTHORIZE_WORKOS_ATOMS_REPRODUCIBLE_DEMO_ENVIRONMENT_V1`  
**Branch:** `feat/f7i-owner-rate-activation`  
**Plan:** `docs/plans/2026-08-10-001-feat-atoms-reproducible-demo-environment-plan.md`  
**Scope affirmed:** wipe-and-rebuild · full inventory · Golden extract-only  

## Verdict

```text
WORKOS_ATOMS_REPRODUCIBLE_DEMO_ENVIRONMENT_V1 = PASS
DEMO_DATA = SYNTHETIC
REAL_DEV_DB_COMMITTED = NO
DEMO_DB_GENERATION = DETERMINISTIC
BACKEND_REAL = YES
FRONTEND_REAL = YES
BUSINESS_LOGIC_REAL = YES
PRODUCT_TRUTH_MUTATIONS = 0
DB_SCHEMA_CHANGES = 0
PII_SCAN = PASS
DEMO_BOOTSTRAP = PASS
DEMO_REBUILD = PASS
ATOMS_READY = YES
GITHUB_PUSH = NO
```

## Architecture

**Option A** — wipe-and-rebuild dedicated SQLite `backend/demo/workos_demo.db` via Alembic + `seed_atoms_demo_v1.py`. Binary DB never committed (`*.db` + explicit demo ignores).

Hard guard: `backend/demo/db_guard.py` + PowerShell path checks — refuse `backend/dev.db` / basename `dev.db`.

## Reused

- Registry/template seeds via existing `seed_sync_all` composition (workforce registry **skipped**)
- Golden Gradi fixture pack under `backend/tests/fixtures/intake_v6_golden_gradi/` (extract-only; Golden E2E runner **not** used as seed)
- Real CPP / Quote / Order / EP / assignment / session / material actual / profitability-actual paths
- Dev auth bypass (`__DEV_BYPASS_TOKEN__` / `VITE_ENABLE_DEV_AUTH`) development-bound only

## Added

| Path | Role |
|------|------|
| `backend/demo/db_guard.py` | Fail-closed demo DB path guard |
| `backend/scripts/seed_atoms_demo_v1.py` | Deterministic DEMO inventory seed |
| `scripts/demo-bootstrap.ps1` | Wipe + alembic + seed |
| `scripts/demo-backend.ps1` / `demo-start.ps1` | Demo-stack start (detached) |
| `docs/operations/WORKOS_ATOMS_DEMO_ENVIRONMENT.md` | Atoms runbook |
| `backend/tests/test_atoms_demo_*.py` | Guard + safety tests (10 passed) |
| `backend/models/__init__.py` | Register missing model modules so fresh `create_all` creates V6/snapshot/stock tables (no new migration) |

## Dataset (fixed identities)

- Clients `DEMO-CLIENT-001`…`004`
- Intake complete `DEMO-INTAKE-LETTERS-001` · `d0e10001-…0001`
- Intake draft `DEMO-INTAKE-DRAFT-001` · `d0e10002-…0002`
- Quote `DEMO-QUOTE-EUR-001` · EUR **862.65** / net **712.93** / VAT **149.72**
- Order `DEMO-ORDER-001` · id `1` · locked · EP + assignment + 40 min session + Oracal material actual
- Synthetic employees only (no payroll / real names)

## Runtime proof

- Bootstrap + rebuild: PASS (same DEMO codes)
- In-process API smoke (`backend/demo/smoke_demo_api.py`): PASS
- Isolated UI smoke `:3010` + `:8010` (Owner `:3000`/`:8000` untouched): route matrix §23 PASS — see QA pack screenshots
- Default `demo-start` on `:8000` correctly exit **2** while Owner `dev.db` stack is healthy

## Evidence

`docs/qa/workos-atoms-reproducible-demo-environment-v1/`

## Next

```text
NEXT_RECOMMENDED_TASK = WORKOS_POST_V1_UI_UX_ATOMS_AUDIT_AND_DIRECTION_V1
NEXT_TASK = NOT_AUTHORIZED
GITHUB_PUSH = NO
```
