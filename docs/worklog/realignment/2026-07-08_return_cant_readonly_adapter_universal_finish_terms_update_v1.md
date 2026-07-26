# 2026-07-08 - return cant readonly adapter universal finish terms update v1

HEAD before:

- `515efb4`

HEAD after:

- pending at write time

Task:

- `RETURN_CANT_READONLY_ADAPTER_UNIVERSAL_FINISH_TERMS_UPDATE_V1`

Files touched:

- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldCaptureReadonlyAdapter.ts`
- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldCaptureReadonlyAdapter.test.ts`
- `docs/worklog/realignment/2026-07-08_return_cant_readonly_adapter_universal_finish_terms_update_v1.md`

Reason for update:

1. adapterul readonly folosea inca semantica tranzitorie `oracal` / `ral_paint`;
2. boundary-ul final cere termenii universali `stock_color | vinyl_application | paint_application`;
3. contractul readonly trebuia aliniat fara UI changes, Pricing mutations sau DB work.

Semantic changes applied:

1. `oracal` a fost migrat la `vinyl_application`.
2. `ral_paint` a fost migrat la `paint_application`.
3. `stock_color` a ramas neschimbat si expune user-facing label `Culoare Stoc`.
4. adapterul expune acum nested fields `finish_variant.vinyl.*` si `finish_variant.paint.*` prin `target_paths` si payloadul readonly.
5. slotul vechi `finish_extra` a fost inlocuit cu sloturi declarative:
   - `pricing_keys.vinyl_material`
   - `pricing_keys.vinyl_application_labor`
   - `pricing_keys.ral_paint_material_by_width`
   - `pricing_keys.ral_paint_labor`
6. formulele readonly au fost facute explicite:
   - vinyl material quantity = `perimetru_ml x latime_cant_m`
   - vinyl labor quantity = `perimetru_ml`
   - paint material quantity = `pricing_target_by_width`
   - paint labor quantity = `perimetru_ml`

Remaining blockers retained honestly:

1. current live return/cant runtime is still direct-input `Oracal 651` only;
2. `Oracal 641` is represented as reusable contract support, but not directly expressible from the current Intake V6 bridge/runtime rows without UI/runtime follow-up;
3. cant vinyl labor and width-aware RAL pricing rows remain alignment targets, not proven live runtime ownership.

Forbidden scope confirmation:

- no UI changes
- no Pricing changes
- no DB / seed / migration
- no Product Truth writes
- no Quote / Order / Execution changes

Validation run:

- `git diff --check`
- `npx.cmd --yes pnpm@8.10.0 exec vitest run src/lib/intakeV6/productTruth/returnCantTruthFieldCaptureReadonlyAdapter.test.ts`
- result: `1` test file passed, `6` tests passed

Next recommended prompt:

- `RETURN_CANT_RUNTIME_AND_UI_VINYL_SERIES_EXPANSION_V1`