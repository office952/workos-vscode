# Intake V6 vector catalog and print/laminate service alignment

## Task
- Repair and align Intake V6 / Quote summary cataloging for volumetric letters.
- Keep existing UI structure.
- Avoid hardcoded redesign and avoid aggressive pricing logic changes.
- Show operator-friendly labels `Vector Litere` and `Vector Atipic`.
- Stop surfacing `artwork` and `pseudo:*` as the main operator/client-facing titles.
- Separate print / lamination materials from print / lamination / application services.
- Reuse existing registry/configuration paths where available.
- No DB migration or seed.

## Owner direction checkpoint
- Intake V6 remains the entry point.
- SVG Analyzer suggests, operator confirms, Product Truth stays canonical.
- This slice does not expand into execution materialization or broader product-system remodeling.
- The work stays aligned with the modular product direction by changing vocabulary and breakdown semantics at the owning mapping/building layers, not by adding one-off UI strings in random surfaces.

## Audit findings
- Operator-facing V6 surfaces still exposed legacy naming such as `artwork` in places where owner wording requires `Vector Atipic`.
- Layer role mapping still surfaced technical role semantics instead of operator-friendly naming for letters/artwork.
- Breakdown rows mixed material and service concepts for print/lamination flows.
- Some flows emitted print-related rows without a matching application service.
- Targeted backend tests for this area were partially blocked by a stale shared fixture template code, causing `template_out_of_scope` before the exercised logic ran.
- Frontend Vitest execution is currently blocked by repo-level alias resolution for several `@/...` imports before test collection starts.
- Frontend root `build` and `typecheck` scripts also fail from repo-root because they expect a different app root (`index.html` and `tsconfig.json` not found at repo root).

## Implementation summary
- Updated layer role label overrides so operator-facing surfaces use `Vector Litere` and `Vector Atipic` while preserving technical keys.
- Updated Review / Confirm / operator summary wording so `artwork` is no longer the primary visible category title in the touched Intake V6 slices.
- Updated artwork finish section wording and confirmation copy to use `Vector Atipic`.
- Split print and lamination materials into separate breakdown material rows.
- Split print, lamination, and application into separate service rows.
- Added/retained owner fallback service rates for m2-based print/lamination/application service rows when registry pricing is missing.
- Added application-service emission for plain face vinyl letter flows and `vinyl_only` artwork flows.
- Updated live technical breakdown display labels and row filters to reflect the separated catalog.
- Aligned the backend test helper fixture with the current pilot template code so targeted validations can hit the changed logic.

## Files touched
- `frontend/src/lib/intakeV6/intakeV4LayerRoleOptions.ts`
- `frontend/src/components/workos/intake-v6/IntakeV6ArtworkFinishSection.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ReviewLetterGroupsSection.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ConfirmOperationalSummary.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6OperatorWorkSummary.tsx`
- `frontend/src/lib/intakeV6/intakeV4LiveMaterialsUsedDisplay.ts`
- `frontend/src/lib/intakeV6/intakeV6LiveCalculationRowFilters.ts`
- `backend/services/intake_v4_artwork_complexity_service.py`
- `backend/services/intake_v4_material_breakdown_service.py`
- `backend/tests/test_intake_v4_material_breakdown.py`
- `frontend/src/components/workos/intake-v6/IntakeV6ArtworkFinishSection.test.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6LayersRoleTable.test.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.test.tsx`

## Validation run
### Passed
- Static diagnostics on touched production files: no errors.
- Backend targeted pytest:
  - `test_print_laminate_rows_when_face_finish_print`
  - `test_printed_vinyl_skips_laminate_material_but_keeps_application_service`
  - `test_operation_price_falls_back_to_owner_service_rate_for_m2_rows`
- Quote live UI verification still shows corrected VAT display: `TVA (21%)`.

### Blocked / partial
- Frontend Vitest for touched suites fails before collection because repo alias imports do not resolve in current test harness:
  - `@/lib/intakeV6/intakeV6ReturnCantBridge`
  - `@/lib/intakeV6/intakeV6LayerRoleOptions`
  - `@/lib/intakeV6/intakeV6FaceBackPrepCostDraftDisplay`
- `pnpm.cmd build` from repo root fails because repo root is not the app root for Vite: missing `index.html`.
- `pnpm.cmd typecheck` from repo root fails because repo root lacks `tsconfig.json`.
- Live browser toggles for some collapsible panels were not interactable through automation despite the routes loading; therefore visual verification is partial and route-level.

## Exact visual verification steps
1. Open `/intake-v6/IR-MR2MP11C/operator`.
2. Move to Review and Confirm surfaces.
3. Confirm the operator-facing category wording uses `Vector Litere` and `Vector Atipic` in the touched cards/summaries.
4. Confirm `artwork` is not the primary visible title for those touched operator-facing sections.
5. Confirm no `pseudo:*` label is shown as the main visible title in those same sections.
6. Open `/quotes/Q-V6-IV6-930BCFCD-1782997881`.
7. Confirm quote totals still show `TVA (21%)`.
8. Expand `Breakdown tehnic live Intake V6`.
9. Confirm the technical breakdown includes separated rows for:
   - `Material print Orafol`
   - `Material laminare Orafol`
   - `Serviciu print`
   - `Serviciu laminare X-PRO`
   - `Serviciu aplicare`
10. Confirm these appear as distinct technical rows, not merged into a single print/lamination line.

## Known gaps / risks
- Frontend automated tests are currently not a trustworthy gate for this slice until alias resolution is repaired in the repo test harness.
- Repo-root build/typecheck scripts are not scoped to the actual frontend app root, so they do not currently validate this UI slice.
- Live browser automation could load the pages and confirm route-level data, but panel expansion interactions timed out, so row-level live UI confirmation remains manual.

## Next safe step
- Repair the frontend test/build invocation path so UI slices can be validated from CI-style commands at the correct app root without relying on manual browser inspection.
