# C1 — F4/U4 Pre-Push Owner Gate Report

**Stamp:** `OWNER ACCEPT WITH PRE-PUSH CONDITIONS` → C1 hardening evidence  
**Controller HEAD at proof:** `8918717c`  
**Date:** 2026-08-02

## Verdict

```text
C1 runtime / migration / baseline / targeted tests = PASS
Pricing.badges = pre-existing flake (not weakened; not full FE green)
Platform Profitability Complete = NOT READY
Production Ready / UI Complete / WorkOS Complete = NOT DECLARED
Employee Mobile = not touched
```

## Commit audit (integrated chain)

| SHA | Scope | Ownership | Migrations | Tests | Contamination |
|-----|-------|-----------|------------|-------|---------------|
| `1a983f2a` | F4 material actuals + closed-job | backend inventory/actual-cost + profitability consumers | `s62_material_actuals_closed_job_v1` (`reverses_movement_id`) | `test_material_actuals_closed_job_v1` | none |
| `a10d0d28` | U4A scorecard part 1 | docs/qa UI wave4 | none | n/a | none |
| `aa3c661b` | U4A scorecard part 2 | docs/qa UI wave4 | none | n/a | none |
| `8918717c` | U4B Execution Closure UI | frontend Execution Detail local panel + closure API client | none | `executionClosureUi.test.ts` | none |

Checks: no DB files, secrets, runtime logs, `project_sources`, `_tmp` product code, Employee Mobile, commercial repricing in chain.  
`git diff --check`: trailing whitespace in `FULL_APPLICATION_SCORECARD.md` → isolated correction commit.

## Migration (`s62`)

- `down_revision = s61`
- Single Alembic head: `s62`
- Fresh DB upgrade PASS
- Upgrade from previous schema PASS
- Downgrade to `s61` + re-upgrade PASS (`qa-dbs/c1-s62-fresh.db`, not committed)
- `backend/dev.db` not modified for migration proof

## U4B runtime identity

```text
commit = 8918717c
database = backend/qa-dbs/c1-u4b-runtime.db
backend = :8018
frontend = :3040
CORS = http://127.0.0.1:3040
dev auth = bypass + optional WORKOS_DEV_AUTH_USER_ID
order = 880041 (ready fixture) / 880042 (incomplete)
```

## Runtime matrix

| State | Evidence | Result |
|-------|----------|--------|
| Open + ready | `screenshots/day/01-open-ready.png` + close button path | PASS |
| Close authorized | `day/02-closed-margin.png` — Job închis, marjă 890 | PASS |
| Reopen + reason | `day/03-reopened.png` — Pregătit, marjă Indisponibilă | PASS |
| Reclose | `day/04-reclosed.png` + API `execution_closure_status=closed` | PASS |
| Blocked incomplete | `day/05-blocked-incomplete.png` (880042 active session) | PASS |
| Dark closure | `dark/02-closure-panel.png` — closed + margin 890 | PASS |
| Operator read-only | `roles/operator-readonly.png` + `u4b-operator-results.json` | PASS |
| Unauthorized close | HTTP 403 `execution.job_close` as operator | PASS |

## Console

- Zero CORS failures on admin lifecycle.
- Zero new nested-button warnings on closure surface.
- Pre-existing page noise (report separately): `product_system/preview` 404, `operator/.../task-truth` 422, React Router future-flag warning. Not treated as U4 regression.

## Tests run

```text
test_material_actuals_closed_job_v1.py          4 PASS  (-W error::RuntimeWarning)
test_profitability_actual_read_model.py         PASS
test_post_job_truth.py                          PASS
(combined material+profit+post_job)             17 PASS with -W error::RuntimeWarning
test_auth_dev_impersonation.py                  8 PASS (clean env)
frontend executionClosureUi.test.ts             2 PASS
Pricing.badges                                  FAIL (pre-existing flake; not scope-expanded)
```

## Protected baseline `973019`

| Fact | Value |
|------|-------|
| Snapshot SHA256 prefix | `2d412e6e1234ae44` MATCH |
| Execution plan | id `21` |
| Closures on 973019 | none |
| Stock movements on 973019 | none |
| Reality rows on 973019 | none |

## Stash

```text
stash@{0}: wip-employee-unrelated  (intact)
```

## Push gate inputs

- Corrective: scorecard whitespace + this C1 evidence pack (no QA DBs, no `_seed*`, no capture runners required for runtime).
- Push integrated controller chain only after correction SHA lands.
- F5/U5 must branch from post-push remote tip and remain unpushed.
