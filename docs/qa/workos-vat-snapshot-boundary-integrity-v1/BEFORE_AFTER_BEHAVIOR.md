# BEFORE_AFTER_BEHAVIOR

## Before

Post-freeze authoritative offer and pricing-review:

1. Load frozen CPP (tax-exclusive net)
2. `vat_rate = await get_default_vat_pct(db)` (**live Settings**)
3. Recompute gross

Changing Settings VAT after freeze changed displayed/authoritative review/offer gross.

## After

Post-freeze:

1. Load frozen CPP
2. Resolve VAT via `resolve_frozen_commercial_vat_rate(notes, cpp)`
   - primary: `notes.commercial_adjustment_trace.vat_percent`
   - secondary: CPP `vat_rate_percent` (new freezes may stamp this)
   - else FAIL_CLOSED
3. Recompute gross from **frozen** rate only

Live Settings VAT after freeze: **FORBIDDEN**.

Pre-freeze dry-run / new work: still uses Settings default (**ALLOWED_AS_DEFAULT**).

## Historical data

No backfill. Artifacts without notes VAT (and without CPP rate) fail closed — do not guess.
