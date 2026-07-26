# Screenshots — Montaj E2E Critical Audit

**Route base:** `http://127.0.0.1:3000/intake-v6/{id}/operator`  
**Workspace:** `3fb7a2b5-ec60-48e4-8b5c-c8649c0c8982` (`IV6-EA145E74`)  
**Fixture:** `litere-cu-fundal-acm-segmentat.svg`  
**Evidence tools:** Playwright; browser MCP navigate (port check).

| Path | State | Expected | Actual | Verdict | Evidence |
|------|-------|----------|--------|---------|----------|
| `01_montaj_acm_first_paint_1440.png` | intended Montaj | Montaj tab | **Finisaje still active** (bad click) | INVALID for Montaj | early capture bug |
| `02_montaj_acm_commercial_region.png` | commercial | — | unreliable tab | INVALID | — |
| `03_montaj_acm_pricing_viewport.png` | pricing | Tarife Accesorii | Tarife lipsă Accesorii visible on Finisaje too | USE for pricing | probe/API |
| `04_confirmare_acm.png` | confirm | Confirmare page | likely still operator | UNRELIABLE | URL stayed operator later |
| `05_diagnostic_closed.png` | diag closed | entry | entry | PASS | — |
| `06_diagnostic_open.png` | diag open | drawer | drawer | PASS | — |
| `07_montaj_acm_after_reload.png` | reload | persist | persist | PASS visual | API match |
| `08_montaj_acm_1920.png` | 1920 | layout | layout | PASS viewport | — |
| `09_montaj_acm_1100.png` | 1100 | narrow | narrow | PASS viewport | — |
| `10_montaj_tab_selected_1440.png` | **Montaj selected** | Fundal/ACM/segmented | Fundal + ACP + segmented + 220V + Tarife Accesorii | **PRIMARY PASS** | `montaj_tab_probe.json` |
| `11_montaj_after_commercial_click.png` | commercial click | — | follow-up | SUPPORT | — |
| `12_pricing_details_lines.png` | details lines | Accesorii row | opened details | SUPPORT | — |
| `13_confirmare_page.png` | confirm attempt | Confirmare | URL remained operator | FAIL navigate | probe conf.url |

## Missing mandatory shots (GAP)

Simple letters; premount activated; prep-only; site-active; cable relevant UI; service corner form; segmented truly confirmed API; Confirmare ready; electrical complete — **not captured** (see matrix).

## Owner view (8)

1. `10_montaj_tab_selected_1440.png` — product vs commercial mix  
2. `03` / pricing — Accesorii Tarife lipsă with scope none  
3. `07` — reload  
4. `06` — diagnostic boundary  
5. `08`/`09` — width  
6. API JSON slice — not a screenshot but truth for PROPOSED vs UI  
7. Aggregate conflicts — runtime JSON  
8. Do not use `01` as Montaj proof
