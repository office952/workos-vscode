## Purpose

Align Intake V6 `Calcul live` PSU material rows with the actual `finish_setup.psu_configuration` instead of collapsing multi-PSU plans into a single arbitrary SKU.

## Cause

Two backend layers were mismatched:

1. `backend/services/intake_v4_material_breakdown_service.py`
   - treated `psu_configuration` only as a count
   - selected one PSU SKU from the max wattage only
   - example live defect: `[200, 100]` became `MAT-LED-PSU-12V-200W × 2`

2. `backend/services/gradi_logical_list_read_model_service.py`
   - expected a single exact consumable key `led_psu`
   - after splitting PSU rows by wattage, it needed prefix aggregation to keep the logical parent visible

## Expected PSU Rows

Canonical rule:

- `psu_configuration = [160, 60, 60]` => `160W × 1`, `60W × 2`
- live route today: `psu_configuration = [200, 100]` => `200W × 1`, `100W × 1`

## Files Changed

- `backend/services/intake_v4_material_breakdown_service.py`
- `backend/services/gradi_logical_list_read_model_service.py`
- `backend/tests/test_intake_v4_material_breakdown.py`
- `backend/tests/test_gradi_logical_list_read_model.py`

## Tests Run

- `python -m pytest tests/test_intake_v4_material_breakdown.py -q -k "led_psu"`
  - Result: `3 passed`
- `python -m pytest tests/test_gradi_logical_list_read_model.py -q`
  - Result: `25 passed`

## Runtime Route Checked

- `http://127.0.0.1:3000/intake-v6/IR-MRBMAK7Z/operator`

## Before / After Proof

Before:

- `material-breakdown` collapsed PSU into one row
  - `MAT-LED-PSU-12V-200W`
  - `quantity = 2`
- `logical-list-read-model`
  - generic parent `Sursa LED 12V`
  - child row only `MAT-LED-PSU-12V-200W`
  - wrong multi-PSU representation

After:

- `material-breakdown` emits exact rows from configuration:
  - `led_psu_100w` -> `MAT-LED-PSU-12V-100W` -> `1 buc` -> `19.2 EUR`
  - `led_psu_200w` -> `MAT-LED-PSU-12V-200W` -> `1 buc` -> `48.0 EUR`
- `logical-list-read-model` parent aggregates split rows:
  - `Sursa LED 12V`
  - `2 buc`
  - `67.2 EUR`
  - child rows preserve exact 100W and 200W identities

## Scope Guard

- No LED consumption formula change
- No PSU safety margin formula change
- No pricing registry rate change
- No Quote / Order / Execution work
- No DB / seed / migration work
- No Vector Logo badge logic change
- No layout width work