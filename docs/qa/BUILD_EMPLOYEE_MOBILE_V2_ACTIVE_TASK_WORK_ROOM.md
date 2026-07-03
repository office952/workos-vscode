# BUILD: Employee Mobile v2 Active Task Work Room

## Purpose

Foundation for `/employee-app-v2` Work Room — operational task screen with pause/resume mobile API, fixed multi-session done derivation, minimal admin `block_reason` visibility.

## Preflight

| Check | Result |
|-------|--------|
| Branch | `local/integration-pr4-plus-svg-path` |
| HEAD (before) | `27d0d92` |
| Migrations | None |
| v1 | Untouched |

## Files changed

### Backend
- `backend/services/task_work_session_service.py`
- `backend/services/employee_mobile_tasks_service.py`
- `backend/routers/employee_mobile_tasks.py`
- `backend/routers/operator_tasks.py`
- `backend/tests/test_task_work_sessions.py`
- `backend/tests/test_employee_mobile_tasks.py`

### Frontend
- `frontend/src/components/workos/employee-mobile-v2/EmployeeMobileV2TaskDetailPage.tsx`
- `frontend/src/components/workos/employee-mobile-v2/EmployeeMobileV2WorkRoomActionBar.tsx` (new)
- `frontend/src/api/employeeMobileTasks.ts`
- `frontend/src/pages/OperatorView.tsx`
- `frontend/src/hooks/useOperatorData.ts`
- `frontend/src/lib/mockData.ts`

### Docs
- `docs/architecture/EMPLOYEE_MOBILE_V2_ACTIVE_TASK_WORK_ROOM_DECISION.md`

## Commands

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_employee_mobile_tasks.py tests/test_task_work_sessions.py -q

cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/pages/EmployeeMobileV2App.test.tsx src/lib/employeeMobileV2Status.test.ts
```

## Boundary

Excluded: join/assist, ExecutionTaskIssue, multi-person confirmations, PWA, v1 changes, migrations.

## Status

See test results in commit message / final agent report.
