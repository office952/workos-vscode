# BUILD_INTAKE_V4_TASK_DRY_RUN_CNC_FROM_OPERATION_ROWS

## Purpose

Align Intake V4 Production Preview / task dry-run CNC with Material Breakdown `operation_rows` (shared CNC model). One canonical source for CNC preview quantities and metadata.

## Root cause

- Material Breakdown already emitted CNC `operation_rows` via `build_volumetric_letters_cnc_operation_rows`.
- Task dry-run / Production Preview still used `legacy_parallel_mapping` (`face_and_backing_cnc_cut`, aggregated `face_cnc_cut`).
- Operators saw divergent CNC basis (`sheet_nesting_role_split_quote_estimate`) vs per-operation ml / passes in breakdown.

## New canonical source

```txt
CNC_TASK_DRY_RUN_SOURCE = "operation_rows"
```

Defined in `backend/services/intake_v4_cnc_operation_dry_run_service.py`.

Fallback compatibility mapping (`legacy_parallel_mapping` token) is used only when `operation_rows` are missing — warning emitted, not silent divergence.

## Mapping: operation_rows → dry-run candidates

| operation_row key | task candidate | preview fields |
|-------------------|----------------|----------------|
| `cnc_face_cutting_plexiglas_3mm` | separate task | qty ml, MCH-CNC-4020, cnc_router, cnc_operator |
| `cnc_face_bevel_plexiglas_3mm` | separate task | same perimeter basis |
| `cnc_backing_cutting_forex_10mm` | when backing active | passes=5, equivalent ml-pass when owner override |
| `cnc_backing_bevel_forex_10mm` | `forex_10_with_bevel` only | backing bevel perimeter |

Service: `cnc_operation_row_to_task_candidate()`, `cnc_operation_row_to_dry_run_candidate()`, `build_iv3_cnc_candidate_tasks_from_operation_rows()`.

API fields:

- `IntakeV4TaskGenerationDryRunResponse`: `cnc_task_source`, `cnc_operation_candidate_count`, `cnc_operation_candidates`, `compat_cnc_mapping_used` (+ backward-compatible `legacy_cnc_mapping_used`)
- `IntakeV4ProductionHandoffPreviewResponse`: same CNC fields

## PBL expected values (IV4-4B172FD4 fixture geometry)

Face perimeter ≈ **13.62 ml** (`FACE_ML` in tests).

| backing_mode | CNC candidates |
|--------------|----------------|
| `none` | face cut + face bevel; no backing CNC |
| `forex_10_no_bevel` | + backing cut, passes=5, equiv ≈ 68.11 ml-pass; no backing bevel |
| `forex_10_with_bevel` | + backing bevel |

## Quantity comparison (before / after)

| Surface | Before | After |
|---------|--------|-------|
| Production Preview CNC | 1× `face_and_backing_cnc_cut` or generic nesting basis | 2–4 separate operation_rows-aligned candidates |
| Quantities | catalog / nesting estimate | same ml as Material Breakdown `operation_rows` |
| Forex backing cut | not split / no passes in preview | passes=5, equivalent ml-pass visible |

## Files changed

- `backend/services/intake_v4_cnc_operation_dry_run_service.py` (new)
- `backend/services/intake_v4_task_generation_dry_run_service.py`
- `backend/services/intake_v4_production_handoff_preview_service.py`
- `backend/services/intake_v4_production_task_dry_run_service.py`
- `backend/schemas/intake_v4.py`
- `backend/tests/test_intake_v4_cnc_operation_dry_run.py` (new)
- `frontend/src/lib/intakeV4/intakeV4Api.ts`
- `frontend/src/lib/intakeV4/intakeV4CncDryRunDisplay.ts` (new)
- `frontend/src/components/workos/intake-v4/IntakeV4CncOperationPreviewSection.tsx` (new)
- `frontend/src/components/workos/intake-v4/IntakeV4TaskGenerationDryRunPanel.tsx`
- `frontend/src/components/workos/intake-v4/IntakeV4ProductionHandoffPreviewPanel.tsx`
- `frontend/src/components/workos/intake-v3/IntakeV3ProductionTaskDryRunPanel.tsx`
- `docs/architecture/SHARED_CNC_OPERATION_MODEL_AND_CUTTING_SERVICE_TEMPLATE.md`
- `docs/architecture/PRODUCTSYSTEM_SHARED_TECHNICAL_MODULES.md`

## Tests

### Backend

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_cnc_operation_dry_run.py -q
```

Covers: backing modes, quantity match breakdown, passes/equiv, source=operation_rows, missing_rate, boundary flags, production preview V3 compatibility candidates, no fallback when rows exist.

### Frontend

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/intakeV4/intakeV4CncDryRunDisplay.test.ts src/components/workos/intake-v4/IntakeV4CncOperationPreviewSection.test.tsx
```

## Runtime smoke (PBL IV4-4B172FD4)

Workspace operator URL: `http://localhost:3000/intake-v4-app/0f300dcf-0b77-4fc1-affd-6e2a20329804/operator`

Scenarios: `backing_mode` none / `forex_10_no_bevel` / `forex_10_with_bevel` — verify Production Preview CNC section matches Material Breakdown operation rows.

## Remaining gaps

- `operation_catalog_key` still `pending_mapping` for some rows — mapping_gaps shown in preview.
- CNC operation rates not in Pricing Registry — `missing_rate` intentional.
- `TPL-CNC-CUTTING-SERVICE` UI not in scope.
- Real task creation, ExecutionPlan, stock consumption — future guarded builds.

## Non-goals (confirmed)

No real tasks, ExecutionPlan, `tasks_json`, stock consumption, Pricing Registry, CostEngine, employee assignment, Oracal UI catalog migration, quote/order creation.

## Boundary

Preview/dry-run alignment only. Material rows (Plexiglas / Forex) remain separate from CNC operation rows.
