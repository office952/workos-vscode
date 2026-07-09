# 2026-07-09 - return cant pricing ui runtime recheck v1

HEAD before:

- `25f24c9`

Task:

- `RETURN_CANT_PRICING_UI_RUNTIME_RECHECK_V1`

Mode:

- QA / read-only only

Safety gate:

- HEAD confirmed = `25f24c9`
- no staged files
- `git diff --check` clean
- unrelated dirty untracked worktree preserved untouched

Runtime status:

- backend `127.0.0.1:8000` = `200`
- frontend `127.0.0.1:3000` = `200`

DB verification:

- DB path rechecked: `C:\Users\offic\workos_app_vs\backend\dev.db`
- all six target rows still present
- values unchanged and correct:
  - `RETURN_CANT_VINYL_APPLICATION_LABOR = 1 EUR/ml`
  - `RETURN_CANT_RAL_PAINT_LABOR = 1 EUR/ml`
  - `MAT-VOPSEA-RAL-CANT-30MM = 2 EUR/ml`
  - `MAT-VOPSEA-RAL-CANT-60MM = 2.5 EUR/ml`
  - `MAT-VOPSEA-RAL-CANT-80MM = 3 EUR/ml`
  - `MAT-VOPSEA-RAL-CANT-100MM = 4 EUR/ml`

Legacy non-regression still present:

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

API verification:

- `GET /api/v1/pricing/registry?template_code=TPL-VOLUMETRIC-LETTERS`
- all six target keys returned with:
  - `base_cost` populated
  - `status = active`
  - `confidence = owner_confirmed`
  - correct unit / currency / rate basis

UI verification:

- route checked: `http://127.0.0.1:3000/inventory/pricing`
- clicked `Actualizează`
- kept `Toate intrările`
- captured general screenshot on unfiltered audit view
- search `RETURN_CANT_` showed:
  - `Manopera vopsit RAL pe cant = 1,00 EUR`
  - `Aplicare folie autocolanta pe cant = 1,00 EUR`
- search `MAT-VOPSEA-RAL-CANT-` showed:
  - `Vopsire RAL cant 30 mm - material = 2,00 EUR`
  - `Vopsire RAL cant 60 mm - material = 2,50 EUR`
  - `Vopsire RAL cant 80 mm - material = 3,00 EUR`
  - `Vopsire RAL cant 100 mm - material = 4,00 EUR`
- none of the six keys showed `Lipsă`, `Rată lipsă`, or `Blochează calcul complet`

Screenshot references from this recheck run:

- Pricing general / `Toate intrările`
- Pricing search `RETURN_CANT_`
- Pricing search `MAT-VOPSEA-RAL-CANT-`

Honest UI opinion:

- the operator-facing outcome for this narrow fix is now good enough to trust;
- data is aligned across DB, API, and UI;
- the page remains visually dense, but the `return_cant` pricing visibility issue itself is resolved.

Files touched:

- `docs/qa/return-cant-pricing-ui-runtime-recheck-2026-07-09/RETURN_CANT_PRICING_UI_RUNTIME_RECHECK_V1.md`
- `docs/worklog/realignment/2026-07-09_return_cant_pricing_ui_runtime_recheck_v1.md`

Forbidden scope confirmation:

- no UI changes
- no code changes except docs
- no Pricing values changed
- no backfill rerun
- no seed run
- no DB migration
- no Product Truth changes
- no adapter changes
- no Intake UI changes
- no Quote/Order/Execution
- no ProductAggregate/TaskGraph/ExecutionPlan

Validation required before commit:

- `git diff --check` for the two docs

Recommended next prompt:

- `RETURN_CANT_ADAPTER_PRICING_TARGETS_FINAL_ALIGNMENT_V1`