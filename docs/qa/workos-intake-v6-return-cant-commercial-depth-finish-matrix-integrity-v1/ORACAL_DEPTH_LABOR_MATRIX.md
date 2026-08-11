# ORACAL_DEPTH_LABOR_MATRIX

Same perimeter **P = 12.5 ml**. Oracal 651 material rate **5 EUR/m²**. Labor **1 EUR/ml** via `RETURN_CANT_VINYL_APPLICATION_LABOR`.

Proven by `tests/test_intake_v6_return_cant_depth_finish_matrix.py::test_oracal_material_monotone_with_depth_and_constant_labor`.

| Case | Depth | Material qty (m²) | Material subtotal | Labor qty (ml) | Labor unit | Labor subtotal |
|---|---:|---:|---:|---:|---:|---:|
| O30 | 30 | P × 0.03 = 0.375 | 1.875 | 12.5 | 1.0 | **12.5** |
| O60 | 60 | P × 0.06 = 0.750 | 3.750 | 12.5 | 1.0 | **12.5** |
| O80 | 80 | P × 0.08 = 1.000 | 5.000 | 12.5 | 1.0 | **12.5** |
| O100 | 100 | P × 0.10 = 1.250 | 6.250 | 12.5 | 1.0 | **12.5** |

## Required checks

| Check | Result |
|---|---|
| labor O30 = O60 = O80 = O100 | **YES** (all 12.5) |
| material varies with depth | **YES** (monotone) |
| depth affects only material, not per-ml labor | **YES** |

## Mixed groups (no dominant depth)

| Group | Finish | Depth | Perimeter | Material area | Labor ml |
|---|---|---:|---:|---:|---:|
| A | Oracal | 30 | 5.0 | 0.15 | 5.0 |
| B | Oracal | 100 | 7.5 | 0.75 | 7.5 |
| **Aggregate** | | | **12.5** | **0.90 m² → 4.50 EUR** | **12.5 → 12.5 EUR** |

No averaged width. No total-area labor.
