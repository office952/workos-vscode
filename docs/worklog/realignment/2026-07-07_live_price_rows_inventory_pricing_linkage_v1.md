## TASK

LIVE_PRICE_ROWS_TO_INVENTORY_PRICING_LINKAGE_AUDIT_AND_FIX_V1

## HEAD before work

- `fb2eb40`

## Safety state

- `git status -sb`: tracked worktree clean before edits; historical untracked files present
- `git diff --cached --name-only`: empty before work
- `git status --short --untracked-files=no`: empty before work
- `git diff --check`: clean before edits

## Audit findings

### Active runtime source of contradiction

- The active owner-facing `Calcul live` surface prefers the logical list read-model when present.
- Visible label splitting did not come only from raw `material_rows`; it was reintroduced by:
  - [frontend/src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.tsx](c:/Users/offic/workos_app_vs/frontend/src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.tsx)
  - [frontend/src/lib/intakeV6/intakeV4LiveMaterialsUsedDisplay.ts](c:/Users/offic/workos_app_vs/frontend/src/lib/intakeV6/intakeV4LiveMaterialsUsedDisplay.ts)
- Additional base row wording drift also existed in:
  - [backend/services/intake_v4_material_breakdown_service.py](c:/Users/offic/workos_app_vs/backend/services/intake_v4_material_breakdown_service.py)

### Root cause

- The fallback live-calc helper explicitly split shared plexiglas by role into separate visible identities (`plexi_letters`, `plexi_emblems`) based on letters/logo area shares.
- The logical list path surfaced two top-level rows for the same shared plexiglas identity:
  - `material.plexiglas_face`
  - `material.logo_plexiglas_face`
- Several visible labels used role/context wording as if it were the resource identity:
  - `Plexiglas 3 mm / fata litere`
  - `Plexiglas 3 mm / embleme/logo`
  - `Forex 10 mm / spate litere`
  - `Cant / volum litere + interioare + artwork`
  - `Lipire cant / volum pe fata litere`

## Resource identity policy applied

1. Visible material rows group by resource identity, not product role.
2. Visible operation rows group by operation identity, not letters/logo role wording.
3. Usage context stays available only in technical details.
4. The same registry/material code + unit + price source + unit price can collapse into one visible row.
5. Different real material codes stay separate.
6. Distinct operations stay separate.
7. Statuses remain preserved.
8. No prices, markup rules, registry entries, or DB records changed.

## Pricing page linkage summary

### Materials confirmed on `/inventory/pricing`

- `MAT-ACP-FATA-LITERE` -> `PMMA / plexiglas acrilic 3 mm — față litere`
- `MAT-SPATE-PVC-LITERE` -> `PVC expandat 10 mm`
- `MAT-ORACAL-641` -> `Folie autocolantă PVC — Oracal 641 Economy Cal`
- `MAT-ORACAL-651` -> `Folie autocolantă PVC — Oracal 651`
- `MAT-ORACAL-8500` -> `Folie autocolantă PVC — Oracal 8500 Translucent Cal`
- `MAT-VINYL-PRINT` -> `Folie autocolantă PVC — print față litere`
- `MAT-VINYL-PRINT-LAMINATED` -> `Folie autocolantă PVC — print + laminare față litere`
- `MAT-LED-MODULE` -> `Modul LED 12V — backlit`
- `MAT-CONSUMABILE-MONTAJ` -> `Consumabile montaj`

### Service / rate identities confirmed on `/inventory/pricing`

- `CNC_ROUTER` -> `CNC router — tăiere/debitare`
- `LARGE_FORMAT_PRINT` -> `Serviciu print autocolant`
- `LAMINATION` -> `Serviciu laminare print`
- `FACE_VINYL_APPLICATION_LABOR` -> `Manoperă aplicare folie fețe litere`
- `RETURN_PROFILE_FACE_BONDING` -> `Lipire cant profil pe față litere`
- `RETURN_PROFILE_MACHINE_FORMING` -> `Modelare cant profil litere — utilaj`

## Fix summary

- Shared plexiglas is now shown as one visible owner row: `Plexiglas 3 mm`.
- Same-identity cant rows are shown as one visible owner row: `Cant / volum`.
- Fallback forex label is shown as `Forex 10 mm`.
- Fallback edge bonding is shown as `Lipire cant / volum`.
- Role/source wording is preserved only in technical details, where the UI now shows the contributing source rows and codes.
- The logical-list path and fallback material-breakdown path now align on the same visible identity principle.

## Files changed

- [backend/services/intake_v4_material_breakdown_service.py](c:/Users/offic/workos_app_vs/backend/services/intake_v4_material_breakdown_service.py)
- [backend/tests/test_intake_v4_material_breakdown.py](c:/Users/offic/workos_app_vs/backend/tests/test_intake_v4_material_breakdown.py)
- [frontend/src/lib/intakeV6/intakeV4LiveMaterialsUsedDisplay.ts](c:/Users/offic/workos_app_vs/frontend/src/lib/intakeV6/intakeV4LiveMaterialsUsedDisplay.ts)
- [frontend/src/lib/intakeV6/intakeV6LiveMaterialsUsedDisplay.test.ts](c:/Users/offic/workos_app_vs/frontend/src/lib/intakeV6/intakeV6LiveMaterialsUsedDisplay.test.ts)
- [frontend/src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.tsx](c:/Users/offic/workos_app_vs/frontend/src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.tsx)
- [frontend/src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.test.tsx](c:/Users/offic/workos_app_vs/frontend/src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.test.tsx)
- [docs/worklog/realignment/2026-07-07_live_price_rows_inventory_pricing_linkage_v1.md](c:/Users/offic/workos_app_vs/docs/worklog/realignment/2026-07-07_live_price_rows_inventory_pricing_linkage_v1.md)

## Tests run

- `pnpm.cmd -C "c:\Users\offic\workos_app_vs\frontend" exec vitest run src/lib/intakeV6/intakeV6LiveMaterialsUsedDisplay.test.ts src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.test.tsx --reporter=verbose`
  - PASS (`28/28`)
- `cd backend; .\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_material_breakdown.py -q -k "artwork_raw_skips_global_oracal_face_fallback or artwork_oracal_641_adds_logo_specific_vinyl_and_application or artwork_oracal_8500_adds_logo_specific_vinyl_and_application or artwork_print_laminate_adds_logo_specific_rows or artwork_finish_totals_are_additive_relative_to_raw"`
  - PASS (`5 passed`)
- `git diff --check`
  - PASS

## Runtime UI verification

### A. `cerc100cm.svg`

- Route used: `/intake-v6/IR-MRAUMOXT/operator`
- `Calcul live — detalii` opened successfully
- Visible rows confirmed:
  - `Plexiglas 3 mm`
  - `Cant / volum`
  - no `Plexiglas 3 mm / fata litere`
  - no `Plexiglas 3 mm / embleme/logo`
- Logo-only visible plexiglas row showed one generic identity instead of a role-split pair.

### B. `gradi-curat.svg`

- Route used: `/intake-v6/IR-MR2MP11C/operator`
- Visible rows confirmed in `Calcul live — detalii`:
  - `Plexiglas 3 mm`
  - `Forex 10 mm`
  - `Cant / volum`
  - `Lipire cant / volum`
  - no role-specific plexiglas split rows
  - no role-specific forex wording
  - no `Cant / volum litere + interioare + artwork` in visible mode
- Technical toggle confirmed source split after enabling `Afișează detalii tehnice`.

### C. `/inventory/pricing`

- Verified live-calculation material and service identities are present as real Pricing/Inventory entries or rates.
- No UI-only invented plexiglas/forex/service identity was used as if it were a pricing source.

## Remaining risks

- Technical details currently preserve source context using source-line text and runtime codes; this is sufficient for operator traceability, but a future dedicated canonical `technical_usage` contract could make the data cleaner and less UI-derived.
- Logical-list source rows still retain legacy-rich source labels internally; the owner-facing view now normalizes them correctly.

## Forbidden scope confirmation

- no Pricing Registry rewrite
- no price changes
- no Quote/Order
- no Execution
- no ProductAggregate/TaskGraph/ExecutionPlan
- no DB/seed/migration
- no Logo root activation
- no ACP root activation
- no Image Analyzer runtime edits