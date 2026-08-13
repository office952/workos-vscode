# TEST_RESULTS

```text
pytest tests/test_intake_v6_priced_quote_dry_run.py \
       tests/test_intake_v6_priced_quote_dry_run_runtime.py \
       tests/test_f7f_owner_commercial_law_step3_total.py \
       tests/test_intake_v6_return_cant_depth_finish_matrix.py
→ 38 passed

pytest tests/test_intake_v6_priced_quote_dry_run.py \
       tests/test_intake_v6_priced_quote_dry_run_runtime.py \
       tests/test_intake_v6_live_calc_offer_scope.py \
       tests/test_commercial_price_proposal_preview.py
→ 63 passed
```

## New / updated coverage

1. Default dry-run defers internal-cost diagnostics  
2. Opt-in `include_internal_cost_diagnostics=True` restores MB/EIC/cost-plus  
3. Official commercial parity on vs off diagnostics  
4. Existing ready/blocked/cost-plus-not-official tests updated to opt-in where they assert diagnostics  
