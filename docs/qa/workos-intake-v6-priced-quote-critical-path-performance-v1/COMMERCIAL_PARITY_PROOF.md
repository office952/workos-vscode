# COMMERCIAL_PARITY_PROOF

## Unit

`test_dry_run_official_commercial_parity_with_or_without_diagnostics`  
Asserts identical: `pricing_status`, `pricing_authority`, `commercial_totals`, `commercial_line_items`, blocker codes.

## Runtime (QA clone)

```text
workspace_id = 09cea6e2-41d3-44a3-a862-add13b01af84
commercial_parity = true
pricing_status = V6_PRICED_DRY_RUN_BLOCKED (both)
blocker_codes identical
commercial_totals identical
line_count = 22 (both)
off: internal/eic/diag = false
on:  internal/eic/diag = true
```

## Authority unchanged

```text
CPP → priced-quote-dry-run → commercial_totals → offer rail
```

No frontend price calculation. No Pricing Registry / RETURN-CANT / VAT / FX policy edits.
