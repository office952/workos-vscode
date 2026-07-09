# RETURN_CANT_RUNTIME_PRICING_BACKFILL_APPLY_V1

## Verdict

```text
RETURN_CANT_RUNTIME_PRICING_BACKFILL_APPLIED
```

## Scope checked

- runtime apply of dedicated backfill script only
- no code changes in apply slice
- no Pricing UI changes
- no Product Truth changes
- no adapter changes
- no Intake UI changes
- no Quote / Order / Execution changes
- no ProductAggregate / TaskGraph / ExecutionPlan changes
- no DB migration
- no general seed run
- no conflict overwrite

## Accepted HEAD

- `60ece9d`

## Runtime DB target

- local active DB path: `C:\Users\offic\workos_app_vs\backend\dev.db`

## Pre-apply inspection

### Missing target rows before apply

- `RETURN_CANT_VINYL_APPLICATION_LABOR`
- `RETURN_CANT_RAL_PAINT_LABOR`
- `MAT-VOPSEA-RAL-CANT-30MM`
- `MAT-VOPSEA-RAL-CANT-60MM`
- `MAT-VOPSEA-RAL-CANT-80MM`
- `MAT-VOPSEA-RAL-CANT-100MM`

### Protected legacy rows confirmed before apply

- `MAT-ORACAL-641 = 6.5 EUR`
- `MAT-ORACAL-651 = 9 EUR`
- `MAT-PROFIL-LATERAL-LITERE-30MM = 2 EUR`
- `MAT-PROFIL-LATERAL-LITERE-60MM = 3 EUR`
- `MAT-PROFIL-LATERAL-LITERE-80MM = 4 EUR`
- `MAT-PROFIL-LATERAL-LITERE-100MM = 5 EUR`
- `MAT-VOPSEA-RAL = 10 EUR/buc`
- `FACE_VINYL_APPLICATION_LABOR = 5 EUR/mp`
- `PAINTING = 4 EUR/ml`
- `VINYL_APPLICATION = 3 EUR/mp`

## Tests before apply

Command run:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_return_cant_runtime_pricing_backfill.py tests/test_return_cant_pricing_registry_keys.py tests/test_return_cant_owner_confirmed_materials.py tests/test_volumetric_operation_labor_rates.py -q
```

Result:

- `13 passed, 2 warnings in 1.55s`

## Script apply

Command run:

```text
.\.venv\Scripts\python.exe scripts/backfill_return_cant_pricing_keys.py
```

Script output summary:

- `inserted = 6`
- `already_ok = 0`
- `conflicts = 0`
- `skipped = 0`

Inserted rows:

- `MAT-VOPSEA-RAL-CANT-30MM`
- `MAT-VOPSEA-RAL-CANT-60MM`
- `MAT-VOPSEA-RAL-CANT-80MM`
- `MAT-VOPSEA-RAL-CANT-100MM`
- `RETURN_CANT_VINYL_APPLICATION_LABOR`
- `RETURN_CANT_RAL_PAINT_LABOR`

Conflict verdict:

```text
NO_CONFLICTS
```

## Post-apply inspection

### Target rows present after apply

- `MAT-VOPSEA-RAL-CANT-30MM` -> `ml`, `2 EUR`, `EUR`, `active`, `accepted_override`
- `MAT-VOPSEA-RAL-CANT-60MM` -> `ml`, `2.5 EUR`, `EUR`, `active`, `accepted_override`
- `MAT-VOPSEA-RAL-CANT-80MM` -> `ml`, `3 EUR`, `EUR`, `active`, `accepted_override`
- `MAT-VOPSEA-RAL-CANT-100MM` -> `ml`, `4 EUR`, `EUR`, `active`, `accepted_override`
- `RETURN_CANT_VINYL_APPLICATION_LABOR` -> `per_linear_meter`, `1 EUR/ml`, `active`
- `RETURN_CANT_RAL_PAINT_LABOR` -> `per_linear_meter`, `1 EUR/ml`, `active`

### Protected legacy rows after apply

Legacy rows stayed unchanged:

- `MAT-ORACAL-641`
- `MAT-ORACAL-651`
- `MAT-PROFIL-LATERAL-LITERE-30MM`
- `MAT-PROFIL-LATERAL-LITERE-60MM`
- `MAT-PROFIL-LATERAL-LITERE-80MM`
- `MAT-PROFIL-LATERAL-LITERE-100MM`
- `MAT-VOPSEA-RAL`
- `FACE_VINYL_APPLICATION_LABOR`
- `PAINTING`
- `VINYL_APPLICATION`

## API verification

Endpoint checked:

- `GET /api/v1/pricing/registry?template_code=TPL-VOLUMETRIC-LETTERS`

Result:

- all six target keys returned with `base_cost != null`
- all six target keys returned with `status = active`
- all six target keys returned with `confidence = owner_confirmed`

Exact values confirmed by live API:

- `RETURN_CANT_VINYL_APPLICATION_LABOR = 1 EUR/ml`
- `RETURN_CANT_RAL_PAINT_LABOR = 1 EUR/ml`
- `MAT-VOPSEA-RAL-CANT-30MM = 2 EUR/ml`
- `MAT-VOPSEA-RAL-CANT-60MM = 2.5 EUR/ml`
- `MAT-VOPSEA-RAL-CANT-80MM = 3 EUR/ml`
- `MAT-VOPSEA-RAL-CANT-100MM = 4 EUR/ml`

## Pricing UI verification

Verification status:

- `run`

Route checked:

- `http://127.0.0.1:3000/inventory/pricing`

Observed UI results:

- `Toate intrările` refreshed successfully
- verification badge changed from prior blocked state to `Verificare1`
- search `RETURN_CANT_` shows:
  - `RETURN_CANT_RAL_PAINT_LABOR = 1,00 EUR`
  - `RETURN_CANT_VINYL_APPLICATION_LABOR = 1,00 EUR`
- search `MAT-VOPSEA-RAL-CANT-` shows:
  - `MAT-VOPSEA-RAL-CANT-30MM = 2,00 EUR`
  - `MAT-VOPSEA-RAL-CANT-60MM = 2,50 EUR`
  - `MAT-VOPSEA-RAL-CANT-80MM = 3,00 EUR`
  - `MAT-VOPSEA-RAL-CANT-100MM = 4,00 EUR`

Screenshots captured in the integrated browser during this apply run:

- Pricing general / `Toate intrările`
- Pricing search for `RETURN_CANT_`
- Pricing search for `MAT-VOPSEA-RAL-CANT-`

## Validation

- focused pytest rerun: pass
- runtime DB inspection after apply: pass
- live API verification: pass
- live UI verification: pass
- `git diff --check`: expected docs-only validation still required before commit

## Next recommended prompt

```text
RETURN_CANT_PRICING_UI_RUNTIME_RECHECK_V1
```