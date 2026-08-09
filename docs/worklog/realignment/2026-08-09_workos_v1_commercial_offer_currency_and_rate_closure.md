# 2026-08-09 — WorkOS V1 Commercial Offer Currency and Rate Closure

## Owner GO

```text
AUTHORIZE_WORKOS_V1_COMMERCIAL_OFFER_CURRENCY_AND_RATE_CLOSURE
```

## Baseline

```text
HEAD = d3dc93fc
V1_PRODUCT = LETTERS / TPL-VOLUMETRIC-LETTERS_v2
```

## Decisions applied (no invent FX / no invent rates)

| Topic | Classification | Resolution |
|-------|----------------|------------|
| Currency law | CANONICAL_DEFAULT + AI_DECISION_ALLOWED | Native EUR ops (F7H presentation); Order convert accepts EUR\|RON; no FX |
| F7I.1 provisional | OWNER_CONFIRMED | PROVISIONAL_ALLOWED_FOR_V1 |
| Oracal 641 | Registry Owner confirmed 6.5 EUR/m² | V1_READY |
| printed_vinyl | Fail-closed | LATER / MISSING not forced into V1 |
| Currency mix | CANONICAL_DEFAULT | COMMERCIAL_CURRENCY_MIX_UNRESOLVED fail-closed |

## Code changes

- Order Snapshot V2 convert: allow EUR and RON (no FX)
- Freeze commercial envelope: net / VAT / gross / vat% / adjustment trace
- Dry-run/write: stamp currency + vat_percent on adjustment trace
- Snapshot commercial payload: stop hardcoding RON
- Profitability actual RM: surface net/VAT/gross when frozen

## Verdict

```text
WORKOS_V1_COMMERCIAL_OFFER_CURRENCY_AND_RATE_CLOSURE = PASS
OFFER_CURRENCY = EUR (Letters presentation)
FX_AUTHORITY = NOT_REQUIRED
HISTORICAL_REVENUE_STABILITY = PROVEN
PROFITABILITY_REVENUE_READINESS = READY
ROADMAP_COMMERCIAL_DOMAIN = DONE_FOR_V1
NEXT_RECOMMENDED_BUILD =
  WORKOS_V1_PRODUCTION_SECURITY_WRITE_GATE_CLOSURE
NEXT_TASK = NOT_AUTHORIZED
```
