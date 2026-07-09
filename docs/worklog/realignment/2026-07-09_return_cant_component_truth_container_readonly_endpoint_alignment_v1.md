# RETURN_CANT_COMPONENT_TRUTH_CONTAINER_READONLY_ENDPOINT_ALIGNMENT_V1

## Scope

- Read-only only.
- No delete.
- No Pricing.
- No ProductDefinition.
- No Product Truth writer.
- No ProductAggregate runtime write.
- No LOGO activation.
- No DB migration.
- No live seed.

## HEAD before

- `9077b09`

## Files read

- `docs/worklog/realignment/2026-07-09_return_cant_component_truth_container_readonly_alignment_v1.md`
- `docs/worklog/realignment/2026-07-09_product_component_composition_read_model_alignment_v1.md`
- `docs/worklog/realignment/2026-07-09_product_component_composition_contract_v1.md`
- `docs/worklog/realignment/2026-07-09_return_cant_component_source_path_alignment_readonly_v1.md`
- `docs/architecture/product-system/RETURN_CANT_COMPONENT_CONFIRMATION_CONTRACT.md`
- `docs/architecture/product-system/PRODUCT_SYSTEM_COMPONENT_OWNED_CALCULATION_BOUNDARY.md`
- `frontend/src/pages/ProductSystem.tsx`
- `frontend/src/pages/ProductSystem.badges.test.tsx`
- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldsReadonlyMapper.ts`
- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldCaptureReadonlyAdapter.ts`
- `backend/data/mini_module_registry_volumetric_v2.py`
- `backend/data/shared_volumetric_component_contracts.py`
- `backend/services/product_aggregate_service.py`
- `backend/services/product_template_availability_service.py`
- `backend/services/intake_v6_modular_form_contract_service.py`

## Files touched

- `frontend/src/features/product-system/returnCantReadonlyContainerModel.ts`
- `frontend/src/pages/ProductSystem.tsx`
- `frontend/src/pages/ProductSystem.badges.test.tsx`
- `docs/worklog/realignment/2026-07-09_return_cant_component_truth_container_readonly_endpoint_alignment_v1.md`

## Source ownership audit

### Does UI build the model directly today?

Before this slice, effectively yes: the Return/Cant truth container explanation lived inline in `ProductSystem.tsx`.

### Is the readonly mapper sufficient?

Partially.

- `returnCantTruthFieldsReadonlyMapper.ts` already defines canonical readonly field language and blockers.
- `returnCantTruthFieldCaptureReadonlyAdapter.ts` already defines target paths under `components.return_cant.instances.*` and the notion of per-instance capture.

But neither was being consumed as one stable Product System source for the container explanation.

### Is there already enough backend read-only service / endpoint?

No stable dedicated backend source exists specifically for this Product System panel.

- ProductAggregate is too broad and is explicitly read model only.
- modular form contract gives fields, not the full return/cant truth container model.
- adding a new backend endpoint now would duplicate readonly language without solving missing runtime truth.

### Does ProductAggregate expose something reusable?

Only partially.

It exposes component presence, provenance, linked module traces, and support diagnostics, but it must not be treated as canonical source of truth for `return_cant` container semantics.

### Where was language duplicated?

- inline UI arrays in `ProductSystem.tsx`
- readonly mapper field language
- readonly adapter target path language
- docs/worklogs

### Conclusion

The duplication problem was mostly frontend-side readonly explanation drift, not missing backend mutation/runtime infrastructure. The smallest correct fix is a shared frontend helper that centralizes the return/cant readonly container model.

## RETURN_CANT_READONLY_CONTAINER_MODEL

Implemented stable readonly model shape:

- `componentKey`
- `targetContainerPath`
- `legacyAliasPaths`
- `upstreamDependencies`
- `sourceTypeRows`
- `blockers`
- `readiness`
- `productAggregateBoundaryNote`
- `missingTruthFields`

This model is now built in:

- `frontend/src/features/product-system/returnCantReadonlyContainerModel.ts`

Current target container remains:

```text
components.return_cant.instances[]
```

## Implementation level decision

Decision:

`frontend helper only`

Reason:

- existing readonly frontend mappers already define the canonical language
- Product System needed a stable shared source, not a new backend endpoint
- backend endpoint now would mostly duplicate readonly explanation without adding real new truth
- this keeps the slice strictly read-only and avoids premature backend surface expansion

## Endpoint/helper decision

- frontend helper only: YES
- backend read-only service: NO
- backend read-only endpoint: NO
- docs-only blocked: NO

## UI changes

- Added a stable shared helper:
  - `frontend/src/features/product-system/returnCantReadonlyContainerModel.ts`
- `ProductSystem.tsx` now consumes that helper for the Return/Cant truth container section.
- The panel still shows:
  - target container `components.return_cant.instances[]`
  - FACE dependency `components.face.confirmed_perimeter`
  - legacy alias note for `components.returnCant.*`
  - source type table
  - blocked readiness
  - ProductAggregate read-model disclaimer

No new UI mutation, button, or runtime write behavior was added.

## Screenshot paths

- `docs/worklog/realignment/assets/2026-07-09_return_cant_component_truth_container_readonly_endpoint_alignment_v1/product_system_letters_context.png`
- `docs/worklog/realignment/assets/2026-07-09_return_cant_component_truth_container_readonly_endpoint_alignment_v1/product_system_return_cant_truth_container.png`
- `docs/worklog/realignment/assets/2026-07-09_return_cant_component_truth_container_readonly_endpoint_alignment_v1/product_system_face_to_return_cant_dependency.png`
- `docs/worklog/realignment/assets/2026-07-09_return_cant_component_truth_container_readonly_endpoint_alignment_v1/product_system_return_cant_legacy_alias_and_missing_fields.png`

## Tests run

```powershell
Set-Location C:\Users\offic\workos_app_vs\frontend
npm.cmd run test -- src/pages/ProductSystem.badges.test.tsx
```

Result:

- `4 passed`

## Blockers

- `source_face_perimeter_ref` still missing
- `confirmed_perimeter_m` still missing on return/cant instance
- `material_profile` still missing as explicit truth field
- `layer_group_ids` still missing as explicit truth field
- `confirmation_state` still missing as explicit truth field
- root geometry context still exists as explanatory fallback

## Recommendation

1. Next step should stay readonly or migration-planning oriented.
2. If a backend surface is introduced later, it should only happen once there is a clear need to share one canonical readonly container model outside Product System.
3. For now, the helper-backed model is enough and avoids premature endpoint growth.

## Forbidden scope confirmation

- no delete performed
- no seed modified
- no DB migration
- no seed live
- no Pricing
- no ProductDefinition
- no Product Truth writer change
- no UI mutation beyond readonly clarification
- no ProductAggregate runtime write
- no LOGO activation

## Next recommended prompt

```text
TASK — RETURN_CANT_COMPONENT_TRUTH_CONTAINER_MIGRATION_PLAN_V1
```

Suggested scope:

- docs and migration planning only
- define how `material_profile`, `source_face_perimeter_ref`, `confirmed_perimeter_m`, `layer_group_ids`, and `confirmation_state` move from explanatory/read-only gaps to real component-owned truth fields
- no write implementation yet
- no delete
- no Pricing
- no ProductDefinition
