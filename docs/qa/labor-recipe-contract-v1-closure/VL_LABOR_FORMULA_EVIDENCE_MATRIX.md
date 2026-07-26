# VL Labor Formula Evidence Matrix (12)

Kickoff dump: labor recipes on `TPL-VOLUMETRIC-LETTERS_v2` (registry/commercial links; runtime `formula_id=null`).

| # | Catalog / op | Evidence | Final status | Qty key (if any) | Owner missing |
|---|--------------|----------|--------------|------------------|---------------|
| 1 | RETURN_PROFILE_FACE_BONDING | perimeter ownership + commercial return_profile_ml; seed formula name unregistered | QUANTITY_KEY_CONFIRMED | `letter_perimeter_m` | labor formula binding (not productivity invent) |
| 2 | FACE_VINYL_APPLICATION_LABOR | `face_vinyl_used_sqm` handler + finish area | QUANTITY_KEY_CONFIRMED | `letter_face_area_m2` | explicit VL ops formula_id attach |
| 3 | LAMINATION | finish area commercial | QUANTITY_KEY_CONFIRMED | `letter_face_area_m2` | versioned service formula |
| 4 | PAINTING | overlaps return RAL labor; perimeter | QUANTITY_KEY_CONFIRMED | `letter_perimeter_m` | XOR vs RETURN_CANT_RAL_PAINT_LABOR |
| 5 | RETURN_CANT_RAL_PAINT_LABOR | return_cant bridge + perimeter | QUANTITY_KEY_CONFIRMED | `letter_perimeter_m` | ops formula attach |
| 6 | RETURN_CANT_VINYL_APPLICATION_LABOR | return_cant bridge + perimeter | QUANTITY_KEY_CONFIRMED | `letter_perimeter_m` | basis wrap vs ml confirm |
| 7 | montaj / SITE_INSTALLATION_STANDARD | commercial fixed locatie | FORMULA_CONFIRMED | (fixed / produs) | registry rate if blocked |
| 8 | LARGE_FORMAT_PRINT | finish/print area | QUANTITY_KEY_CONFIRMED | `letter_face_area_m2` | versioned print formula |
| 9 | PACKAGING | commercial PACKAGING_PENDING | MISSING_OWNER_FORMULA | — | packaging commercial rule |
| 10 | PREPRESS | readiness gate ≠ labor qty | OPERATION_ONLY | — | priced PREPRESS qty basis |
| 11 | ELECTRICAL_WIRING | module role only | OPERATION_ONLY | — | per letter/PSU/job |
| 12 | LED_ASSEMBLY | `letter_led_module_count` stable; do **not** bind `led_assembly_time` defaults | QUANTITY_KEY_CONFIRMED | `letter_led_module_count` | productivity if time formula desired |

**Rule:** `led_assembly_time` exists in FORMULA_REGISTRY but uses default throughput — **not** promoted to FORMULA_CONFIRMED.
