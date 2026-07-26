## Purpose

Remove the false `PSU_UNDERSIZED` blocker from the Intake V6 logical-list LED PSU row when the effective configured PSU capacity already satisfies required wattage.

## Context

Live workspace `IR-MRBMAK7Z` showed `material.led_psu` as `BLOCAT` even though:

- the logical row had quantity `1` and subtotal `24 EUR`
- the child runtime material row was `MAT-LED-PSU-12V-160W`
- `finish_setup.psu_configuration = [160]`
- `finish_setup.psu_allocation_status = ok`

The blocker logic in the logical read-model was comparing only `selected_psu_watts` (`100`) against `required_psu_watts` (`140.4`), ignoring the effective configured PSU capacity.

## Files Changed

- `backend/services/gradi_logical_list_read_model_service.py`
- `backend/tests/test_gradi_logical_list_read_model.py`

## Commands

- `python -m pytest tests/test_gradi_logical_list_read_model.py -q`
  - Result: `25 passed`
- `GET /api/v1/intake-v6/workspaces/668ffeb2-5d2b-4eb6-a5c4-1a4618c6de7c/logical-list-read-model`
  - Result: `material.led_psu` keeps `quantity=1`, `subtotal=24`, `warnings=[]`, `blockers=[]`, `configured_psu_capacity=160.0`

## Boundary

- No pricing registry, formulas, dry-run totals, quote/order/execution, DB, seed, or migration changes.
- No frontend semantics change; the row unblocks because the backend blocker truth is corrected.

## Next Steps

- If future PSU allocation can represent parallel supplies with richer structure, keep using effective configured capacity as the blocker source instead of stale selected wattage.