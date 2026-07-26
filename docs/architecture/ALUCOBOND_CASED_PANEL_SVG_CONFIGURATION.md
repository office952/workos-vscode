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

## Material desfășurat preview (technical, read-only)

Owner / UI / atelier term: **material desfășurat**.  
Repo / code alias: `blank_*` (nu folosi „blank” în UI atelier).

Owner terms → repo:

| Owner (atelier / UI) | Repo |
|----------------------|------|
| Față (cotă exterioară) | `W` / `H` (`width_mm` / `height_mm`) |
| Pliu / întoarcere 1 | `L1` / `l1_mm` (= `return_depth_mm`, adâncime casetă) |
| Pliu / întoarcere 2 | `L2` / `l2_mm` (= `rear_lip_mm`, doar `fold_count=2`) |
| Nr. pliuri | `fold_count` ∈ {1,2} |
| **Material desfășurat** | `blank_width_mm` / `blank_height_mm` |
| Marjă fixare CNC | `cnc_fixing_margin_mm` = **10** (OWNER_CONFIRMED 2026-07-23) |

```text
fold_sum = L1                    (fold_count = 1)
fold_sum = L1 + L2               (fold_count = 2)
BW = W + 2 × fold_sum + 10
BH = H + 2 × fold_sum + 10
```

Same as: față + (L1×2) + (L2×2 dacă există) + 1 cm marjă fixare CNC.

No DXF / CUT/FOLD / CPP in this build.

## CNC sketches + DXF (owner)

V-groove / Decupare taxonomy + geometry diagrams:

- [`CNC_PROCESS_TAXONOMY_RO.md`](./CNC_PROCESS_TAXONOMY_RO.md)
- [`ACM_ARTCAM_DXF_OWNER_GOLDEN.md`](./ACM_ARTCAM_DXF_OWNER_GOLDEN.md) — ArtCAM: negru Cut outside · roșu V-groove along line
- [`../worklog/realignment/audit_assets/24_acm_vgroove_fold_geometry.png`](../worklog/realignment/audit_assets/24_acm_vgroove_fold_geometry.png)
- DXF: [`30_acm_un_pliu_200x30_owner.dxf`](../worklog/realignment/audit_assets/30_acm_un_pliu_200x30_owner.dxf) · [`30_acm_2_pliuri_100x30_owner.dxf`](../worklog/realignment/audit_assets/30_acm_2_pliuri_100x30_owner.dxf)

## Unit guard

If SVG root uses `cm` and implied physical width is absurd (>8 m), candidate metrics use viewBox-as-mm correction and set `unit_ambiguity=true`.
