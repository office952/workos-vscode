# TPL-VOLUMETRIC-LETTERS â€” Costing Logic Audit

**Scope:** Active template only (`TPL-VOLUMETRIC-LETTERS`). Archived templates are out of scope.

**Date:** 2026-06-06 (mounting bar logic verified)

## Summary

Costing for volumetric letters uses **EUR** as base currency. Quote pricing is driven by **unit-based** operations and materials. **Rates are stored excluding TVA**; TVA is configured separately. **Duration** remains calibration/planning metadata where applicable. **QC / control calitate** is **internal-only**. **Generic ASSEMBLY** and **LASER_CUTTING** are **not quote-priced** for this template.

## Owner Operation Decisions (implemented)

| Operation | Workcenter | Basis | Rate (excl. TVA) | Quantity input | Formula |
|-----------|------------|-------|------------------|----------------|---------|
| vector_prep | PREPRESS | per letter | 2 EUR | `letter_count` | `letter_count_material` |
| face_cnc_cut | CNC_ROUTER | per ml/pass | 1.5 EUR | `letter_perimeter_m` Ã— passes | `perimeter_pass_linear_meter` (2 passes) |
| back_cut | CNC_ROUTER | per ml/pass | 1.5 EUR | `letter_perimeter_m` Ã— passes | `perimeter_pass_linear_meter` (5 passes) |
| mounting_template_cnc_cut | CNC_ROUTER | per ml/pass | 1.5 EUR | `letter_perimeter_m` Ã— 1 pass | `perimeter_pass_linear_meter` (1 pass) |
| led_install_letters | LED_ASSEMBLY | per module | 0.05 EUR | `led_module_count` | `led_module_count` |
| electrical_letters | ELECTRICAL_WIRING | per letter | 2 EUR | `letter_count` | `letter_count_material` |
| painting | PAINTING | per ml | 4 EUR | `letter_perimeter_m` | `letter_perimeter` |
| packaging_letters | PACKAGING | per mp | 10 EUR | `letter_face_area_m2` | `letter_face_area` |
| side_forming | RETURN_PROFILE_MACHINE_FORMING | per ml | 5 EUR | `letter_perimeter_m` | `letter_perimeter` |
| return_face_bonding | RETURN_PROFILE_FACE_BONDING | per ml | 5 EUR | `return_material_perimeter_ml` | `letter_perimeter` with `perimeter_quote_input_key` |

**Not quote-priced (no blocker):**

| Operation | Workcenter | Rationale |
|-----------|------------|-----------|
| qc_letters | QC_INSPECTION | Internal calibration only |
| assembly_letters | ASSEMBLY | Duplicate â€” forming, bonding, LED, electrical, painting, packaging priced explicitly |
| LASER_CUTTING | â€” | Removed from template; bevel/sanfren requires CNC, not laser |

## CNC Pass Logic

| Material / job | Cut passes | Bevel passes | Total passes | Notes |
|----------------|------------|--------------|--------------|-------|
| Plexiglas face 3 mm | 1 | 1 | **2** | Owner rule for VIZUAL FAÈšÄ‚ |
| Forex 10 mm back | 3 | 2 (7 mm depth) | **5** | Owner rule for CAPAC SPATE â€” no generic `ceil(thickness/3)` |
| Forex 3 mm mounting template | 1 | 0 | **1** | Default from prior calibration; owner may refine |

Pass count lives in `formula_params` (`pass_count`, `cut_passes`, `bevel_passes`). CostEngine multiplies `letter_perimeter_m Ã— pass_count`; rate is EUR/ml (per pass).

## Unit Basis Table

| rate_basis | Stored in | Quantity source |
|------------|-----------|-----------------|
| `per_piece` | `rate_per_linear_meter` column | `letter_count`, `led_module_count` |
| `per_linear_meter` | `rate_per_linear_meter` column | `letter_perimeter_m`, `total_pass_linear_m` |
| `per_square_meter` | `rate_per_linear_meter` column | `letter_face_area_m2` |
| `per_hour` | `rate_per_hour` column | minutes (not used for listed owner ops) |

## TVA

All owner-defined operation rates in `workcenter_rates` are **excluding TVA**. `source_notes` on each rate documents this. Commercial quotes apply TVA via separate configuration.

## LED_ASSEMBLY conversion note

Owner reference: **0.20 RON/module**. Manual conversion at **5.2 RON/EUR** â†’ 0.03846 EUR; commercially rounded to **0.05 EUR/module**. Not live FX.

## MAT-VOPSEA-RAL â€” whole spray tube material

| Field | Value |
|-------|-------|
| Code | `MAT-VOPSEA-RAL` |
| Type | Material consumable (not painting service) |
| Unit | `buc` (tub) |
| unit_cost | **10 EUR/tub** (excluding TVA) |
| source_review_status | `accepted_override` / owner-confirmed |

**Owner reference:** 50 RON/tub. Manual conversion at **5.2 RON/EUR** â†’ 9.61 EUR, commercially rounded to **10 EUR/tub**. Not live FX.

**Quantity formula:** `ceil_quote_input_quantity`

- Quote input: `paint_tube_count` (preferred) or `estimated_paint_tubes`
- Charged quantity: `ceil(raw_estimate)` â€” never fractional tubes
- Examples: 3 â†’ 3 tubes; 3.2 â†’ 4 tubes

**Product 001 example:** `paint_tube_count=3` â†’ 3 Ã— 10 EUR = **30 EUR** material

## PAINTING operation â€” separate labor/service

| Field | Value |
|-------|-------|
| Operation | `painting` |
| Workcenter | `PAINTING` |
| Basis | per linear meter |
| Rate | **4 EUR/ml** (excluding TVA) |
| Quantity | `letter_perimeter_m` |

**Product 001 example:** 18 m Ã— 4 EUR = **72 EUR** service

**Total paint-related (material + service):** 30 + 72 = **102 EUR**

Do not mix: MAT-VOPSEA-RAL is consumable only; PAINTING does not include paint material cost.

## Product 001 example (simulate-cost payload)

```
letter_face_area_m2 = 2.88
letter_perimeter_m = 18
letter_count = 9
led_module_count = 180
```

| Line | Calculation | Total EUR |
|------|-------------|-----------|
| PREPRESS | 9 Ã— 2 | 18 |
| CNC face | 18 Ã— 2 Ã— 1.5 | 54 |
| CNC back | 18 Ã— 5 Ã— 1.5 | 135 |
| CNC mounting template | 18 Ã— 1 Ã— 1.5 | 27 |
| Forming | 18 Ã— 5 | 90 |
| Bonding | 18 Ã— 7 | 126 |
| LED assembly | 180 Ã— 0.05 | 9 |
| Electrical | 9 Ã— 2 | 18 |
| Painting | 18 Ã— 4 | 72 |
| Packaging | 2.88 Ã— 10 | 28.8 |

Materials (LED modules, PSU, plates, etc.) add separately from inventory rates.

## ASSEMBLY de-scope rationale

Generic `assembly_letters` overlapped with already-priced steps: profile forming, face bonding, LED assembly, electrical wiring, painting, and packaging. No distinct commercial action â†’ `quote_priced=false`, duration calibration only.

## LASER_CUTTING exclusion rationale

Illuminated volumetric letters require bevel/sanfren; laser cannot perform that. `back_cut` uses **CNC_ROUTER** with owner Forex 10 mm pass rule. No LASER workcenter in active template operations.

## Formula safeguards

- Missing quote inputs â†’ `NEEDS_QUOTE_INPUT` and basis-specific quantity errors â€” never silent zero.
- Prices only in Pricing Registry / workcenter_rates â€” not in CostEngine.

## Face finish pricing (owner-confirmed, excluding TVA)

| `face_finish_type` | Material code | Rate | Operation | Rate | Quantity |
|--------------------|---------------|------|-----------|------|----------|
| `none` | â€” | â€” | â€” | â€” | â€” |
| `oracal_651` | MAT-ORACAL-651 | 5 EUR/mp | vinyl_application (VINYL_APPLICATION) | 3 EUR/mp | `letter_face_area_m2` |
| `printed_vinyl` | MAT-VINYL-PRINT | 10 EUR/mp | vinyl_application | 3 EUR/mp | `letter_face_area_m2` |
| `printed_laminated_vinyl` | MAT-VINYL-PRINT-LAMINATED | 10 EUR/mp | vinyl_application | 3 EUR/mp | `letter_face_area_m2` |

**Future yield logic:** Oracal roll nesting on 1.00 m and 1.26 m widths â€” documented for later optimization; current quantity uses `letter_face_area_m2`.

## Mounting template (independent from `mounting_system`)

| Field | Type | Default | Effect |
|-------|------|---------|--------|
| `mounting_template_enabled` | boolean | `true` (preserves baseline sablon cost) | Gates MAT-SABLON-MONTAJ + `mounting_template_cnc_cut` |
| `mounting_template_area_m2` | number | â€” | Required when enabled; quantity for sablon material |

Legacy `mounting_system=forex_template` maps to `direct_wall` + `mounting_template_enabled=true`.

## Premount bars (`46c8260`)

| `mounting_system` | Material | Rate (profile-specific) | Quantity formula | Labor |
|-------------------|----------|-------------------------|------------------|-------|
| `direct_wall` | â€” | â€” | â€” | â€” |
| `steel_bars` | MAT-PREMOUNT-BAR-STEEL | **2 EUR/ml** when `mounting_bar_profile=30x30x1.5` | `mounting_bar_total_length` | `mounting_labor_not_priced` when profile priced |
| `aluminum_bars` | MAT-PREMOUNT-BAR-ALUMINUM | **3.5 EUR/ml** when `mounting_bar_profile=30x30x1.5` | `mounting_bar_total_length` | same |
| `acm_panel` | â€” | â€” | â€” | `captured_option_requires_separate_template` (not priced here) |

### Bar length default rule

```
assembly_width_m = width_mm / 1000
mounting_bar_count = quote_input.mounting_bar_count OR 2
total_bar_length_m = assembly_width_m Ã— mounting_bar_count
```

Default **2 bars** = one at top, one at bottom (owner-confirmed premount assembly rule).

### Override behavior

When `mounting_bar_length_m` is set, it is used as **total bar length** â€” width is **not** used for derivation.

### Known priced profiles (excluding TVA)

| Material | Profile | Rate |
|----------|---------|------|
| Steel | 30Ã—30Ã—1.5 | 2 EUR/ml |
| Aluminum | 30Ã—30Ã—1.5 | 3.5 EUR/ml |

Other profiles (e.g. `20x20x1.5`, `40x40x2`) may be selectable in QuoteWizard but are **not priced** until owner-confirmed registry rows exist.

### Worked examples (width_mm=4800)

| Case | Length | Steel total | Aluminum total |
|------|--------|-------------|----------------|
| Auto (count=2) | 9.6 ml | 19.20 EUR | 33.60 EUR |
| Override `mounting_bar_length_m=5` | 5 ml | 10.00 EUR | 17.50 EUR |
| `mounting_bar_count=3` | 14.4 ml | 28.80 EUR | â€” |

Simulate totals vs baseline (844.41 EUR): steel auto **863.61**, aluminum auto **878.01**, steel override **854.41**, aluminum override **861.91**.

### Unknown profile behavior

- Template material line gated off (`mounting_bar_profile_in` gate in seed).
- Warning: `mounting_bar_profile_price_missing:<steel|aluminum>:<profile>`
- **No silent fallback** to 30Ã—30Ã—1.5 pricing.

### ACM panel â€” separate template

- Captured option only; **no ACM material/rate** inside TPL-VOLUMETRIC-LETTERS.
- Dimensions are **not** derived from letter width/height.
- Panoul ACM/Alucobond casetat needs its own template (e.g. future TPL-ACM-CASSETTED-PANEL) with separate dimensions â€” usually larger than the letter assembly.

## Production metadata vs costing

Work Intake and QuoteWizard now carry production metadata alongside costing fields. These **do not change unit rates** but surface soft warnings when incomplete:

| Field | Cost impact | Warning when missing |
|-------|-------------|----------------------|
| `paint_ral_code` / `paint_ral_name` | none (tubes priced via `paint_tube_count`) | `production_metadata_missing:paint_ral_code` if `paint_tube_count > 0` |
| `face_vinyl_color_code`, `face_vinyl_roll_width_mm` | none until finish selected | Oracal/print vinyl warnings |
| `face_finish_subtype=oracal_8500` | priced as Oracal 651 | `production_metadata:oracal_8500_priced_as_oracal_651` |

RAL code is production information; paint cost remains whole-tube material (`MAT-VOPSEA-RAL`).

## Blueprint Dossier

Template-level dossier seeded via `backend/seeds/seed_tpl_volumetric_letters_dossier.py` (idempotent, **v2** task order). Includes structural `costengine_mapping_json`, `output_blocks_json`, `task_rules_json`, allowed variants, CNC/back-bevel/mounting rules â€” **no commercial prices in dossier**.

Task rules reference `quote_input` conditions: vinyl when `face_finish_type != none`, bars when `mounting_system` is steel/aluminum, mounting template when `mounting_template_enabled`, vector verification first, QC internal before packaging, ACM as separate-template note only.

After seed: dossier-related readiness warnings clear; `letters_vector_file_required` remains; `ready_for_quote` may still be `false` until vector/file policy satisfied.

## Remaining blockers / owner decisions

1. **Vector/file for final quote** â€” `letters_vector_file_required` remains after dossier seed.
2. **Estimated materials** (MAT-CONSUMABILE-MONTAJ) â€” `needs_review` if policy treats as blocker.
3. **Mounting bar labor** â€” material priced; manoperÄƒ montaj bare not owner-confirmed yet.
4. **ACM panel premount** â€” captured only until owner rules exist.
5. **Mounting template CNC** â€” 1 pass default; confirm if area-based quantity is preferred later.
6. **Conditional params** (`illumination_enabled`, `paint_finish`) â€” not yet enforced in CostEngine.
7. **Future materials/thickness** â€” additional CNC pass rules should extend `formula_params`, not hardcoded CostEngine logic.

## Commits reference

- `d4264fa` â€” QC internal-only
- `8a15e28` â€” template pricing currency EUR
- `76fb2c4` â€” only TPL-VOLUMETRIC-LETTERS active
- `2a3c321`â€“`a535b59` â€” finish/mounting capture and pricing
- `46c8260` â€” derive premount bar length from assembly width Ã— bar count; profile-specific gates
- `fe0be10` â€” blueprint dossier seed for TPL-VOLUMETRIC-LETTERS
