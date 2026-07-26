# Screenshots — Intake V6 vocabulary residual UI cleanup (2026-07-19)

**Stack:** FE `http://127.0.0.1:3001` (proxy) · BE `http://127.0.0.1:8003` · Compat PASS  
**SVG:** `litere-cu-fundal-acm-segmentat.svg` (Desktop fixtures)  
**Capture:** `frontend/e2e/intake-v6-vocab-cleanup-screenshots.spec.ts` (+ Figma MCP for #14)

| # | File | Tab/section | Expected state | Visual opinion |
|---|------|-------------|----------------|----------------|
| 1 | `01_page2_tab_labels.png` | Configurare tabs | Finisaje · Iluminare și surse · Montaj | Clear three-tab IA; composition still competes above tabs |
| 2 | `02_iluminare_si_surse.png` | Iluminare | LED + surse labeling | Tab rename reads correctly |
| 3 | `03_fundal_si_carcasa.png` | Montaj / Fundal | Cluster primary | Hierarchy readable |
| 4 | `04_montaj_comercial_collapsed.png` | Montaj comercial | Collapsed accordion | Good demotion when not needed |
| 5 | `05_montaj_comercial_expanded.png` | Montaj comercial | Site section inside accordion | PASS — no orphan site block |
| 6 | `06_avansat_collapsed.png` | Avansat | Collapsed | Optional technical path clear |
| 7 | `07_avansat_diagnostics_raw.png` | Avansat expanded | Ownership notes allowed | Raw diagnostics stay optional |
| 8 | `08_owner_decision_primary.png` | Montaj primary | RO labels; no OWNER_GATE | No screaming enums in primary |
| 9 | `09_sticky_blocker_summary.png` | Sticky banner | Actionable blockers | Distinct from warnings |
| 10 | `10_segmented_confirmed_or_proposal.png` | Fundal segmented | Proposal/confirm path | Depends on fixture timing |
| 11 | `11_electrical_panel.png` | Electrical | RO supply labels when present | Unit/E2E covered separately |
| 12 | `12_final_confirmation_footer.png` | Footer | Continuă / Confirmare | Unchanged behavior |
| 13 | `13_full_montaj_page.png` | Full Montaj | Commercial + Fundal + Avansat | Coherent vertical order |
| 14 | `14_figma_montaj_runtime_sync.png` | Figma frame `74:3` | IA mirror | Structural only — runtime is truth |

## Figma

- File key: `0CDPIuqoaZ1OQgNnvNyl1F`
- Frame: `Intake V6 — Page 2 Montaj (runtime sync 2026-07-19)`
- URL: https://www.figma.com/design/0CDPIuqoaZ1OQgNnvNyl1F?node-id=74-3
