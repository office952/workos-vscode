# BACKUP-BASELINE-01 — Full local application backup and restore verification

**Task:** BACKUP-BASELINE-01 — FULL_LOCAL_APPLICATION_BACKUP_AND_RESTORE_VERIFICATION_V1  
**Date:** 2026-07-15  
**Starting HEAD:** `deb5d69`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Verdict:** `BACKUP_BASELINE_01_BACKUP_PASS_RESTORE_PARTIAL`  
**Next:** `BACKUP-BASELINE-01B-RESTORE-CLOSURE`

## Purpose

Safety baseline before normal roadmap continuation. Full local backup outside worktree, isolated DB restore proof, manifest/checksums — without modifying application logic or business data.

## Backup location

| Field | Value |
|-------|-------|
| Backup ID | `workos_full_backup_20260715_125751_deb5d69` |
| Backup root | `C:\w\workos_backups\workos_full_backup_20260715_125751_deb5d69` |
| Restore test DB | `C:\w\wrt\b01\database\dev.db` |
| Timestamp | 2026-07-15T12:57:51+03:00 |

## Repository safety (gate 1)

- **HEAD:** `deb5d6942865448114bcad634a738eefc3bda19e` (`deb5d69`)
- **Branch:** `feature/product-system-active-path-isolation-v1`
- **Worktree:** `C:\w\psiso` — **DIRTY** (256 lines `git status --short`)
- Dirty state preserved: repository copy + `git_state/diff_*.patch` + `untracked_inventory.txt`
- No unrelated commits; no discard of uncommitted files

## Process inventory and shutdown

Canonical writers stopped before DB backup:

- `:3000` frontend (CANONICAL)
- `:8001` backend (CANONICAL)
- `:8000` ghost (GHOST — same `dev.db` risk; port closed before backup)
- `:8011` pilot — not listening

Evidence: `docs/qa/product-system-active-path-isolation-v1/backup_baseline_01/process_inventory_*.json`

## Database

| Check | Result |
|-------|--------|
| Engine | SQLite (`backend/dev.db`) |
| Method | `sqlite3.Connection.backup` API after writers stopped |
| Integrity | `ok` |
| Size | 2,174,976 bytes |
| SHA-256 | `010f3b1a6e63ac9441061e1b38b7f4e819ada8c331a59fe615bf67ee914ac0c2` |
| Tables | 51 |
| Classification | `DATABASE_BACKUP_PASS` |

Isolated restore DB at `C:\w\wrt\b01\database\dev.db`: integrity `ok`, table counts match backup.

## Repository copy

- **Path:** `repository\psiso\` (5,680 files, ~746 MB)
- **`.git`:** included
- **Exclusions:** `node_modules`, `.venv`, `__pycache__`, build caches — documented in `manifest/repository_exclusions.json`

## Runtime files

No `backend/storage/*` uploads present at backup time. Inventory recorded; DB is primary runtime artifact.

## Config and secrets

- Variable names only in `config_inventory/`
- **Secrets exposed in evidence:** NO
- JWT values not written to manifests

## Restore test summary

| Domain | Result |
|--------|--------|
| Git restore | PASS — HEAD/branch match; dirty state preserved |
| Database restore | PASS — isolated copy; counts match |
| Backend restore (`:8021`) | PASS — health, employees, machines, orders (prior evidence) |
| Frontend restore (`:3021`) | **NOT_EXECUTED_SAFE_DEFERRED** |
| Representative reads | PASS (backend, prior evidence) |

### Frontend deferral (owner-directed)

Per owner instruction: **no** `node_modules` install, delete, move, or link in isolated restore. Frontend runtime startup deferred to **BACKUP-BASELINE-01B-RESTORE-CLOSURE**. This is **not** a backup failure.

## Source integrity

- `C:\w\psiso` HEAD/branch unchanged
- `frontend/node_modules` present (source)
- Business table counts unchanged vs backup baseline
- Ephemeral delta only: `oidc_states` 0→1 (non-business auth state)
- Parity flags: ALL_FALSE

## Validation matrix

See `docs/qa/product-system-active-path-isolation-v1/backup_baseline_01/final_backup_validation_matrix.json`

**Backup validation:** PARTIAL (frontend runtime deferred only)

## Files changed (docs only)

- `docs/qa/product-system-active-path-isolation-v1/backup_baseline_01/*.json`
- `docs/worklog/backup/2026-07-15_backup_baseline_01_full_local_application_backup_restore_v1.md`
- `docs/master/workos-e2e/WORKOS_E2E_STATUS.md` (backup/safety checkpoint)
- `docs/master/workos-e2e/WORKOS_E2E_TASK_GRAPH.md` (backup/safety checkpoint)

## Commands

- DB backup: `database/_backup_db.py` (sqlite3 backup API)
- Closure verification: `restore_test/_minimal_closure_verify.py`
- No archive committed to git; folder backup is primary artifact

## Boundary

- No application logic changes
- No schema/migration changes
- No push / PR
- Backup artifacts remain outside `C:\w\psiso`

## Roadmap

`APP-AUTH-06C-PARITY-SIGNAL-INTERPRETATION-PLAN` remains blocked until **BACKUP-BASELINE-01B** completes isolated frontend restore closure.

## Delivery footer

```
Task: BACKUP-BASELINE-01
Starting HEAD: deb5d69
Backup ID: workos_full_backup_20260715_125751_deb5d69
Backup root: C:\w\workos_backups\workos_full_backup_20260715_125751_deb5d69
Source worktree: C:\w\psiso — DIRTY
Repository backed up: PASS
Database backed up: PASS
Frontend restore runtime: NOT_EXECUTED_SAFE_DEFERRED
Verdict: BACKUP_BASELINE_01_BACKUP_PASS_RESTORE_PARTIAL
Next: BACKUP-BASELINE-01B-RESTORE-CLOSURE
Code changed: NO
DB business data changed: NO
```
