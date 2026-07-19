# Screenshots — Intake V6 Page 1 & composition clarity

**Date:** 2026-07-19  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Baseline:** `bfddb1e`  
**Runtime:** FE `http://127.0.0.1:3001` · BE `http://127.0.0.1:8003`  
**SVG:** `litere-cu-fundal-acm-segmentat.svg` (Desktop fixtures)  
**Figma:** `0CDPIuqoaZ1OQgNnvNyl1F` node `82:2` (page `16 — Configurare UI/UX Polish`)

| # | File | Section | Expected | Visual note |
|---|------|---------|----------|-------------|
| 1 | `01_page1_initial_analysis.png` | Page 1 after upload | Element N labels; handoff pending; Continue disabled | PASS — no `pseudo fill-*` |
| 2 | `02_detected_elements_legend.png` | Inspect legend | Operator titles Element N | PASS |
| 3 | `03_proposed_role_cards.png` | Role cards | Propunere visible; not confirmed style | PASS |
| 4 | `04_confirmed_role.png` | After confirm-all | Confirmed / ready handoff | PASS |
| 5 | `05_unresolved_or_attention.png` | Pending state | Actionable pending count | PASS |
| 6 | `06_technical_diagnostics_collapsed.png` | Technical details | Collapsed disclosure | when present |
| 7 | `07_technical_diagnostics_expanded.png` | Technical details | Raw keys under details | when present |
| 8 | `08_composition_on_page1.png` | Composition (Page 1) | Concise components | PASS |
| 9 | `09_page1_ready_summary.png` | Handoff ready | Pagina 2 configuration message | PASS |
| 10 | `10_page1_blocked_or_pending_summary.png` | Handoff pending | Pending count message | PASS |
| 11 | `11_page2_composition_summary.png` | Page 2 composition | Status + confirm CTA; no SURFACE_FINISH dump | PASS |
| 12 | `12_page2_sticky_blocker.png` | Sticky blocker | Concise composition issue | PASS |
| 13 | `13_segmented_handoff_montaj.png` | Montaj tab | Fundal / comercial / Avansat present | PASS — IA frozen |
| 14 | `14_reloaded_state.png` | After reload | Review + Montaj cluster | PASS |
| 15 | `15_full_page1.png` | Full Page 1 | Operator structure | PASS |
| 16 | `16_figma_structural_checkpoint.png` | Figma | A–F structural map | Structural only |

## Honest visual opinion

Page 1 now reads as decisions, not parser dumps. Composition on Page 2 is still prominent when unconfirmed (correct), but PD/binding prose is demoted. Residual noise: FinishSetup ACP save warning chip and sticky calc still compete for attention — out of Montaj scope; next build can tighten composition placement vs sticky calc if needed.
