# DEAD_PIECES_CHECK

| Item | Verdict | Note |
|------|---------|------|
| `return_wrap_area` seed formula_id | **ALIVE** | Registered + handler + tests |
| `compute_return_wrap_area_m2` | **ALIVE** | Shared by freeze formula + pricing row builder |
| Pricing default depth 60 in `build_edge_cant_oracal_651_material_row` | **KEPT** (pricing path only) | Freeze formula does **not** use that default |
| `return_paint_consumption` seed formula_id | **DECLARED / UNRESOLVED** | Still unregistered; honest `source_missing` |
| Inventory / material_inputs / materialize | **OUT OF SCOPE** | Untouched |
| Frontend formula calc | **NONE** | No FE change this batch |
| Group-level wrap perimeter subset | **GAP** | Job-level `letter_perimeter_m` when finish globally wrapped |

No dead product code introduced. Paint remains intentionally unresolved pending Owner yield decision.
