# Worklog — Montaj Authority Split Canonical Runtime Restore

**Date:** 2026-07-19 / restore executed 2026-07-20 local  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**HEAD:** `184b9dc`  
**Scope:** runtime restore + verification only — **no application code changes**

## Problem

Acceptance FE `:3000` must use BE `:8003`, but `:8003` served pre-`184b9dc` authority truth while temporary `:8013` served the repaired truth for the same workspace.

## Root cause

Not a living uvicorn parent on `:8003`. Netstat showed ghost LISTENING PIDs (dead). Actual servers were **orphaned `multiprocessing.spawn` workers** whose `parent_pid` matched those dead reload workers. They kept answering HTTP with old composition code.

## Actions

1. Inventoried ports/processes/command lines (pre-flight).
2. Proved `:8003` vs `:8013` PD/Agg delta on ACM WS (same `updated_at` → code, not DB).
3. Stopped only mapped orphans: `35220`, `23792`, `29460`, `40616`, `32180`.
4. Verified `:8003` released.
5. Started canonical BE: venv uvicorn `--host 127.0.0.1 --port 8003` from `C:\w\psiso\backend`, **no `--reload`**, `DATABASE_URL=sqlite+aiosqlite:///./dev.db`.
6. Restarted FE with `BACKEND_PORT=8003`.
7. Compared `:8003` == `:8013` (match), then stopped temporary `:8013`.
8. Ran authority test suites; captured UI screenshots.

## Result

Canonical topology restored:

- FE `http://127.0.0.1:3000`
- Proxy `BACKEND_PORT=8003`
- BE `http://127.0.0.1:8003` → repaired authority (`confirmed`, no `MOUNTING_SCOPE_INACTIVE`)
- `:8013` stopped

## Docs pack

`docs/qa/intake-v6-montaj-authority-split-runtime-restore-2026-07-19/`

## Foreign WIP

Untouched.
