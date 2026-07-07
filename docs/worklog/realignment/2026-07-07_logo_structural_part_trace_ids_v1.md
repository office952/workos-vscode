# 2026-07-07 Logo Structural Part Trace IDs V1

## Head Before

- HEAD before: `8bec0fc`

## Safety

- `git status -sb`: tracked worktree clean, only unrelated untracked files present
- `git diff --cached --name-only`: none
- `git status --short --untracked-files=no`: none
- `git diff --check`: clean before and after edit

## Trace Gap Before

On `IR-MR8TNT0O / logo.svg` the physical material source was already corrected to footprint/out-of-box, but the provenance chain still lost the source part id.

Before:

- `plexiglas_face`
  - `quantity_basis = artwork_box_bounding_footprint_quote_estimate`
  - `quantity_source = quote_geometry.artwork_boxes|bounding_box_footprint`
  - `source_part_ids = []`
- `forex_backing`
  - `quantity_basis = backing_area_fallback_from_artwork_box_footprint`
  - `quantity_source = quote_geometry.artwork_boxes|bounding_box_footprint`
  - `source_part_ids = []`

Root cause:

- logo-only driving part remained classified as `artwork_part` in nesting preview
- `material_traces` only collected ids from parts already counted in `counted_in_material_lines`
- logo-only physical footprint rows were using `artwork_boxes` fallback, so no trace ids were being propagated from the material row into nesting preview or logical list

## Fix

### What changed

Added trace-contract fields and propagated real source ids through the existing backend path.

Files changed:

- `backend/schemas/intake_v4.py`
- `backend/services/intake_v4_material_breakdown_service.py`
- `backend/services/intake_v4_nesting_preview_service.py`
- `backend/services/gradi_logical_list_read_model_service.py`
- `backend/services/cnc_machine_operation_pricing_read_model_service.py`
- `backend/tests/test_intake_v4_material_breakdown.py`
- `backend/tests/test_gradi_logical_list_read_model.py`
- `backend/tests/test_intake_v4_nesting_preview.py`

### Propagation path

1. `material-breakdown`
- logo-only footprint rows now carry `source_part_ids`
- when artwork/logo parts are the driver of footprint-based physical material quantity, those part ids are attached directly to `plexiglas_face` and compatible `forex_backing`

2. `nesting-preview`
- `material_traces` now prefer row-level `source_part_ids` when present
- fallback to placement-derived ids still remains for normal face/backing routes

3. `logical-list`
- `child_rows` and top-level rows now propagate `source_part_ids`
- shared logo Plexiglas override inherits ids from the runtime material row

### No runtime behavior change in pricing/quantity

- quantities unchanged
- subtotals unchanged
- pricing formulas unchanged
- only provenance improved

## Runtime Verification

### Main Target — `IR-MR8TNT0O / logo.svg`

#### Material breakdown

- Plexiglas:
  - quantity: `2.25 m2`
  - subtotal: `36.00 EUR`
  - source: `quote_geometry.artwork_boxes|bounding_box_footprint`
  - source_part_ids: `part_logo_dreapta_001`
- Forex:
  - quantity: `2.25 m2`
  - subtotal: `43.20 EUR`
  - source: `quote_geometry.artwork_boxes|bounding_box_footprint`
  - source_part_ids: `part_logo_dreapta_001`
- raw area used for physical material truth: no

#### Logical list

- `material.logo_plexiglas_face`
  - quantity: `2.25 m2`
  - subtotal: `36.00 EUR`
  - source_part_ids: `part_logo_dreapta_001`
- `material.forex_backing`
  - quantity: `2.25 m2`
  - subtotal: `43.20 EUR`
  - source_part_ids: `part_logo_dreapta_001`
  - child row also carries the same id

#### Nesting preview traces

- `plexiglas_face`
  - source_part_ids: `part_logo_dreapta_001`
- `forex_backing`
  - source_part_ids: `part_logo_dreapta_001`

### Regression Runtime Smoke

- `IR-MRAUMOXT / cerc100cm.svg`
  - Plexiglas visible: yes, `1 m2 / 16.00 EUR`
  - Forex visible: yes
  - no `7 m2` regression
- `IR-MR2MP11C / gradi-curat.svg`
  - Plexiglas/Forex/Cant/print/laminare/aplicare visible
- `IR-MR87EU55 / litere-vol-1-layer.svg`
  - Plexiglas/Forex visible
- `IR-MR8FWG1N / litere-vol-2-layere.svg`
  - Plexiglas/Forex visible

No role-suffix labels reappeared in the main visible rows.

## Tests

Focused command run:

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

## Remaining Risks

1. `source_part_ids` is now populated, but the part is still classified as `artwork_part`, not a structural part. That is acceptable for provenance, but downstream route-trace fields are still incomplete.
2. `print/lamination/folie` still need a broader explicit footprint-source hardening pass beyond the narrow tested path.
3. Some broader backend test files still have legacy alias noise unrelated to this slice.

## Scope Confirmation

- no Pricing Registry rewrite
- no price changes
- no broad formula rewrite
- no Quote/Order
- no Execution
- no ProductAggregate/TaskGraph/ExecutionPlan
- no DB/seed/migration
- no Logo root activation
- no ACP root activation
- no Image Analyzer runtime edits