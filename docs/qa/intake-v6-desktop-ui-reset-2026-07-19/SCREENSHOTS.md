# Screenshots — Desktop UI Reset Audit 2026-07-19

Stack: FE `http://127.0.0.1:3000` · `BACKEND_PORT=8003` · BE `:8003`  
Workspace: `29472e22-5fe1-4e8d-af66-f9ab75d5fe32`  
Fixture: `litere-cu-fundal-acm-segmentat.svg`  
Viewport primary: 1440×1000 · narrow: 1100×900

| File | Surface | Annotations / findings visible |
|------|---------|--------------------------------|
| `01_page1_straturi_full.png` | Page 1 | Preview, roles, composition, rail |
| `01b_page1_after_support_role.png` | Page 1 ACM | Support role path |
| `02_finisaje_top.png` | Finisaje top | Produs nesting, rose banner, pricing, footer duplication |
| `03_finisaje_letter_expanded.png` | Letter group | Anatomy controls / nesting |
| `04_iluminare_top.png` | Iluminare | Dual top fields + specialized section; empty space |
| `04b_iluminare_section.png` | Lighting section | Decisions vs results split |
| `05_iluminare_calculated_results.png` | Results | L3 band |
| `06_montaj_top.png` | Montaj top | Banner + tabs + start of montaj |
| `06b_montaj_panel.png` | Montaj panel | Orphaned șablon fields, Fundal nesting, Product System badge, hashes |
| `07_montaj_commercial.png` | Commercial | Nested inactive cards, empty site box |
| `08_fundal_carcasa.png` | Fundal | Cluster shell |
| `09_support_structure.png` | Support/ACP | Solution panel |
| `10_montaj_avansat.png` | Avansat | Advanced disclosure |
| `11_warnings_near_bottom.png` | Bottom | Footer stress stack |
| `12_montaj_full_scroll.png` | Montaj full | Scroll length |
| `13_pricing_rail.png` | Pricing | Secondary rail + missing rates |
| `14_footer.png` | Footer | Next-step + inventory |
| `15_confirmare.png` | Confirmare | Collapsed primary content risk (expand shot not retained; defect confirmed in code + first paint) |
| `16_drawer_footer_issues.png` | Drawer | Duplicate inventory |
| `17_narrow_desktop.png` | Narrow desktop | Width pressure |

Capture scripts: `run-desktop-ui-reset-capture.mjs` + runtime JSON under `runtime/`.
