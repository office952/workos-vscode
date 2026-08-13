# SAVE_RECALC_STATE_MODEL

Derived helper: `deriveIntakeV6OfferLifecycleStatus`  
File: `frontend/src/lib/intakeV6/intakeV6OfferLifecycleStatus.ts`

## Signals reused (no new global store)

| Signal | Source |
|---|---|
| `selectorPendingSave` | finish compare vs hydrated |
| `commercialInputsPendingSave` | commercial dirty serialize |
| `saving` | PUT finish-setup in flight |
| `loadingPricedQuote` | priced-quote-dry-run in flight (new explicit flag) |
| `error` | save failure |
| `pricedQuoteError` | dry-run failure |
| `offerRecentlyUpdated` | brief flash after user-driven reprice |

## Phases

| Phase | Label | offerStale |
|---|---|---|
| pending_save | Se salvează… | true |
| saving | Se salvează… | true |
| recalculating | Recalculez oferta… | true |
| updated | Ofertă actualizată | false (ephemeral ~1.8s) |
| save_failed | Salvare eșuată | true |
| reprice_failed | Actualizare ofertă eșuată | true |
| idle | (none) | false |

## Money honesty

Option A: keep prior dry-run amounts when present, mark `data-offer-stale="true"` and dim gross while lifecycle is non-current.  
Never invent FE money. Never show “Ofertă actualizată” on save/reprice failure.