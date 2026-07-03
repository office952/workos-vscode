# BUILD — INTAKE_V3_PRODUCTION_TASK_GENERATION_DRY_RUN_CONTRACT

## Purpose

Add a **read-only production task generation dry-run contract** for Intake V3 / TPL-VOLUMETRIC-LETTERS. Returns candidate task groups, candidate preview tasks, dependencies, inputs, blockers, and warnings — without creating ExecutionPlan, ExecutionTask, WorkSession, Inventory mutations, or starting production.

## Context

- Base commit: `1d326c0` — material quantity / geometry / material cost breakdown informative
- Scope: `dry_run_scope = production_task_generation_preview_only`
- IV3 chain through convert + production readiness + material breakdown remains unchanged

## Production / task model audit

| Question | Answer |
|----------|--------|
| ExecutionPlan model? | Yes — `backend/models/execution_plan.py`: `order_id`, `order_code`, `snapshot_version`, `tasks_json`, `total_estimated_time_minutes`. Write-once from order snapshot via `ExecutionPlanService.from_order()`. |
| ExecutionTask model? | No dedicated SQLAlchemy model — tasks live in `ExecutionPlan.tasks_json` as JSON dicts (`PlannedTask.to_dict()`). |
| Existing task generation from Order? | `ExecutionPlanService.from_order()` reads order snapshot only; IV3 handoff uses `build_task_seed_candidates()` in `intake_v3_production_handoff_adapter.py` (preview seeds, `non_executable=True`). |
| Accidental task creation risk? | Dry-run service does not import `ExecutionPlanService` or execution routers. All mutation flags hard-coded false. |
| Default real task status? | N/A for dry-run. Execution layer uses `tasks_json` state in plan (not created here). |
| Required ExecutionTask fields? | N/A — preview uses `IntakeV3CandidateProductionTask` with `will_create_real_task=false`. |
| Task dependencies in model? | Seeds carry `depends_on: list[str]` in handoff adapter; dry-run maps to `IntakeV3CandidateTaskDependency`. |
| assigned_to / station / department? | Not on ExecutionPlan JSON in IV3 path; preview exposes `station_hint` / `department_hint` from seed catalog. |
| Multi-person / assistable? | Not modeled in dry-run; `employee_mobile_action_allowed=false` on seeds. |
| IV3 data for useful dry-run? | Confirmed model, finish assignments, operation flags, geometry summary (material breakdown service), production readiness status. |

## Dry-run context / data sources

- `load_iv3_source_context()` — shared with material breakdown (order / quote / workspace)
- Production readiness status — `get_iv3_order_production_readiness*` (read-only)
- Geometry + material rows — `extract_geometry_summary`, `resolve_material_quantity_rows` (read-only)
- Task seeds — `build_task_seed_candidates(workspace, operation_flags)` from handoff adapter
- Order linkage for workspace path — `check_existing_order_for_iv3_quote()` when quote converted

## Candidate groups strategy (TPL-VOLUMETRIC-LETTERS)

Eight preview groups mapped from handoff seed catalog:

1. Prepress / verificare fișiere
2. CNC fețe plexiglas (+ optional șanfren when bevel perimeter present)
3. CNC backing Forex (parallel hint with face/return forming)
4. Cant aluminiu / modelare cant
5. Finisaj / colantare (conditional on finish flags)
6. LED / electrică
7. Asamblare litere
8. Ambalare / predare montaj

Groups/tasks conditioned on confirmed model, finish assignments, and seed `active` flags — not hardcoded HUB in service (HUB only in tests).

## Candidate task strategy

- Preview IDs: `dryrun-{seed-with-dashes}`; CNC face/backing split from combined seed
- Inputs: real letters / contours / holes (holes ≠ letters), material row quantities with quality
- No real task IDs, employees, schedules, inventory reservations, or operational cost

## Dependency strategy

- Seed `depends_on` chains mapped to candidate task IDs
- Extra preview edges: prepress/CNC file prep → face cutting; assembly → packaging
- Parallelization hints via `parallel_with` on backing CNC task

## Blockers / warnings

| Code | Severity | When |
|------|----------|------|
| `missing_confirmed_production_model` | blocking | No confirmed snapshot |
| `missing_finish_assignments` | blocking | No finish data |
| `production_readiness_not_ready` | blocking | Readiness status blocked |
| `missing_production_readiness` | warning | Quote-only / missing order path |
| `missing_material_breakdown` | warning | Material inputs may be partial |
| `geometry_partial` | warning | Incomplete perimeter metrics |
| `unsupported_product_template` | warning | Non TPL-VOLUMETRIC-LETTERS |

## Explicit no Execution / Inventory evidence

- Service imports no `ExecutionPlanService`, inventory routers, or CostEngine
- Tests assert `ExecutionPlan` and `StockMovement` counts unchanged; order/quote status unchanged
- Response boundary flags all false for mutations

## Files changed

### Backend

- `backend/services/intake_v3_production_task_dry_run_service.py` (new)
- `backend/schemas/intake_v3.py` — dry-run response models
- `backend/routers/intake_v3_workspaces.py` — GET endpoints
- `backend/services/intake_v3_workspace_service.py` — wrappers
- `backend/tests/test_intake_v3_production_task_dry_run.py` (new)

### Frontend

- `frontend/src/lib/intakeV3/productionTaskDryRunContracts.ts` (new)
- `frontend/src/lib/intakeV3/api.ts` — fetch helpers
- `frontend/src/lib/intakeV3/contracts.ts` — re-exports
- `frontend/src/components/workos/intake-v3/IntakeV3ProductionTaskDryRunPanel.tsx` (new)
- `frontend/src/pages/IntakeV3App.tsx` — panel + refresh
- `frontend/src/lib/intakeV3/flowState.ts` — `task_dry_run` step
- `frontend/src/lib/intakeV3QuoteCommercialGuard.ts` — guidance copy
- `frontend/src/components/workos/intake-v3/IntakeV3OrderProductionReadinessPanel.tsx` — guidance copy
- Tests: `IntakeV3App.test.tsx`, `flowState.test.ts`

### Docs

- `docs/qa/BUILD_INTAKE_V3_PRODUCTION_TASK_GENERATION_DRY_RUN_CONTRACT.md` (this file)
- Updated `docs/intake-v3/00_STATUS.md`, `06_BUILD_ROADMAP.md`, `07_DECISIONS_LOG.md`, `03_WORK_INTAKE_TO_QUOTES_ORDERS_PRODUCTION.md`, `04_READINESS_AND_BLOCKERS_MODEL.md`

## Endpoints (read-only)

```http
GET /api/v1/intake-v3/orders/{order_id}/production-task-dry-run
GET /api/v1/intake-v3/quotes/{quote_id}/production-task-dry-run
GET /api/v1/intake-v3/workspaces/{workspace_id}/production-task-dry-run
```

## Commands + results

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v3_production_task_dry_run.py tests/test_intake_v3_material_quantity_breakdown.py tests/test_intake_v3_order_production_readiness.py tests/test_intake_v3_guarded_convert_to_order.py -q
# 54 passed

.\.venv\Scripts\python.exe -m pytest tests/test_intake_v3_guarded_accept_flow.py ... tests/test_volumetric_execution_task_order.py -q
# 221 passed

cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/pages/IntakeV3App.test.tsx src/lib/intakeV3/flowState.test.ts src/lib/intakeV3QuoteCommercialGuard.test.ts src/lib/quoteCommercialGuidance.test.ts
# 176 passed
```

## Boundary

- Does **not** create ExecutionPlan, ExecutionTask, WorkSession
- Does **not** mutate Order, Quote, Inventory, StockMovement
- Does **not** call CostEngine or compute operational cost/labor
- Does **not** assign employees or start production
- UI has **no** Generate Tasks / Start Production / Assign / Reserve buttons

## Next build options

1. Geometry metrics snapshot persistence (reduce `geometry_partial` warnings)
2. Inventory availability read-only check
3. Guarded ExecutionPlan / ExecutionTask creation foundation

## Verdict

**PASS** — dry-run contract implemented read-only with tests green; no commit per build instructions.
