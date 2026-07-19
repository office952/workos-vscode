# Screenshots — Desktop Presentation Reset V1

**Stack:** FE `http://127.0.0.1:3000` · `BACKEND_PORT=8003` · BE `:8003`  
**ACM workspace:** `854fbb73-2329-4ee2-b9a0-21158f8eb1b9` (`IV6-45B6C558`)  
**Simple letters:** `6fcdb7e7-b9b8-4249-9c77-b270a6c34f2f`  
**Fixture ACM:** `litere-cu-fundal-acm-segmentat.svg`  
**Fixture simple:** `litere-vol-1-layer.svg`  
**Viewports:** 1440×1000 · 1100×900  

Before baselines copied from audit pack `docs/qa/intake-v6-desktop-ui-reset-2026-07-19/screenshots/`.  
Capture: `run-presentation-reset-capture.mjs` (+ `_recapture-confirm-diag.mjs` for Confirmare/diagnostic).

| # | Before | After | State | Expected | Actual |
|---|--------|-------|-------|----------|--------|
| 1 | `01_before_finisaje_first_paint.png` | `01_after_finisaje_first_paint.png` | Finisaje first paint | Decisions above fold; compact Produs; no footer-hint banner | PASS — letter anatomy visible; compact rose chip |
| 2 | `02_before_finisaje_cant.png` | `02_after_finisaje_cant.png` | Cant / letter row | Local Cant ownership | PASS — letter row owns finish state |
| 3 | `03_before_iluminare_first_paint.png` | `03_after_iluminare_first_paint.png` | Iluminare | One lighting owner | PASS — specialized section only; no duplicate contract fields |
| 4 | `04_before_iluminare_results.png` | `04_after_iluminare_results.png` | Lighting results | Read-only results | PASS |
| 5 | `05_before_montaj_acm.png` | `05_after_montaj_acm.png` | Montaj ACM | Fundal leads | PASS — Fundal și carcasă first |
| 6 | `06_before_fundal_carcasa.png` | `06_after_fundal_carcasa.png` | Fundal cluster | Physical support clear | PASS |
| 7 | `07_before_segmented.png` | `07_after_segmented.png` | Segmented | Local segmented truth | PASS |
| 8 | `08_before_commercial_inactive.png` | `08_after_commercial_inactive.png` | Commercial inactive | No empty card wall | PASS — collapsed commercial |
| 9 | `09_before_commercial_active.png` | `09_after_commercial_active.png` | Commercial expand | Secondary to Fundal | PASS |
| 10 | `10_before_montaj_avansat.png` | `10_after_montaj_avansat.png` | Avansat | Collapsed/weak | PASS |
| 11 | `11_before_confirmare_blocked.png` | `11_after_confirmare_blocked.png` | Composition gate | Real blocker visible once | PASS — Configurare composition CTA (Confirmare not entered until composition confirmed) |
| 12 | `12_before_confirmare_ready.png` | `12_after_confirmare_ready.png` | Confirmare first paint | Status + checklist visible | PASS — first paint; diagnostics collapsed; no raw codes in handoff |
| 13 | `13_before_pricing_compact.png` | `13_after_pricing_compact.png` | Pricing | Compact secondary | PASS — short composition gate copy |
| 14 | `14_before_diagnostic.png` | `14_after_diagnostic_collapsed.png` | Diagnostic collapsed | No diagnostic content on L1 | PASS |
| 15 | — | `15_after_diagnostic_expanded.png` | Diagnostic expanded | Explicit disclosure | PASS — Product Truth / planner only when open |
| 16 | `16_before_footer.png` | `16_after_footer.png` | Footer | Owns next action | PASS |
| 17 | `17_before_full_1440.png` | `17_after_full_1440.png` | 1440×1000 | Width used | PASS |
| 18 | `18_before_narrow_1100.png` | `18_after_narrow_1100.png` | 1100×900 | Narrow desktop | PASS |
| 19 | — | `19_after_reloaded.png` | Reload | Persistence | PASS |
| 20 | — | `20_after_simple_letters_finisaje.png` | Simple letters | No ACM novel | PASS |

## OWNER DESKTOP ACCEPTANCE VIEW (6)

1. `01_after_finisaje_first_paint.png` — Produs + Finisaje hierarchy  
2. `03_after_iluminare_first_paint.png` — single lighting owner  
3. `05_after_montaj_acm.png` — Fundal-first Montaj  
4. `12_after_confirmare_ready.png` — Confirmare first paint  
5. `13_after_pricing_compact.png` — secondary commercial  
6. `15_after_diagnostic_expanded.png` — technical only behind disclosure  

Routes: `/intake-v6/{workspace_id}/operator` · ACM `854fbb73-2329-4ee2-b9a0-21158f8eb1b9`
