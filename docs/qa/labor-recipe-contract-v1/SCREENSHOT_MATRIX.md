# LABOR_RECIPE_CONTRACT_V1 — Screenshot Matrix

Viewport: 1440×1100. FE: `http://127.0.0.1:3000` with `BACKEND_PORT=8020`.

| # | File | URL / template | Steps | Expected | Verdict |
|---|------|----------------|-------|----------|---------|
| 01 | `01_product_system_overview.png` | `/product-system/products` | open | Product System catalog | PASS |
| 02 | `02_acm_detail.png` | ACM detail | open | ACM product detail | PASS |
| 03 | `03_acm_pricing_labor.png` | ACM → Prețuri template | click tab `pricing` | Studio + labor section | PASS |
| 04 | `04_acm_labor_section.png` | ACM labor section crop | — | 3 recipes; 2 missing; 1 rate-basis warning; T/C split | PASS |
| 05 | `05_vl_pricing_labor.png` | VL → Prețuri template | click pricing | Studio + labor | PASS |
| 06 | `06_vl_labor_section.png` | VL labor crop | — | 12 recipes; registry-linked formulas empty; warnings visible | PASS |
| 07 | `07_volum_aluminiu_detail_no_pricing_tab.png` | Volum Aluminiu detail | open | **No Prețuri tab** (component-first bucket) | PASS_WITH_WARNINGS — API has 2 labor recipes |
| 08 | `08_logo_labor.png` | Logo → Prețuri template | click pricing | 3 labor refs via commercial lines | PASS |
| 09 | `09_acm_cost_vs_commercial.png` | ACM pricing scroll | — | Cost intern ≠ tarif comercial labels | PASS |
| 10 | `10_technical_vs_commercial_readiness.png` | ACM pricing | — | `T:da · C:nu` on rows | PASS |
| 11 | `11_missing_rate_blocker.png` | ACM pricing | — | Tarif lipsă chips | PASS |
| 12 | `12_rate_basis_warning.png` | ACM pricing | — | Atenție + DQ message | PASS |
| 13 | `13_cpp_preview_unchanged.png` | ACM CPP card | — | Structural preview only | PASS |
| 14 | `14_eic_provenance.png` | ACM EIC card | — | Provenance unchanged | PASS |
| 15 | `15_full_page_workos.png` | last open page | — | WorkOS shell context | PASS |

## Sincere UI opinion

Operator understands ownership in ~10 seconds on ACM/VL. Cost vs commercial and T/C chips are clear. VL formulas mostly empty (registry-linked) — honest, not fake authority. Volum Aluminiu UI gap is the main visibility warning.
