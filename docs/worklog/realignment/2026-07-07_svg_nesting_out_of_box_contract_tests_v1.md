# 2026-07-07 SVG Nesting Out-of-Box Contract Tests V1

## Head Before

- HEAD before: `7aecd1e`

## Safety

- `git status -sb`: tracked worktree clean, only unrelated untracked files present
- `git diff --cached --name-only`: none
- `git status --short --untracked-files=no`: none
- `git diff --check`: clean before and after edit

## Scope

Tests-first only.

No production/runtime code was changed in this slice.

## Canonical Rules Covered

1. Physical material quantity must not use raw area aliases as final truth when out-of-box / footprint source exists.
2. Logo-only physical rows should use a shared compatible footprint source for Plexiglas and Forex.
3. Holes/interiors are negative contours, not separate positive material pieces.
4. Cant / volum remains perimeter-based, not area-based.
5. Route trace debt for logo-only physical rows may remain, but it must be explicit in tests.

## Tests Added

### `backend/tests/test_intake_v4_material_breakdown.py`

- `test_logo_only_physical_material_rows_use_artwork_box_footprint_source`
  - protects logo-only Plexiglas/Forex physical rows from falling back to raw `artwork_area_m2` / `face_area_m2`
  - asserts compatible `bounding_box_footprint` source for both physical material rows

- `test_print_material_should_not_use_raw_area_alias_as_final_physical_source`
  - protects print-material row from exposing raw `face_area_m2` / `artwork_finishes|svg_analysis_json.layers` as the final quantity source string in the current tested scenario
  - status: PASS in current targeted fixture

### `backend/tests/test_gradi_logical_list_read_model.py`

- `test_logo_only_logical_rows_keep_compatible_physical_footprint_source_for_plexi_and_forex`
  - protects logo-only logical rows from re-diverging after the material-breakdown fix
  - asserts Plexiglas and Forex remain aligned on compatible footprint-derived source semantics

- `test_logo_only_logical_rows_still_expose_trace_debt_when_source_part_ids_are_missing`
  - documents current trace debt for logo-only material rows through preserved `quantity_source`

### `backend/tests/test_intake_v4_letter_part_hole_classification.py`

- `test_letter_O_with_inner_hole_should_nest_as_one_piece_with_negative_cutout_not_two_material_parts`
  - protects `O`-style inner hole semantics

- `test_letter_A_inner_counter_should_not_be_nested_as_positive_material_piece`
  - protects `A`-style inner counter semantics

### `backend/tests/test_intake_v4_nesting_preview.py`

- `test_logo_only_artwork_footprint_trace_can_be_empty_part_ids_and_still_marks_trace_debt`
  - documents current logo-only trace debt: footprint quantity source can be correct while `source_part_ids` stay empty

## Production Code Changes

- none

## Current Failures / Conflicts

None in the newly added targeted contract tests.

Broader existing backend suites remain noisy if run file-wide because some older fixtures still use `TPL-VOLUMETRIC-LETTERS` alias rather than current `TPL-VOLUMETRIC-LETTERS_v2` scope expectations. That noise is pre-existing and outside this tests-first slice.

## Files Touched

- `backend/tests/test_intake_v4_material_breakdown.py`
- `backend/tests/test_gradi_logical_list_read_model.py`
- `backend/tests/test_intake_v4_letter_part_hole_classification.py`
- `backend/tests/test_intake_v4_nesting_preview.py`

## Tests Run

Targeted new contract tests:

```powershell
Push-Location C:\Users\offic\workos_app_vs\backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_material_breakdown.py::TestIntakeV4MaterialBreakdownLetterGroups::test_logo_only_physical_material_rows_use_artwork_box_footprint_source tests/test_intake_v4_material_breakdown.py::TestIntakeV4MaterialBreakdownLetterGroups::test_print_material_should_not_use_raw_area_alias_as_final_physical_source tests/test_gradi_logical_list_read_model.py::test_logo_only_logical_rows_keep_compatible_physical_footprint_source_for_plexi_and_forex tests/test_gradi_logical_list_read_model.py::test_logo_only_logical_rows_still_expose_trace_debt_when_source_part_ids_are_missing tests/test_intake_v4_letter_part_hole_classification.py::TestIntakeV4LetterPartHoleClassification::test_letter_O_with_inner_hole_should_nest_as_one_piece_with_negative_cutout_not_two_material_parts tests/test_intake_v4_letter_part_hole_classification.py::TestIntakeV4LetterPartHoleClassification::test_letter_A_inner_counter_should_not_be_nested_as_positive_material_piece tests/test_intake_v4_nesting_preview.py::TestIntakeV4NestingPreview::test_logo_only_artwork_footprint_trace_can_be_empty_part_ids_and_still_marks_trace_debt -q
Pop-Location
```

Result:

- PASS
- 7 passed

Patch sanity:

```powershell
Push-Location C:\Users\offic\workos_app_vs
git diff --check
Pop-Location
```

Result:

- PASS

## Runtime Smoke

- not run
- reason: no production/runtime behavior change in this slice

## Remaining Risks

1. `source_part_ids` remains empty for logo-only physical material traces.
2. Route trace fields are still incomplete for a full row-by-row provenance contract.
3. Broad existing backend suites still contain legacy alias/noise unrelated to these added contract tests.
4. Print/lamination/folie route still needs dedicated footprint-source hardening beyond these initial contract guards.