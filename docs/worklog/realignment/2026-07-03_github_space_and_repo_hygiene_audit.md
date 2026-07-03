# GitHub space and repo hygiene audit - 2026-07-03

## Context

Audit read-only before continuing WorkOS form fixes. Requested local repo root: `C:\Users\offic\workos_app_vs`. Requested GitHub repo: `office952/workos-vscode`.

No commit, push, deletion, cleanup, or functional code change was performed.

## Workspace verification

Verified with explicit root location:

- Root: `C:\Users\offic\workos_app_vs`
- Required folders present: `frontend`, `backend`, `docs`, `fisiere-teste-svg`

## Branch / remote

Current branch:

- `fix/intake-v6-quotes-integration`

Recent commits:

- `5b0840d feat(intake-v6): modularization audit, UI cleanup, product plugin registries`
- `7ad7642 fix: wire intake-v6 priced quote bridge in Quotes UI`
- `d712802 feat(step9): add read-only materialization audit`
- `e9f8033 docs(step9): record fresh runtime persist verification`
- `7d317a0 docs(step9): sync persist draft validation`

Configured remote:

- fetch: `https://github.com/office952/workos-active.git`
- push: `https://github.com/office952/workos-active.git`

Risk: prompt says GitHub repo should be `office952/workos-vscode`, but local `origin` points to `office952/workos-active`. Treat as BLOCKED for push until owner confirms or remote is corrected.

## Git status summary

Porcelain summary from repo root:

- Modified: 47
- Untracked: 140
- Deleted: 0
- Staged: 0
- Conflicts: 0

No files are staged.

Representative modified areas:

- backend V6 routers/schemas/services/tests
- frontend Intake V6 components/libs/tests
- docs architecture/worklog files

Representative untracked areas:

- new backend V6 services/tests
- many docs/worklogs
- `database_candidates/`
- `fisiere-teste-svg/`
- frontend V6/product-system additions
- local scratch outputs such as `frontend_vite_build_check.txt`, `frontend_tsc_runtime_check.txt`, `tmp_build_intakev6_freeze_fix.exitcode`
- `backend/test_placeholder.db`

## Git object size

`git count-objects -vH`:

- count: 75
- size: 267.44 KiB
- in-pack: 3165
- packs: 1
- size-pack: 6.29 MiB
- prune-packable: 0
- garbage: 0
- size-garbage: 0 bytes

No tracked files over 10 MB were reported by the tracked-file size scan.

## Large files found

Working tree files over 20 MB, excluding `.git`, `node_modules`, and `.venv`:

| Path | Size MB | Tracked? | Recommendation |
| --- | ---: | --- | --- |
| `backend/logs/app_20260701_025223.log` | 365.85 | ignored/untracked local log | Do not commit; safe cleanup candidate after GO owner. |
| `backend/logs/app_20260703_000615.log` | 187.24 | ignored/untracked local log | Do not commit; safe cleanup candidate after GO owner. |
| `backend/logs/app_20260701_011645.log` | 44.32 | ignored/untracked local log | Do not commit; safe cleanup candidate after GO owner. |
| `backend/logs/app_20260702_101723.log` | 20.24 | ignored/untracked local log | Do not commit; safe cleanup candidate after GO owner. |

Tracked files over 10 MB:

- None found.

## Suspicious files

Suspicious untracked scan found:

- `backend/test_placeholder.db` - local DB artifact; should not be committed.
- `docs/worklog/realignment/2026-07-03_intake_v6_review_sync_pending_live_fix.png` - image artifact; review whether needed before commit.
- `frontend_vite_build_check.txt` - local build/check output; should not be committed unless intentionally documented.
- `frontend_tsc_runtime_check.txt` - local typecheck/runtime output; should not be committed unless intentionally documented.
- `tmp_build_intakev6_freeze_fix.exitcode` - temporary exit-code artifact; should not be committed.

The scan also matched markdown files with names containing `build`; these are docs/worklog/QA files and are not automatically suspicious merely because of the word `build`.

## Build/cache/dependency directories

Dependency/cache/build-like directories exist locally, especially:

- root `node_modules/`
- `frontend/node_modules/`
- nested pnpm package directories under those `node_modules/`

These are covered by `.gitignore` and did not appear as tracked large files.

## .gitignore audit

Current `.gitignore` covers:

- `node_modules/`
- `.pnpm-store/`
- `.venv/`, `venv/`
- `__pycache__/`
- `*.py[cod]` (covers `.pyc`, though not exact literal `*.pyc`)
- `.pytest_cache/`
- `dist/`
- `build/`
- `*.tsbuildinfo`
- `.env`
- `.env.*` (covers `.env.local`)
- `dev.db`, `dev.db-journal`, `dev.db.forensic*`, `dev.backup*`, `dev.FORENSIC*`, `local_dev.db`, `local_dev.db-journal`, `*.db-journal`
- logs including `logs/`, `backend/logs/`, `*.log`
- `.vite/`
- coverage/cache/test artifacts
- local storage/upload/export folders

Important missing or incomplete generic patterns:

- `*.db` is not generically ignored; this is why `backend/test_placeholder.db` appears untracked.
- `*.sqlite` is not ignored.
- `*.zip`, `*.rar`, `*.7z` are not ignored.
- `*.bak` is not ignored generically, although `dev.backup*` is covered.

Suggested `.gitignore` patch after GO owner:

```gitignore
# Generic local database / archives / backups
*.db
*.sqlite
*.sqlite3
*.zip
*.rar
*.7z
*.bak
*.backup
```

Do not apply this blindly if the repo intentionally tracks a small fixture DB/archive. First check intended tracked fixtures.

## Recommendation finala

Verdict: BLOCKED for push.

Reasons:

1. Remote mismatch: requested GitHub repo is `office952/workos-vscode`, configured `origin` is `office952/workos-active`.
2. There are large ignored local logs that should not be committed and can be cleaned only after GO owner.
3. There is at least one untracked `.db` artifact not protected by generic `.gitignore`.
4. `.gitignore` lacks generic archive and backup exclusions.
5. Working tree is broad: 47 modified and 140 untracked entries. Commit scope needs curation before any push.

Commit/push safety:

- Do not push until remote target is confirmed/corrected.
- Do not stage all files.
- Stage only reviewed code, tests, docs, worklogs, and small intended SVG fixtures.
- Exclude local DB/log/temp/image artifacts unless explicitly approved.

## Ce NU am modificat

- No commit.
- No push.
- No deletion.
- No cleanup.
- No `.gitignore` patch applied.
- No functional code changed.
- No database/schema/migration touched.

## Next safe step

1. Owner confirms correct remote: keep `workos-active` or switch to `office952/workos-vscode`.
2. Owner gives GO to patch `.gitignore` with generic local DB/archive/backup patterns.
3. Owner gives GO for manual cleanup/move of local logs and scratch artifacts.
4. Curate commit scope with explicit `git add <paths>` rather than staging everything.
