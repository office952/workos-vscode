# TEST_RESULTS

## Backend

```text
python -m pytest -q \
  tests/test_intake_v6_priced_quote_dry_run.py \
  tests/test_intake_v6_commercial_input_path_integrity_v1.py \
  tests/test_vat_snapshot_boundary_integrity_v1.py \
  tests/test_frozen_commercial_vat_resolver.py \
  tests/test_intake_v6_snapshot_authoritative_offer.py \
  tests/test_fx_commercial_authority_closure_v1.py \
  tests/test_company_commercial_settings.py \
  --ignore=tests/manual
```

Result: **53 passed**

## Frontend

```text
vitest run \
  src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.test.tsx \
  src/lib/intakeV6/intakeV6OfferCalculator.test.ts
```

Result: **38 passed**

## Regressions

- `VAT_BEHAVIOR_CHANGED = NO`
- `FX_BEHAVIOR_CHANGED = NO` (FX suite green)
