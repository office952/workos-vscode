# BUILD — PROD-FLEX-COLLABORATION-PHASE-1

**Date:** 2026-07-16  
**Purpose:** Deliver HELPER-only collaboration membership foundation (migration, join/leave, read v1.1).  
**Boundary:** No help table, pools, session/assignment/claim changes, UI, Mobile UX, Product System, snapshots.

## Files changed (implementation)

| Area | Paths |
|------|-------|
| Migration | `backend/alembic/versions/s57_create_execution_task_participants.py` |
| Model | `backend/models/execution_task_participant.py`, `backend/models/__init__.py` |
| Flag | `backend/services/flex_membership_flags.py` |
| Service | `backend/services/execution_task_membership_service.py` |
| Read | `backend/schemas/execution_task_collaboration_read.py`, `backend/services/execution_task_collaboration_read_service.py` |
| Schemas | `backend/schemas/execution_task_membership.py` |
| Routers | `backend/routers/operator_tasks.py`, `backend/routers/employee_mobile_tasks.py` |
| Tests | `backend/tests/test_execution_task_participants.py`, collaboration read version bumps |
| Manifest | `scripts/workos-canonical-openapi-paths.json` |
| Docs | worklog + this BUILD |

## Commands + results

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_execution_task_participants.py tests/test_execution_task_collaboration_read.py -q
# 32 passed

.\.venv\Scripts\python.exe -m pytest tests/test_task_work_sessions.py tests/test_employee_mobile_claim_concurrency.py tests/test_execution_task_assignment.py -q
# 15 passed

.\.venv\Scripts\python.exe -m alembic upgrade s57_create_execution_task_participants
.\.venv\Scripts\python.exe -m alembic downgrade s56_add_execution_plan_source_metadata
# upgrade/downgrade OK on temp SQLite
```

Runtime: order `23099` join/leave/rejoin on task `...:vector_prep` via operator collaboration endpoints — PASS.

## Next steps

- Phase 2: help requests, split pools, helper session start
- Phase 3: Operator/Mobile UI consumers
- Do not treat Phase 1 as My Tasks visibility for helpers
