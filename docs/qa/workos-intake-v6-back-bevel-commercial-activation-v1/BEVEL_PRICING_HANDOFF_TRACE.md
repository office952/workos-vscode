# BEVEL_PRICING_HANDOFF_TRACE

Layer/group `backing_mode` is now authoritative when persist strips globals.

## Path

1. `finish_setup.letter_group_finishes[].backing_mode`
2. `resolve_volumetric_backing_state` / `iter_explicit_layer_backing_modes`
3. `resolve_backing_bevel_perimeter_ml` (ON groups only)
4. quote_input `back_bevel_enabled` + `backing_bevel_perimeter_ml`

## Runtime (layer-owned persist)

| | OFF | ON |
|--|--|--|
| payload global `backing_mode` | null | null |
| layer mode | `forex_10_no_bevel` | `forex_10_with_bevel` |
| QI `backing_mode` | `forex_10_no_bevel` | `forex_10_with_bevel` |
| QI `back_bevel_enabled` | false | **true** |
| QI `backing_bevel_perimeter_ml` | null | **7.41749** |

```text
LAYER_PATH_LOSS = REPAIRED
```
