# Screenshots — Letter Pilot Completion 2026-07-19

Stack: FE `http://127.0.0.1:3000` · proxy `BACKEND_PORT=8003` · BE `http://127.0.0.1:8003`  
Fixtures: `litere-cu-fundal-acm-segmentat.svg` (ACM), `litere-vol-1-layer.svg` (simple letters)  
Before baselines: copied from `docs/qa/workos-configurator-letter-pilot-2026-07-19/screenshots/` (pre-quieting letter pilot).

| # | File | URL / workspace | Fixture | State | Expected | Actual |
|---|------|-----------------|---------|-------|----------|--------|
| 1 | `01_before_finisaje_full.png` | prior letter pilot pack | letters | before quieting | ERP-dense Page 2 | baseline copy |
| 2 | `02_before_composition_scope.png` | prior letter pilot pack | letters | before | composition/scope dense | baseline copy |
| 3 | `03_before_pricing_rail.png` | prior letter pilot pack | letters | before | pricing dominant | baseline copy |
| 4 | `04_before_iluminare.png` | prior letter pilot pack | letters | before lighting | lighting before hierarchy | baseline copy |
| 5 | `05_before_narrow_note.png` | prior letter pilot pack | letters | before | note — same source as full before | baseline copy |
| 6 | `06_finisaje_full.png` | `/intake-v6/{acm}/operator` review | ACM | Finisaje, unconfirmed | product-first + quiet rail | PASS |
| 7 | `07_product_first_hierarchy.png` | `/intake-v6/{simple}/operator` review | simple letters | Finisaje | product → decisions → commercial | PASS |
| 8 | `08_composition_compact.png` | ACM review | ACM | compact Produs | identity + CTA; no authority L1 | PASS (`technicalAuthorityOnL1=false`) |
| 9 | `09_composition_disclosure.png` | ACM review | ACM | technical open | registry/authority in disclosure | PASS |
| 10 | `10_scope_blocker_state.png` | ACM review | ACM | scope strip | compact scope strip | PASS |
| 10b | `10b_blocker_banner_area.png` | ACM review | ACM | blockers visible | red attention banner kept | PASS |
| 11 | `11_pricing_compact.png` | ACM review | ACM | rail compact | Rezultat comercial secondary | PASS `data-pricing-weight=secondary` |
| 12 | `12_pricing_expanded.png` | ACM review | ACM | commercial adjustments open | details on request | PASS |
| 13 | `13_iluminare_results.png` | ACM review | ACM | Iluminare tab | decisions + results | PASS |
| 14 | `14_footer_sticky.png` | ACM review | ACM | footer clip | next action in footer | PASS |
| 15 | `15_narrow_viewport.png` | ACM review | ACM | 390×844 | essentials remain | PASS |
| 16 | `16_reloaded.png` | ACM review after reload | ACM | reload | hierarchy preserved | PASS |
| 17 | `17_confirmare_regression.png` | ACM confirm attempt | ACM | incomplete | honest gate / no false unlock | PASS (still blocked) |
| 18 | `18_montaj_regression.png` | ACM Montaj tab | ACM | Montaj | no Montaj IA change | PASS (tab only) |

Runtime probe: `runtime/pilot_completion_summary.json`.
