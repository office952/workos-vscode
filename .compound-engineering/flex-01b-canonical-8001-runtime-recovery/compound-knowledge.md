# FLEX-01B — Canonical :8001 runtime recovery (compound knowledge)

## Root cause: ghost listeners on :8001

- **Symptom:** `netstat` shows multiple `LISTENING` rows on `127.0.0.1:8001` (7 observed); `/health` returns 200; OpenAPI **missing** `task-collaboration-read`.
- **Cause:** Orphaned uvicorn `--reload` **worker** processes (`multiprocessing.spawn`) whose **parent reloader PIDs are dead** (ghost in `Get-Process` / `Win32_Process`).
- **Evidence pattern:** Child cmdline contains `spawn_main(parent_pid=<ghost_pid>)` while parent PID is unresolvable.
- **Why `npm run dev:stack` reused stale code:** `Resolve-PortService` in `scripts/start-dev.ps1` treats port occupied + `/health` OK as "already running" (`Test-BackendDevReady` does not check FLEX route freshness). Stale detection (`Test-WorkOsBackendListenerStale`) only runs when health probe **fails**; ghost parent PID path is never refreshed.

## Safe shutdown (WorkOS stack)

1. Enumerate `Get-NetTCPConnection -LocalPort 8001 -State Listen` and `netstat -ano | findstr :8001`.
2. For each ghost parent PID, find living children: `Get-CimInstance Win32_Process` where `CommandLine` matches `parent_pid=<ghost>`.
3. **Stop only confirmed WorkOS uvicorn spawn workers** (and optional temp backends on other ports from prior verification runs).
4. Do **not** `kill-all` on port; do **not** stop unknown PIDs.
5. Stop frontend on :3000 if restarting full stack (`vite` from `C:\w\psiso\frontend`).

## Safe restart

```powershell
# After ports free:
npm run dev:stack
```

- Canonical worktree: `C:\w\psiso`
- Canonical ports: backend **8001**, frontend **3000**
- Expect **one** `LISTENING` row on :8001 after clean start.

## Port ownership checks

```powershell
netstat -ano | findstr ":8001" | findstr LISTENING
Get-NetTCPConnection -LocalPort 8001 -State Listen
Get-CimInstance Win32_Process -Filter "ProcessId=<pid>"
```

- Ghost parent: `Get-Process` and CIM return empty for PID, but `netstat` still lists it.
- Live backend: uvicorn cmdline `--port 8001 --reload`; child `spawn_main(parent_pid=<live_parent>)`.

## OpenAPI route verification (canonical PASS gate)

```powershell
$o = Invoke-RestMethod http://127.0.0.1:8001/openapi.json
$o.paths.'/api/v1/operator/orders/{order_id}/task-collaboration-read'
```

Route must be present on **8001** — alternate ports (e.g. 18012) do not satisfy FLEX-01B.

## Live GET verification

```powershell
Invoke-WebRequest http://127.0.0.1:8001/api/v1/operator/orders/23099/task-collaboration-read -UseBasicParsing
```

- Read-only; dev auth bypass in `APP_ENV=development`.
- Fixture order: **23099** (`ORD-W5INT02-GATE`).
- **DB writes: 0** (confirm via `dev.db` mtime unchanged).

## Stability check

After first PASS, wait ≥15s, then re-verify:

- Single listener on :8001
- Same backend PID still alive
- `/health`, OpenAPI route, GET 200 again

One HTTP 200 is insufficient.

## Known traps

| Trap | Mitigation |
|------|------------|
| Health OK but stale OpenAPI | Always check route in OpenAPI, not just `/health` |
| Ghost parent PIDs | Kill spawn **children**, not unresolvable parents |
| `start-dev.ps1` reuse | Requires owner GO to fix tooling; runtime recovery = stop orphans + restart |
| Windows kernel ghost (port 8000 class) | Different from uvicorn orphan workers; see `windows-ghost-listener-8000-clear-v1` |

## Tooling defect (document only — no auto-fix)

`scripts/start-dev.ps1` + `Test-BackendDevReady`: health-only reuse allows stale backend code to satisfy canonical port contract. **Owner GO required** for script change.

## Scope boundaries

- No FLEX-02
- No DB / UI / Product System / snapshot / participant persistence changes
- No startup script edits in FLEX-01B
