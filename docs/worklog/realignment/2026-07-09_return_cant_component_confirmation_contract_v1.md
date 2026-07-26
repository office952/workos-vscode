# 2026-07-09 - return cant component confirmation contract v1

HEAD before:

- `2068699`

Task:

- `RETURN_CANT_COMPONENT_CONFIRMATION_CONTRACT_V1`

Mode:

- docs-only / contract-only

Safety gate:

- HEAD confirmed = `2068699`
- no staged files before work
- `git diff --check` clean before work
- unrelated dirty untracked worktree preserved untouched

Mandatory context read:

- `docs/architecture/product-system/RETURN_CANT_CANONICAL_RUNTIME_CONTAINER_CONTRACT.md`
- `docs/worklog/realignment/2026-07-09_return_cant_adapter_pricing_targets_final_alignment_v1.md`
- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldCaptureReadonlyAdapter.ts`
- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldsReadonlyMapper.ts`
- `frontend/src/lib/intakeV6/productTruth/productTruthDraftBuilder.ts`
- `frontend/src/lib/intakeV6/productTruth/productTruthTypes.ts`
- `frontend/src/lib/intakeV6/useIntakeV6Workspace.ts`
- `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx`
- `backend/services/intake_v6_workspace_service.py`
- relevant readiness / Product Truth tests reviewed

Audit findings:

- Step 1 confirmation exists via `layer_role_setup.confirmation_status` and per-layer `confirmation_state`.
- Finish setup confirmation exists via `finish_setup.confirmed`.
- Row-level confirmation exists via `letter_group_finishes[].confirmed` and `artwork_finishes[].confirmed`.
- Product composition confirmation exists via `product_composition_confirmed.confirmed`.
- Internal draft quote confirmation exists via `finish_setup.internal_draft_quote_confirmed`.
- Product Truth draft builder and readonly mapper already distinguish `confirmed`, `hydrated`, `fallback`, `blocked`, but there is still no canonical runtime field for `components.return_cant.instances.<instance_key>.confirmation_state`.

Decision:

- `RETURN_CANT_COMPONENT_CONFIRMATION_CONTRACT_READY`

Contract summary:

- final runtime field: `components.return_cant.instances.<instance_key>.confirmation_state`
- final values:
  - `missing`
  - `draft`
  - `blocked`
  - `confirmed`
- optional companion field: `confirmation_source`
- allowed final confirmation sources:
  - `operator_component_confirmation`
  - `system_migration_verified`
  - `imported_verified_truth`
- forbidden as final confirmation source:
  - `step1_layer_confirmation`
  - `finish_setup_confirmation`
  - `row_confirmation`
  - `analyzer_evidence`

Signals that cannot set `confirmed` by themselves:

- Step 1 confirmed
- layer role selected
- `finish_setup.confirmed`
- row confirmed
- Oracal selected
- RAL selected
- stock color selected
- pricing keys present
- analyzer perimeter present
- `quote_geometry.letter_perimeter_m`
- product composition confirmed
- internal draft quote confirmed

Required conditions for `confirmed`:

- stable `instance_key`
- valid `source_kind`
- valid `source_ref`
- valid `layer_group_ids` or equivalent final mapping
- valid `material_profile.width_mm`
- valid `finish_variant.type`
- required pricing keys present for the selected variant
- valid `geometry.confirmed_perimeter_m`
- explicit component confirmation action
- allowed `confirmation_source`
- no active blockers

Canonical blockers documented:

- `RETURN_CANT_INSTANCE_KEY_MISSING`
- `RETURN_CANT_SOURCE_KIND_MISSING`
- `RETURN_CANT_SOURCE_REF_MISSING`
- `RETURN_CANT_LAYER_MAPPING_MISSING`
- `RETURN_CANT_PROFILE_WIDTH_MISSING`
- `RETURN_CANT_FINISH_VARIANT_INCOMPLETE`
- `RETURN_CANT_PRICING_KEYS_MISSING`
- `RETURN_CANT_CONFIRMED_PERIMETER_MISSING`
- `RETURN_CANT_COMPONENT_CONFIRMATION_MISSING`
- `RETURN_CANT_GEOMETRY_EVIDENCE_ONLY`
- `RETURN_CANT_LEGACY_PATH_ONLY`

Files created:

- `docs/architecture/product-system/RETURN_CANT_COMPONENT_CONFIRMATION_CONTRACT.md`
- `docs/qa/return-cant-component-confirmation-contract-2026-07-09/RETURN_CANT_COMPONENT_CONFIRMATION_CONTRACT_V1.md`
- `docs/worklog/realignment/2026-07-09_return_cant_component_confirmation_contract_v1.md`

Validation planned:

- `git diff --check`
- docs-only scoped status check
- no tests required because no code touched

Forbidden scope confirmation:

- no UI changes
- no Pricing changes
- no adapter changes
- no Product Truth writer
- no runtime bridge
- no runtime DB writes
- no seed run
- no Quote/Order/Execution
- no ProductAggregate/TaskGraph/ExecutionPlan
- no DB migration

Next recommended prompt:

- `RETURN_CANT_CONFIRMED_PERIMETER_SOURCE_CONTRACT_V1`