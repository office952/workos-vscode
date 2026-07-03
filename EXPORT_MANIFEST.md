# WorkOS Full Application Export — Manifest

## Identity

| Field | Value |
|-------|-------|
| Branch | `feature/step-7g-commercial-price-proposal` |
| HEAD | `1e32692` |
| Remote | `origin` → `https://github.com/office952/workos-active.git` |
| Source path | `C:\Users\offic\Desktop\workos-active` |
| ZIP name | `tmp/workos_full_app_export_2026-06-30_1e32692.zip` |
| Export staging | `tmp/workos_full_export/` |

## Folders included

| Path | Included |
|------|----------|
| `backend/` | Yes (excl. `.venv`, caches, `logs/`, backup DBs) |
| `frontend/` | Yes (excl. `node_modules`, `dist`, `build`, `coverage`) |
| `docs/` | Yes (full tree on disk, incl. untracked worklogs) |
| `scripts/` | Yes |
| `database_candidates/` | Yes (excluded DB inventory only) |
| Root config files | Yes (at export root, not `root-files/` subfolder) |

## Folders / artifacts excluded

- `.git/`
- `node_modules/`, `frontend/node_modules/`
- `backend/.venv/`, `backend/.venv312/`
- `__pycache__/`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`
- `dist/`, `build/`, `coverage/`, `.vite/`
- `backend/logs/` (`*.log`)
- `*.pyc`
- `C:\Users\offic\workos` (forbidden old repo)
- Prior ZIPs in `tmp/` (not bundled into this export)
- `.cursor/`, `.vscode/` (editor config — not required for run)

## Database files

### Included

| File | Size (bytes) | Notes |
|------|--------------|-------|
| `backend/dev.db` | 9,465,856 | Canonical dev DB per `scripts/dev.ps1` |

### Excluded (24 files)

Pattern: `backend/dev.backup-*`, `backend/dev.FORENSIC-*`  
Full list: `database_candidates/EXCLUDED_DB_FILES.txt`

## File counts and size

- **Staging file count:** 2,720 files (before ZIP; includes 4 export docs + database_candidates)
- **ZIP size:** 15413858 bytes (14.7 MB)

## Working tree status at export

**Not clean** — docs-only delta:

- **Deleted (tracked):** `docs/worklog/realignment/2026-06-30_vs_code_full_app_audit_for_step8.md` — absent from export
- **Untracked docs included in export:**
  - `docs/architecture/app-flows/` (entire directory)
  - `docs/architecture/realignment/21_WORKOS_IMPLEMENTATION_ROUTE.md`
  - 13 untracked `docs/worklog/realignment/2026-06-30_*.md` worklogs
- **Non-doc code changes:** **None** (no modified/untracked backend or frontend source)

## Warnings

1. Working tree had **uncommitted docs** — included as on-disk state; not a git snapshot.
2. One **tracked worklog deleted** locally — not in archive.
3. Root `package.json` duplicates frontend package metadata; use **`frontend/`** for `pnpm install` and `pnpm dev`.
4. No real `.env` shipped — only `.env.example` templates.
5. `validate:frontend` / full TS gate known **FAIL** in repo (~85 TS errors per `AGENTS.md`) — export is runnable, not typecheck-clean.

## Export actions performed

- File inventory and robocopy staging only
- No backend/frontend logic edits
- No DB mutation, seed, reset, migration
- No POST materialize, sessions, or Employee Mobile changes
- No commit, no push
