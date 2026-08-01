# RETURN_WRAP_AREA_CONTRACT

**Verdict:** IMPLEMENT_MODEL_A  
**FormulaId:** `return_wrap_area`  
**Owner:** Volum aluminiu / return cant linked module (`TPL-VOLUM-ALUMINIU_v1`)

## Geometry

```text
band_width_m = (return_depth_mm + RETURN_VINYL_BAND_EXTRA_MM) / 1000
quote_perimeter_m = letter_perimeter_m × (1 + EDGE_CANT_QUOTE_WASTE_PERCENT/100)
area_m2 = round(quote_perimeter_m × band_width_m, 4)
```

Constants (authorized in repo, not invented here):

| Constant | Value | Source |
|----------|-------|--------|
| `RETURN_VINYL_BAND_EXTRA_MM` | 10 | `volumetric_face_vinyl_service.py` |
| `EDGE_CANT_QUOTE_WASTE_PERCENT` | 20 | `shared_edge_cant_rules.py` |

Matches `build_edge_cant_oracal_651_material_row` geometry (without pricing).

## Inputs

| Input | Required | Missing behavior |
|-------|----------|------------------|
| `letter_perimeter_m` | yes | `source_missing`, qty null |
| `return_depth_mm` | yes | `source_missing`, qty null — **no default 60** |

## Variant

Gate: `return_finish_type = oracal_wrapped` (seed). Inactive / Stock / RAL paint → not emitted.

## Unit

Output: m² (template `mp`).

## Freeze

Evaluated only inside `apply_technical_material_requirements` before Quote Snapshot V2 freeze.
