# TEST_RESULTS

## Primary suite

```text
cd backend
APP_ENV=test ENVIRONMENT=test
python -m pytest -q \
  tests/test_company_commercial_settings.py \
  tests/test_fx_commercial_authority_closure_v1.py \
  tests/test_intake_v6_priced_quote_dry_run.py \
  tests/test_vat_snapshot_boundary_integrity_v1.py \
  tests/test_frozen_commercial_vat_resolver.py \
  tests/test_order_snapshot_v2_convert.py \
  --ignore=tests/manual
```

Result: **71 passed**

## Extra

- `tests/test_order_currency_conversion.py` — passed
- `tests/test_f7h_owner_eur_functional_closure.py` — passed (with logo suite; see note)
- FE: `vitest run src/lib/intakeV6/intakeV6OfferCalculator.test.ts` — 6 passed

## Matrix coverage

| Matrix | Coverage |
|--------|----------|
| A persistence 4.97 | `test_matrix_a_settings_persistence_4_97` |
| B missing FX | `test_matrix_b_missing_fx_fail_closed_no_write` |
| C no row | `test_matrix_c_no_row_money_read_does_not_persist_fx` |
| D Quote→Order | `test_matrix_d_*` |
| E profitability freeze | `test_matrix_e_*` + existing convert suite |
| F Logo/CPP | `test_matrix_f_*` |
| G dry-run | dry-run suite + resolve_configured patch; official EUR without inventing FX |
| H demo | `seed_atoms_demo_v1._seed_company_commercial_settings` |

## VAT regression

VAT snapshot suites in the primary command: **green** → `VAT_BEHAVIOR_CHANGED = NO`

## Note

`test_packaging_deferred_and_sablon_not_doubled` failed once in a broader logo file run (sablon line count). Unrelated to FX authority (no packaging/sablon edits in this GO); not part of FX PASS gate.
