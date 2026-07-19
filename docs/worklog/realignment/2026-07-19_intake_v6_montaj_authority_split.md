# Worklog — Intake V6 Montaj Authority Split

**Date:** 2026-07-19  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Audit baseline:** `392d6e1`  
**Visual candidate:** `5336734`  
**Commit:** (see git after isolated commit)

## Owner decisions D1–D5

| ID | Applied |
|----|---------|
| D1 | Fundal/ACM/segmentation = product truth; composition includes ACM at scope none |
| D2 | ACM + `mounting_scope=none` valid; no `MOUNTING_SCOPE_INACTIVE` |
| D3 | Single-panel → legacy corner; confirmed multi-panel segmented owns electrical (skip legacy corner even if ECM DRAFT) |
| D4 | Accesorii 5% = manufacturing consumable; operator label renamed; not Montaj field blocker; formula unchanged |
| D5 | Template inactive under scope none; legacy `true` retained, no delete; process adapter `template_selected=false` |

## Pre-flight

- Checkpoint: `docs/qa/intake-v6-montaj-authority-split-2026-07-19/AUTHORITY_SPLIT_CHECKPOINT.md`
- No DB migration required
- Foreign WIP present — not staged

## Authority before → after

| Concern | Before | After |
|---------|--------|-------|
| ACM + scope none | PD/Agg `MOUNTING_SCOPE_INACTIVE` | Composition confirmed; ACM node included |
| Template + scope none | Priced / process-active risk | Retained inactive; UI notice; adapter inactive |
| Service corner | Always required for alucobond_cased | Skipped when segmented multi-panel CONFIRMED |
| Accesorii | “Accesorii montaj” language | “Consumabile producție — accesorii / conectori” |
| Segmented confirm | Coalesce could overwrite CONFIRMED→PROPOSED | CONFIRMED protected unless `force_repropose` |

## Blockers before → after (ACM WS `3fb7a2b5-…`)

| Blocker | Before (ghost :8003 / audit) | After (proof :8013 / FE proxy) |
|---------|------------------------------|--------------------------------|
| `MOUNTING_SCOPE_INACTIVE` | present | **absent** |
| `COMPOSITION_GRAPH_BLOCKED` | present | **absent** |
| `PROCESS_RESOLVER_SERVICE_CORNER_REQUIRED` | present | **absent** (segmented CONFIRMED owns corner) |

## Persistence / PD / Aggregate / Confirmare / UI

- Persist keys unchanged; interpretation corrected
- PD: ACM child included; solution_status `confirmed`
- Aggregate: no composition/corner conflicts on ACM WS
- Confirmare: no `MOUNTING_SCOPE_INACTIVE` in UI text
- Montaj UI authorities: `product-support`, `commercial-mounting`, `electrical-service`, advanced disclosure

## Compatibility

- Preferred policy: **retained but inactive** for legacy `mounting_template_enabled=true` under scope none
- No key rename / no destructive cleanup

## Runtime note (critical)

Windows **ghost listeners** on `:8003` continued serving stale code after process kill. Acceptance API proof used **`:8013`** with FE `BACKEND_PORT=8013`. Direct `:8003` remained stale until OS clears ghosts.

## Tests

- `backend/tests/test_montaj_authority_split_v1.py` — 31 passed (with composition suite)
- FE Vitest: LiveCalculationSummary, quote handoff readiness, montajServiceCornerPrecedence — passed

## Screenshots

`docs/qa/intake-v6-montaj-authority-split-2026-07-19/screenshots/` + `runtime/api_truth.json`

## Remaining risks

1. Ghost `:8003` can fool local acceptance if FE proxies to it  
2. ECM still DRAFT on ACM WS — electrical completeness separate from legacy corner  
3. Confirmare may still show other product blockers (e.g. Vector Logo) unrelated to commercial mounting  
4. Mutation scenarios 4/7/10 in matrix documented via unit tests + notes; not all live-mutated on this WS  

## Files (this build)

See final report §25.
