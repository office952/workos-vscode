# 2026-07-09 - return cant adapter pricing targets final alignment v1

HEAD before:

- `e7f891a`

Task:

- `RETURN_CANT_ADAPTER_PRICING_TARGETS_FINAL_ALIGNMENT_V1`

Decision:

- `RETURN_CANT_ADAPTER_PRICING_TARGETS_FINAL_ALIGNMENT_PASS`

Scope:

- align readonly `return_cant` adapter pricing target references to the final confirmed runtime keys;
- keep the adapter read-only / diagnostic / evidence-only;
- do not modify Product Truth write paths or runtime storage.

Mandatory context read:

- `docs/qa/return-cant-pricing-ui-runtime-recheck-2026-07-09/RETURN_CANT_PRICING_UI_RUNTIME_RECHECK_V1.md`
- `docs/worklog/realignment/2026-07-09_return_cant_pricing_ui_runtime_recheck_v1.md`
- `docs/architecture/product-system/RETURN_CANT_CANONICAL_RUNTIME_CONTAINER_CONTRACT.md`
- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldCaptureReadonlyAdapter.ts`
- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldCaptureReadonlyAdapter.test.ts`
- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldsReadonlyMapper.ts`
- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldsReadonlyMapper.test.ts`
- `frontend/src/lib/intakeV6/productTruth/productTruthTypes.ts`

Legacy targets found in adapter/test scope:

- `return_cant_vinyl_application_labor`
- `ral_paint_material_<width>mm`
- `ral_paint_application_labor`
- alignment-only blocker semantics tied to these transitional targets

Final targets applied:

- `RETURN_CANT_VINYL_APPLICATION_LABOR`
- `RETURN_CANT_RAL_PAINT_LABOR`
- `MAT-VOPSEA-RAL-CANT-30MM`
- `MAT-VOPSEA-RAL-CANT-60MM`
- `MAT-VOPSEA-RAL-CANT-80MM`
- `MAT-VOPSEA-RAL-CANT-100MM`

Implementation notes:

- added explicit depth-to-RAL-paint material key map in the readonly adapter;
- default readonly pricing evidence now reflects the accepted runtime baseline confirmed in the prior recheck;
- readonly pricing slots now emit the final runtime pricing keys instead of legacy lowercase placeholders;
- vinyl and RAL slots now report `present` or `missing` against required runtime pricing refs;
- adapter remains `blocked` when required pricing refs are explicitly missing from evidence;
- mapper file was reviewed but did not require a change for this slice.

Files modified:

- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldCaptureReadonlyAdapter.ts`
- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldCaptureReadonlyAdapter.test.ts`
- `docs/worklog/realignment/2026-07-09_return_cant_adapter_pricing_targets_final_alignment_v1.md`

Files reviewed but not modified:

- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldsReadonlyMapper.ts`
- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldsReadonlyMapper.test.ts`
- `frontend/src/lib/intakeV6/productTruth/productTruthTypes.ts`

Tests run:

```powershell
cd frontend
npm.cmd exec --yes pnpm@8.10.0 exec vitest run src/lib/intakeV6/productTruth/returnCantTruthFieldCaptureReadonlyAdapter.test.ts src/lib/intakeV6/productTruth/returnCantTruthFieldsReadonlyMapper.test.ts src/lib/intakeV6/productTruth/productTruthDraftBuilder.test.ts

npm.cmd exec --yes pnpm@8.10.0 exec vitest run src/lib/intakeV6/productTruth/returnCantTruthFieldCaptureReadonlyAdapter.test.ts
```

Results:

- `3` files passed
- `40` tests passed
- rerun after final cleanup: adapter suite `8/8` passed

Legacy targets removed:

- `return_cant_vinyl_application_labor`
- `ral_paint_material_<width>mm`
- `ral_paint_application_labor`

Legacy targets retained intentionally:

- none in the readonly adapter pricing slot mapping logic;
- legacy Product Truth writer shape `components.returnCant` remains untouched by scope.

Forbidden scope confirmation:

- no Pricing values changed
- no Pricing UI changes
- no seed run
- no runtime DB writes
- no Product Truth writer
- no runtime bridge
- no Intake UI visual changes
- no Quote/Order/Execution
- no ProductAggregate/TaskGraph/ExecutionPlan
- no DB migration

Next recommended prompt:

- `RETURN_CANT_COMPONENT_CONFIRMATION_CONTRACT_V1`