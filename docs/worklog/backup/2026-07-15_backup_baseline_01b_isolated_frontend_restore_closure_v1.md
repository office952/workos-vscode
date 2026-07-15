# BACKUP-BASELINE-01B — Isolated frontend restore closure

**Task:** BACKUP-BASELINE-01B — ISOLATED_FRONTEND_RESTORE_CLOSURE_V1  
**Date:** 2026-07-15  
**Starting HEAD:** `682235a`  
**Verdict:** `BACKUP_BASELINE_01B_FRONTEND_RESTORE_PASS`  
**Next:** `APP-AUTH-06C-PARITY-SIGNAL-INTERPRETATION-PLAN`

## Objective

Close the deferred isolated frontend restore from BACKUP-BASELINE-01 without modifying source application code or `C:\w\psiso\frontend\node_modules`.

## Safety checkpoint

| Item | Value |
|------|-------|
| Source HEAD | `682235a` |
| Source git status lines | 256 (before evidence) |
| Source `node_modules` | YES (59 top-level dirs) |
| Restored frontend | `C:\w\wrt\b01\repository\frontend` |
| Restored `node_modules` before | NO (prior partial copy removed) |
| Backup folder | YES |
| Restored DB | `C:\w\wrt\b01\database\dev.db` |
| Backend 8021 before task | DOWN (restarted for proof) |

## Dependency method

**Method A — OFFLINE_INSTALL** (single attempt, PASS)

```text
cd C:\w\wrt\b01\repository\frontend
npx --yes pnpm@8.10.0 install --frozen-lockfile --prefer-offline
```

- Exit code: 0 (~8.7s)
- Target: `C:\w\wrt\b01\repository\frontend\node_modules`
- Source `node_modules`: not touched (59 dirs before/after)
- Junction: not used

## Restored configuration

Process environment only (no tracked file overwrites):

| Variable | Value |
|----------|-------|
| `VITE_PORT` | `3021` |
| `BACKEND_PORT` | `8021` |
| `DATABASE_URL` | `sqlite+aiosqlite:///C:/w/wrt/b01/database/dev.db` (backend only) |
| Parity flags | unset / false |

API proxy: `vite.config.ts` → `http://localhost:${BACKEND_PORT}` → **8021**

## Backend revalidation (`:8021`)

- Health: `healthy`
- Employees read: 8
- Parity flags: `0 0 0`
- Isolated DB only (not source `dev.db`)

## Frontend build

```text
npx --yes pnpm@8.10.0 run build
```

- Classification: **BUILD_PASS**
- Artifact: `C:\w\wrt\b01\repository\frontend\dist\index.html` (~4.46 MB tree)

## Frontend runtime (`:3021`)

| Check | Result |
|-------|--------|
| `GET /` | 200 |
| `GET /modules` | 200 (representative route) |
| `GET /governance` | 200 |
| Proxy `GET /api/v1/operational-registry/employees` | 200, total=8 |

Classification: **PASS**

## API target

Frontend proxy verified via `:3021/api/...` returning restored backend data. **8021** used; **8001** not used as API target.

## Visual verification

- Route: `/modules`
- HTTP shell load: PASS
- Screenshot: **PARTIAL** — Playwright chromium not installed in environment; owner can verify at `http://127.0.0.1:3021/modules` during a future session

## Source invariance

| Check | Result |
|-------|--------|
| HEAD unchanged | YES (`682235a`) |
| Source `node_modules` | YES, 59 dirs unchanged |
| Business DB counts | unchanged |
| Application code modified by this task | NO |

## Cleanup

- Stopped restored frontend `:3021` and backend `:8021`
- Ports closed
- No junction to remove
- Backup and restore tree preserved

## Backup closure

**FULL** — BACKUP-BASELINE-01 + 01B complete.

## Evidence

`docs/qa/product-system-active-path-isolation-v1/backup_baseline_01b/*.json`

## Delivery footer

```
Verdict: BACKUP_BASELINE_01B_FRONTEND_RESTORE_PASS
Dependency method: OFFLINE_INSTALL
Frontend build: PASS
Frontend runtime: PASS
API target: 8021
Next: APP-AUTH-06C-PARITY-SIGNAL-INTERPRETATION-PLAN
Code changed: NO
Commit: docs/evidence only
```
