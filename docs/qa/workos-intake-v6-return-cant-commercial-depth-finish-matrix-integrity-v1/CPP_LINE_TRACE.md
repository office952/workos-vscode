# CPP_LINE_TRACE

| Finish | Lines | Qty / rate |
|---|---|---|
| stock | `modelare_cant_aluminiu` only (no `finisaje_cant_*`) | forming flat 5 EUR/ml |
| Oracal material | `finisaje_cant_oracal_material` | perimeter × depth → m² × series catalog |
| Oracal labor | `finisaje_cant_oracal_labor` | perimeter → ml × `RETURN_CANT_VINYL_APPLICATION_LABOR` @ 1 EUR/ml |
| RAL | `finisaje_cant_ral_material`, `finisaje_cant_ral_labor` | ml × depth tier / registry labor |

## Oracal quantity warnings

| Line | Warning |
|---|---|
| material | `quantity_source=perimeter_m_x_return_depth_mm_to_m2` or `letter_group_perimeter_m_x_return_depth_mm_to_m2` |
| labor | `quantity_source=letter_perimeter_m` or `letter_group_perimeter_m_sum` |

## Registry binding (labor)

`registry_bound=RETURN_CANT_VINYL_APPLICATION_LABOR;…;rate_basis=per_linear_meter`

## RAL mixed

`cant_ral_mixed_depth_weighted_avg` when tiers differ.

## Face (unchanged — not cant)

`finisaje_aplicare_autocolant_fata` → F7F `VINYL_APPLICATION_EUR_M2` = 3 EUR/m² on face area.
