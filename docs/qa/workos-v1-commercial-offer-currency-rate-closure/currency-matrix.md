# COMMERCIAL_CURRENCY_MATRIX — Letters V1

| Layer | Currency | Conversion | Snapshot |
|-------|----------|------------|----------|
| Catalog VL sell rules | EUR | none | embedded in CPP |
| Presentation | EUR | none | CPP breakdown |
| Adjustments/VAT totals | stamps presentation | none | Quote + Order envelope |
| Order convert | EUR or RON only | **forbidden** live FX | `accepted_currency` frozen |
| EIC diagnostic | EUR internal × Settings FX | diagnostic only | not commercial total |
| Mix across lines | blocked | — | `COMMERCIAL_CURRENCY_MIX_UNRESOLVED` |

```text
FX_AUTHORITY = NOT_REQUIRED
CURRENCY_RULE = native offer currency; no invent FX
```
