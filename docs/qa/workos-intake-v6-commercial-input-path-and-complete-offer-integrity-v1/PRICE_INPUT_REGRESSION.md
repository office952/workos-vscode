# PRICE_INPUT_REGRESSION

Subset of exhaustive audit commercial-input scenarios (logic re-verified via targeted pytest):

| Scenario | Before | After |
|----------|--------|-------|
| A_MARKUP_10 / markup | CPP OFAT NO_EFFECT; FE local delta | Dry-run authoritative Adaos delta; FE matches BE after refetch |
| A_DISCOUNT_5 | same | Dry-run authoritative discount |
| A_MANUAL_RON_100 | CPP NO_EFFECT; FE RON→EUR mix | Backend converts with FX; FE no local money authority |
| A_CONFIRMED_FALSE | P0 TOTAL_COMPOSITION | **Unchanged / out of scope** (separate confirm-gate root) |

Runner full 46 not required; commercial-input + complete_offer authority covered by:
`tests/test_intake_v6_priced_quote_dry_run.py`,
`tests/test_intake_v6_commercial_input_path_integrity_v1.py`.
