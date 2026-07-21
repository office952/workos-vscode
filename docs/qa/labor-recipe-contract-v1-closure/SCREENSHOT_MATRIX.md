# LABOR_RECIPE_CONTRACT_V1_CLOSURE — Screenshot Matrix

Viewport 1440×1100 · FE `http://127.0.0.1:3000` · `BACKEND_PORT=8020`

| # | File | URL / template | Steps | Expected | Verdict |
|---|------|----------------|-------|----------|---------|
| 01 | `01_volum_aluminiu_detail.png` | `/product-system/products/TPL-VOLUM-ALUMINIU_v1` | open | module detail, legacy bucket identity | PASS |
| 02 | `02_volum_aluminiu_pricing_tab.png` | same → Prețuri template | click pricing tab | Studio + module note | PASS |
| 03 | `03_volum_aluminiu_labor.png` | labor section crop | — | 2 recipes; QUANTITY_KEY_CONFIRMED; missing rates | PASS |
| 04 | `04_vl_pricing_overview.png` | VL → Prețuri | click pricing | Studio overview | PASS |
| 05 | `05_vl_labor_section.png` | VL labor crop | — | 12 recipes; status labels; qty keys | PASS |
| 06–09 | VL scroll shots | VL pricing | — | confirmed / qty / unresolved / T·C | PASS |
| 10 | `10_acm_freeze_regression.png` | ACM pricing | — | 5/0 + labor; treatments blocked | PASS |
| 11 | `11_cpp_unchanged.png` | ACM CPP card | — | structural preview | PASS |
| 12 | `12_eic_provenance.png` | ACM EIC card | — | provenance | PASS |
| 13 | `13_full_page_final.png` | full page | — | WorkOS hierarchy | PASS |

## UI opinion

Volum Aluminiu access is clear in ~10s. Formula status labels remove silent blanks. VL qty keys readable; packing/owner gaps stay honest.
