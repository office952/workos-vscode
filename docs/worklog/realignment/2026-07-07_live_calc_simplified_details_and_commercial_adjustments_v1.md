# Live Calc Simplified Details And Commercial Adjustments V1

Date: 2026-07-07
HEAD before work: fb4a473

## Safety state

- `git status -sb`: only known uncommitted live-calc/review/pricing files were modified.
- `git diff --cached --name-only`: empty before work.
- `git status --short --untracked-files=no`: no tracked changes outside the known current surface.

## Files changed

- frontend/src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.tsx
- frontend/src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.test.tsx
- frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx
- frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.commercialSettings.test.tsx
- frontend/src/lib/intakeV6/intakeV4NearestOracalColor.ts
- frontend/src/lib/intakeV6/intakeV6NearestOracalColorCompatContract.test.ts
- frontend/src/lib/intakeV6/intakeV6LetterGroups.test.ts
- backend/services/intake_v4_artwork_complexity_service.py
- backend/services/gradi_logical_list_read_model_service.py
- backend/services/shared_cnc_operation_model.py
- backend/services/cnc_machine_operation_pricing_read_model_service.py
- backend/tests/test_intake_v4_artwork_complexity.py
- backend/tests/test_shared_cnc_operation_model.py

## Simplified details toggle

- Default row display now hides formula ids, child row counts, gap/debug text.
- Added `Afișează detalii tehnice` toggle.
- Detailed mode reveals the technical metadata again.
- Simplified mode remains default.

## Commercial adjustment root cause

- ReviewStep initialized local commercial inputs before persisted workspace payload hydration.
- Once persisted values arrived, the sync effect was blocked by a false-positive `commercialInputsPendingSave` mismatch.
- Result: UI kept stale defaults like `35` even when backend payload already persisted `15`.

## Commercial adjustment fix

- Added explicit dirty-state handling for commercial inputs in ReviewStep.
- Persisted backend values now hydrate into UI when the operator has not edited the fields locally.
- Local operator edits still debounce-save and remain stable after save.

## Tests run

- `pnpm.cmd exec vitest run src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.test.tsx --reporter=verbose`
- `pnpm.cmd exec vitest run src/components/workos/intake-v6/steps/IntakeV6ReviewStep.commercialSettings.test.tsx --reporter=verbose`
- `pnpm.cmd exec vitest run src/lib/intakeV6/intakeV6NearestOracalColorCompatContract.test.ts src/lib/intakeV6/intakeV6LetterGroups.test.ts --reporter=verbose`
- `python -m pytest tests/test_intake_v4_artwork_complexity.py tests/test_volumetric_finish_mounting_pricing.py::TestVolumetricFinishMountingPricing::test_face_finish_none_skips_vinyl_lines -q`
- `python -m pytest tests/test_shared_cnc_operation_model.py tests/test_intake_v4_cnc_router_passes_and_bevel_costing.py::TestCncPassPolicy tests/test_gradi_logical_list_read_model.py::test_gradi_logical_read_model_keeps_cnc_and_totals_stable_after_cnc_closeout tests/test_gradi_logical_list_read_model.py::test_gradi_logical_read_model_adds_forex_back_trace_metadata tests/test_gradi_logical_list_read_model.py::test_gradi_logical_read_model_uses_geometry_fallback_for_cnc_trace_when_operation_rows_missing -q`
- `git.exe diff --check`

## Runtime verification

- Workspace checked: `http://127.0.0.1:3000/intake-v6/0cfafcb6-ea95-4ff5-9799-bbd88b24bf71/operator`
- Verified simplified details default hides formula/debug text.
- Verified technical toggle reveals formula/debug text.
- Verified persisted markup in DOM matches backend payload (`15`).
- Verified raw plexiglas selection persists and removes Oracal/print/lamination/application rows.

## Forbidden scope confirmation

- No DB/seed/migration changes.
- No Quote/Order changes.
- No Execution changes.
- No ProductAggregate/TaskGraph/ExecutionPlan changes.
- No ProductDefinition pricing rewrite.
- No Logo offerability changes.
- No Image Analyzer runtime work.

## Commit recommendation

- If the full review/pricing surface is accepted together, one coherent commit is reasonable:
  `Fix live calculation review pricing controls and details`