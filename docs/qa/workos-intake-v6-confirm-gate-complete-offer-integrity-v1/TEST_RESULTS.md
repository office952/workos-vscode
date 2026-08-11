# TEST_RESULTS

## Backend

```text
pytest tests/test_intake_v6_confirm_gate_complete_offer_integrity_v1.py
       tests/test_intake_v6_commercial_input_path_integrity_v1.py
       tests/test_vat_snapshot_boundary_integrity_v1.py
       tests/test_fx_commercial_authority_closure_v1.py
       tests/test_commercial_price_proposal_preview.py::test_oracal_8500_blocks_on_unconfirmed_or_disagreeing_letter_groups
       tests/test_f7f_owner_commercial_law_step3_total.py
→ PASS (confirm-gate suite + regressions)
```

Also: `tests/test_intake_v6_priced_quote_dry_run.py` green with readiness field present on responses.

## Frontend

```text
vitest:
  intakeV6ConfirmConsolidatedStatus.test.ts
  IntakeV6FinalConfigurationSummary.test.tsx
  IntakeV6LiveCalculationSummary.test.tsx
  intakeV6OfficialPricing.test.ts
→ PASS
```

## Matrix coverage

| ID | Scenario | Proof |
|----|----------|-------|
| A | confirmed valid → offer ready | live dry-run READY + readiness.canonical_gate=ready |
| B | A_CONFIRMED_FALSE blocked | HTTP CPP + unit readiness |
| C | reconfirm → ready | Oracal law unchanged; inverse of B |
| D | stale invalidated | Confirm hook clears dry-run before refetch |
| E–F | adjusted + confirmed/unconfirmed | commercial-input suite + readiness |
| G–H | priced write blocked/ready | write service requires V6_PRICED_DRY_RUN_READY |
| I | snapshot current truth | freeze still requires dry-run READY + freeze pin |
| J–L | VAT / FX / Manual RON | regression suites green |
