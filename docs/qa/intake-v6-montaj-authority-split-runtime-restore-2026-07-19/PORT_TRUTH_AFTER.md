# PORT TRUTH AFTER

## Listeners

| Port | State | Owner |
|------|-------|-------|
| 3000 | LISTENING | Vite (`BACKEND_PORT=8003` root cmd PID `40136`, listen node PID `3640`) |
| 8003 | LISTENING | Canonical uvicorn — parent `8844` (venv) / worker `34480` (Python 3.12), **no `--reload`** |
| 8013 | **none** | Temporary proof BE stopped |

## Health

| Port | Health |
|------|--------|
| 8003 | `{"status":"healthy"}` |
| 3000 | HTTP 200 |
| 8013 | connection refused (expected) |

## ACM PD/Aggregate (canonical :8003)

| Field | Value |
|-------|-------|
| solution_status | `confirmed` |
| blockers | `[]` |
| ACM included | `true` (`TPL-ACM-BOXED-MOUNTING-SUPPORT_v1`) |
| Aggregate conflicts | `[]` |
| finish.updated_at | `2026-07-19T15:37:15.857960` (unchanged — no data rewrite) |

## FE proxy

`http://127.0.0.1:3000/api/v1/.../product-definition` matches direct `:8003` (`confirmed`, blockers `[]`).

## Ghost orphans

Mapped spawn workers for dead :8003 parents — **terminated**. Port released, then fresh BE started from `C:\w\psiso\backend`.
