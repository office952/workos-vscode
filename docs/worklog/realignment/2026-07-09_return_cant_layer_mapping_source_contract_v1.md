# 2026-07-09 - return cant layer mapping source contract v1

HEAD before:

- `72d7694`

Task:

- `RETURN_CANT_LAYER_MAPPING_SOURCE_CONTRACT_V1`

Mode:

- docs-only / contract-only

Safety gate:

- HEAD confirmed = `72d7694`
- no staged files before work
- `git diff --check` clean before work
- unrelated dirty untracked worktree preserved untouched

Mandatory context read:

- `docs/architecture/product-system/RETURN_CANT_CANONICAL_RUNTIME_CONTAINER_CONTRACT.md`
- `docs/architecture/product-system/RETURN_CANT_COMPONENT_CONFIRMATION_CONTRACT.md`
- `docs/architecture/product-system/RETURN_CANT_CONFIRMED_PERIMETER_SOURCE_CONTRACT.md`
- `docs/qa/return-cant-confirmed-perimeter-source-contract-2026-07-09/RETURN_CANT_CONFIRMED_PERIMETER_SOURCE_CONTRACT_V1.md`
- `docs/worklog/realignment/2026-07-09_return_cant_confirmed_perimeter_source_contract_v1.md`
- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldCaptureReadonlyAdapter.ts`
- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldsReadonlyMapper.ts`
- `frontend/src/lib/intakeV6/productTruth/productTruthDraftBuilder.ts`
- `frontend/src/lib/intakeV6/productTruth/productTruthTypes.ts`
- `frontend/src/lib/intakeV6/useIntakeV6Workspace.ts`
- `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx`
- `backend/services/intake_v6_workspace_service.py`
- relevant tests for layer roles, artwork layers, finish setup, and product truth awareness

Additional focused reads used to close the contract:

- `frontend/src/lib/intakeV6/intakeV4LetterGroups.ts`
- `frontend/src/lib/intakeV6/intakeV4ArtworkFinish.ts`
- `frontend/src/lib/intakeV6/intakeV6LayerRoleBridge.ts`
- `frontend/src/lib/intakeV6/intakeV6LayerRoleOptions.ts`
- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldsReadonlyMapper.test.ts`
- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldCaptureReadonlyAdapter.test.ts`
- `backend/schemas/intake_v4.py`
- `backend/tests/test_letter_group_finish_readiness.py`
- `backend/tests/test_intake_v6_logo_only_readiness.py`

Audit findings:

- `group_key` already exists as a stable row key for `letter_group_finishes[]` and is derived from Step 1 layer keys for face layers.
- `layer_key` already exists as a stable row key for `artwork_finishes[]` and is derived from Step 1 layer keys for artwork/logo layers.
- `layer_role_setup.layers[]` persists `layer_key`, optional `layer_id`, `layer_name`, `auto_role`, `confirmed_role`, and `confirmation_state`.
- readonly adapter currently uses `source_row_key` directly in target paths and warns `LAYER_GROUP_IDS_CAPTURED_AS_ROW_ID_EVIDENCE_ONLY`, which proves current mapping is still evidence-oriented.
- readonly mapper treats `selectedLayerRefs` and confirmed Step 1 keys as `context_only`, not canonical `layer_group_ids` truth.
- Product Truth draft legacy `components.returnCant` carries finish/depth/color evidence, but no canonical per-instance mapping object.
- owner role labels `Vector Litere` and `Vector Logo` are semantic role labels only and cannot serve as final identity keys.

Decision:

- `RETURN_CANT_LAYER_MAPPING_SOURCE_CONTRACT_READY`

Contract summary:

- `source_kind` final values:
  - `letter_group`
  - `artwork_layer`
- `instance_key` final derivation:
  - `letter_group:<group_key>`
  - `artwork_layer:<layer_key>`
- `source_ref` final shape:
  - `group_key?`
  - `layer_key?`
  - `source_label?`
  - `source_role?`
- `layer_group_ids` remains canonical at instance level, not duplicated inside `source_ref`

Rules fixed:

- `group_key` is required for `letter_group`
- `layer_key` is required for `artwork_layer`
- UI labels and unstable names are forbidden as final identity
- no invented fallback key when a stable key is missing
- `layer_group_ids` must represent real layer ids / keys supporting the instance
- `layer_group_ids` is required for `confirmed`
- ambiguous or missing mapping blocks confirmation

Canonical blockers documented:

- `RETURN_CANT_INSTANCE_KEY_MISSING`
- `RETURN_CANT_SOURCE_KIND_MISSING`
- `RETURN_CANT_SOURCE_REF_MISSING`
- `RETURN_CANT_GROUP_KEY_MISSING`
- `RETURN_CANT_LAYER_KEY_MISSING`
- `RETURN_CANT_LAYER_GROUP_IDS_MISSING`
- `RETURN_CANT_LAYER_MAPPING_AMBIGUOUS`
- `RETURN_CANT_LAYER_ROLE_UNSUPPORTED`
- `RETURN_CANT_LAYER_MAPPING_LEGACY_ONLY`

Relationship to confirmation documented:

- missing `instance_key` => `missing` or `blocked`
- missing `source_kind` => `blocked`
- missing `source_ref` => `blocked`
- missing `layer_group_ids` => cannot be `confirmed`
- ambiguous mapping => `blocked`
- only stable mapping + component confirmation + confirmed perimeter can allow `confirmed`

Next-slice decision:

- `RETURN_CANT_PRODUCT_TRUTH_CAPTURE_RUNTIME_BRIDGE_IMPLEMENTATION_PLAN_V1`

Reason:

- stable raw keys already exist;
- the remaining gap is controlled implementation, not missing source fundamentals.

Files created:

- `docs/architecture/product-system/RETURN_CANT_LAYER_MAPPING_SOURCE_CONTRACT.md`
- `docs/qa/return-cant-layer-mapping-source-contract-2026-07-09/RETURN_CANT_LAYER_MAPPING_SOURCE_CONTRACT_V1.md`
- `docs/worklog/realignment/2026-07-09_return_cant_layer_mapping_source_contract_v1.md`

Validation planned:

- `git diff --check`
- docs-only scoped status/diff check
- no tests required because no code touched

Forbidden scope confirmation:

- no UI changes
- no Pricing changes
- no adapter changes
- no Product Truth writer
- no runtime bridge
- no runtime DB writes
- no seed run
- no Quote / Order / Execution
- no ProductAggregate / TaskGraph / ExecutionPlan
- no DB migration