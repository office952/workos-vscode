# RETURN_CANT_PRICING_KEYS_READONLY_VERIFICATION_V1

## Verdict

```text
RETURN_CANT_PRICING_KEYS_READONLY_VERIFIED
```

## Scope checked

- read-only pricing verification only
- no Pricing changes
- no UI changes
- no adapter changes
- no Product Truth changes
- no DB / seed / migration
- no Quote / Order / Execution

## Accepted HEAD

- `98ebcb0`

## HEAD after verification

- pending at write time; finalized by docs-only commit if staged

## Keys verified

Materiale:

- `MAT-VOPSEA-RAL-CANT-30MM`
- `MAT-VOPSEA-RAL-CANT-60MM`
- `MAT-VOPSEA-RAL-CANT-80MM`
- `MAT-VOPSEA-RAL-CANT-100MM`

Labor / rates:

- `RETURN_CANT_VINYL_APPLICATION_LABOR`
- `RETURN_CANT_RAL_PAINT_LABOR`

## Values verified

- `RETURN_CANT_VINYL_APPLICATION_LABOR` = `1 EUR/ml`
- `MAT-VOPSEA-RAL-CANT-30MM` = `2 EUR/ml`
- `MAT-VOPSEA-RAL-CANT-60MM` = `2.5 EUR/ml`
- `MAT-VOPSEA-RAL-CANT-80MM` = `3 EUR/ml`
- `MAT-VOPSEA-RAL-CANT-100MM` = `4 EUR/ml`
- `RETURN_CANT_RAL_PAINT_LABOR` = `1 EUR/ml`

## Read-only evidence summary

1. `backend/seeds/seed_intake_v5_volumetric_letters_pricing.py` contains the new material rows with `unit = ml` and the new workcenter rows with `basis = per_linear_meter`.
2. `backend/seeds/seed_volumetric_owner_confirmed_prices.py` contains the owner-confirmed return-cant RAL material rows with the expected EUR/ml values and accepted-override semantics.
3. `backend/seeds/seed_volumetric_workcenter_rates.py` contains the dedicated return-cant labor rows and explicitly keeps them separate from legacy `PAINTING`, `VINYL_APPLICATION`, and `FACE_VINYL_APPLICATION_LABOR`.
4. `backend/services/pricing_registry_service.py` still builds the operator-facing Pricing Registry surface from `V6_MATERIAL_PRICES` and `V6_WORKCENTER_RATES`, so the newly implemented keys remain in the required V2 surface.
5. `backend/tests/test_return_cant_pricing_registry_keys.py` verifies the new keys are visible in the Pricing Registry surface with exact units and values.
6. `backend/tests/test_return_cant_owner_confirmed_materials.py` verifies the new material rows are owner-confirmed and that `MAT-VOPSEA-RAL`, `MAT-ORACAL-641`, and `MAT-ORACAL-651` retain their expected units and values.
7. `backend/tests/test_volumetric_operation_labor_rates.py` verifies the new labor rows retain `per_linear_meter` basis and `1.0` values.

## Non-regression confirmation

Confirmed unchanged in read-only evidence and focused tests:

- `MAT-ORACAL-641` remains `6.5 EUR/mp`
- `MAT-ORACAL-651` remains `9 EUR/mp`
- `MAT-PROFIL-LATERAL-LITERE-30MM` remains `2 EUR/ml`
- `MAT-PROFIL-LATERAL-LITERE-60MM` remains `3 EUR/ml`
- `MAT-PROFIL-LATERAL-LITERE-80MM` remains `4 EUR/ml`
- `MAT-PROFIL-LATERAL-LITERE-100MM` remains `5 EUR/ml`
- `FACE_VINYL_APPLICATION_LABOR` remains `5 EUR/mp`
- `VINYL_APPLICATION` remains legacy and was not promoted to final `return_cant` semantics
- `PAINTING` remains `4 EUR/ml` generic labor
- `MAT-VOPSEA-RAL` remains `10 EUR/buc` tube-based material

## Tests run

- `python -m pytest tests/test_return_cant_pricing_registry_keys.py tests/test_return_cant_owner_confirmed_materials.py tests/test_volumetric_operation_labor_rates.py -q`

Result:

- `9 passed`

## Runtime Pricing UI verification

Status:

- `not_run_runtime_not_started`

Reason:

- local ports `8000` and `3000` were not listening
- no services were started because this slice is read-only and forbids starting runtime just for verification

Screenshot:

- none

## Forbidden scope confirmation

- no Pricing changes
- no UI changes
- no adapter changes
- no Product Truth changes
- no Quote / Order / Execution changes
- no ProductAggregate / TaskGraph / ExecutionPlan changes
- no DB migration
- no seed run without owner GO
- no cleanup on the unrelated dirty worktree

## Validation

- `git diff --check`
- focused backend pytest command above

## Next recommended prompt

```text
RETURN_CANT_PRODUCT_TRUTH_CAPTURE_RUNTIME_BRIDGE_PLAN_V1
```