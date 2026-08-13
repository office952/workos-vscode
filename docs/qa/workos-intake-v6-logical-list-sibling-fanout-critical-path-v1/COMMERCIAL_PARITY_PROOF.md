# COMMERCIAL_PARITY_PROOF

D2 does not touch:

- `build_intake_v6_priced_quote_dry_run`
- CPP / Pricing Registry
- commercial adjustment math
- VAT / FX

Offer lifecycle still derives CURRENT from `loadingPricedQuote` only (no LL in stale condition).

Runtime after discrete changes: lifecycle shows `Ofertă actualizată` at PQ settle while LL may still complete afterward.
