# RUNTIME-FRESHNESS-04A — Canonical backend freshness guard (compound knowledge)

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
| `ambiguous_process_tree` (non-uvicorn or mixed) | block, no stop |
| `multiple_listeners` (unresolved mixed ownership) | block, no stop |

**Same-worktree proof:** venv path under project root, `uvicorn main:app` on expected port, parent/child spawn tree. Spawn workers may be `ambiguous` when cmdline lacks root; full uvicorn-only tree without foreign/other-worktree proof may reuse (see limitation).

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

- **System-python uvicorn:** When interpreter is global Python (not `.venv` under project root) but tree is exclusively uvicorn reloader/worker and routes+health pass, guard classifies `current_and_ready` / reuse. Worktree path is not cryptographically proven; mitigated by OpenAPI route freshness and foreign/other-worktree blockers.
- Runtime proof is on canonical worktree only; foreign/other-worktree scenarios exercised via contract tests, not live hostile processes.

## Files changed (04A)

- `scripts/_workos-dev-backend-freshness.ps1` (new)
- `scripts/workos-canonical-openapi-paths.json` (new)
- `scripts/_workos-dev-contract.ps1`
- `scripts/start-dev.ps1`
- `scripts/canonical_startup_contract.test.mjs`

## Test commands

```powershell
npm run test:startup-contract
cd backend; .\.venv\Scripts\python.exe -m pytest tests/test_execution_task_collaboration_read.py -q
cd backend; .\.venv\Scripts\python.exe -m pytest tests/test_task_work_sessions.py tests/test_execution_task_assignment.py tests/test_employee_mobile_tasks.py::test_claim_success_assigns_and_lists_in_my_tasks -q
```

## Forbidden scope

- No backend application code, routers, schemas, services
- No frontend, DB, migrations, seeds, Product System, snapshots, FLEX-02
- No fingerprint endpoint, no generic kill-all

## Accepted HEAD

`3535378` (plan ready); implementation commit follows on `feature/product-system-active-path-isolation-v1`.
