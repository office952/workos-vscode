# Alucobond cased panel — SVG configuration (V1)

| Field | Value |
|-------|-------|
| Owner role label | Panou Alucobond casetat |
| Process support_type | `alucobond_cased` |
| Product System component | `ALUCOBOND_CASED_PANEL` (later compilation) |
| Mounting template | `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` |

## Typed storage

`finish_setup.svg_support_selection` (`svg_support_selection_v1`) plus `mounting_solution.configuration` mapped:

| Owner-facing | Technical | Existing ACM field |
|--------------|-----------|--------------------|
| Prima întoarcere / adâncime casetă | `l1_mm` = `finished_depth_mm` | `return_depth_mm` |
| A doua întoarcere | `l2_mm` (fold_count=2) | `rear_lip_mm` |
| Număr întoarceri | `fold_count` ∈ {1,2} | `fold_count` |
| Colț de service | `service_corner` | `power_supply_service_corner` |
| Cadru interior | `internal_frame_enabled` | `frame_clearance_mm` > 0 when active |
| Element SVG | `svg_support_element_id` / `contour_id` | configuration passthrough |

## Blank preview (technical, read-only)

```text
fold_sum = L1 (+ L2 if 2 folds)
BW = W + 2 × fold_sum
BH = H + 2 × fold_sum
```

No DXF / CUT/FOLD / CPP in this build.

## Unit guard

If SVG root uses `cm` and implied physical width is absurd (>8 m), candidate metrics use viewBox-as-mm correction and set `unit_ambiguity=true`.
