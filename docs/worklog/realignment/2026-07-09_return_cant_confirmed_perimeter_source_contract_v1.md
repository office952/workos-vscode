# 2026-07-09 - return cant confirmed perimeter source contract v1

HEAD before:

- `f3d1a88`

Task:

- `RETURN_CANT_CONFIRMED_PERIMETER_SOURCE_CONTRACT_V1`

Mode:

- docs-only / contract-only

Safety gate:

- HEAD confirmed = `f3d1a88`
- no staged files before work
- `git diff --check` clean before work
- unrelated dirty untracked worktree preserved untouched

Mandatory context read:

- `docs/architecture/product-system/RETURN_CANT_CANONICAL_RUNTIME_CONTAINER_CONTRACT.md`
- `docs/architecture/product-system/RETURN_CANT_COMPONENT_CONFIRMATION_CONTRACT.md`
- `docs/qa/return-cant-component-confirmation-contract-2026-07-09/RETURN_CANT_COMPONENT_CONFIRMATION_CONTRACT_V1.md`
- `docs/worklog/realignment/2026-07-09_return_cant_component_confirmation_contract_v1.md`
- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldCaptureReadonlyAdapter.ts`
- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldsReadonlyMapper.ts`
- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldsReadonlyMapper.test.ts`
- `frontend/src/lib/intakeV6/productTruth/productTruthDraftBuilder.ts`
- `frontend/src/lib/intakeV6/productTruth/productTruthTypes.ts`
- `frontend/src/lib/intakeV6/useIntakeV6Workspace.ts`
- `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx`
- `frontend/src/lib/intakeV6/intakeV6QuoteGeometry.ts`
- `frontend/src/lib/intakeV6/intakeV6QuoteGeometry.test.ts`
- `backend/services/intake_v6_workspace_service.py`
- focused geometry/perimeter grep results across frontend/backend

Audit findings:

- `quote_geometry.letter_perimeter_m` is produced from analyzer/path geometry flows and reused in multiple display/commercial contexts.
- readonly mapper treats `quote_geometry.letter_perimeter_m` as `context_only`, blocked, and not as confirmed dependency.
- readonly adapter emits geometry-context warnings and `RETURN_CANT_DEPENDENCY_FACE_GEOMETRY_UNCONFIRMED`.
- generic Product Truth draft geometry contains `returnMaterialPerimeterMl` and generic `confirmed`, but not canonical `return_cant` confirmed perimeter truth.
- Review/UI computes operator perimeter displays and diagnostics, but no runtime writer exists for canonical per-instance confirmed perimeter.
- current code has a separate `components.face.confirmed_perimeter` dependency model, but not a final contract for `components.return_cant.instances.<instance_key>.geometry.confirmed_perimeter_m`.
- mapper warnings `SELECTED_LAYER_REFS_NOT_MAPPED_TO_RETURN_CANT` and `LAYER_CONFIRMATION_EXISTS_BUT_COMPONENT_MAPPING_MISSING` show that layer/source mapping remains incomplete.

Decision:

- `RETURN_CANT_CONFIRMED_PERIMETER_SOURCE_CONTRACT_READY`

Contract summary:

- final field in scope: `components.return_cant.instances.<instance_key>.geometry.confirmed_perimeter_m`
- canonical geometry shape includes:
  - `perimeter_source`
  - `evidence_perimeter_m`
  - `confirmed_perimeter_m`
  - `confirmed_perimeter_source`
  - `confirmed_perimeter_at`
  - `confirmed_by`
  - `blockers`
- allowed confirmed sources:
  - `operator_confirmed`
  - `imported_verified_truth`
  - `system_migration_verified`
- forbidden confirmed sources:
  - raw analyzer output
  - raw `quote_geometry.letter_perimeter_m`
  - layer geometry evidence
  - Step 1 confirmed
  - layer role selected
  - `finish_setup.confirmed`
  - row confirmed
  - pricing keys present
  - product composition confirmed

Required rules documented:

- `quote_geometry.letter_perimeter_m` can populate only `evidence_perimeter_m`
- quote geometry forces `perimeter_source = evidence_only`
- quote geometry cannot populate `confirmed_perimeter_m`
- quote geometry cannot set component `confirmation_state = confirmed`
- confirmed perimeter must be finite, positive, meters, instance-bound, and layer/source mapped
- confirmed perimeter cannot be auto-copied from evidence without explicit confirmation or verified provenance
- evidence/confirmed divergence over approved tolerance requires `RETURN_CANT_PERIMETER_EVIDENCE_CONFLICT`

Canonical blockers documented:

- `RETURN_CANT_CONFIRMED_PERIMETER_MISSING`
- `RETURN_CANT_PERIMETER_EVIDENCE_ONLY`
- `RETURN_CANT_PERIMETER_CONFIRMATION_MISSING`
- `RETURN_CANT_PERIMETER_SOURCE_INVALID`
- `RETURN_CANT_PERIMETER_UNIT_INVALID`
- `RETURN_CANT_PERIMETER_NON_POSITIVE`
- `RETURN_CANT_PERIMETER_INSTANCE_MISMATCH`
- `RETURN_CANT_PERIMETER_LAYER_MAPPING_MISSING`
- `RETURN_CANT_PERIMETER_EVIDENCE_CONFLICT`

Relationship to component confirmation documented:

- no component `confirmed` without valid `confirmed_perimeter_m`
- evidence-only perimeter stays blocked
- confirmed perimeter without component confirmation stays `draft` or `blocked`
- component confirmation without confirmed perimeter stays blocked

Next-slice decision:

- `RETURN_CANT_LAYER_MAPPING_SOURCE_CONTRACT_V1`

Reason:

- perimeter-source semantics are now clear enough;
- the remaining blocker before any writer plan is canonical mapping of `instance_key`, `layer_group_ids`, and `source_ref`.

Files created:

- `docs/architecture/product-system/RETURN_CANT_CONFIRMED_PERIMETER_SOURCE_CONTRACT.md`
- `docs/qa/return-cant-confirmed-perimeter-source-contract-2026-07-09/RETURN_CANT_CONFIRMED_PERIMETER_SOURCE_CONTRACT_V1.md`
- `docs/worklog/realignment/2026-07-09_return_cant_confirmed_perimeter_source_contract_v1.md`

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