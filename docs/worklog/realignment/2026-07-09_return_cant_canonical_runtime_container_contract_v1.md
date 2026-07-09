# 2026-07-09 - return cant canonical runtime container contract v1

HEAD before:

- `7ac67fe`

Task:

- `RETURN_CANT_CANONICAL_RUNTIME_CONTAINER_CONTRACT_V1`

Files read:

- `docs/architecture/product-system/RETURN_CANT_PRODUCT_TRUTH_BRIDGE_BLOCKER_ALIGNMENT_PLAN.md`
- `docs/qa/return-cant-product-truth-bridge-blocker-alignment-plan-2026-07-09/RETURN_CANT_PRODUCT_TRUTH_BRIDGE_BLOCKER_ALIGNMENT_PLAN_V1.md`
- `docs/worklog/realignment/2026-07-09_return_cant_product_truth_bridge_blocker_alignment_plan_v1.md`
- `docs/architecture/product-system/RETURN_CANT_PRODUCT_TRUTH_CAPTURE_RUNTIME_BRIDGE_PLAN.md`
- `frontend/src/lib/intakeV6/productTruth/productTruthDraftBuilder.ts`
- `frontend/src/lib/intakeV6/productTruth/productTruthTypes.ts`
- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldCaptureReadonlyAdapter.ts`
- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldsReadonlyMapper.ts`
- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldCaptureReadonlyAdapter.test.ts`
- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldsReadonlyMapper.test.ts`
- `frontend/src/lib/intakeV6/productTruth/productTruthDraftBuilder.test.ts`
- `backend/services/form_system_contract_backbone_service.py`
- `backend/services/intake_v6_workspace_service.py`
- `backend/tests/test_form_system_contract_backbone.py`
- `backend/tests/test_letter_group_finish_readiness.py`

Files touched:

- `docs/architecture/product-system/RETURN_CANT_CANONICAL_RUNTIME_CONTAINER_CONTRACT.md`
- `docs/qa/return-cant-canonical-runtime-container-contract-2026-07-09/RETURN_CANT_CANONICAL_RUNTIME_CONTAINER_CONTRACT_V1.md`
- `docs/worklog/realignment/2026-07-09_return_cant_canonical_runtime_container_contract_v1.md`

Decision:

- `RETURN_CANT_CANONICAL_RUNTIME_CONTAINER_CONTRACT_READY`

Main findings:

1. canonical final target stays `components.return_cant`, not `components.returnCant` and not `components.return.*`;
2. `instance_key` must be stable and prefixed by source kind:
   - `letter_group:<group_key>`
   - `artwork_layer:<layer_key>`;
3. `layer_group_ids` belongs to the instance root, not inside `source_ref`, because readonly target paths already point there;
4. `material_profile` should stay structural only and must not duplicate Pricing ownership;
5. `quote_geometry.letter_perimeter_m` remains evidence only and cannot unlock confirmed geometry;
6. current builder and backbone paths are legacy/transitional evidence and require compatibility discipline, but they do not block fixing the final container contract now.

Readiness / contract notes:

1. instance rows may exist in `draft` or `blocked` before confirmation semantics are fully closed;
2. missing `group_key` / `layer_key` means no synthetic `instance_key` is allowed;
3. Step 1 confirmation, row confirmation and `finish_setup.confirmed` remain non-equivalent to component truth confirmation;
4. final pricing refs stay under `pricing_keys.*`, not duplicated elsewhere.

Next recommended slice:

- `RETURN_CANT_ADAPTER_PRICING_TARGETS_FINAL_ALIGNMENT_V1`

Reason:

- after the target shape is fixed, the closest high-signal mismatch is still the readonly adapter's legacy Pricing targets;
- adapter paths are already near the final model and can be aligned without writing runtime truth;
- builder/backbone compatibility remains important, but not more urgent than removing known legacy pricing target aliases from the readonly contract layer.

Validation run:

- read-only audit only
- `git diff --check`
- docs-only diff expected

Next recommended prompt:

- `RETURN_CANT_ADAPTER_PRICING_TARGETS_FINAL_ALIGNMENT_V1`# 2026-07-09 - return cant canonical runtime container contract v1

HEAD before:

- `7ac67fe`

Task:

- `RETURN_CANT_CANONICAL_RUNTIME_CONTAINER_CONTRACT_V1`

Files read:

- `docs/architecture/product-system/RETURN_CANT_PRODUCT_TRUTH_BRIDGE_BLOCKER_ALIGNMENT_PLAN.md`
- `docs/qa/return-cant-product-truth-bridge-blocker-alignment-plan-2026-07-09/RETURN_CANT_PRODUCT_TRUTH_BRIDGE_BLOCKER_ALIGNMENT_PLAN_V1.md`
- `docs/worklog/realignment/2026-07-09_return_cant_product_truth_bridge_blocker_alignment_plan_v1.md`
- `docs/architecture/product-system/RETURN_CANT_PRODUCT_TRUTH_CAPTURE_RUNTIME_BRIDGE_PLAN.md`
- `frontend/src/lib/intakeV6/productTruth/productTruthDraftBuilder.ts`
- `frontend/src/lib/intakeV6/productTruth/productTruthTypes.ts`
- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldCaptureReadonlyAdapter.ts`
- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldsReadonlyMapper.ts`
- `backend/services/form_system_contract_backbone_service.py`
- `backend/services/intake_v6_workspace_service.py`
- selected frontend/backend tests around Product Truth, form system backbone, letter group finish readiness

Files touched:

- `docs/architecture/product-system/RETURN_CANT_CANONICAL_RUNTIME_CONTAINER_CONTRACT.md`
- `docs/qa/return-cant-canonical-runtime-container-contract-2026-07-09/RETURN_CANT_CANONICAL_RUNTIME_CONTAINER_CONTRACT_V1.md`
- `docs/worklog/realignment/2026-07-09_return_cant_canonical_runtime_container_contract_v1.md`

Decision:

- `RETURN_CANT_CANONICAL_RUNTIME_CONTAINER_CONTRACT_READY`

Main findings:

1. canonical target shape-ul poate fi definit acum pe `components.return_cant.instances.<instance_key>`;
2. `components.returnCant` si `components.return.*` trebuie ramase explicit legacy only;
3. `layer_group_ids` trebuie field top-level per instance, nu doar source metadata nested;
4. pricing keys trebuie centralizate sub `pricing_keys.*`, fara dublare in `material_profile`;
5. `quote_geometry.letter_perimeter_m` ramane evidence-only si nu poate promova singur `confirmed_perimeter_m`;
6. dupa fixarea acestui contract, urmatorul slice cel mai mic si util ramane alinierea readonly adapterului la key-urile finale de pricing.

Validation run:

- read-only audit only
- docs-only diff validation pending commit
- `git diff --check`

Next recommended prompt:

- `RETURN_CANT_ADAPTER_PRICING_TARGETS_FINAL_ALIGNMENT_V1`