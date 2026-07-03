# BUILD — Startup / Validation Friction Fix

**Date:** 2026-06-08  
**Build status:** **PASS**  
**Boundary:** scripts + docs only — no business logic, no TS/pytest debt fixes

## Agent Compatibility scores

| Metric | Score |
|--------|-------|
| Before onboarding | 59/100 |
| After onboarding (composite) | 67/100 |
| Docs reliability | 84/100 |
| Startup review | 86/100 |
| Validation review | 77/100 |
| Deterministic scan | 60/100 |

Target for full website audit: **70+**. This build addresses tooling friction blocking the next ~3 points without touching typecheck or full-suite test debt.

## Problems addressed

| Issue | Fix |
|-------|-----|
| Root scripts required global `pnpm` | Switched to `npx --yes pnpm@8.10.0 --dir frontend …` |
| `dev:backend` failed without `python` on PATH | Shared resolver: `WORKOS_PYTHON` → `python` → `py -3` |
| Machine-specific hardcoded Python path in `start-dev.ps1` | Removed; uses `scripts/_workos-python.ps1` |
| `test:backend` missing pytest in fresh venv | Installs `requirements-dev.txt` before pytest |
| README/AGENTS implied `validate:frontend` is green | Documented as intended gate, currently FAIL (TS debt) |
| E2E docs bash-only | PowerShell + Bash variants for `PW_SKIP_WEB_SERVER` |
| AGENTS seed block missing env vars | Full PowerShell seed with `APP_ENV`, `DATABASE_URL`, etc. |
| `.env` copy guidance misleading | Clarified helper injection vs manual uvicorn; `backend/.env` not auto-loaded |
| Migration steps unclear | Documented `create_all` local boot; Alembic for separate builds |

## Files changed

| File | Change |
|------|--------|
| `package.json` | Frontend scripts use `npx pnpm@8.10.0` |
| `scripts/_workos-python.ps1` | **New** — shared Python resolution + venv + pip helpers |
| `scripts/dev-backend.ps1` | Uses shared resolver; documents no `.env` auto-load |
| `scripts/test-backend.ps1` | Uses shared resolver; installs `requirements-dev.txt` |
| `scripts/start-dev.ps1` | Removed hardcoded Python312 path; uses shared resolver |
| `README.md` | Validation truth, env/.env, E2E PS/Bash, create_all, targeted tests |
| `AGENTS.md` | Same + seed env vars, validation truth table |
| `docs/qa/BUILD_STARTUP_VALIDATION_FRICTION_FIX.md` | This doc |

## Canonical commands (aligned)

```json
{
  "dev:frontend": "npx --yes pnpm@8.10.0 --dir frontend dev",
  "dev:backend": "powershell … scripts/dev-backend.ps1",
  "dev:stack": "powershell … scripts/start-dev.ps1",
  "validate:frontend": "npx --yes pnpm@8.10.0 --dir frontend validate",
  "test:frontend": "npx --yes pnpm@8.10.0 --dir frontend test",
  "test:backend": "powershell … scripts/test-backend.ps1",
  "test:e2e:workintake-finish": "npx --yes pnpm@8.10.0 --dir frontend test:e2e:workintake-finish"
}
```

## Python resolution behavior

Order in `scripts/_workos-python.ps1`:

1. **Existing venv** — if `backend/.venv/Scripts/python.exe` exists, use it (no host Python required)
2. `$env:WORKOS_PYTHON` if set and path exists
3. `python` on PATH
4. Windows launcher `py -3` → `sys.executable`
5. Clear error: *"Set WORKOS_PYTHON or install Python 3.12 / add python to PATH."*

Used by: `dev-backend.ps1`, `test-backend.ps1`, `start-dev.ps1`.

## Backend dev requirements

`test-backend.ps1` runs:

```powershell
pip install -r requirements.txt
pip install -r requirements-dev.txt   # pytest, pytest-asyncio
pytest tests/ -q
```

Quiet install on each run; acceptable for agent cold-start reliability.

## Verification run

| Check | Command | Result |
|-------|---------|--------|
| Root scripts | `node -e "console.log(require('./package.json').scripts)"` | **PASS** — all use `npx pnpm@8.10.0` |
| Targeted Vitest | `npm run test:frontend -- src/lib/colorRegistry/colorRegistry.test.ts` | **PASS** — 6/6 |
| Backend pytest setup | `npm run test:backend` | **PARTIAL** — pytest runs, dev deps install OK; 3 collection errors (pre-existing packaging tests), not missing pytest |
| `validate:frontend` | Not required | Known FAIL (TS debt) — out of scope |

First `test:backend` attempt failed when host Python absent but venv missing resolution was added: reuse existing `backend/.venv` without PATH python.

## Boundary confirmation

**Not modified:** frontend/backend runtime logic, CostEngine, Pricing, Inventory, WorkIntake, QuoteWizard, ProductSystem, DB schemas, migrations, test assertions, TS errors.

## Remaining issues (next builds)

1. **Frontend Typecheck Debt Audit** — fix ~85 TS errors so `validate:frontend` becomes a real gate
2. **Backend test debt triage** — full pytest suite has known failures; document subsets for CI
3. **GitHub Actions CI** — targeted gates once validate subset is defined
4. **Bash backend helpers** — optional `scripts/test-backend.sh` for Linux agents
5. **Agent Compatibility re-scan** — expect composite lift toward 70+

## Related docs

- [`BUILD_AGENT_ONBOARDING_FOUNDATION.md`](BUILD_AGENT_ONBOARDING_FOUNDATION.md)
- [`BUILD_CI_E2E_WORKINTAKE_TO_QUOTE_FINISH_DISPLAY.md`](BUILD_CI_E2E_WORKINTAKE_TO_QUOTE_FINISH_DISPLAY.md)
