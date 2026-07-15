# Collaboration membership (HELPER-only)

**Captured:** 2026-07-16 after PROD-FLEX-COLLABORATION-PHASE-1

## Reusable truth

- Membership rows in `execution_task_participants` are **authorization intent**, not work proof.
- Actual work/time remains in `execution_reality` sessions.
- Optional principal remains `assigned_employee_id` on the plan — never a PRINCIPAL membership row.
- JOIN/LEAVE must not start/stop sessions, claim, or change assignment.
- Parent identity for V2: `(order_id, task_id)` where `task_id` is the deterministic materialized key.
- Prefer DB unique `(order_id, task_id, employee_id)` + IntegrityError reactivation over application-only uniqueness.
- Alembic multi-head: upgrade to explicit `s57_create_execution_task_participants`, not bare `head`, while orphan `s50_execution_plan_prepared_by_clarification_target` exists.
- Collaboration read contract: `execution_task_collaboration_read/v1.1` adds `helper_memberships[]` / `authorized_helper_count` without replacing session-derived `actual_workers`.

## Non-goals (still deferred)

Help requests, split pools, `_has_active_session_by_other`, helper My Tasks visibility, UI/Mobile consumers.
