# WorkOS V1 Commercial Offer Currency and Rate Closure — REPORT

```text
WORKOS_V1_COMMERCIAL_OFFER_CURRENCY_AND_RATE_CLOSURE = PASS
BASELINE_HEAD = d3dc93fc
V1_PRODUCT = LETTERS
OFFER_CURRENCY = EUR
FX_AUTHORITY = NOT_REQUIRED
CURRENCY_RULE = native offer currency (EUR|RON); no live FX at convert; mix fail-closed
HISTORICAL_REVENUE_STABILITY = PROVEN
PROFITABILITY_REVENUE_SOURCE = order_snapshot_v2.accepted_commercial_total
PROFITABILITY_REVENUE_READINESS = READY
ACTUAL_COST_TO_QUOTE_BACKFLOW = 0
DB_SCHEMA_CHANGES = 0
QA_MUTATIONS = 0
ROADMAP_COMMERCIAL_DOMAIN = DONE_FOR_V1
NEXT_RECOMMENDED_BUILD = WORKOS_V1_PRODUCTION_SECURITY_WRITE_GATE_CLOSURE
NO_PUSH = YES
```

## Currency / rate summary

| Item | Status |
|------|--------|
| Letters presentation | EUR (`VOLUMETRIC_PRESENTATION_CURRENCY`) |
| Order convert | EUR or RON (native); USD+ blocked |
| FX | NOT_REQUIRED (no invent) |
| Mix | fail-closed `COMMERCIAL_CURRENCY_MIX_UNRESOLVED` |
| F7I.1 provisional | ALLOWED_FOR_V1 |
| Oracal 641 | 6.5 EUR/m² Owner-confirmed in registry UI |
| Oracal 651 / 8500 / print+laminate | F7F Owner law |
| printed_vinyl | fail-closed LATER |
| Adjustments | base → markup → manual → discount → VAT |

## Historical stability

- Snapshot freeze ignores live registry change (existing F7H proof)
- Order convert copies frozen CPP + envelope; `no_reprice_policy=True`
- EUR convert proven in `test_eur_currency_converts_natively_no_fx`

## Regression

```text
pytest convert + dry_run + F7H + F7I.1 + profitability RM → green
```

## Browser

- `screenshots/01_pricing_registry_eur_letters.png` — Monedă bază EUR; Letters coverage; Oracal 641 confirmed
- `screenshots/02_quotes_list.png` — Quotes list still aggregates as RON (historical mixed) — NON_BLOCKING UI polish later

## Residual LATER

- Quotes list aggregate currency honesty
- printed_vinyl
- ACM/Logo commercial expansion
