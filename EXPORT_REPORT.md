# EXPORT_REPORT

## 1. Data exportului

- Export generated: 2026-06-28 00:00 local time
- Export scope: full WorkOS repository audit + sanitized runnable archive

## 2. Ce contine arhiva

- Root repo files including `package.json`, `pnpm-lock.yaml`, `README.md`, `AGENTS.md`, `scripts/`, `docs/`
- Full frontend source under `frontend/` including `src/`, `public/`, `index.html`, Vite/TS/test config, unit tests, Playwright tests, Intake V6 components, and local frontend libraries
- Full backend source under `backend/` including FastAPI app, routers, services, schemas, models, database layer, Alembic migrations, seed modules, helper scripts, and backend tests
- Database artifacts: root `dev.db` and backend `dev.db`
- Sanitized env examples created for export: root `.env.example` and `.env.development.example`
- Local run guide: `RUN_LOCAL.md`

## 3. Ce a fost exclus

- `node_modules/`
- `.venv/`
- `__pycache__/`
- `.pytest_cache/`
- `.git/`
- real `.env` files
- `logs/`
- `frontend/dist/`
- `frontend/test-results/`
- temporary and cache artifacts

## 4. Structura proiectului

```text
workos-essential-audit-20260624/
  package.json
  pnpm-lock.yaml
  README.md
  AGENTS.md
  RUN_LOCAL.md
  EXPORT_REPORT.md
  docs/
  scripts/
  dev.db
  frontend/
    src/
    public/
    e2e/
    index.html
    vite.config.ts
    tsconfig*.json
    vitest.config.ts
    playwright.config.ts
  backend/
    main.py
    requirements.txt
    requirements-dev.txt
    .env.example
    alembic/
    routers/
    services/
    models/
    schemas/
    seeds/
    scripts/
    tests/
    dev.db
```

## 5. Scripturi disponibile

### Frontend package scripts

- `dev`
- `build`
- `lint`
- `typecheck`
- `validate`
- `preview`
- `test`
- `test:e2e`
- `test:e2e:commercial-live`
- `test:e2e:commercial-warn-ack`
- `test:e2e:commercial-spine-demo`
- `test:e2e:commercial`
- `test:e2e:workintake-finish`
- `test:e2e:intake-v4-open`
- `test:e2e:intake-v4-pbl-complex`

### Backend install / run / test commands

- Install runtime deps: `.\.venv\Scripts\pip install -r requirements.txt`
- Install dev deps: `.\.venv\Scripts\pip install -r requirements-dev.txt`
- Migrate DB: `.\.venv\Scripts\python.exe -m alembic upgrade head`
- Seed canonical data: `.\.venv\Scripts\python.exe -m scripts.seed_sync_all`
- Seed V6 unified pricing: `.\.venv\Scripts\python.exe -m seeds.seed_intake_v6_unified_pricing`
- Run backend: `.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000`
- Run backend tests: `.\.venv\Scripts\python.exe -m pytest tests/ -q`

## 6. Verificari functionale rulate

- Frontend build: PASS
- Frontend focused Intake V6 tests: PASS
- Backend focused Intake V6 test: PASS
- Backend import with local env: PASS
- Backend startup on temporary port `8011`: PASS
- Backend `/health`: PASS (`200 {"status":"healthy"}`)
- DB inspection: PASS
- Migration inventory inspection: PASS

## 7. Status build

- `frontend`: production build passed
- Notes from build:
  - CSS minification warnings about unbalanced bracket utility selectors
  - large bundle warning for `dist/assets/index-*.js`

## 8. Status teste

- Frontend targeted V6 tests passed:
  - `src/lib/intakeV6/intakeV6OperatorRoutes.test.ts`
  - `src/lib/intakeV6/intakeV6ClientSvgImport.test.ts`
- Backend targeted V6 test passed:
  - `tests/test_intake_v6_order_snapshot_payload.py`
- Full frontend typecheck is not clean at export time; terminal run surfaced a large failing set of TypeScript errors across multiple unrelated areas and tests

## 9. Status backend

- Backend exists in current project and is included in export
- FastAPI imports successfully
- Routers for `intake_v4`, `intake_v5`, `intake_v6`, pricing, quotes, orders, inventory, auth, and execution are present
- Temporary startup on `127.0.0.1:8011` completed successfully

## 10. Status DB

### Root `dev.db`

- Exists: yes
- Tables: 45
- Data: no
- Non-empty tables: 0
- Verdict: structurally present but effectively empty

### Backend `backend/dev.db`

- Exists: yes
- Tables: 50
- Data: yes
- Non-empty tables: 23
- Notable rows:
  - `intake_v6_workspaces`: 74
  - `intake_v4_workspaces`: 65
  - `intake_v5_projects`: 6
  - `quotes`: 22
  - `orders`: 8
  - `inventory_materials`: 60
- Verdict: usable local development DB and the correct DB artifact for the runnable full-stack flow

### DB regen / migration / seed

- Migrations folder exists: yes (`backend/alembic/versions`, 38 files)
- Alembic command available: yes
- Canonical seed orchestrator exists: yes (`backend/scripts/seed_sync_all.py`)
- V6 pricing seed exists: yes (`backend/seeds/seed_intake_v6_unified_pricing.py`)

## 11. Status Intake V6

- Single active intake route only: no
- Intake V6 present: yes
- V2/V3/V4/V5 eliminated from routes/nav: no
- Active `IntakeV4` / `intakeV4` imports still exist: yes
- Conceptual V6 -> V4 dependencies still exist: yes
- SVG upload included: yes
- SVG analysis included: yes
- V6 UI components included: yes
- V6 tests included: yes

### Intake routing facts

- Active nav entries include `Work Intake`, `Intake V6`, and `Intake V5`
- Active routes include:
  - `/intake`
  - `/intake/:id`
  - `/intake-v2/:id`
  - `/intake-v4/operator`
  - `/intake-v4/:workspaceId/operator`
  - `/intake-v5`
  - `/intake-v6/operator`
  - `/intake-v6/:workspaceId/operator`
  - `/intake-v4-app/*`
  - `/intake-v6-app/*`

### Intake V6 implementation facts

- V6 operator shell and screens are present under `frontend/src/components/workos/intake-v6/`
- SVG upload and analysis flow is present through files such as:
  - `IntakeV6Nest2SvgUploader.tsx`
  - `steps/IntakeV6SvgAnalyzerStep.tsx`
  - `frontend/src/lib/intakeV6/intakeV6SvgUploadFlow.ts`
- V6 also still co-locates many `IntakeV4*` components inside the same `intake-v6` area

## 12. Probleme cunoscute ramase

- Frontend global typecheck is failing at export time
- Frontend build passes, but bundle size is large and CSS utility warnings remain
- Intake is not V6-only; older intake generations remain routed or present in source
- V6 is not conceptually isolated from V4 naming and implementation layers
- Root `README.md` is not a full-stack runbook; `RUN_LOCAL.md` was added for that purpose
- `root/dev.db` is empty and should not be used as the primary runnable DB

## 13. Ce lipseste

- No dedicated root-level backend README was found
- No clean root `.env.example` existed before this export
- No evidence of dedicated V6 Playwright E2E tests was found; frontend V6 coverage appears primarily unit/integration oriented

## 14. Verdict

`FULL-STACK EXPORT PASS`

Reasoning:

- The repository contains frontend, backend, DB, migrations, seeds, configs, scripts, docs, and tests
- The backend imports, starts, and serves `/health`
- The frontend production build passes
- The local backend DB contains seeded V6-relevant data
- The export is complete enough for coherent local full-stack startup, with known issues documented rather than hidden