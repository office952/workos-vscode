# RUNTIME-FRESHNESS-04 — Canonical backend freshness guard (compound knowledge)

## 04B correction (ambiguous fail-closed)

**Owner review:** 04A `APPROVE_WITH_EXPLICIT_LIMITATION` — ambiguous all-uvicorn trees could reuse when health + OpenAPI passed.

**04B rule:** OpenAPI freshness ≠ process ownership. Decision matrix:

| Ownership | Freshness | Action |
|-----------|-----------|--------|
| `same_worktree` | fresh | reuse |
| `same_worktree` | stale routes | controlled_stop |
| `other_worktree` | any | BLOCK, no stop |
| `foreign_process` | any | BLOCK, no stop |
| `ambiguous` | any | BLOCK, no stop, no reuse |

Removed: `allUvicornAmbiguous` bypass, `onlyWorkOsUvicornTree` reuse, health-only fallback reuse.

## Parent-lineage proof (Windows uvicorn reload)

- Reload listener PID often shows **system-python** executable; venv proof is on **parent chain**.
- `Test-WorkOsBackendProcessParentLineageProof` walks ancestors for:
  - `backend/.venv/Scripts/python.exe` under `ProjectRoot` in parent cmdline, or
  - `dev-backend.ps1` / `start-dev.ps1` / `dev.ps1` under `ProjectRoot`.
- Evidence tag: `parent_lineage_project_venv`.
- Spawn workers inherit proven parent via `spawn_worker_inherits_proven_parent`.

**Limitation:** Lineage trusts canonical launcher ancestry under `ProjectRoot`; listener executable alone is insufficient on Windows reload.

## Original ghost-worker root cause (FLEX-01B)

- Orphaned uvicorn `--reload` workers on `127.0.0.1:8001` with dead parent PIDs.
- `/health` returned 200 while OpenAPI lacked shipped routes (e.g. `task-collaboration-read`).
- Legacy `start-dev.ps1` reused any occupied port when health alone passed.

## Freshness contract (BackendFresh)

```
BackendFresh =
  health OK
  AND all canonical OpenAPI manifest paths present
  AND process/listener tree safe for current WorkOS worktree
```

Health-only readiness is **rejected**. Missing manifest routes fail closed (or trigger controlled stop when same-worktree is proven).

## Manifest

- **Path:** `scripts/workos-canonical-openapi-paths.json`
- **Version:** `1`
- **Routes (v1):**
  1. `/api/v1/operator/orders/{order_id}/task-collaboration-read`
  2. `/api/v1/operator/orders/{order_id}/task-truth`
  3. `/api/v1/operator/tasks`
  4. `/api/v1/execution/plan/{order_id}`
  5. `/api/v1/intake-v6/workspaces`
- **Fail closed:** missing file, malformed JSON, missing `manifest_version`, empty `required_paths`, duplicate paths.
- Single source of truth — do not duplicate route lists in other scripts.

## Process classification

| Classification | Action |
|----------------|--------|
| `current_and_ready` | reuse |
| `backend_absent` | start |
| `canonical_routes_missing` / stale same-worktree | `controlled_stop` → start |
| `other_worktree` | block, no stop |
| `foreign_process` | block, no stop |
| `ambiguous_process_tree` | block, no stop, no reuse |
| `multiple_listeners` (unresolved mixed ownership) | block, no stop |

**Same-worktree proof:** venv executable path under project root, venv path in parent cmdline (lineage), or canonical launcher script under `ProjectRoot`. Reuse requires `$ownerships -contains "same_worktree"`.

**Never:** kill-all, foreign kill, other-worktree kill.

## Uvicorn reload / spawn handling

- Enumerate **all** `LISTENING` rows on port 8001 (dedupe by PID).
- Resolve reloader + `spawn_main(parent_pid=…)` workers; detect ghost parents.
- Controlled stop targets resolved tree PIDs only (`Stop-WorkOsBackendProcessTreeControlled`).

## Bounded retries

| Probe | Attempts | Delay |
|-------|----------|-------|
| OpenAPI fetch | 3 | 500 ms |
| Port release after stop | 20 | 250 ms |
| Health startup (`Wait-ForService`) | existing start-dev bounds | — |

No infinite restart loop.

## Runtime acceptance (04A session)

- Worktree: `C:\w\psiso`
- Ports: backend `8001`, frontend `3000`
- `npm run dev:stack` → backend ready ~6s
- Second `start-dev.ps1` → reuse, no duplicate listeners
- Live GET order `23099` → 200, `execution_task_collaboration_read/v1`, 13 tasks, DB mtime unchanged

## Known limitations

- **Parent-lineage on Windows reload:** Listener may show global `python.exe`; proof is via ancestor venv/launcher cmdline under `ProjectRoot`, not listener `Get-Process.Path` alone.
- Runtime proof is on canonical worktree only; foreign/other-worktree/ambiguous scenarios exercised via contract tests.

## Files changed (04A + 04B)

- `scripts/_workos-dev-backend-freshness.ps1`
- `scripts/workos-canonical-openapi-paths.json` (04A only)
- `scripts/_workos-dev-contract.ps1` (04A only)
- `scripts/start-dev.ps1` (04A only)
- `scripts/canonical_startup_contract.test.mjs`

## Accepted HEAD

`c2ceaf9` (04A); 04B commit follows.

## Test commands

```powershell
npm run test:startup-contract
cd backend; .\.venv\Scripts\python.exe -m pytest tests/test_execution_task_collaboration_read.py -q
cd backend; .\.venv\Scripts\python.exe -m pytest tests/test_task_work_sessions.py tests/test_execution_task_assignment.py tests/test_employee_mobile_tasks.py::test_claim_success_assigns_and_lists_in_my_tasks -q
```

## Forbidden scope

- No backend application code; no DB/migrations; no FLEX-02; no fingerprint endpoint; no kill-all
