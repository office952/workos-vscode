# PERFORMANCE_REQUEST_TRACE

HEAD: `303add0f` · No Owner DB mutations · Timing from live API + code fan-out map

## Operator-visible latency model (Step 2 finish change)

```text
click selector
→ local React (<16–50 ms typical)
→ autosave debounce 700–1400 ms (finish) / 700 ms (commercial)
→ PUT finish-setup
→ bumpPreviewRefresh fan-out (up to 8–9 GET groups)
→ UI total updates when priced-quote-dry-run returns
```

**Estimated operator-visible floor after one finish change:**  
`debounce (700–1400) + PUT + max(GET chain)` ≈ **1.0–2.0+ s** even when CPP itself is ~40–50 ms.

## Measured endpoint times (Owner workspace, sequential)

| Endpoint | ms |
|----------|-----|
| priced-quote-dry-run | **307** |
| logical-list-read-model | **322** |
| material-breakdown | 20 |
| pricing-input-preview | 10 |
| quote-handoff-preview | 31 |
| product-system-binding | 14 |
| task-preview | 11 |
| production-task-dry-run | 33 |
| production-handoff-preview | 41 |

Serial sum of typical eager set ≈ **~790 ms** (plus browser parallelization variance).

## CPP-only OFAT (no workspace write)

Face/cant/back preview POSTs: **36–50 ms** each. Backend pricing compute is not the dominant lag.

## Fan-out after finish dirty (`intakeV6ReviewRefetchDomains.ts`)

`face_finish` / `backing` / `lighting` refresh:

- breakdown, pricing, pricedQuote, productionDryRun, productionHandoff, quoteHandoff, taskPreview, orderBoundReadiness

**Production/diagnostic groups refresh while operator only changes a finish selector.**

## Duplicate / unnecessary patterns

| Pattern | Evidence |
|---------|----------|
| Eager production GETs on Step 2 | task-preview, production-task-dry-run, production-handoff, task-generation, order-bound, AI assist |
| Logical list cost | 322 ms — heavy relative to breakdown 20 ms |
| Commercial spine second dry-run | when diagnostic drawer opens with quoteId |
| Stale-clear on Confirm refetch | null dry-run until GET returns (flash) |
| N+1 serial feel | debounce then multi-GET waterfall |

## Representative actions (no Owner mutation — inferred + API)

| Action | Local | Writes | Refetch groups | Dry-run | Expected visible latency |
|--------|-------|--------|----------------|---------|--------------------------|
| Face none→641 | instant | 1 PUT after debounce | 8 groups | ~300 ms | **WORKS_BUT_SLOW**; money may still be wrong (token drift) |
| 641→651 | instant | 1 PUT | 8 | ~300 ms | same |
| Cant stock→Oracal | instant | 1 PUT | 8 | ~300 ms | money should move if token preserved |
| Oracal→RAL | instant | 1 PUT | 8 | ~300 ms | money should move |
| Back no→with bevel | instant | 1 PUT | 8 | ~300 ms | **NO_EFFECT** on commercial_totals |

## Recommended V1 targets (feasibility)

| Metric | Target | Warning | Current estimate |
|--------|--------|---------|------------------|
| Selector visual response | <100 ms | — | OK (local) |
| Save acknowledgement | <500 ms | >800 ms | Debounce alone often >700 ms |
| Official live-price refresh | <1.0 s | >1.5 s | Often **>1.5 s** with full fan-out |
