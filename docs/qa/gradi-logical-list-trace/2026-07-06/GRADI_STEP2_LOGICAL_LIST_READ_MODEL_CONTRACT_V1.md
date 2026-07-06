# GRADI_STEP2_LOGICAL_LIST_READ_MODEL_CONTRACT_V1

## Result

Status: `PASS - UI WIRING IMPLEMENTED AFTER AUDIT CONTRACT`

Initial decision: `A. AUDIT-ONLY`

Follow-up decision: `IMPLEMENTED - MINIMAL FRONTEND UI WIRING`

## Boundary

Validated only:

- Step 2 Review runtime display.
- Step 3 Confirm read-only gate state.
- Backend `logical-list-read-model` API response.
- Backend `material-breakdown` API response.
- Backend `priced-quote-dry-run` API response.
- Backend/frontend code paths that fetch or display the relevant data.
- Frontend logical-list display wiring.

Not validated or changed:

- write handoff;
- quote creation;
- order creation;
- inventory;
- Product Truth persistence;
- CostEngine;
- DB schema;
- migrations;
- execution/task graph.

## Runtime Fixture

- SVG: `fisiere-teste-svg/gradi-curat.svg`
- Workspace: `IV6-0EFC6C31`
- Workspace id: `3c494f9f-4507-497a-912f-4f45fe709642`
- Route: `/intake-v6/3c494f9f-4507-497a-912f-4f45fe709642/operator`

## UI Evidence

Step 2 Review showed:

- `Cost intern referinta 772,92 EUR`
- `Pret oficial cu TVA 6.439,08 RON`
- `net 5.321,55 RON`
- filters `Toate`, `Materiale`, `Servicii / Operatii`, `Manopera`, `Detalii`
- tabs `Finisaje`, `Iluminare`, `Montaj`
- `Vector Litere` group with 4 letter rows
- `Vector Logo` group with 2 logo rows

After UI wiring, Step 2 Review also showed:

- `Lista logică read-model · 21/21 rânduri`
- `21` visible logical rows
- categories `Materiale · 14`, `Servicii / Operații · 6`, `Manoperă · 1`
- formula metadata for `21` rows
- visible gap/warning samples including `BACKING_AREA_FALLBACK_USED`, `ORACAL_ROLL_COLOR_SPLIT_MISSING`, `FORMULA_TRACE_MISSING`, `COMMERCIAL_FORMULA_UNVERSIONED`

Step 3 Confirm showed:

- `Handoff catre oferta reala: blocat`
- `Confirmari 1/2`
- `Creeaza oferta pretuita` disabled
- `Creeaza draft intern V6` disabled

No write action was triggered.

## API Evidence - Logical Read Model

Endpoint:

- `/api/v1/intake-v6/workspaces/3c494f9f-4507-497a-912f-4f45fe709642/logical-list-read-model`

Observed envelope:

- `source: gradi_logical_list_read_model_v1`
- `core_row_count: 21`
- `target_core_row_count: 21`
- `core_rows_complete: true`
- `categories: TOATE, MATERIALE, SERVICII / OPERATII, MANOPERA`
- `warnings: BACKING_AREA_FALLBACK_USED, ORACAL_ROLL_COLOR_SPLIT_MISSING`
- `blockers: []`
- `validation.formula_trace_metadata_present: true`

Observed rows:

| Row id | Status | Quantity | Formula status | Gaps |
| --- | --- | --- | --- | --- |
| `material.plexiglas_face` | `MATCHED` | `1.2638 m2` | `proposed_binding` | none |
| `material.logo_plexiglas_face` | `MATCHED` | `0.8005 m2` | `proposed_binding` | none |
| `material.forex_backing` | `PARTIAL` | `1.2638 m2` | `proposed_binding` | `BACKING_AREA_FALLBACK_USED` |
| `material.face_oracal` | `PARTIAL_TARIFF_CONFIRMATION_REQUIRED` | `1.3751 m2` | `proposed_binding` | none; warning color split |
| `material.print` | `SPLIT_IN_RUNTIME` | `0.996821 m2` | `proposed_binding` | `PRINT_ROWS_AGGREGATED_FOR_LOGICAL_LIST` |
| `material.lamination` | `SPLIT_IN_RUNTIME` | `0.996821 m2` | `proposed_binding` | `LAMINATION_ROWS_AGGREGATED_FOR_LOGICAL_LIST` |
| `material.return_profile` | `MATCHED` | `31.6382 m` | `proposed_binding` | none |
| `material.led_modules` | `MATCHED` | `144 buc` | `legacy_unversioned` | `FORMULA_TRACE_MISSING` |
| `material.led_psu` | `MATCHED` | `1 buc` | `legacy_unversioned` | none |
| `material.adhesive_cant` | `MATCHED` | `53.4944 ml` | `proposed_binding` | none |
| `material.adhesive_led` | `MATCHED` | `28.8 ml` | `proposed_binding` | none |
| `material.wire_letters` | `MATCHED` | `19 ml` | `proposed_binding` | none |
| `material.wire_supply` | `MATCHED` | `5 ml` | `proposed_binding` | none |
| `material.mounting_accessories` | `MATCHED` | `1 job` | `legacy_unversioned` | `COMMERCIAL_FORMULA_UNVERSIONED` |
| `service.cnc_face` | `MATCHED` | `25.0188 ml` | `proposed_binding` | none |
| `service.cnc_face_bevel` | `MATCHED` | `25.0188 ml` | `proposed_binding` | none |
| `service.cnc_back` | `MATCHED` | `25.0188 ml` | `proposed_binding` | none in live compact API; service remains bridge-sensitive by code audit |
| `service.print` | `SPLIT_IN_RUNTIME` | `1.1962 m2` | `proposed_binding` | `PRINT_SERVICE_ROWS_AGGREGATED_FOR_LOGICAL_LIST` |
| `service.lamination` | `SPLIT_IN_RUNTIME` | `1.1962 m2` | `legacy_unversioned` | `LAMINATION_SERVICE_ROWS_AGGREGATED_FOR_LOGICAL_LIST` |
| `service.application` | `SPLIT_IN_RUNTIME` | `1.1962 m2` | `legacy_unversioned` | `APPLICATION_SERVICE_ROWS_AGGREGATED_FOR_LOGICAL_LIST` |
| `labor.cant_glue` | `MATCHED` | `31.6382 m` | `proposed_binding` | none |

## API Evidence - Material Breakdown

Observed counts:

- material rows: `9`
- consumable rows: `8`
- operation rows: `12`
- edge/cant operation rows: `1`
- nesting rows: `16`
- nesting preview: present

Observed warnings:

- `backing_area_fallback_used`
- `sheet_nesting_quantity_floor_applied`
- `nesting_used_for_quote_not_stock`
- `roll_nesting_color_split_missing`
- `mounting_accessories_internal_cost_percent_applied`

Observed totals:

- `estimated_cost_total: 772.92 EUR`
- `contains_estimates: true`
- `contains_missing_prices: false`

## API Evidence - Priced Dry Run

Observed status:

- `V6_PRICED_DRY_RUN_READY`

Observed totals:

- net `5321.55 RON`
- VAT `1117.53 RON`
- gross `6439.08 RON`

Observed commercial lines:

- `debitare_fata`
- `modelare_cant_aluminiu`
- `debitare_spate`
- `sistem_led_module`
- `sursa_led`
- `finisaje_colantare_vopsire`
- `sablon_montaj_forex`
- `ambalare` owner decision required
- `montaj` owner decision required

Contract note: `ambalare` and `montaj` are not part of the 21 logical core rows.

## Backend Code Audit

Controlling service:

- `backend/services/gradi_logical_list_read_model_service.py`

Findings:

- `_line(...)` emits formula code, formula version, formula status, quantity, unit, subtotal, runtime source, child rows, gaps, warnings, and blockers.
- `build_gradi_logical_list_read_model_from_runtime(...)` constructs the 21 rows.
- The endpoint uses `get_material_breakdown_for_workspace(...)` and `build_intake_v6_priced_quote_dry_run(...)` as read-only inputs.
- The route exists at `backend/routers/intake_v6_workspaces.py`.

## Frontend Code Audit

Findings:

- `IntakeV6ReviewStep.tsx` fetches `getIntakeV6LogicalListReadModel(workspaceId)`.
- It stores the response in `logicalListReadModel`.
- It passes `logicalList={logicalListReadModel}` into `IntakeV6LiveCalculationSummary`.
- `IntakeV6LiveCalculationSummary.tsx` now consumes `logicalList` in its row-building path.
- Rows shown in the live calculation sidebar are derived from `logicalList.rows` when present.
- Rows fall back to `buildIntakeV6LiveMaterialsUsedRows({ breakdown, ... })` only when `logicalList.rows` is absent or empty.
- `intakeV6LiveCalculationRowFilters.ts` already knows logical row keys, but the source rows are not backend logical rows.
- `IntakeV6LogicalListReadModelResponse` and `IntakeV6LogicalListLineTrace` now have concrete frontend definitions in `intakeV6PricedQuoteTypes.ts`.

## Tests After UI Wiring

Command:

```powershell
pnpm.cmd --dir frontend exec vitest run src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.test.tsx --reporter=verbose
```

Result: `13 passed`.

Covered behavior:

- logical-list rows become the primary owner-facing list when present;
- material-breakdown rows are not used as the primary list while logical rows exist;
- formula metadata, gaps, categories, and child counts render;
- material-breakdown fallback remains covered by existing tests.

Requested companion test note:

- `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.test.tsx` does not exist, so it was not run.

Diff checks:

```powershell
git diff --check
git diff --cached --check
```

Result: no output.

## Conclusion

Backend produces the Step 2 logical read-model contract and the frontend now renders that read-model as the Step 2 source of truth when rows are present.

No backend calculation repair was required.

## Recommended Next Slice

`IMPLEMENT_GRADI_STEP2_LOGICAL_LIST_UI_CONTRACT_V1`

Acceptance focus:

- define frontend logical-list types;
- render the 21 backend rows read-only;
- expose formula/gap metadata in a detail/internal surface;
- keep official priced dry-run totals unchanged;
- keep Quote/Order/Inventory/Execution untouched.