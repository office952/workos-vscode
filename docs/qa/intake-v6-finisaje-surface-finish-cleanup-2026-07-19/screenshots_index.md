# Screenshots — Finisaje SURFACE_FINISH ownership cleanup

**Date:** 2026-07-19  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Baseline:** `51ea07a`  
**Runtime:** FE `http://127.0.0.1:3001` · BE `http://127.0.0.1:8003`  
**SVG:** `litere-cu-fundal-acm-segmentat.svg`  
**Route:** `/intake-v6/:id/operator` → Configurare → Finisaje

| # | File | Expected | Note |
|---|------|----------|------|
| 1 | `01_finisaje_initial.png` | Finisaje tab; controls first | PASS |
| 2 | `02_active_finish_controls.png` | Față/Cant/Spate section visible | PASS |
| 3 | `03_incomplete_or_controls_visible.png` | Incomplete actionable without raw ownership | PASS |
| 4 | _(owner-decision)_ | N/A — ownership accordion has no owner action | Honest gap |
| 5 | `05_confirmed_or_configured_finish.png` | Controls + technical expanded | PASS |
| 6 | `06_technical_details_collapsed.png` | No `SURFACE_FINISH` in primary | PASS |
| 7 | `07_technical_details_expanded.png` | Raw tokens only under technical line | PASS |
| 8 | `08_no_raw_token_primary.png` | Collapsed primary clean | PASS |
| 9 | `09_reloaded_state.png` | Technical stays collapsed | PASS |
| 10 | `10_full_finisaje_tab.png` | Full tab | PASS |
| 11 | `11_page2_tab_structure.png` | 3 tabs unchanged | PASS |
| 12 | `12_montaj_regression_check.png` | Fundal / comercial / Avansat | PASS |

## Honest visual opinion

Hierarchy improved: finish controls lead; technical ownership sits below and collapsed. Density of Page 2 chrome (composition + scope + sticky blocker + live calc) still high, but the Finisaje ownership leak is gone from the primary scan. The accordion remains useful as a single diagnostic pocket; it no longer competes with Față/Cant decisions.
