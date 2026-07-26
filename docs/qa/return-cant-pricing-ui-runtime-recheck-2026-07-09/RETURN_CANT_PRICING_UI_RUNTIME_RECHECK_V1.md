# RETURN_CANT_PRICING_UI_RUNTIME_RECHECK_V1

## Verdict

```text
RETURN_CANT_PRICING_UI_RUNTIME_RECHECK_PASS
```

## Runtime status

- backend `http://127.0.0.1:8000` = `200`
- frontend `http://127.0.0.1:3000` = `200`
- active Pricing route reachable: `http://127.0.0.1:3000/inventory/pricing`

## DB verification

Active DB path confirmed:

- `C:\Users\offic\workos_app_vs\backend\dev.db`

Target rows present and correct:

- `RETURN_CANT_VINYL_APPLICATION_LABOR` -> `1 EUR/ml`, `status=active`, `rate_basis=per_linear_meter`
- `RETURN_CANT_RAL_PAINT_LABOR` -> `1 EUR/ml`, `status=active`, `rate_basis=per_linear_meter`
- `MAT-VOPSEA-RAL-CANT-30MM` -> `2 EUR/ml`, `status=active`, `currency=EUR`
- `MAT-VOPSEA-RAL-CANT-60MM` -> `2.5 EUR/ml`, `status=active`, `currency=EUR`
- `MAT-VOPSEA-RAL-CANT-80MM` -> `3 EUR/ml`, `status=active`, `currency=EUR`
- `MAT-VOPSEA-RAL-CANT-100MM` -> `4 EUR/ml`, `status=active`, `currency=EUR`

## API verification

Endpoint checked:

- `GET http://127.0.0.1:8000/api/v1/pricing/registry?template_code=TPL-VOLUMETRIC-LETTERS`

Result for all six keys:

- `base_cost != null`
- `status = active`
- `confidence = owner_confirmed`
- unit / currency / rate basis correct

Exact live API values:

- `RETURN_CANT_VINYL_APPLICATION_LABOR = 1 EUR/ml`
- `RETURN_CANT_RAL_PAINT_LABOR = 1 EUR/ml`
- `MAT-VOPSEA-RAL-CANT-30MM = 2 EUR/ml`
- `MAT-VOPSEA-RAL-CANT-60MM = 2.5 EUR/ml`
- `MAT-VOPSEA-RAL-CANT-80MM = 3 EUR/ml`
- `MAT-VOPSEA-RAL-CANT-100MM = 4 EUR/ml`

## UI verification

Route checked:

- `http://127.0.0.1:3000/inventory/pricing`

Steps performed:

1. opened / reused live Pricing page
2. clicked `Actualizează`
3. selected `Toate intrările`
4. searched `RETURN_CANT_`
5. searched `MAT-VOPSEA-RAL-CANT-`

Visual confirmation:

- `RETURN_CANT_VINYL_APPLICATION_LABOR = 1,00 EUR`
- `RETURN_CANT_RAL_PAINT_LABOR = 1,00 EUR`
- `MAT-VOPSEA-RAL-CANT-30MM = 2,00 EUR`
- `MAT-VOPSEA-RAL-CANT-60MM = 2,50 EUR`
- `MAT-VOPSEA-RAL-CANT-80MM = 3,00 EUR`
- `MAT-VOPSEA-RAL-CANT-100MM = 4,00 EUR`

Negative confirmation:

- for these six keys the UI no longer shows `Lipsă`
- for these six keys the UI no longer shows `Rată lipsă`
- for these six keys the UI no longer shows `Blochează calcul complet`

## Screenshot references

Integrated browser screenshots captured in this recheck run:

1. Pricing general / `Toate intrările`
2. Pricing search `RETURN_CANT_`
3. Pricing search `MAT-VOPSEA-RAL-CANT-`

## Non-regression legacy

Legacy protected rows still verified as healthy in DB:

- `PAINTING`
- `MAT-VOPSEA-RAL`
- `FACE_VINYL_APPLICATION_LABOR`
- `VINYL_APPLICATION`
- `MAT-ORACAL-641`
- `MAT-ORACAL-651`
- `MAT-PROFIL-LATERAL-LITERE-30MM`
- `MAT-PROFIL-LATERAL-LITERE-60MM`
- `MAT-PROFIL-LATERAL-LITERE-80MM`
- `MAT-PROFIL-LATERAL-LITERE-100MM`

## Honest UI opinion

Pentru obiectivul strict al acestui slice, Pricing UI este acum coerent și operator-safe: datele din runtime, API și UI sunt aliniate, filtrele arată exact cele 6 intrări urmărite, iar starea blocantă de dinainte nu mai este vizibilă pentru aceste key-uri. UI-ul rămâne încă dens și orientat audit-first, dar nu mai induce în eroare pe zona `return_cant`.

## Forbidden scope confirmation

- no UI changes
- no code changes except docs
- no Pricing values changed in this task
- no backfill rerun
- no seed run
- no DB migration
- no Product Truth changes
- no adapter changes
- no Intake UI changes
- no Quote/Order/Execution
- no ProductAggregate/TaskGraph/ExecutionPlan

## Next recommended prompt

```text
RETURN_CANT_ADAPTER_PRICING_TARGETS_FINAL_ALIGNMENT_V1
```