# BEFORE_AFTER

## Before

- CPP correctly nulls `complete_offer_total` when Oracal 8500 groups are unconfirmed.
- Dry-run empties `commercial_totals` when CPP blocked.
- Confirm UI still rendered blocked product EUR subtotals next to “Blocat comercial” without clear non-Ofertă labeling.
- Confirm consolidated status did not surface dry-run commercial blockers as a composition-incomplete gate.
- No FE-facing derived readiness summary mirroring existing gates.
- Prior dry-run totals could remain in Confirm state until refetch completed (`ws.updated_at` change).

## After

- Dry-run exposes `offer_composition_readiness` (derived read-model only).
- Canonical READY/BLOCKED remains `pricing_status` / CPP complete offer / `commercial_freeze_allowed`.
- Confirm Ofertă headline refuses composition-blocked totals.
- Blocked product EUR amounts labeled as composition-only — “nu este Ofertă client”.
- Consolidated status blocked when `commercial_composition_complete=false`.
- Confirm refetch clears `pricedQuoteDryRun` before fresh backend fetch (no stale flash).
- Oracal 8500 law unchanged; VAT/FX/commercial-input unchanged.
