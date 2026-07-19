# Runtime Scenario Matrix

**Runtime:** FE `http://127.0.0.1:3000` · BE `http://127.0.0.1:8003`  
**Primary fixture workspace:** `3fb7a2b5-ec60-48e4-8b5c-c8649c0c8982` / `IV6-EA145E74`  
**Fixture file:** `litere-cu-fundal-acm-segmentat.svg`  
**Plugins used:** Playwright + HTTP API (+ browser MCP navigate). Sentry/Datadog: N/A.

| # | Scenario | Workspace | Page2 / Montaj state | Persisted payload (key facts) | Pricing | Blockers / Aggregate | Confirmare | PD | Aggregate | Task preview | Screenshot | Coverage |
|---|----------|-----------|----------------------|-------------------------------|---------|----------------------|------------|----|-----------|--------------|------------|----------|
| 1 | Simple letters, no support | not freshly seeded this audit | — | — | — | — | — | — | — | — | — | **GAP** — code-path inferred only |
| 2 | Letters + ACM single panel | ACM WS (dims single panel geom) | Fundal ACP form visible | ACM solution present; svg_support confirmed | commercial lines without Accesorii in dry-run JSON; UI Tarife lipsă Accesorii | graph `MOUNTING_SCOPE_INACTIVE` | Continuă stayed on operator in capture | frozen ACM + scope none | COMPOSITION_GRAPH_BLOCKED + SERVICE_CORNER_REQUIRED | catalog ops active | `10_montaj_tab_selected_1440.png` | **PARTIAL** |
| 3 | Letters + ACM segmented | same | UI shows multi-panel + 220V editors | API `segmented_background.status=PROPOSED` | segmented unpriced | FE warning path for PROPOSED | — | proposal zero-effects marker | segmented false in aggregate summary | no segmented tasks | same + probe | **COVERED with contradiction** |
| 4 | Metal premount | UI option visible | selector lists metal | not activated on this WS | — | — | — | module warning TRIGGER_FIELD_MISMATCH | — | — | snippet in probe | **UI-only** |
| 5 | ACM + commercial none | same | scope=`none` | template_enabled=true nonetheless | sablon gated off by prep inactive | MOUNTING_SCOPE_INACTIVE | — | composition blocked | blocked | — | API slice | **COVERED** |
| 6 | ACM + prep only | — | — | — | — | — | — | — | — | — | — | **GAP** |
| 7 | ACM + site installation | — | — | — | — | — | — | — | — | — | — | **GAP** |
| 8 | Cable relevant | cable null; illuminated true | cable not in Montaj first paint | null | no cable line observed | — | — | mains_cable false in PD keys | — | — | probe hasCable false | **PARTIAL** |
| 9 | Cable irrelevant | same | hidden | null | — | — | — | — | — | — | — | **PARTIAL** |
| 10 | Service corner relevant | Aggregate requires corner for alucobond | UI: „Colțul service unic nu se mai configurează aici” under segmented UI | corner null | — | `PROCESS_RESOLVER_SERVICE_CORNER_REQUIRED` | — | service_corner key possible | error conflict | — | probe + Aggregate JSON | **COVERED conflict** |
| 11 | Service corner irrelevant | when no ACM | — | — | — | — | — | — | — | — | — | **GAP** |
| 12 | Segmentation proposed | API PROPOSED | UI also shows “a fost confirmat” text | PROPOSED | unpriced | warning intended | — | proposal marker | no segmented effects | informational | probe snippets | **CONTRADICTION** |
| 13 | Segmentation confirmed | claimed in UI | electrical editors shown | API still PROPOSED | — | — | — | — | — | — | — | **NOT PROVEN ready** |
| 14 | Letter crossing joint | — | — | — | — | FE blocker codes exist | — | — | — | — | — | **CODE-ONLY** |
| 15 | Cutout/inlay crossing | — | — | — | — | FE/BE 422 path | — | — | — | — | — | **CODE-ONLY** |
| 16 | Electrical incomplete | panels show UNCONFIRMED options | editors visible | nested under PROPOSED | none | warning path | — | — | — | — | probe | **PARTIAL** |
| 17 | Electrical complete | — | — | — | — | — | — | — | — | — | — | **GAP** |
| 18 | Montaj incomplete | attention `! 2 probleme` | Finisaje issues also | — | Tarife lipsă Accesorii | Aggregate conflicts | — | blocked graph | errors | — | screenshots | **COVERED** |
| 19 | Montaj complete | — | — | — | — | — | — | — | — | — | — | **GAP — no ready proof** |
| 20 | Save/reload | reload after Montaj | same Fundal/ACM | API unchanged keys | same Tarife banner | same | — | — | — | — | `07_montaj_acm_after_reload.png` | **PASS reload visual** |
| 21 | Confirmare blocked | Continuă did not leave operator; confirm shot may be operator | checklist pending expected | composition confirmed earlier | — | footer 1 blocant | **not genuinely ready** | — | — | — | `04`/`13` | **PARTIAL** |
| 22 | Confirmare ready | — | — | — | — | — | — | — | — | — | — | **GAP — not claimed** |

## Runtime errors

No Sentry/Datadog. Browser console not exhaustively harvested. API PD/Aggregate returned 200 with explicit conflict codes.
