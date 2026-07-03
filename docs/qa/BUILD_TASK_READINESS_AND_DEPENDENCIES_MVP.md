# BUILD: Task Readiness & Dependencies MVP

## Purpose

Introduce real task dependencies on `execution_plan.tasks_json`, compute readiness server-side, block Start on ineligible tasks, and surface readiness in Employee Mobile pipeline and Operator Blueprint.

## Audit finding (baseline)

- Dependencies were **not** persisted on execution plans at runtime.
- `Acum` / current task was **assignment + frontend order only**.
- Order 1 had T-004 `in_progress` while T-003 was not done — no guard.
- Material blocks at Start: **deferred** (unchanged).

## Assigned vs startable

| Concept | Meaning |
|---------|---------|
| **Alocat** | `assigned_employee_id` set on plan task |
| **Eligibil / startable** | Dependencies satisfied, not done/blocked, assigned to employee |
| **Așteaptă task anterior** | `depends_on_task_ids` not all `done` in reality |
| **În lucru** | Active work session; may show dependency warning if started early |

## MVP dependency map (process_id → resolved task_ids)

| Task | depends_on |
|------|------------|
| T-004 Lipire canturi (`return_face_bonding`) | T-002, T-003 |
| T-006 Montaj LED (`led_install_letters`) | T-005 |
| T-007 Cablare (`electrical_letters`) | T-006 |
| T-009 Asamblare (`assembly_letters`) | T-004, T-005, T-006, T-007 |
| T-010 QC (`qc_letters`) | T-009 |
| T-011 Ambalare (`packaging_letters`) | T-010 |
| T-008 Pregătire montaj | **no strict deps** (parallel OK) |
| T-001 Vector prep | **soft gate only** (not global hard dep) |

## Material requirements

Deferred. Model reserves `waiting_material` status; no inventory check at Start.

## Readiness statuses

`done`, `in_progress`, `blocked_manual`, `waiting_predecessor`, `waiting_material`, `eligible`, `assigned_not_mine`, `unassigned`

## Backend guard

`employee_mobile_tasks_service.start_my_task` evaluates readiness before creating a work session. Returns **409** with `code: task_not_ready` when `is_startable=false`.

Existing guards preserved: assignment, blocked, done, employee guard, work sessions.

Operator start override: **deferred** (no silent bypass).

## Inconsistent existing reality

If a task is already `in_progress` but predecessors are incomplete:

- **Do not** auto-stop or close sessions.
- UI/API expose `dependency_warning` on in_progress tasks.

## Files changed

### Backend

- `backend/services/task_dependency_rules_service.py` (new)
- `backend/services/task_readiness_service.py` (new)
- `backend/routers/execution.py` — apply deps on new plan generation
- `backend/services/employee_mobile_tasks_service.py` — readiness on list + start guard
- `backend/services/employee_mobile_order_blueprint_service.py` — readiness fields + current task logic
- `backend/services/order_production_blueprint_service.py` — operator readiness
- `backend/routers/employee_mobile_tasks.py` — response models
- `backend/services/dev_employee_mobile_sandu_fixture_service.py` — idempotent dependency backfill
- `backend/tests/test_task_readiness_dependencies.py` (new)

### Frontend

- `frontend/src/lib/employeeMobilePipelineEligibility.ts`
- `frontend/src/components/workos/employee-mobile/EmployeeMobileOrderPipelineView.tsx`
- `frontend/src/api/employeeMobileOrderBlueprint.ts`
- `frontend/src/api/employeeMobileTasks.ts`
- `frontend/src/api/operatorProductionBlueprint.ts`
- `frontend/src/components/workos/OperatorProductionBlueprintPanel.tsx`
- Tests: pipeline eligibility + EmployeeMobileApp

## Commands + results

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_task_readiness_dependencies.py tests/test_employee_mobile_tasks.py tests/test_employee_mobile_order_blueprint.py tests/test_operator_production_blueprint.py tests/test_task_work_sessions.py -q
# 48 passed

cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/employeeMobilePipelineEligibility.test.ts src/pages/EmployeeMobileApp.test.tsx
```

Dev backfill (existing plans only):

```powershell
cd backend
$env:DATABASE_URL='sqlite+aiosqlite:///.../backend/dev.db'
.\.venv\Scripts\python.exe scripts/dev_seed_employee_mobile_sandu_fixture.py --apply
# plan_dependencies_backfilled
```

**Note:** Production/staging plans created before this build are **not** auto-migrated. Only new plans from `POST /execution/plan/from-order` and dev Sandu fixture backfill.

## Smoke (Sandu)

After backend reload + fixture `--apply`:

- T-004 `in_progress` + `dependency_warning` (T-003 blocking)
- T-006 `waiting_predecessor` (T-005)
- T-007 `waiting_predecessor` (T-006)
- T-008 eligible if assigned and not blocked/done
- No cost/preț/marjă/payroll in employee payloads

## Deferred

- Material reservation / inventory-at-start
- Dependency editor UI
- Operator/admin force-start override + audit log
- Auto-scheduling / per-station queues
- Assist eligibility engine

## Boundary

- No CostEngine changes
- No work session model changes
- No commit/push in this build log entry
