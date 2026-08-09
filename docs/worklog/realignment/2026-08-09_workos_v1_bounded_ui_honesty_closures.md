# WorkOS — V1 Bounded UI Honesty Closures

**Date:** 2026-08-09  
**Starting HEAD:** `438bb4a1`  
**Owner GO:** `AUTHORIZE_WORKOS_V1_BOUNDED_UI_HONESTY_CLOSURES`  
**Verdict:** PASS

```text
WORKOS_V1_BOUNDED_UI_HONESTY_CLOSURES = PASS
UI_HONESTY_V1 = DONE_FOR_V1
V1_BLOCKING_UI_HONESTY_REMAINING = 0
NEW_UI_FEATURES = 0
DB_SCHEMA_CHANGES = 0
QA_MUTATIONS = 0
WORKOS_V1_COMPLETION_ESTIMATE ≈ 92%
NEXT_RECOMMENDED_BUILD = WORKOS_V1_PRODUCTION_READINESS_SMOKE_PACK
NEXT_TASK = NOT_AUTHORIZED
```

## Routes audited

`/intake` · Intake V6 · `/quotes` · `/orders` · `/execution` · `/execution/:orderId` (Profitability panels) · `/execution/machine-runs` · `/utilaje` · `/dashboard` · `/modules` · `/governance` · nav shell

## Issue matrix (implemented)

| Class | Finding | Fix |
|-------|---------|-----|
| V1_BLOCKING | Quotes list KPI summed mixed currencies | Suppress amount → `—` + honest label |
| V1_BLOCKING | Quote revision hardcodes RON | `formatQuoteMoney` + quote currency |
| V1_BLOCKING | Intake V6 spine hero defaulted RON | Pass `quote_commercial_totals.currency` |
| V1_BLOCKING | Convert panel implied RON order total for EUR V2 | EUR Order Snapshot notice; Settings FX = Profitability stamp only |
| V1_MATERIAL | “Înghețată” before freeze | Gate label on `acceptedSnapshotV2Id` |
| V1_MATERIAL | Unpriced draft “0 RON” copy | Currency-aware placeholder |
| V1_MATERIAL | Orders KPI hardcoded RON with mixed risk | Suppress when base currencies differ |
| V1_MATERIAL | Modules: Profitability NOT_STARTED | DONE_FOR_V1 Policy A + support cards |
| V1_MATERIAL | Capacity framed as “activ” | IMPLEMENTED_INACTIVE on Dashboard/Execution/Utilaje |
| V1_MATERIAL | Closure “Marjă actuală” | Contribuție cunoscută V1 + currency |
| V1_MATERIAL | Legacy nav unmarked | “Acțiune task/Stații (legacy)” |

## Deferred (LATER / polish)

- Golden-pilot Accepted quotes with `0,00` and empty line_items (fixture data)
- PostJobTruth / TechnicalDetails legacy margin wording (secondary surfaces)
- Full Quotes list currency provenance when `line_items` lack currency field
- Mobile / spacing / icon polish

## Runtime proof

Stack `:3000` + `:8000` healthy. Screenshots under `docs/qa/workos-v1-bounded-ui-honesty-closures/screenshots/`.

- Quotes: KPI currency label; legacy nav labels visible  
- Modules: `Profitabilitate` + `Policy A` + `IMPLEMENTED_INACTIVE`; `NOT_STARTED` absent  
- Execution: Capacity Stage 1 · IMPLEMENTED_INACTIVE strip  

## Tests

```text
vitest: quoteCurrency.test.ts · shellNavigation.test.ts · Governance.presentTruth.test.tsx
→ 34 passed
```

## Forbidden scope

No redesign, no FX/Profitability expansion, no Capacity activation, no push.
