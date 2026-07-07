# 2026-07-07 Logo SVG Face Backing Quantity Source Mismatch V1

## Head Before

- HEAD before: `e776c66`

## Safety

- `git status -sb`: tracked worktree clean, only unrelated untracked files present
- `git diff --cached --name-only`: none
- `git status --short --untracked-files=no`: none
- `git diff --check`: clean before and after edit

## Root Cause

Primary divergence was in the backend source-of-truth path, not in the UI.

### Exact controlling files/functions

- `backend/services/intake_v4_material_breakdown_service.py`
- `backend/services/gradi_logical_list_read_model_service.py`
- `backend/services/cnc_machine_operation_pricing_read_model_service.py`

### Why Plexiglas and Forex diverged

1. `material-breakdown` was still emitting physical `plexiglas_face` from raw face-area fallback:
   - `quantity_basis = area_with_waste_fallback`
   - `quantity_source = quote_geometry|path_geometry_summary`
2. `material-breakdown` was also emitting `forex_backing` from gross face fallback:
   - `quantity_basis = backing_area_fallback_from_gross_face_area`
   - `quantity_source = face_area_gross|backing_area_missing`
3. `logical-list` then overrode only logo Plexiglas using `artwork_area_m2` through the shared batch helper, while Forex remained on the material-breakdown fallback.

Result before fix on `IR-MR8TNT0O / logo.svg`:

- Plexiglas logical/UI: `1.5547 m2`
- Forex logical/UI: `2.2506 m2`

### Area aliases involved

Yes.

- `artwork_area_m2` was being used as logo Plexiglas logical quantity.
- `face_area_m2` / gross face fallback was being used to derive physical material rows.

That violated the owner rule for physical materials.

## Source-of-Truth Change

### New rule applied

For `logo-only` / no confirmed `Vector Litere` cases:

- physical material quantity must not use raw `face_area_m2`
- physical material quantity must not use raw `artwork_area_m2`
- when available, use `quote_geometry.artwork_boxes` bounding footprint as the explicit out-of-box source

### Plexiglas change

`plexiglas_face` now uses:

- `quantity_basis = artwork_box_bounding_footprint_quote_estimate`
- `quantity_source = quote_geometry.artwork_boxes|bounding_box_footprint`

### Forex change

`forex_backing` now uses compatible artwork-box footprint fallback when the row is still allowed:

- `quantity_basis = backing_area_fallback_from_artwork_box_footprint`
- `quantity_source = quote_geometry.artwork_boxes|bounding_box_footprint`

### Backing rule

- material breakdown no longer treats normalized default backing state as implicit confirmation
- backing estimate is only allowed when the raw finish payload explicitly carries backing mode or backing layer confirmation exists

### Logical-list change

`material.logo_plexiglas_face` now prefers the runtime structural material quantity instead of synthesizing the quantity from raw `artwork_area_m2` when a runtime `plexiglas_face` row already exists.

### Hole/interior rule

No implementation change was needed in hole logic for this slice.

Existing guard remains:

- holes/interiors are negative contours, not independent nestable material parts

## Quantity Source Before / After

### Before

`IR-MR8TNT0O / logo.svg`

| Row | Quantity | Basis | Source |
|---|---:|---|---|
| Plexiglas | 1.5547 m2 in logical/UI | `MATERIAL_PLEXI_LOGO_FACE_BY_AREA_V1` logical batch | raw `artwork_area_m2` route |
| Forex | 2.2506 m2 | `backing_area_fallback_from_gross_face_area` | gross face area fallback |

### After

| Row | Quantity | Basis | Source |
|---|---:|---|---|
| Plexiglas | 2.25 m2 | `artwork_box_bounding_footprint_quote_estimate` | `quote_geometry.artwork_boxes|bounding_box_footprint` |
| Forex | 2.25 m2 | `backing_area_fallback_from_artwork_box_footprint` | `quote_geometry.artwork_boxes|bounding_box_footprint` |

## Files Changed

- `backend/services/intake_v4_material_breakdown_service.py`
- `backend/services/gradi_logical_list_read_model_service.py`
- `backend/services/cnc_machine_operation_pricing_read_model_service.py`
- `backend/tests/test_intake_v4_material_breakdown.py`
- `backend/tests/test_gradi_logical_list_read_model.py`

## Focused Tests

Command run:

```powershell
Push-Location C:\Users\offic\workos_app_vs\backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_material_breakdown.py::TestIntakeV4MaterialBreakdownLetterGroups::test_logo_only_artwork_blocks_letters_sheet_prorated_fallback_for_plexiglas tests/test_intake_v4_material_breakdown.py::TestIntakeV4MaterialBreakdownLetterGroups::test_logo_only_unconfirmed_backing_does_not_emit_forex_from_area_fallback tests/test_intake_v4_material_breakdown.py::TestIntakeV4NestingMaterialPrecisionIntegration::test_backing_not_confirmed_excludes_forex_from_estimate tests/test_gradi_logical_list_read_model.py::test_logo_only_runtime_does_not_emit_letters_plexiglas_logical_row tests/test_intake_v4_letter_part_hole_classification.py::TestIntakeV4LetterPartHoleClassification::test_hole_not_nestable_independent_part -q
Pop-Location
```

Result:

- PASS
- 5 tests passed

Covered:

1. logo-only Plexiglas source moves from area fallback to artwork box footprint
2. unconfirmed backing does not emit Forex fallback in targeted backend scenario
3. logo-only logical Plexiglas row reuses runtime material quantity/cost
4. inner hole remains non-nestable independent material part

## Runtime Verification Matrix

### A. `IR-MR8TNT0O` / `logo.svg`

- Plexiglas visible: yes
- Plexiglas quantity/subtotal/source:
  - `2.25 m2`
  - `36.00 EUR`
  - `artwork_box_bounding_footprint_quote_estimate`
  - `quote_geometry.artwork_boxes|bounding_box_footprint`
- Forex visible: yes
- Forex quantity/subtotal/source:
  - `2.25 m2`
  - `43.20 EUR`
  - `backing_area_fallback_from_artwork_box_footprint`
  - `quote_geometry.artwork_boxes|bounding_box_footprint`
- mismatch resolved: yes
- raw area used for physical material truth: no
- shared source compatibility: yes

### B. Regression Cases

#### `IR-MRAUMOXT` / `cerc100cm.svg`

- Plexiglas visible: yes, `1 m2`, `16.00 EUR`
- Forex visible: yes, `1 m2`, `19.20 EUR`
- Cant visible: yes
- LED visible: yes
- role-suffix labels visible in main list: no
- `7 m2` regression: no

#### `IR-MR2MP11C` / `gradi-curat.svg`

- Plexiglas visible: yes, `2.0643 m2`, `33.03 EUR`
- Forex visible: yes, `1.2638 m2`, `20.22 EUR`
- Cant visible: yes
- LED visible: yes
- print / laminare / aplicare visible: yes
- role-suffix labels visible in main list: no

#### `IR-MR87EU55` / `litere-vol-1-layer.svg`

- Plexiglas visible: yes, `1.2 m2`, `19.20 EUR`
- Forex visible: yes, `1.2 m2`, `19.20 EUR`
- Cant visible: yes
- LED visible: yes
- role-suffix labels visible in main list: no

#### `IR-MR8FWG1N` / `litere-vol-2-layere.svg`

- Plexiglas visible: yes, `1.1395 m2`, `18.23 EUR`
- Forex visible: yes, `1.1395 m2`, `18.23 EUR`
- Cant visible: yes
- LED visible: yes
- role-suffix labels visible in main list: no

## Owner Nesting Rules Applied

- physical materials use nesting / footprint / out-of-box source, not raw geometric area
- area remains allowed only for LED vector atipic and print/lamination/service-style artwork calculations, not for physical Plexiglas/Forex truth
- holes/interiors remain negative contours, not positive material pieces

## Validation

Commands run:

```powershell
Push-Location C:\Users\offic\workos_app_vs
git diff --check
Pop-Location
```

```powershell
Push-Location C:\Users\offic\workos_app_vs\backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_material_breakdown.py::TestIntakeV4MaterialBreakdownLetterGroups::test_logo_only_artwork_blocks_letters_sheet_prorated_fallback_for_plexiglas tests/test_intake_v4_material_breakdown.py::TestIntakeV4MaterialBreakdownLetterGroups::test_logo_only_unconfirmed_backing_does_not_emit_forex_from_area_fallback tests/test_intake_v4_material_breakdown.py::TestIntakeV4NestingMaterialPrecisionIntegration::test_backing_not_confirmed_excludes_forex_from_estimate tests/test_gradi_logical_list_read_model.py::test_logo_only_runtime_does_not_emit_letters_plexiglas_logical_row tests/test_intake_v4_letter_part_hole_classification.py::TestIntakeV4LetterPartHoleClassification::test_hole_not_nestable_independent_part -q
Pop-Location
```

Results:

- `git diff --check`: PASS
- focused backend tests: PASS
- no frontend files touched in this slice

## Remaining Risks

1. `nesting-preview` still reports `backing_not_confirmed` while `material-breakdown` can price Forex when raw finish payload explicitly carries backing mode. That trace alignment is still imperfect and should be audited separately.
2. `artwork_boxes` remains a bounding-box / out-of-box approximation, not true CNC shape nesting. This is allowed by owner rule, but it is still an approximation contract.
3. Logo-only runtime currently has no `source_part_ids` for physical material traces because artwork parts are still classified as artwork-only in nesting preview.

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