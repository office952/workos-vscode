# TEST_RESULTS

Targeted pytest (backend venv):

- `tests/test_intake_v6_back_bevel_commercial_activation.py` — PASS
- `tests/test_intake_v4_backing_mode.py::TestLayerBackingBevelHandoff` — PASS
- `tests/test_intake_v4_cnc_operation_dry_run.py::test_backing_cut_and_bevel_share_one_candidate_task` — PASS
- `tests/test_intake_v4_cnc_operation_dry_run.py::test_production_preview_groups_backing_cut_and_bevel` — PASS
- `tests/test_intake_v4_pricing_input.py` — PASS (after schema-default presence fix)
- `tests/test_commercial_price_proposal_preview.py` — PASS
- `tests/test_f7i1_owner_confirmed_provisional_rate_activation.py` — PASS
- `tests/test_f7i_commercial_tariff_registry_closure.py` — PASS
- `tests/test_letters_commercial_measurement_contract.py` — PASS
- `tests/test_intake_v6_per_layer_backing_processing.py` — PASS
- `tests/test_shared_cnc_operation_model.py` — PASS
- `tests/test_letters_cpp_measurement_consumption.py` — PASS
- `tests/test_f7h_owner_eur_functional_closure.py` — PASS

Frontend: `pnpm exec vitest run src/lib/intakeV6/intakeV6LiveMaterialsUsedDisplay.test.ts` — 11 passed.

`sanfren_spate` is **not** in `OWNER_CONFIRMED_PROVISIONAL_COMMERCIAL_LINE_CODES`.
