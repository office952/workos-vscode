# Material Consumption and Nesting Contract

## 1. Purpose

This document defines the official contract for real material consumption, nesting, roll-width consumption, and conditional graphic splitting/panelization for Intake V6, Product Truth, and Commercial Preview.

Core rule:

```text
geometry_area != real_material_consumption
```

Intake V6 may display nesting or material preview surfaces, but Product Truth must distinguish geometry measurement from real material consumption. Commercial Preview must not become quote-ready when material quantity is only area-based for materials that require sheet nesting, roll nesting, split, or panelization.

For roll materials such as Oracal, vinyl, autocolant, print vinyl, and laminate, consumption is based on selected roll width multiplied by roll length used. It is not based on the visible cut percentage of the roll width. If the graphic does not fit the selected material format, the system must define a split/panelization decision before quote-readiness.

This contract does not implement a nesting engine, split algorithm, Pricing formula, Quote, Order, Execution, DB schema, UI redesign, or stock reservation. It defines the boundary and Product Truth model required before those systems can safely consume material quantities.

## 2. Scope

In scope:

- Plexiglas;
- Forex;
- ACM/Bond;
- Oracal/vinyl/autocolant;
- print vinyl;
- laminate;
- rigid sheet nesting;
- roll material nesting;
- roll width selection in Intake V6 / Form System;
- conditional graphic splitting/panelization;
- waste and efficiency;
- material quote-readiness.

Out of scope:

- Pricing formula implementation;
- nesting engine implementation;
- automatic split/panelization algorithm implementation;
- stock reservation;
- Quote/Order/Execution;
- ProductAggregate;
- TaskGraph;
- ExecutionPlan;
- DB schema;
- seeds/migrations;
- machine-specific CAM nesting;
- multi-job/gang nesting optimization.

## 3. Core Principle

`geometry_area != real_material_consumption`

Definitions:

- `geometry_area`: vector/path area measured from the SVG or derived geometry.
- `visible_area`: area visible in the final product.
- `bounding_box_area`: width x height bounding rectangle for a part or graphic.
- `nested_consumption_area`: area occupied by nested parts on actual material format.
- `purchased_material_area`: full purchased/allocated material area, usually full sheets or full roll width x length.
- `billable_material_area`: material area used for commercial preview or quote, after readiness rules.
- `roll_width_consumption_area`: `selected_roll_width_mm * roll_length_used_mm`.
- `roll_length_used_mm`: length advanced/consumed along the roll after arranging graphics.
- `waste_area`: purchased/allocated material area minus nested/visible useful area, depending on material class.
- `efficiency_percent`: useful/nested area divided by purchased/allocated area.

Rules:

- `geometry_area` may be used for preview/estimate only.
- `real_material_consumption` requires nesting on a real sheet or roll format.
- For roll materials, consumed width is selected roll width, not cut geometry width.
- Usable roll width is fit validation only; commercial/material consumption uses selected roll width.
- If a graphic or part does not fit the selected material format, a split/panelization decision is required before quote-readiness.

## 4. Material Classes

| Material class | Examples | Format type | Needs nesting? | Needs split if oversized? | Consumption basis | Quote-ready requirement |
| --- | --- | --- | --- | --- | --- | --- |
| `rigid_sheet` | Plexiglas, Forex, ACM/Bond | sheet | yes | yes | sheet count / nested sheet consumption / purchased sheet area | sheet format, nesting result, unplaced/oversized decisions resolved |
| `roll_vinyl` | Oracal 651, cutting vinyl, autocolant | roll | yes | yes | selected roll width x roll length used | selected roll width, usable width check, roll nesting, split decision if needed |
| `roll_print` | print vinyl | roll | yes | yes | selected roll width x print length used | selected roll width, print layout, panelization if oversized |
| `roll_laminate` | laminate film | roll | yes | yes | selected laminate roll width x laminate length used | laminate width compatible with print panels and confirmed layout |
| `consumables` | LED, screws, adhesives | piece/linear/other | conditional | no | count, length, pack, or operation-specific basis | source/state and quantity rule confirmed |
| `profile_linear` | cant, profile, F-cant if applicable | linear/profile | linear optimization later | conditional | linear length + waste/profile stock rule | profile length rule and waste policy confirmed |

## 5. Rigid Sheet Nesting Contract

Rules:

- Applies to Plexiglas, Forex, ACM/Bond, and other sheet materials.
- Default/configurable sheet format: `3000 x 2000 mm`.
- Material rules decide whether rotation/orientation is allowed.
- Parts must be nested on sheets; consumption is not the sum of part areas only.
- If a part exceeds sheet width/height in every allowed orientation, mark `oversized_for_sheet`.
- If oversized but technically splittable, propose split/panelization.
- Split/panelization is required only when the part does not fit the sheet.
- Split pieces must each fit inside the selected sheet format.
- Split must preserve technical meaning: visible face split lines, possible joint/overlap, assembly risk, and operator approval requirement.

Required output fields:

- `sheet_width_mm`;
- `sheet_height_mm`;
- `sheet_count`;
- `used_area_mm2`;
- `waste_area_mm2`;
- `efficiency_percent`;
- `nested_parts[]`;
- `unplaced_parts[]`;
- `oversized_parts[]`;
- `split_required`;
- `split_plan[]`;
- `nesting_status`.

Product Truth expected path:

```text
product_truth.material_consumption.rigid_sheets[]
```

Readiness:

- only area-based quantity -> `partial`;
- sheet format missing -> `blocked` or `partial`;
- nesting not computed -> `partial`;
- unplaced parts -> `blocked`;
- part oversized and no split plan -> `blocked` / `needs_decision`;
- split plan exists but is not operator-confirmed -> `partial`;
- nesting computed and split/oversized decisions confirmed -> `material_consumption_ready = true`.

## 6. Roll Material Nesting Contract

Rules:

- Applies to Oracal/vinyl/autocolant, print vinyl, and laminate.
- Material is roll-based, not sheet-based.
- Roll width is selected in Intake V6/Form System.
- Initial supported roll widths: `1000 mm`, `1260 mm`.
- Safety margin: `20 mm` left and `20 mm` right.
- Usable widths:
  - `1000 mm` roll -> `960 mm` usable;
  - `1260 mm` roll -> `1220 mm` usable.
- Roll length used is calculated from actual arranged graphics along the roll.
- Consumption is `selected_roll_width_mm x roll_length_used_mm`.
- Do not calculate roll material consumption as geometry area.
- Do not calculate roll material consumption by the percentage of material actually cut.
- If a graphic uses only `200 mm` width but needs `1500 mm` length and selected roll width is `1260 mm`, material consumption is `1260 mm x 1500 mm`, not `200 mm x 1500 mm`.
- If selected roll width is `1000 mm` and length used is `1500 mm`, material consumption is `1000 mm x 1500 mm`.
- Roll usable width is only maximum fitting width after margins; full selected width remains consumed width.
- If graphic width fits usable width, do not split by default.
- If one graphic side exceeds usable width in all allowed rotations, split/panelization must be proposed.
- Split/panelization is required only when the graphic cannot fit within usable roll width.
- Split pieces must each fit inside usable width.
- Print and laminate split plans must preserve print/lamination consistency.

Required split fields for roll materials:

- `panel_count`;
- `panel_width_mm`;
- `panel_height_mm`;
- `overlap_mm` if required;
- seam/join notes;
- operator approval requirement.

Required output fields:

- `selected_roll_width_mm`;
- `usable_width_mm`;
- `left_margin_mm`;
- `right_margin_mm`;
- `roll_length_used_mm`;
- `roll_width_consumption_area_mm2`;
- `geometry_area_mm2`;
- `waste_area_mm2`;
- `efficiency_percent`;
- `nested_parts[]`;
- `unplaced_parts[]`;
- `oversized_parts[]`;
- `split_required`;
- `split_plan[]`;
- `nesting_status`.

Product Truth expected path:

```text
product_truth.material_consumption.roll_materials[]
```

Readiness:

- roll width not chosen -> `partial` / `blocked`;
- usable width not applied -> `partial`;
- only geometry area -> `partial`;
- graphic exceeds usable width and no split plan exists -> `blocked` / `needs_decision`;
- split plan exists but is not operator-confirmed -> `partial`;
- split confirmed and all panels fit -> `material_consumption_ready = true`;
- nesting computed without split because it fits -> `material_consumption_ready = true`.

## 7. Roll Width Selection Contract

Rules:

1. Roll width must be an explicit Form System field for roll materials.
2. Initial supported values: `1000 mm`, `1260 mm`.
3. Selected roll width becomes Product Truth input.
4. Usable width is selected roll width minus `40 mm` total margin.
5. Commercial/material consumption uses `selected_roll_width_mm`, not `usable_width_mm`.
6. `usable_width_mm` is only for fit validation.
7. `roll_length_used_mm` is determined by nesting layout along the roll.
8. If graphics are narrow, leftover roll width is still consumed unless there is a formal multi-job/gang nesting policy.
9. No multi-job/gang nesting policy is assumed in this contract.
10. Any future gang nesting must be a separate owner-approved contract.

Product Truth expected fields:

- `selected_roll_width_mm`;
- `usable_width_mm`;
- `left_margin_mm`;
- `right_margin_mm`;
- `roll_length_used_mm`;
- `roll_width_consumption_area_mm2`;
- `roll_width_source`;
- `roll_width_state`;
- `roll_width_confirmed`.

## 8. Conditional Graphic Split / Panelization Contract

Split/panelization is not a default operation. It is allowed or required only when the graphic or part cannot fit within the selected material format.

Rules:

1. First try to fit the graphic/part as a whole.
2. Try allowed rotations/orientations if material/process permits.
3. If it fits, no split is allowed by default.
4. If it does not fit, mark `oversized_for_material_format = true`, `split_required = true`, and `split_status = proposed | confirmed | rejected | blocked`.
5. Split must create panels/pieces that fit the selected material format.
6. Split must be visible in Product Truth, not hidden inside Pricing.
7. Operator must confirm split before quote-ready.
8. Split may introduce production risks: visible seam, overlap, alignment risk, assembly time, additional operations, and customer approval.
9. If split is rejected and no material format can fit the full graphic, material consumption readiness is blocked.
10. Split applies to both rigid sheet materials and roll materials.

Product Truth expected path:

```text
product_truth.material_consumption.split_plans[]
```

Canonical split plan object:

```json
{
  "material_code": "string",
  "material_class": "rigid_sheet | roll_vinyl | roll_print | roll_laminate",
  "source_geometry_id": "string",
  "selected_format_type": "rigid_sheet | roll",
  "selected_format_width_mm": 0,
  "selected_format_height_or_roll_usable_width_mm": 0,
  "oversized_for_material_format": true,
  "split_required": true,
  "split_status": "proposed | confirmed | rejected | blocked",
  "panel_count": 0,
  "panels": [
    {
      "panel_id": "string",
      "width_mm": 0,
      "height_mm": 0,
      "fits_format": true,
      "overlap_mm": 0,
      "seam_side": "string",
      "notes": "string"
    }
  ],
  "operator_confirmed": false,
  "customer_approval_required": false,
  "blockers": [],
  "warnings": []
}
```

## 9. Intake V6 UI Surface Addendum

These surface IDs extend `INTAKE_V6_UI_SURFACE_INVENTORY_CONTRACT.md`.

| Surface ID | Step | Surface | Applies to | Current UI | Product Truth path | Readiness | Commercial boundary | Risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| IV6-S2-NESTING-PREVIEW | Pas 2 | Nesting preview / `Nesting activ` / nest2 comparison | rigid sheets and some preview rows | material breakdown panel / nesting technical accordion | `product_truth.material_consumption.*` later | partial until real nesting output exists | preview only; not stock consumption | HIGH if treated as final consumption |
| IV6-S2-RIGID-SHEET-NESTING | Pas 2 | Plexiglas/Forex/ACM sheet layout | rigid sheet materials | material breakdown / sheet quote candidates | `product_truth.material_consumption.rigid_sheets[]` | partial until sheet format + nesting + oversized decisions exist | not quote-ready from area only | HIGH |
| IV6-S2-ROLL-MATERIAL-NESTING | Pas 2 | Vinyl/print/laminate roll layout | roll materials | current material rows/warnings; formal UI missing | `product_truth.material_consumption.roll_materials[]` | partial until roll width + roll layout exist | not quote-ready from geometry area | HIGH |
| IV6-S2-ROLL-WIDTH-SELECTION | Pas 2 | Selected roll width field | roll materials | partial option contract exists; formal Form System field required | `product_truth.material_consumption.roll_materials[].selected_roll_width_mm` | partial until selected and confirmed | consumption uses selected width | HIGH if omitted |
| IV6-S2-MATERIAL-CONSUMPTION-REALITY | Pas 2 | Real material consumption vs geometry area | all material rows | material breakdown and live calc | `product_truth.material_consumption.*` | partial while area-only | commercial preview must label partial | HIGH |
| IV6-S2-MATERIAL-WASTE-EFFICIENCY | Pas 2 | Waste and efficiency | sheet and roll materials | nesting rows show efficiency where present | `product_truth.material_consumption.*.waste_area_mm2`, `efficiency_percent` | partial until computed | preview only until confirmed | MEDIUM/HIGH |
| IV6-S2-MATERIAL-SPLIT-PANELIZATION | Pas 2 | Conditional split/panelization decision | oversized sheets/roll graphics | not formalized today | `product_truth.material_consumption.split_plans[]` | blocked/partial until proposed and confirmed | no quote-ready when required and missing | HIGH |
| IV6-S2-OVERSIZED-MATERIAL-WARNING | Pas 2 | Oversized for selected material format warning | sheets and rolls | not formalized today | `product_truth.material_consumption.*.oversized_parts[]` | blocked until resolved | must block quote/order if unresolved | HIGH |
| IV6-S3-MATERIAL-CONSUMPTION-SUMMARY | Pas 3 | Confirmare material consumption summary | all quoteable materials | Confirmare summary / pricing sidebar today | `product_truth.material_consumption.summary` | partial until Product Truth material readiness exists | cannot look final if partial | HIGH |
| IV6-S3-SPLIT-PANELIZATION-SUMMARY | Pas 3 | Confirmare split/panelization summary | oversized cases | not formalized today | `product_truth.material_consumption.split_plans[]` | partial/blocked until operator confirmed | must block quote/order if unresolved | HIGH |

Contract notes:

- `Nesting activ` exists visually in Review, but it must not be treated as real consumption unless tied to Product Truth material consumption output.
- If current nesting is only visual or comparative, status is `partial`.
- If commercial materials use area-only quantities for sheet/roll materials, risk is HIGH.
- If roll material consumption uses cut geometry width instead of selected roll width, risk is HIGH.
- If oversized graphics have no split/panelization decision, risk is HIGH.
- If split exists but is not confirmed, quote-readiness is `partial` or `blocked`.

## 10. Product Truth Material Consumption Model

Canonical rigid sheet object:

```json
{
  "material_code": "string",
  "material_label": "string",
  "format_type": "rigid_sheet",
  "sheet_width_mm": 3000,
  "sheet_height_mm": 2000,
  "sheet_count": 0,
  "geometry_area_mm2": 0,
  "nested_consumption_area_mm2": 0,
  "purchased_material_area_mm2": 0,
  "waste_area_mm2": 0,
  "efficiency_percent": 0,
  "oversized_parts": [],
  "split_required": false,
  "split_plan_id": null,
  "nesting_status": "missing | preview | computed | blocked | confirmed",
  "source": "svg_geometry | nesting_preview | nesting_engine | operator_override | fallback_area_estimate",
  "state": "estimate_area_only | nesting_preview | computed | confirmed | blocked | owner_override_confirmed",
  "confirmed": false,
  "blockers": [],
  "warnings": []
}
```

Canonical roll material object:

```json
{
  "material_code": "string",
  "material_label": "string",
  "format_type": "roll",
  "selected_roll_width_mm": 1260,
  "usable_width_mm": 1220,
  "left_margin_mm": 20,
  "right_margin_mm": 20,
  "roll_length_used_mm": 0,
  "roll_width_consumption_area_mm2": 0,
  "geometry_area_mm2": 0,
  "waste_area_mm2": 0,
  "efficiency_percent": 0,
  "oversized_parts": [],
  "split_required": false,
  "split_plan_id": null,
  "nesting_status": "missing | preview | computed | blocked | confirmed",
  "source": "form_system_roll_width_field | roll_format_registry | nesting_preview | nesting_engine | fallback_area_estimate",
  "state": "estimate_area_only | nesting_preview | computed | confirmed | blocked | owner_override_confirmed",
  "confirmed": false,
  "blockers": [],
  "warnings": []
}
```

Canonical split plan object:

```json
{
  "split_plan_id": "string",
  "material_code": "string",
  "material_class": "rigid_sheet | roll_vinyl | roll_print | roll_laminate",
  "reason": "oversized_for_material_format",
  "oversized_for_material_format": true,
  "split_required": true,
  "split_status": "proposed | confirmed | rejected | blocked",
  "panel_count": 0,
  "panels": [],
  "operator_confirmed": false,
  "customer_approval_required": false,
  "source": "split_plan_generator | operator_override",
  "state": "split_proposed | split_confirmed | split_rejected | blocked",
  "blockers": [],
  "warnings": []
}
```

## 11. Commercial Readiness Rules

1. A material line is not quote-ready if consumption is area-only for sheet/roll materials.
2. Rigid sheet materials require sheet nesting or explicit owner override.
3. Roll materials require selected roll width and usable-width margin calculation.
4. Roll material commercial consumption uses selected roll width x roll length used.
5. Roll material commercial consumption does not use cut geometry width.
6. If a part/graphic exceeds material format, quote-readiness requires a split/panelization decision.
7. Split/panelization must be operator-confirmed before quote-ready.
8. Commercial Preview may show area-based estimates only if labeled preview/partial.
9. Confirmare must not present material cost as final if material consumption readiness is partial.
10. Quote/Order cannot use material quantity without `material_consumption_ready` or explicit owner override.
11. Owner override must be explicit, audited, and downstream-visible.
12. Multi-job/gang nesting is not assumed and must not reduce material consumption unless a separate approved contract exists.

| Case | Can show preview? | Can create quote draft? | Can create order? | Required guard |
| --- | --- | --- | --- | --- |
| area-only rigid sheet | yes | no | no | `area estimate only`, `sheet nesting missing` |
| nested rigid sheet ready | yes | yes if all other Product Truth gates pass | no from Intake V6 | sheet format, nesting status, and confirmation visible |
| rigid sheet oversized without split | yes | no | no | `oversized_for_sheet`, split required |
| rigid sheet oversized with unconfirmed split | yes | no | no | `split proposed`, operator confirmation required |
| rigid sheet oversized with confirmed split | yes | yes if all other Product Truth gates pass | no from Intake V6 | split plan id and panels visible |
| area-only roll | yes | no | no | `area estimate only`, roll width/nesting missing |
| roll with selected width but no nesting | yes | no | no | `roll layout missing` |
| roll ready without split | yes | yes if all other Product Truth gates pass | no from Intake V6 | selected width, length used, margins visible |
| roll narrow graphic using full roll width | yes | yes if all other gates pass | no from Intake V6 | show selected width x length used |
| roll oversized without split | yes | no | no | `oversized_for_roll`, split required |
| roll oversized with confirmed split | yes | yes if all other gates pass | no from Intake V6 | split plan confirmed |
| logo-only not offerable | guarded preview only | no | no | `logo_only_candidate_not_offerable` |

## 12. Source/State Rules

Sources:

- `svg_geometry`;
- `nesting_preview`;
- `nesting_engine`;
- `split_plan_generator`;
- `payload_persisted`;
- `operator_override`;
- `fallback_area_estimate`;
- `material_registry`;
- `roll_format_registry`;
- `sheet_format_registry`;
- `form_system_roll_width_field`.

States:

- `estimate_area_only`;
- `nesting_preview`;
- `computed`;
- `split_proposed`;
- `split_confirmed`;
- `split_rejected`;
- `confirmed`;
- `blocked`;
- `override_required`;
- `owner_override_confirmed`.

Critical rules:

- `fallback_area_estimate` cannot become confirmed material consumption automatically.
- Visual nesting preview cannot become commercial truth without an output contract.
- Split plan generator output cannot become confirmed without operator confirmation.
- Split must not be silently hidden inside Pricing.
- Selected roll width is a Product Truth input, not an optimization detail.
- Leftover roll width is still material consumed unless a future gang-nesting contract says otherwise.

## 13. Examples

### A. Plexiglas / Forex

- A part area may be `1.2 sqm`.
- Real consumption depends on layout on a `3000 x 2000 mm` sheet.
- Output may consume one full sheet or part of a sheet depending on the approved consumption policy.
- If a part is `3500 x 800 mm`, it exceeds the `3000 mm` side and needs split/panelization or alternate format.
- Quote readiness requires nesting result and split decision if needed.

### B. Oracal narrow graphic

- Graphic cut geometry: `200 mm x 1500 mm`.
- Selected roll width: `1260 mm`.
- Commercial/material consumption: `1260 mm x 1500 mm`.
- Not allowed: `200 mm x 1500 mm`.
- Reason: the consumed roll length is `1500 mm` and selected roll width is `1260 mm`.

### C. Oracal 1000 mm roll

- Selected roll width: `1000 mm`.
- Usable width: `960 mm`.
- Graphic fits at `800 mm` width and `1500 mm` length.
- Consumption: `1000 mm x 1500 mm`.
- Usable width is only fit validation, not commercial width.

### D. Oracal oversized

- Selected roll width: `1260 mm`.
- Usable width: `1220 mm`.
- Graphic requires `1230 mm` width.
- It does not fit usable width.
- The system must propose split/panelization or alternate material decision.
- Split must be operator-confirmed before quote-ready.

### E. Logo-only

- If `logo.svg` is `1500 x 1500 mm`, it exceeds both `960 mm` and `1220 mm` usable roll widths if printed as one piece.
- Roll material split/panelization must be proposed if print/vinyl face must be produced on roll.
- Even if split/nesting preview exists, commercial surface remains blocked while the Logo template is not root offerable.

## 14. Integration With Existing Contracts

This contract extends, but does not replace:

- `INTAKE_V6_UI_SURFACE_INVENTORY_CONTRACT.md`;
- `INTAKE_V6_PRODUCT_TRUTH_CONTRACT.md`;
- `PRODUCT_SYSTEM_FORM_SYSTEM_COMPOSITION_CONTRACT.md`.

Concrete Form System fields for material consumption, nesting, roll width, and split/panelization are mapped by:

- `FORM_SYSTEM_FIELD_CONTRACT_MAP.md`.

Future implications:

- Form System Field Contract Map must include material consumption fields.
- Commercial Preview Boundary must depend on material consumption readiness.
- Product Truth Confirmation Policy must include split/panelization confirmation.
- Form System must expose roll width as an input where roll materials are involved.
- Any material nesting engine preparation must come later under separate owner GO.

## 15. What Is Still Partial Today

- Current UI shows nesting preview / `Nesting activ`-like surfaces.
- Current material lines may still be area-based or preview-only.
- No confirmed Product Truth path exists for real sheet/roll nesting.
- No formal roll width selection UI contract is implemented as Product Truth.
- No formal sheet format selection UI contract is implemented as Product Truth.
- No formal split/panelization UI contract is implemented.
- No quote readiness gate enforces material consumption reality yet.

## 16. Required Next Slice

Recommended next slice:

```text
FORM_SYSTEM_FIELD_CONTRACT_MAP_V1
```

The field map must include material consumption/nesting/split/roll-width fields:

- `sheet_format`;
- `selected_roll_width_mm`;
- `roll_usable_width_mm`;
- `left_margin_mm`;
- `right_margin_mm`;
- `roll_length_used_mm`;
- `roll_width_consumption_area_mm2`;
- `nesting_status`;
- `oversized_for_material_format`;
- `split_required`;
- `split_status`;
- `split_plan_id`;
- `panel_count`;
- `efficiency_percent`;
- `material_consumption_ready`.

Possible later slice:

```text
MATERIAL_NESTING_ENGINE_PREP_V1
```

Only after explicit owner GO.

## 17. Acceptance Criteria

Docs-only PASS requires:

- new contract exists;
- rigid sheet rules included;
- roll material rules included;
- selected roll width consumption rule included;
- conditional split/panelization included;
- `3000 x 2000 mm` sheet included;
- `1000 mm` and `1260 mm` roll widths included;
- `20 mm` left/right margins included;
- `960 mm` and `1220 mm` usable widths included;
- oversized/split rules included;
- narrow graphic example included: `200 x 1500` on selected roll width;
- Product Truth paths included;
- commercial readiness rules included;
- UI Surface Inventory addendum included;
- no code changes;
- no pricing changes;
- no quote/order/execution changes.