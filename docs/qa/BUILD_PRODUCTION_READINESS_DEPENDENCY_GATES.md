# BUILD: Production Readiness Dependency Gates

## Purpose

Enforce unified backend readiness gates before any task start (Employee Mobile, Operator, ExecutionDetail). Extend preparation dependencies (vector → CNC, template, vinyl) and surface readiness on desktop blueprint + execution UI.

## Context

- Branch: `local/integration-pr4-plus-svg-path`
- Base HEAD (pre-build): `17ee098` — `feat(desktop): add preparation ownership and template costing foundation`
- Prior audit: Production Task Dependencies and Preparation Readiness Gates (read-only)

## MVP rules implemented

See `docs/architecture/PRODUCTION_READINESS_DEPENDENCY_GATES_DECISION.md`.

## Files changed

### Backend

- `backend/services/task_dependency_rules_service.py` — `PREPARATION_DEPENDENCY_RULES`, CNC machine_type fallback
- `backend/services/task_preparation_readiness_service.py` (new) — template, vinyl prep gates
- `backend/services/task_readiness_service.py` — new statuses, structured reasons
- `backend/services/task_start_gate_service.py` (new) — `assert_task_startable`, override metadata
- `backend/services/employee_mobile_tasks_service.py` — shared gate on start
- `backend/routers/operator_tasks.py` — shared gate + override on start
- `backend/routers/execution.py` — shared gate + override on `start-task`
- `backend/services/order_production_blueprint_service.py` — readiness_reasons on tasks
- `backend/services/material_procurement_status_service.py` — planning counters
- `backend/tests/test_production_readiness_start_gates.py` (new)
- `backend/tests/test_task_readiness_dependencies.py` — CNC depends on vector_prep

### Frontend

- `frontend/src/api/operatorProductionBlueprint.ts` — types for reasons + counters
- `frontend/src/api/execution.ts` — startTask override params
- `frontend/src/components/workos/OperatorProductionBlueprintPanel.tsx` — readiness messages, chips
- `frontend/src/pages/ExecutionDetail.tsx` — blueprint readiness fetch, disabled Start, override reason

### Docs

- `docs/architecture/PRODUCTION_READINESS_DEPENDENCY_GATES_DECISION.md`
- `docs/qa/BUILD_PRODUCTION_READINESS_DEPENDENCY_GATES.md`

## Commands + results

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_task_readiness_dependencies.py tests/test_material_procurement_status.py tests/test_operator_production_blueprint.py tests/test_production_readiness_start_gates.py -q
```

Expected: all targeted tests pass (48+).

Result (2026-06-14): **48 passed** in 2.16s (1 flaky setup retry on blueprint fixture — passes on re-run).

## Boundary

| Area | Touched? |
|------|----------|
| Employee Mobile UX / Work Room | No |
| PWA / start_url | No |
| CostEngine | No |
| Pricing | No |
| Migrations | No |
| Auto-assignment / join-assist | No |
| Notification Center | No |
| Generic document block | No |
| Global `not_checked` material block | No |

## PASS criteria

- [x] All start paths use `assert_task_startable`
- [x] CNC blocked without `vector_prep` (unless override)
- [x] `mounting_template_cnc_cut` respects paper/forex/none
- [x] `waiting_template_decision` when template type missing/invalid
- [x] Operator/ExecutionDetail cannot bypass readiness silently
- [x] Employee Mobile compatible (409 `task_not_ready`)
- [x] Desktop UI shows readiness reason; Start disabled or override with reason
- [x] Targeted backend tests pass

## Deferred

- Required/critical document gate (mechanism missing)
- Generic print file gate
- Operator blueprint inline Start button (panel is read-only for start; operator uses task-action API)

## Verdict

**PASS**
