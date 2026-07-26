# FLEX-01A Compound Knowledge

**Accepted HEAD:** `34cc288` → FLEX-01A commit pending  
**Task:** `FLEX-01A-OPERATION-COMPLETION-SEMANTICS-AND-LIVE-RUNTIME-VERIFICATION`  
**Worklog:** `docs/worklog/realignment/2026-07-15_flex_01a_operation_completion_semantics_and_live_runtime_verification.md`

## Durable truths

| Topic | Truth |
|-------|-------|
| `assigned_employee_id` | optional principal — not participation proof |
| sessions | authority for actual work/time |
| session closed (`status=ended`) | **not** operation complete |
| all_sessions_closed | **not** operation complete |
| `derive_task_status_from_sessions == done` | legacy/display only — **not** `operation_completed` |
| `operation_completed` authority | per-session `status=completed` OR `completed_by_employee_id` on **all** closed sessions |
| multi-worker | operation complete only when every session explicitly completed |
| `legacy_or_derived_task_status` | blueprint bucket from legacy derive — may show `done` while `operation_completed=false` |

## Completion authority (files)

- Write: `execution_reality_service.end_task` — `completed` vs `ended` (`backend/services/execution_reality_service.py`)
- Read projection: `derive_operation_completion_truth` (`backend/services/execution_task_collaboration_read_service.py`)
- **No** task-level persisted operation_completed field exists

## Endpoint

`GET /api/v1/operator/orders/{order_id}/task-collaboration-read`  
Permission: `execution.production_blueprint`

## Runtime trap

Port **8001** may host **ghost/stale listeners** (non-killable PIDs). `npm run dev:stack` may reuse stale code. Verify OpenAPI route after restart; use fresh uvicorn if route missing.

## Boundaries (unchanged)

- No DB / migration / UI / participant persistence
- FLEX-02 blocked
- `participants_json` DEFERRED

## Review note

Independent review: APPROVE_WITH_EXPLICIT_LIMITATION — multi-worker requires all sessions explicitly completed; legacy `done` may diverge from `operation_completed`.
