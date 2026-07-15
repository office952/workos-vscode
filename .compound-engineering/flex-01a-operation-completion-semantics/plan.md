# FLEX-01A Plan — Operation completion semantics and live runtime verification

**Starting HEAD:** `34cc288`  
**Verdict target:** `FLEX_01A_OPERATION_COMPLETION_SEMANTICS_AND_LIVE_RUNTIME_COMPLETE`

## Workstream A — Completion authority audit (confirmed)

### Facts

1. **No task-level operation_completed field** exists in `execution_plan.tasks_json` or a separate table.
2. **Session-level explicit complete** is written by `ExecutionRealityService.end_task` when `completion_fields.completed_by_employee_id` is set (`execution_reality_service.py` L254–257) → `status=completed`.
3. **Session stop without complete** uses `end_task` without completion_fields → `status=ended`.
4. **`completed_by_employee_id` is session-scoped**, not operation-scoped (`employee_mobile_tasks_service.complete_my_task`, `operator_tasks` complete action).
5. **`derive_task_status_from_sessions`** (`task_work_session_service.py` L74–83) returns `done` when no active sessions and any `ended_at` — **does not distinguish stop vs complete**.
6. **Pause** annotates session (`paused_at`) without ending; not completion.

### Decision: CASE A (partial explicit authority)

Use **per-session explicit completion signals** for `operation_completed`:

- `operation_completed=true` only when **all sessions closed** AND **every closed session** has `status==completed` OR `completed_by_employee_id`.
- `operation_completed=false` when active sessions remain OR any closed session is `ended` without explicit complete.
- `operation_completed=null` only when ambiguous empty edge (no sessions → false with source `no_sessions`).

**Do NOT** use `derive_task_status_from_sessions == "done"` for `operation_completed`.

Expose legacy separately as `legacy_or_derived_task_status` (blueprint bucket).

### Prohibited

- Modifying `derive_task_status_from_sessions`
- Modifying write paths

## Workstream B — Runtime route audit (confirmed)

- Route registered in `operator_tasks.py` via auto `include_routers_from_package` in `main.py`.
- Prior FLEX-01 report: live process stale → OpenAPI missing route.
- Fix: restart `npm run dev:stack`, verify OpenAPI + live GET with dev auth bypass.

## Files permitted

- `backend/schemas/execution_task_collaboration_read.py`
- `backend/services/execution_task_collaboration_read_service.py`
- `backend/tests/test_execution_task_collaboration_read.py`
- `docs/worklog/realignment/2026-07-15_flex_01a_operation_completion_semantics_and_live_runtime_verification.md`
- `.compound-engineering/flex-01a-operation-completion-semantics/compound-knowledge.md`
- `.compound-engineering/flex-01a-operation-completion-semantics/plan.md`
- Canonical status/task graph (post-verify)

## Files forbidden

- DB, migrations, frontend, mobile write paths, global session helpers, FLEX-02

## Tests

Update scenarios 3–6 in `test_execution_task_collaboration_read.py`; add live runtime script evidence in worklog.

## Rollback

Revert collaboration read service/schema/test changes only.

## Stop conditions

- If explicit session signals insufficient → use `unknown` not false positive complete
- If live route missing after restart → PARTIAL/BLOCKED runtime
