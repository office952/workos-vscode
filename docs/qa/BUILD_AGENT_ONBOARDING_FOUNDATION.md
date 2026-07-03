# BUILD — Agent Onboarding Foundation: Root README + AGENTS.md + Canonical Commands

**Date:** 2026-06-08  
**Build status:** **PASS**  
**Agent Compatibility (before):** **59/100**

## Purpose

Reduce onboarding friction for new agents and developers: single entry point, explicit boundaries, real commands, fixed dev script path.

**Boundary:** documentation + helper scripts only — no business logic, runtime, schema, or test assertion changes.

## Problems found (Agent Compatibility scan)

| Issue | Impact |
|-------|--------|
| No root `README.md` | Agents guess stack, ports, and setup |
| No `AGENTS.md` | No protected-area or build discipline |
| No root canonical commands | Validation paths scattered in QA docs only |
| `start_app.sh` pointed at `/workspace/project/app/frontend` | Broken on real checkout |
| `frontend/README.md` was generic shadcn template | Misleading project context |
| No minimal CI workflow | No automated gate at PR level |

## What was added

| File | Role |
|------|------|
| [`README.md`](../../README.md) | Project summary, structure, quick start, validation, doc links, template scope |
| [`AGENTS.md`](../../AGENTS.md) | Agent prime directive, commands, protected areas, build discipline, do-not list |
| [`package.json`](../../package.json) | Root npm scripts delegating to frontend pnpm + backend PowerShell helpers |
| [`scripts/dev-backend.ps1`](../../scripts/dev-backend.ps1) | Backend-only uvicorn with local env |
| [`scripts/test-backend.ps1`](../../scripts/test-backend.ps1) | Backend pytest with local env |
| [`frontend/README.md`](../../frontend/README.md) | WorkOS-specific frontend overview (points to root) |

## What was repaired

| File | Fix |
|------|-----|
| [`start_app.sh`](../../start_app.sh) | Resolves repo root; starts `backend/` uvicorn + `frontend/` vite; documents Windows alternative |

Previously:

```bash
cd /workspace/project/app/frontend
pnpm run dev --host 0.0.0.0 --port 3000
```

## Canonical commands

### Root (`npm run …` from repo root)

| Script | Implementation |
|--------|----------------|
| `dev:frontend` | `pnpm --dir frontend dev` |
| `dev:backend` | `scripts/dev-backend.ps1` |
| `dev:stack` | `scripts/start-dev.ps1` (existing, idempotent) |
| `validate:frontend` | `pnpm --dir frontend validate` |
| `test:frontend` | `pnpm --dir frontend test` |
| `test:backend` | `scripts/test-backend.ps1` → `pytest tests/ -q` |
| `test:e2e:workintake-finish` | `pnpm --dir frontend test:e2e:workintake-finish` |

### Bash / WSL

```bash
./start_app.sh
```

### E2E prerequisite

```powershell
cd backend
.\.venv\Scripts\python.exe scripts\seed_commercial_e2e_fixture.py
```

See [`BUILD_CI_E2E_WORKINTAKE_TO_QUOTE_FINISH_DISPLAY.md`](BUILD_CI_E2E_WORKINTAKE_TO_QUOTE_FINISH_DISPLAY.md).

## Verification run (this build)

| Check | Command | Result |
|-------|---------|--------|
| Root docs exist | `README.md`, `AGENTS.md` | **PASS** — both present |
| Root scripts | `node -e "require('./package.json').scripts"` | **PASS** — 7 canonical scripts listed |
| Frontend typecheck | `npx pnpm@8.10.0 run typecheck` (frontend/) | **FAIL (pre-existing)** — TS errors in VectorIntake/WorkIntakeV2/Quotes tests; not introduced by this docs-only build |
| Targeted vitest | `vitest run src/lib/colorRegistry/colorRegistry.test.ts` | **PASS** — 6/6 tests |

Full `pnpm run validate` (lint + typecheck + build) remains the recommended gate; typecheck currently fails on known debt outside this build scope.

## Boundary confirmation

**Not modified:**

- Frontend runtime / WorkIntake V2 / QuoteWizard logic
- Backend business logic, CostEngine, Pricing, Inventory
- DB schemas and migrations
- Test assertions or spec logic
- CI workflow files (none added)

## Next candidates

1. **GitHub Actions CI** — `validate:frontend`, targeted pytest subset, optional Playwright with seeded DB
2. **Cross-platform root backend scripts** — bash equivalents for `dev-backend` / `test-backend` on Linux agents
3. **pnpm workspace** — optional root `pnpm-workspace.yaml` if root dependencies grow
4. **Agent Compatibility re-scan** — expect score lift from README + AGENTS + canonical commands

## Related docs

- [`BUILD_WORKINTAKE_V2_UNIFIED_OPERATOR_FLOW.md`](BUILD_WORKINTAKE_V2_UNIFIED_OPERATOR_FLOW.md)
- [`BUILD_TEMPLATE_INTAKE_MODULARITY_FOUNDATION.md`](BUILD_TEMPLATE_INTAKE_MODULARITY_FOUNDATION.md)
- [`BUILD_COLOR_AND_VINYL_REGISTRY_RAL_ORACAL.md`](BUILD_COLOR_AND_VINYL_REGISTRY_RAL_ORACAL.md)
- [`BUILD_COMMERCIAL_E2E_FIXTURE.md`](BUILD_COMMERCIAL_E2E_FIXTURE.md)
- [`BUILD_CI_E2E_WORKINTAKE_TO_QUOTE_FINISH_DISPLAY.md`](BUILD_CI_E2E_WORKINTAKE_TO_QUOTE_FINISH_DISPLAY.md)
