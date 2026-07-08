# RETURN_CANT_INTAKE_V6_VARIATIONS_TRUTH_CAPTURE_AUDIT_V1

## Verdict

```text
RETURN_CANT_VARIATIONS_AUDIT_READY_FOR_ADAPTER
```

## Scope checked

- docs-only
- screenshots-only for UI evidence
- no adapter implementation
- no UI changes
- no Pricing changes
- no preview/calculation implementation

## HEAD

- accepted HEAD: `8237d9a`
- after audit write: pending at write time

## Safety gate

Confirmed:

- `git rev-parse --short HEAD` -> `8237d9a`
- no staged files before work
- `git diff --check` clean before work
- unrelated untracked files already existed and were ignored

## Routes audited

1. `http://127.0.0.1:3000/intake-v6/IR-MRBMAK7Z/operator`
2. `http://127.0.0.1:3000/intake-v6/IR-MR18L96M/operator`
3. `http://127.0.0.1:3000/inventory/pricing`

Why both Intake routes were used:

- `IR-MRBMAK7Z` is the relevant volumetric letters route;
- `IR-MR18L96M` is logo-only candidate/read-only, but it exposes the clearest `Vector Logo` cant surface needed for the audit contrast.

## UI audit summary

### Sections checked

- `Review > Finisaje`
- `Finisaje pe layer`
- `Vector Litere`
- `Vector Logo`
- `Return/cant diagnostic`
- live Pricing page filter/read-only coverage

### Variations found

Cant finish options found in current UI:

- `Alb`
- `Negru`
- `Auriu`
- `Argintiu`
- `Vopsit RAL`
- `Oracal 651`

Cant depth options found in current UI:

- `30`
- `60`
- `80`
- `100`

### Vector Litere

- 4 rows observed in the live route
- each row has its own cant summary
- current saved/hydrated state on route: all four rows show `Alb · 60 mm`
- letters use `letter_group_finishes[]` as row source
- letters can own per-row finish and per-row depth today

### Vector Logo

- 1 row observed in the logo route
- row shows face personalization method plus cant block
- current saved/hydrated state on route: `Alb · 60 mm`
- logo uses `artwork_finishes[]` as row source
- logo can own per-row finish and per-row depth today

### Finish-specific findings

- `Vopsit RAL` has conditional color picker
- `Oracal 651` has conditional color picker
- there is no separate generic `paint_target` field
- there is no generic extra color list beyond conditional Oracal/RAL pickers
- fixed finishes (`Alb`, `Negru`, `Auriu`, `Argintiu`) are presets, not free color-list choices

## Pricing boundary check

Live Pricing page confirmed these entries exist:

- `MAT-PROFIL-LATERAL-LITERE-30MM`
- `MAT-PROFIL-LATERAL-LITERE-60MM`
- `MAT-PROFIL-LATERAL-LITERE-80MM`
- `MAT-PROFIL-LATERAL-LITERE-100MM`
- `MAT-VOPSEA-RAL`
- `RETURN_PROFILE_MACHINE_FORMING`
- `RETURN_PROFILE_FACE_BONDING`

Interpretation:

- material profile cost is depth-specific in Pricing
- labor cost is present in Pricing, but generic per ml, not per depth
- `Oracal 651` cant wrap remains partially on `shared_edge_cant_rules` owner pricing path, not cleanly on a dedicated cant pricing-registry key

## Decision basis

READY for adapter because:

1. the real UI variations are now explicitly audited
2. depth taxonomy is explicit and aligns with live Pricing material variants
3. letters and logo both expose return/cant at row level
4. the adapter can map truth capture without inventing new variation taxonomy

Not fully clean yet because:

1. canonical Product Truth paths are still unwritten at runtime
2. `material_profile` is still implicit
3. `paint_target` is absent
4. `Oracal 651` cant pricing alignment is incomplete

## Mandatory matrix summary

| ui_surface | vector_type | variation | field_key | current_state | product_truth_path | pricing_key_needed | blocker |
|---|---|---|---|---|---|---|---|
| `Review > Finisaje > Vector Litere` | `Vector Litere` | depth | `return_depth_mm` | hydrated per row | `components.return_cant.depth_mm` | `MAT-PROFIL-LATERAL-LITERE-{30|60|80|100}MM` | no canonical writer |
| `Review > Finisaje > Vector Litere` | `Vector Litere` | stock finish | `return_finish_type` | hydrated per row | `components.return_cant.finish_type` | generic profile+labor downstream | no canonical writer |
| `Review > Finisaje > Vector Litere` | `Vector Litere` | Oracal cant | `return_oracal_code` | conditional/hydrated | `components.return_cant.color_target.oracal_code` | live `MAT-ORACAL-651` vs preview `edge_cant_oracal_651` gap | pricing alignment gap |
| `Review > Finisaje > Vector Litere` | `Vector Litere` | RAL cant | legacy row color fields | conditional/hydrated | `components.return_cant.color_target.ral_code` | `MAT-VOPSEA-RAL` | no paint_target |
| `Review > Finisaje > Vector Logo` | `Vector Logo` | depth | `return_depth_mm` | hydrated per row | `components.return_cant.depth_mm` | `MAT-PROFIL-LATERAL-LITERE-{30|60|80|100}MM` | no canonical writer |
| `Review > Finisaje > Vector Logo` | `Vector Logo` | stock finish | `return_finish_type` | hydrated/manual per row | `components.return_cant.finish_type` | generic profile+labor downstream | no canonical writer |
| `Review > Finisaje > Vector Logo` | `Vector Logo` | Oracal cant | `return_oracal_code` | conditional/hydrated | `components.return_cant.color_target.oracal_code` | same Oracal wrap gap | pricing alignment gap |
| `Review > Finisaje > Vector Logo` | `Vector Logo` | RAL cant | legacy row color fields | conditional/hydrated | `components.return_cant.color_target.ral_code` | `MAT-VOPSEA-RAL` | no paint_target |
| `Return/cant diagnostic` | `Vector Litere` + `Vector Logo` | perimeter dependency | `quote_geometry.letter_perimeter_m` evidence only | context_only | `components.face.confirmed_perimeter` | `RETURN_PROFILE_MACHINE_FORMING`, `RETURN_PROFILE_FACE_BONDING` use ml downstream | missing canonical dependency |

## Formula checkpoint

```text
component: return_cant
quantity_basis: ml
required_quantity_input: components.face.confirmed_perimeter.value
analyzer_required_input: perimeter_m suggestion
quantity_formula: return_cant.quantity_ml = components.face.confirmed_perimeter.value
pricing_required_keys:
  - return_cant.<variation>.material_cost_per_ml
  - return_cant.<variation>.labor_cost_per_ml
pricing_boundary:
  - material/labor costs remain in /inventory/pricing
  - component stores no cost and no price values
```

Audit note:

- material side matches depth variants today
- labor side is generic per ml today, not per variation

## Screenshots saved

- `return-cant-letters-review-zone.png`
- `return-cant-logo-variation-card.png`
- `pricing-return-profile-variants.png`
- `pricing-return-operations.png`

Folder:

- `docs/qa/return-cant-intake-v6-variations-truth-capture-audit-2026-07-08/`

## Blockers

- `components.return_cant.material_profile` missing in runtime
- `components.return_cant.layer_group_ids` missing in runtime
- `components.return_cant.confirmation_state` missing in runtime
- `components.face.confirmed_perimeter` missing in runtime
- `paint_target` absent in UI/runtime
- `Oracal 651` cant wrap pricing alignment gap between live Pricing and `shared_edge_cant_rules`

## Honest UI opinion

- variatiile de cant sunt destul de clare pentru operator pe `Vector Litere`
- diferenta dintre `Vector Litere` si `Vector Logo` este mai clara in cod si in cardul extins de logo decat in shell-ul compact de review
- Pricing boundary nu este suficient de clar pentru cantul cu Oracal, deoarece runtime-ul actual lasa impresia unei reguli locale owner-side, nu a unei surse complet aliniate la Pricing Registry

## Forbidden scope confirmation

- no component root
- no component quote
- no Logo offerability changes
- no Pricing changes
- no Quote/Order changes
- no Execution changes
- no ProductAggregate changes
- no TaskGraph changes
- no ExecutionPlan changes
- no DB/seed/migration
- no UI nou
- no endpoint public nou

## Validation

- `git diff --check`
- docs-only + screenshots-only scope check
- no build
- no tests

## Next prompt

```text
RETURN_CANT_TRUTH_FIELD_CAPTURE_READONLY_CONTRACT_ADAPTER_V1
```

With explicit reminder:

```text
Map the audited UI variations exactly as they exist today. Do not invent depth-specific labor keys, do not promote step-one/logo badges to component truth, and keep Oracal cant pricing alignment as a documented follow-up gap.
```