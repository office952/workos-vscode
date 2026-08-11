# TEST_RESULTS

## Focused fidelity suite

```text
cd backend
APP_ENV=test ENVIRONMENT=test
python -m pytest -q tests/test_intake_v6_face_finish_token_fidelity.py \
  tests/test_intake_v4_pricing_input.py::TestIntakeV4PricingInputPreview::test_grouped_finish_sets_letter_group_count \
  tests/test_intake_v4_pricing_input.py::TestIntakeV4PricingInputPreview::test_grouped_finish_handoff_preserves_each_letter_group \
  tests/test_commercial_price_proposal_preview.py::test_face_oracal_641_651_8500_pricing_no_color_tier \
  tests/test_commercial_price_proposal_preview.py::test_face_oracal_8500_rate_requires_confirmed_roll_width
→ 26 passed
```

## Coverage vs GO checklist

| ID | Scenario | Result |
|---|---|---|
| A | none | PASS — no face Oracal/print/aplicare |
| B | 641 | PASS — QI + CPP 641 lines |
| C | 651 | PASS — QI + CPP 651 lines |
| D | 8500 | PASS — QI + CPP 8500 @ width |
| E | print_laminate | PASS — distinct print line |
| F | mixed groups | PASS — per-group identity |
| G | confirmed/unconfirmed | unchanged path (group confirmed flags still used for 8500 width) |
| H | commercial totals | PASS — material subtotals = rate × area |
| I | confirm-gate regression | PASS — `test_intake_v6_confirm_gate_*` subset |
| J | VAT regression | PASS — dry-run vat subset |
| K | FX regression | PASS — manual_ron / fx subset |
| L | commercial-input regression | PASS — commercial_input_path_integrity subset |

## Closed-foundation regressions

```text
pytest -q tests/test_intake_v6_confirm_gate_complete_offer_integrity_v1.py \
  tests/test_intake_v6_commercial_input_path_integrity_v1.py \
  tests/test_intake_v6_priced_quote_dry_run.py \
  -k "manual_ron or vat or fx or confirm or composition or commercial"
→ 14 passed

pytest -q tests/test_f7f_owner_commercial_law_step3_total.py \
  tests/test_intake_v4_finish_type_vocabulary_contract.py
→ 38 passed
```

## Counters

```text
DB_SCHEMA_CHANGES = 0
PRICING_RULE_CHANGES = 0
PRODUCT_TRUTH_MUTATIONS = 0
```
