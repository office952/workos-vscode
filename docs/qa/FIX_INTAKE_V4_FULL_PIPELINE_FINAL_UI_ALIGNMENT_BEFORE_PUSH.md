# FIX_INTAKE_V4_FULL_PIPELINE_FINAL_UI_ALIGNMENT_BEFORE_PUSH

## Purpose

Close the three operator-facing UI gaps from
`SMOKE_INTAKE_V4_FULL_3_STEP_PIPELINE_PBL_LAYERS_REVIEW_CONFIRM` (CONDITIONAL PASS)
before pushing the 5-commit local stack on `local/integration-pr4-plus-svg-path`.

## Smoke source

- Workspace: `IV4-4B172FD4` / `pbl-layere.svg`
- Gaps:
  1. Layers showed `Cant / volum calculat = 11.63 m` while Review/Confirm used `15.47 m`
  2. Layer role dropdown still had `Return / cant`
  3. Task preview/catalog still showed `Colantare cant …`

## What changed

### Layers geometry (Task B)

- `IntakeV4SvgAnalyzerStep` now uses `resolveQuoteGeometryForWorkspace` (same as Review/Confirm), including `finish_setup` enrichment for `return_material_perimeter_ml`.
- `IntakeV4GeometryPanel`: label **Perimetru LED / exterior** (test id `intake-v4-geometry-led-perimeter`) vs **Cant / volum calculat** on `return_material_perimeter_ml`; CNC row unchanged.

### Layer role dropdown (Task C)

- New `intakeV4LayerRoleOptions.ts`: V4-only labels; `return` value kept, label **Cant / volum** (not removed — still valid for legacy payloads).

### Task catalog wording (Task D)

- New `intake_v4_operator_task_labels.py` — display-only overrides for Intake V4:
  - `return_vinyl_application_workbench` → **Aplicare Oracal 651 pe cant / volum la banc de lucru**
  - `face_vinyl_application_final` → **Aplicare autocolant pe fețele literelor**
- Applied in `build_v4_task_preview_response` and `build_v4_production_task_dry_run` candidate task titles.
- Operation keys, dependencies, and task generation logic unchanged.

## What did NOT change

- Backend geometry formulas, material quantities, quote policy, Pricing Registry, CostEngine
- V3 catalog `display_name` strings in `intake_v3_production_handoff_adapter.py`
- Order / quote / ExecutionPlan / `tasks_json` / inventory
- V2 / V3 / Auth surfaces

## Files changed

| Area | Files |
|------|--------|
| Frontend Layers | `IntakeV4SvgAnalyzerStep.tsx`, `IntakeV4GeometryPanel.tsx` |
| Frontend layer roles | `intakeV4LayerRoleOptions.ts` |
| Backend task labels | `intake_v4_operator_task_labels.py`, `intake_v4_production_preview_service.py`, `intake_v4_production_task_dry_run_service.py` |
| Tests | `IntakeV4GeometryPanel.test.tsx`, `intakeV4LayerRoleOptions.test.ts`, `intakeV4QuoteGeometry.test.ts`, `test_intake_v4_operator_task_labels.py`, `test_intake_v4_finish_adapter.py` |

## Commands + results

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/components/workos/intake-v4/IntakeV4GeometryPanel.test.tsx src/lib/intakeV4/intakeV4LayerRoleOptions.test.ts src/lib/intakeV4/intakeV4QuoteGeometry.test.ts

cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_operator_task_labels.py tests/test_intake_v4_finish_adapter.py -q
```

Runtime smoke (IV4-4B172FD4): verify Layers LED 11.63 vs cant 15.47, no `Return / cant` in dropdown, no `Colantare cant` in task preview/dry-run.

## Boundary

Display-only Intake V4 alignment. No push in this build.

## Next steps

- Push 6-commit stack after review (5 prior + this fix), or hold if runtime smoke finds regressions.
