# Tests / Preflight Integrity

**Repo:** `C:\w\psiso`  
**Date:** 2026-07-31  
**Canonical checklist:** handoff `CI_PREFLIGHT_GATE.md` + `.cursor/rules/ci-preflight-gate.mdc`  
**Mode:** Run documented checks only · report failures · do not fix

---

## Commands run

| Check | Command | Exit | Result |
|-------|---------|------|--------|
| Frontend lint | `cd frontend && pnpm run lint` | **0** | **PASS** |
| Frontend unit (CI allowlist) | `cd frontend && pnpm run test:ci` | **0** | **PASS** — 21 files / 198 tests |
| Frontend build | `cd frontend && pnpm run build` | **0** | **PASS** (chunk-size WARN) |
| Backend targeted pytest | `APP_ENV=test ENVIRONMENT=test` + four CI files | **0** | **PASS** — 28 passed, 3 dep warnings |

Backend file set (aligned with gate):

- `tests/test_dashboard_kpi_metrics.py`
- `tests/test_operational_data_gaps.py`
- `tests/test_pricing_registry.py`
- `tests/test_cost_engine_config.py`

---

## Runtime health (preflight-adjacent)

| Check | Result |
|-------|--------|
| API `:8000 /health` | **200** healthy |
| UI `:3000` | **200** |
| local-compatibility SHA | `a1c28854` matches HEAD |

---

## Known non-goals / debt (not claimed green)

| Item | Status |
|------|--------|
| Full `pnpm run test` (Vitest entire suite) | Known debt — **not run** as CI substitute |
| `npm run validate:frontend` broader TS debt | Documented in AGENTS.md — **not claimed** |
| Full `test:backend` beyond CI four files | Known failures outside CI set — **not run** |
| GitHub Actions live re-poll this minute | Not re-fetched; PR #37 previously stamped CI green in 20D/20E reports |

---

## Artifact logs (ephemeral)

Under `docs/qa/app-integrity-before-next-go/`:

- `_tmp_lint.txt`
- `_tmp_testci.txt`
- `_tmp_build.txt`
- `_tmp_pytest.txt`

---

## Verdict

**PASS** — Documented CI-equivalent preflight commands are green locally. Remaining suite debt is explicitly out of scope and must not be pretended green.
