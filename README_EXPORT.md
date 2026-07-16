# WorkOS Full Application Export

**Export date/time:** 2026-06-30 (local export session)  
**Source repo path:** `C:\Users\offic\Desktop\workos-active`  
**Forbidden source (not included):** `C:\Users\offic\workos`

## Git snapshot

| Field | Value |
|-------|-------|
| Branch | `feature/step-7g-commercial-price-proposal` |
| HEAD | `1e32692` — docs(worklog): record step 9 semantic alignment reviews |
| Remote | `origin` → `https://github.com/office952/workos-active.git` |
| Tracking | ahead of `origin/feature/step-7g-commercial-price-proposal` by 1 commit |

### Working tree summary (at export time)

- **Application code:** no modified/untracked backend or frontend source files.
- **Docs:** multiple **untracked** realignment worklogs and app-flow docs **included** in this archive (on-disk state).
- **Deleted tracked doc:** `docs/worklog/realignment/2026-06-30_vs_code_full_app_audit_for_step8.md` — **not** in this export (deleted in working tree).

## What this archive contains

- `backend/` — Python FastAPI source (excluding `.venv`, caches, logs)
- `frontend/` — React/Vite source (excluding `node_modules`, build output)
- `docs/` — architecture, QA, worklogs (including untracked realignment docs present on disk)
- `scripts/` — Windows dev launchers (`dev.ps1`, `start-dev.ps1`, `dev-backend.ps1`, etc.)
- Root config: `package.json`, `pnpm-lock.yaml`, `README.md`, `AGENTS.md`, `.gitignore`, `.env.example`, `.env.development.example`, `RUN_LOCAL.md`, `start_app.sh`
- **Dev database:** `backend/dev.db` (~9.0 MB SQLite)
- (historical) local `database_candidates/` inventory of **excluded** backup/forensic DB files — removed in repo cleanup 2026-07-16
- Install/export docs: this file, `INSTALL_LOCAL.md`, `ENVIRONMENT_NOTES.md`, `EXPORT_MANIFEST.md`

## What this archive does NOT contain

- `.git/` history
- `node_modules/`, `frontend/node_modules/`
- `backend/.venv/`, `.venv312/`
- `__pycache__/`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`
- `dist/`, `build/`, `coverage/`, `tmp/` (except this export staging content inside the ZIP)
- `*.log`, `*.pyc`
- Real secrets (`.env` files with production keys — only `.env.example` templates included)
- Old repo at `C:\Users\offic\workos`
- 24 backup/forensic SQLite files (`dev.backup-*`, `dev.FORENSIC-*`) — excluded from export; not tracked in git

## Important notes

- **Local export only** — not a production release artifact.
- **No `.git`** — clone history is not preserved; use the source repo for version control.
- **Dependencies not bundled** — run `pip install` and `pnpm install` after unzip (see `INSTALL_LOCAL.md`).
- **Dev DB included** — `backend/dev.db` reflects local development state at export time. Do not reset/seed without owner approval.
- **Materialization:** POST materialize remains **blocked** (DEC-009). This export did not create `execution_tasks`, sessions, or call materialize.
- **Employee Mobile:** frozen / final-final — out of scope for this export workflow.
- **Documentation included:** realignment audits, `docs/architecture/app-flows/`, `docs/architecture/realignment/`, and `docs/worklog/realignment/` (including untracked entries present on disk at export).

## Quick start

See **`INSTALL_LOCAL.md`** for Windows setup and startup.
