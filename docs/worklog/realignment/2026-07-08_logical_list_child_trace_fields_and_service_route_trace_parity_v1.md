Purpose

- Expose live calculation trace fields on logical-list child rows without changing quantities or prices.

Scope

- Backend read-model only.
- No pricing formula or registry changes.
- No quote/order/execution changes.
- No DB or seed changes.

Files Changed

- backend/services/gradi_logical_list_read_model_service.py
- backend/tests/test_gradi_logical_list_read_model.py

Implementation Summary

- Preserved `quantity_basis` and `quantity_source` on logical-list child rows.
- Preserved `warnings` and `gaps` on child rows instead of dropping them.
- Added service child trace fields:
  - `basis_key`
  - `basis_label`
  - `pricing_status`
  - `pricing_rate_key`
  - `operation_equivalent_quantity`
  - `operation_equivalent_unit`
  - `source_material_key`
  - `source_material_quantity`
  - `source_material_unit`
  - `waste_factor`
  - `waste_percent`
  - `waste_note`
- Resolved service `quantity_source` from related runtime material rows when a safe relation exists.
- Marked unresolved service trace with explicit gaps instead of silent nulls.
- Propagated confirmed face `source_part_ids` into `material.plexiglas_face` logical rows when ids are derivable from workspace payload.

Validation

- Focused tests:
  - `.\.venv\Scripts\python.exe -m pytest tests/test_gradi_logical_list_read_model.py -q`
  - Result: `24 passed`
- Runtime API verification completed for:
  - `IR-MRB2TPKK`
  - `IR-MR2MP11C`
  - `IR-MR8TNT0O`

Runtime Outcome

- Child material rows now expose basis/source/ids in logical-list.
- Child service rows now expose basis/rate/status and waste factor.
- `IR-MR2MP11C` application mix is no longer hidden:
  - logo application rows resolve to footprint-sourced print material rows;
  - letter-face fallback application rows remain explicit with `SERVICE_SOURCE_MATERIAL_ROW_MISSING` gaps.
- `priced-quote-dry-run` still provides aggregate parity only; row-level parity remains unavailable because commercial line items are absent and pricing status is blocked for these templates.

Boundary Confirmation

- No quantity changes.
- No price changes.
- No UI hiding.
- No forbidden subsystem changes.