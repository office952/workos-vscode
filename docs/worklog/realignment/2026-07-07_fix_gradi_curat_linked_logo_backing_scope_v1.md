# 2026-07-07 Fix Gradi Curat Linked Logo Backing Scope V1

## Head Before

- HEAD before: `be903e0`

## Safety

- `git status -sb`: tracked worktree clean, only unrelated untracked files present
- `git diff --cached --name-only`: none
- `git status --short --untracked-files=no`: none
- `git diff --check`: clean before and after edit

## Root Cause

For `gradi-curat.svg` letters+logo compositions, the runtime model had two separate problems:

1. linked logo Plexiglas was still represented through the logical logo row path instead of explicit runtime-linked material rows;
2. linked logo Forex backing scope was missing completely, so `material.forex_backing` covered only letters.

That yielded:

- `Plexiglas 3 mm = 2.0643 m2` (letters + logo)
- `Forex 10 mm = 1.2638 m2` (letters only)

with no explicit linked-logo backing policy in the physical material path.

## Policy Implemented

Implemented default owner policy:

- linked volumetric logo physical face => linked volumetric logo backing required

Concrete runtime policy:

- create runtime material rows for linked logo face from `quote_geometry.artwork_boxes|bounding_box_footprint|linked_logo_segment`
- create runtime material rows for linked logo backing from the same footprint source
- keep this as explicit linked-logo fallback until dedicated backing geometry exists
- preserve linked logo as child segment only; no Logo root activation

## Files Changed

- `backend/services/intake_v4_material_breakdown_service.py`
- `backend/services/gradi_logical_list_read_model_service.py`
- `backend/tests/test_intake_v4_material_breakdown.py`
- `backend/tests/test_gradi_logical_list_read_model.py`

## Material Source Proof

### Plexiglas letters

- quantity: `1.2638 m2`
- source: `svg_analysis_json.nesting|sheet_3000x2000|single_face`
- basis: `sheet_nesting_role_split_quote_estimate`

### Plexiglas logo

- quantity: `0.8004 m2`
- source: `quote_geometry.artwork_boxes|bounding_box_footprint|linked_logo_segment`
- basis: `linked_logo_face_bounding_footprint_quote_estimate`
- source part ids: logo part ids

### Forex letters

- quantity: `1.2638 m2`
- source: `sheet_nesting_face_quoteable|backing_area_missing`
- basis: `backing_area_fallback_from_face_quoteable_area`

### Forex logo

- quantity: `0.8004 m2`
- source: `quote_geometry.artwork_boxes|bounding_box_footprint|linked_logo_segment`
- basis: `linked_logo_backing_bounding_footprint_quote_estimate`
- source part ids: logo part ids

### Resulting total in linked letters+logo scope

- Plexiglas total: `2.0642 m2`
- Forex total: `2.0642 m2`

## Tests

Focused command run:

```powershell
Push-Location C:\Users\offic\workos_app_vs\backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_material_breakdown.py::TestIntakeV4MaterialBreakdownLetterGroups::test_logo_only_physical_material_rows_use_artwork_box_footprint_source tests/test_intake_v4_material_breakdown.py::TestIntakeV4MaterialBreakdownLetterGroups::test_letters_plus_logo_linked_segment_adds_logo_backing_and_runtime_face_rows tests/test_gradi_logical_list_read_model.py::test_gradi_logical_read_model_shares_plexiglas_material_batch_between_letters_and_logo tests/test_gradi_logical_list_read_model.py::test_gradi_linked_logo_backing_scope_adds_logo_forex_to_logical_total tests/test_gradi_logical_list_read_model.py::test_gradi_logo_plexiglas_uses_runtime_rows_not_artwork_area_fallback tests/test_gradi_logical_list_read_model.py::test_logo_only_logical_rows_keep_compatible_physical_footprint_source_for_plexi_and_forex tests/test_intake_v4_letter_part_hole_classification.py::TestIntakeV4LetterPartHoleClassification::test_letter_O_with_inner_hole_should_nest_as_one_piece_with_negative_cutout_not_two_material_parts tests/test_intake_v4_letter_part_hole_classification.py::TestIntakeV4LetterPartHoleClassification::test_letter_A_inner_counter_should_not_be_nested_as_positive_material_piece -q
Pop-Location
```

Result:

- PASS
- 8 passed

Broader touched suites were sampled, but still contain unrelated legacy alias noise using `TPL-VOLUMETRIC-LETTERS`; final acceptance for this slice is based on the relevant focused tests above.

Patch sanity:

```powershell
Push-Location C:\Users\offic\workos_app_vs
git diff --check
Pop-Location
```

Result:

- PASS

## Runtime Verification

### `IR-MRB2TPKK`

API:

- material rows:
  - `plexiglas_face = 1.2638 m2 / 20.2208 EUR`
  - `forex_backing = 1.2638 m2 / 20.2208 EUR`
  - `artwork_plexiglas_logo-stanga = 0.4002 m2 / 6.4032 EUR`
  - `artwork_plexiglas_logo-dreapta = 0.4002 m2 / 6.4032 EUR`
  - `artwork_forex_backing_logo-stanga = 0.4002 m2 / 7.6832 EUR`
  - `artwork_forex_backing_logo-dreapta = 0.4002 m2 / 7.6832 EUR`
- logical rows:
  - `material.plexiglas_face = 1.2638 / 20.2208`
  - `material.logo_plexiglas_face = 0.8004 / 12.8064`
  - `material.forex_backing = 2.0642 / 35.5872`
- explicit warning:
  - `LINKED_LOGO_BACKING_FALLBACK_USED`

UI:

- route: `http://127.0.0.1:3000/intake-v6/IR-MRB2TPKK/operator`
- visible rows in `Calcul live`:
  - `Plexiglas 3 mm 2.0642 m2 33.03 EUR`
  - `Forex 10 mm 2.0642 m2 35.59 EUR`
  - warning remains visible as `gap explicit`

### `IR-MR2MP11C`

API:

- same policy now active:
  - letters Plexiglas row
  - letters Forex row
  - logo Plexiglas runtime rows
  - logo Forex runtime rows
  - logical `material.forex_backing = 2.0642 / 35.5872`

UI:

- route: `http://127.0.0.1:3000/intake-v6/IR-MR2MP11C/operator`
- existing shared browser session did not give a stable refreshed extraction after reload
- pre-reload UI snapshot still showed old letters-only Forex scope
- API is the authoritative post-fix verification for this workspace in this session

### `IR-MR8TNT0O`

API remains stable:

- Plexiglas `2.25 m2 / 36.00 EUR`
- Forex `2.25 m2 / 43.20 EUR`
- source part ids populated

UI remains stable:

- route: `http://127.0.0.1:3000/intake-v6/IR-MR8TNT0O/operator`
- visible rows:
  - `Plexiglas 3 mm 2.25 m2 36.00 EUR`
  - `Forex 10 mm 2.25 m2 43.20 EUR`

### Regression Smoke

- `IR-MRAUMOXT / cerc100cm.svg`
  - no `7 m2` regression
  - Plexiglas/Forex visible
- `IR-MR87EU55 / litere-vol-1-layer.svg`
  - Plexiglas/Forex visible

## Remaining Risks

1. `IR-MR2MP11C` UI extraction in the shared browser session remained stale after reload even though API is updated; browser/runtime cache or session state may still be involved.
2. `material.forex_backing` now mixes letters backing fallback and linked-logo backing fallback into one total. This is explicit and traceable, but still transitional until dedicated backing geometry exists.
3. `print/lamination` footprint hardening is still a separate slice.

## Forbidden Scope Confirmation

- no Pricing Registry
- no price formula rewrite
- no Quote/Order
- no Execution
- no ProductAggregate/TaskGraph/ExecutionPlan
- no DB/seed/migration
- no Logo root activation
- no ACP root activation
- no UI-only hiding
- no filename hardcoding