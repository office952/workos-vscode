# PROCESS INVENTORY — before restore

**Captured:** 2026-07-20 (local)  
**Repo:** `C:/w/psiso`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**HEAD:** `184b9dc51b1d9fb4cf449f01954bb909d9a0871c` (`184b9dc`)  
**Staged:** none  
**Foreign WIP:** present (unrelated modified/untracked files; not touched)

## Listeners

### :3000 (FE Vite)

| Field | Value |
|-------|-------|
| PID | `9368` |
| Name | `node.exe` |
| Executable | `C:\Program Files\nodejs\node.exe` |
| Command | `node ...\vite\bin\vite.js --host 127.0.0.1 --port 3000` |
| Start | 2026-07-19 19:01:01 |
| Parent | `20752` → chain rooted at `cmd /c set BACKEND_PORT=8013&& ... vite` (`32104`) |

**Proxy proof (before restore):** FE `/api/v1/.../product-definition` → `blockers=[]` / `confirmed` (matches `:8013`, not stale `:8003`).

### :8003 (canonical BE — STALE / GHOST)

Netstat `LISTENING` PIDs (all **dead** as processes):

| Ghost listen PID | Alive? | Orphan worker still serving |
|------------------|--------|-----------------------------|
| `25988` | NO | `35220` (`spawn_main(parent_pid=25988)`) started 2026-07-19 13:41:35 |
| `27664` | NO | `23792` (`parent_pid=27664`) started 2026-07-19 18:56:43 |
| `30868` | NO | `29460` (`parent_pid=30868`) started 2026-07-19 18:54:32 |
| `11388` | NO | `40616` (`parent_pid=11388`) started 2026-07-19 18:56:59 |
| `34884` | NO | `32180` (`parent_pid=34884`) started 2026-07-19 18:56:14 |

Orphan worker common identity:

- Executable: `C:\Users\offic\AppData\Local\Programs\Python\Python312\python.exe`
- Command pattern: `multiprocessing.spawn.spawn_main(parent_pid=<ghost>, ...)`
- No living uvicorn parent with `--port 8003` in cmdline
- HTTP still answers `/health` and PD with **pre-fix** composition

### :8013 (temporary proof BE — LIVE)

| Field | Value |
|-------|-------|
| Parent PID | `17828` |
| Parent EXE | `C:\w\psiso\backend\.venv\Scripts\python.exe` |
| Parent CMD | `-m uvicorn main:app --host 127.0.0.1 --port 8013` |
| Worker PID | `17840` |
| Worker EXE | `C:\Users\offic\AppData\Local\Programs\Python\Python312\python.exe` |
| Start | 2026-07-19 19:00:55 |
| CWD intent | `C:\w\psiso\backend` (repo venv launch) |

## Other orphan Python (not on :8003 listen map — left alone)

| PID | Dead parent | Note |
|-----|-------------|------|
| `22032` | `9200` | spawn orphan since 2026-07-18; **not** in :8003 listen table |
| `18776` | `38096` | spawn orphan; **not** in :8003 listen table |

## Stop candidates (exact)

Only orphans mapped to ghost `:8003` listen PIDs:

`35220`, `23792`, `29460`, `40616`, `32180`
