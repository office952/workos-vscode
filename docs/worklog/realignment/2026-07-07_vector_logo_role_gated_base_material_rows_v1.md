## TASK

FIX_VECTOR_LOGO_CALCULATION_ROLE_GATED_BASE_MATERIAL_ROWS_V1

## HEAD before work

- `8998986`

## Safety state

- `git status -sb`: tracked worktree clean before edits; historical untracked files present
- `git diff --cached --name-only`: empty before work
- `git status --short --untracked-files=no`: empty before work
- `git diff --check`: clean before edits

## Root cause

- False `6 m2` came from [backend/services/intake_v4_nesting_material_precision.py](c:/Users/offic/workos_app_vs/backend/services/intake_v4_nesting_material_precision.py), function `compute_sheet_nesting_material_split(...)`.
- For `cerc100cm.svg`, the only active placement was `printed_artwork`, which is excluded from sheet face classification.
- That left no classified face placements, so the function returned `mode="prorated_fallback"` using the active `sheet_3000x2000` full area of `6 m2`.
- [backend/services/intake_v4_material_breakdown_service.py](c:/Users/offic/workos_app_vs/backend/services/intake_v4_material_breakdown_service.py) then emitted `plexiglas_face = 6 m2` from `sheet_nesting_prorated_fallback`.
- [backend/services/gradi_logical_list_read_model_service.py](c:/Users/offic/workos_app_vs/backend/services/gradi_logical_list_read_model_service.py) also emitted a separate logo plexiglas row of `1 m2` from `artwork_area_m2`, so the live UI aggregated them into `7 m2`.

## Fix explanation

### 1. Role gate in material breakdown

- Added a local confirmed-letter detector in [backend/services/intake_v4_material_breakdown_service.py](c:/Users/offic/workos_app_vs/backend/services/intake_v4_material_breakdown_service.py).
- When there is zero confirmed/active letter face content and only artwork/logo rows exist, the code now blocks `sheet_nesting_prorated_fallback` for the letters face/base material path.
- This prevents emission of false `plexiglas_face = 6 m2` and suppresses the matching false sheet fallback warning.
- The runtime then falls back to the actual geometry area (`quote_geometry|path_geometry_summary`) for the real provisional logo face material contribution.

### 2. Role gate in logical list

- [backend/services/gradi_logical_list_read_model_service.py](c:/Users/offic/workos_app_vs/backend/services/gradi_logical_list_read_model_service.py) now suppresses `material.plexiglas_face` when there is no confirmed letter face content.
- The logo-only logical row remains, and is still tied to `TPL-VOLUMETRIC-LOGO_v1` as linked child composition.

### 3. Shared plexiglas override correctness

- [backend/services/cnc_machine_operation_pricing_read_model_service.py](c:/Users/offic/workos_app_vs/backend/services/cnc_machine_operation_pricing_read_model_service.py) now supports `has_letter_face_content=False`.
- In logo-only mode, shared batch metadata now becomes:
  - `letter_face_area_m2 = 0`
  - `logo_face_area_m2 = 1`
  - `shared_batch_roles = ["LOGO_FACE"]`
- The shared plexiglas tariff now prefers the real `unit_price` when present, so the owner-facing logical row shows `1 m2 / 16 EUR` instead of inheriting a waste-inflated effective rate.

## Files changed

- [backend/services/cnc_machine_operation_pricing_read_model_service.py](c:/Users/offic/workos_app_vs/backend/services/cnc_machine_operation_pricing_read_model_service.py)
- [backend/services/intake_v4_material_breakdown_service.py](c:/Users/offic/workos_app_vs/backend/services/intake_v4_material_breakdown_service.py)
- [backend/services/gradi_logical_list_read_model_service.py](c:/Users/offic/workos_app_vs/backend/services/gradi_logical_list_read_model_service.py)
- [backend/tests/test_intake_v4_material_breakdown.py](c:/Users/offic/workos_app_vs/backend/tests/test_intake_v4_material_breakdown.py)
- [backend/tests/test_gradi_logical_list_read_model.py](c:/Users/offic/workos_app_vs/backend/tests/test_gradi_logical_list_read_model.py)
- [docs/worklog/realignment/2026-07-07_vector_logo_role_gated_base_material_rows_v1.md](c:/Users/offic/workos_app_vs/docs/worklog/realignment/2026-07-07_vector_logo_role_gated_base_material_rows_v1.md)

## Tests run

- `cd backend; .\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_material_breakdown.py -q -k "sheet_nesting_prorated_fallback_without_placement_metadata or logo_only_artwork_blocks_letters_sheet_prorated_fallback_for_plexiglas or artwork_raw_skips_global_oracal_face_fallback or artwork_oracal_641_adds_logo_specific_vinyl_and_application or artwork_oracal_8500_adds_logo_specific_vinyl_and_application or artwork_print_laminate_adds_logo_specific_rows or artwork_finish_totals_are_additive_relative_to_raw"`
  - PASS (`7 passed`)
- `cd backend; .\.venv\Scripts\python.exe -m pytest tests/test_gradi_logical_list_read_model.py -q -k "logo_only_runtime_does_not_emit_letters_plexiglas_logical_row or gradi_logical_read_model_returns_21_core_rows_and_excludes_extras or gradi_logical_read_model_shares_plexiglas_material_batch_between_letters_and_logo"`
  - PASS (`3 passed`)
- `git diff --check`
  - PASS

## Runtime verification

### A. `cerc100cm.svg`

- Route: `/intake-v6/IR-MRAUMOXT/operator`
- API `material-breakdown` after fix:
  - `plexiglas_face.quantity = 1.0004`
  - `quantity_basis = area_with_waste_fallback`
  - no `plexiglas_face = 6 m2`
  - no `sheet_nesting_prorated_fallback` false base row
- API logical-list after fix:
  - no `material.plexiglas_face`
  - `material.logo_plexiglas_face.quantity = 1`
  - `subtotal = 16`
  - `shared_batch_roles = ["LOGO_FACE"]`
- UI `Calcul live` after fix:
  - `Plexiglas 3 mm`
  - `1 m2`
  - `16,00 EUR`
  - no `7 m2`
  - no `112,00 EUR`

### B. `gradi-curat.svg`

- Route: `/intake-v6/IR-MR2MP11C/operator`
- UI `Calcul live` after fix still shows valid mixed letters+logo material:
  - `Plexiglas 3 mm`
  - `2.0643 m2`
  - `33,03 EUR`
- Valid letters/logo material remains preserved.
- Visible labels remain generic:
  - `Plexiglas 3 mm`
  - `Cant / volum`
  - no role-suffixed plexiglas rows in visible mode

## Forbidden scope confirmation

- no Pricing Registry rewrite
- no price changes
- no Quote/Order
- no Execution
- no ProductAggregate/TaskGraph/ExecutionPlan
- no DB/seed/migration
- no Logo root activation
- no ACP root activation
- no Image Analyzer runtime edits

## Remaining risks

- The linked logo child for `cerc100cm.svg` remains blocked for trusted quote/pricing readiness because binding and finish confirmation are still incomplete.
- `Forex 10 mm` can still appear as a provisional fallback row in the logo-only case; this slice only fixed the false letters-root plexiglas/base material defect at source.