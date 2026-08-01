# Runtime Integrity

**Repo:** `C:\w\psiso`  
**Date:** 2026-07-31 (~23:08–23:20 local)  
**Mode:** Observe only — no start/stop/fix in this batch

---

## Detached stack metadata

From `.workos-dev-detached.json`:

| Field | Value |
|-------|-------|
| `startedAt` | 2026-07-31T23:08:51+03:00 |
| `root` | `C:\w\psiso` |
| `backendPort` | 8000 |
| `frontendPort` | 3000 |
| `backendLauncherPid` | 25264 (powershell — still running) |
| `frontendLauncherPid` | 17980 (powershell — still running) |

Log banners confirm:

- Backend `git_commit = a1c28854`
- Frontend Vite proxy `/api -> http://127.0.0.1:8000`

---

## Ports / processes

| Port | State | Owning PID | Process |
|------|-------|------------|---------|
| 8000 | LISTENING `127.0.0.1` | 28568 | `python` (uvicorn reloader) |
| 3000 | LISTENING `127.0.0.1` | 9044 | `node` (Vite) |

No conflicting second listeners observed on 8000/3000.

---

## Health probes

| Probe | Result |
|-------|--------|
| `GET http://127.0.0.1:8000/health` | **200** `{"status":"healthy"}` |
| `GET http://127.0.0.1:8000/docs` | **200** |
| `GET http://127.0.0.1:8000/api/health` | **404** (path not used; non-blocking) |
| `GET http://127.0.0.1:3000/` | **200** (HTML len≈2543) |
| `GET /api/v1/system/local-compatibility` | **200** — `git_commit=a1c28854`, OD3 gate landed, authorize **false** |

---

## Runtime warnings / errors (observed, not fixed)

| Item | Severity | Notes |
|------|----------|-------|
| `Failed to import module 'routers.intake_v5': No module named 'svgpathtools'` | **WARN** | Startup warning in backend err log; Intake V6 routers still loaded |
| pip “new release available” notice | INFO | Noise |
| Browserslist caniuse-lite stale (frontend err log) | **WARN** | Hygiene only |
| Large Vite chunk warning on build | **WARN** | Build still succeeded |

No crash loops observed in current detached session logs.

---

## Verdict

**PASS WITH WARNINGS** — Backend and frontend are healthy on expected ports with matching SHA. Named warnings are non-blocking for the next Owner GO (do not fix in this audit batch).
