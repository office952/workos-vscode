# RETURN_CANT_SOURCE_FACE_PERIMETER_REF_READONLY_SLICE_V1

## Scope

- First return/cant migration slice only.
- Read-only only.
- No confirmed_perimeter_m migration.
- No material_profile migration.
- No layer_group_ids migration.
- No confirmation_state migration.
- No delete.
- No Pricing.
- No ProductDefinition.
- No Product Truth writer.
- No ProductAggregate runtime write.
- No LOGO activation.

## HEAD before

- `3ab4b83`

## Files read

- `docs/worklog/realignment/2026-07-09_return_cant_component_truth_container_migration_plan_v1.md`
- `docs/worklog/realignment/2026-07-09_return_cant_component_truth_container_readonly_endpoint_alignment_v1.md`
- `docs/worklog/realignment/2026-07-09_return_cant_component_truth_container_readonly_alignment_v1.md`
- `frontend/src/features/product-system/returnCantReadonlyContainerModel.ts`
- `frontend/src/pages/ProductSystem.tsx`
- `frontend/src/pages/ProductSystem.badges.test.tsx`
- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldsReadonlyMapper.ts`
- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldCaptureReadonlyAdapter.ts`
- `backend/data/mini_module_registry_volumetric_v2.py`
- `backend/services/product_aggregate_service.py`

## Files touched

- `frontend/src/features/product-system/returnCantReadonlyContainerModel.ts`
- `frontend/src/pages/ProductSystem.tsx`
- `frontend/src/pages/ProductSystem.badges.test.tsx`
- `docs/worklog/realignment/2026-07-09_return_cant_source_face_perimeter_ref_readonly_slice_v1.md`

## Current state audit

- `source_face_perimeter_ref` did not exist as an explicit dependency anchor in the stable readonly helper.
- `components.face.confirmed_perimeter` already existed in readonly language and dependency explanations.
- `quote_geometry.letter_perimeter_m` already existed and was still doing too much explanatory work as root context.
- The readonly mapper still treated the face dependency as conceptual/blocked rather than surfaced as a first-class dependency anchor field.
- The correct insertion point was the stable helper used by Product System:
  - `frontend/src/features/product-system/returnCantReadonlyContainerModel.ts`

## source_face_perimeter_ref implementation

Implemented read-only only:

- added explicit `source_face_perimeter_ref` emphasis inside the stable readonly container model
- changed its source type to:
  - `component dependency anchor`
- current source now points explicitly to:
  - `components.face.confirmed_perimeter`
- target path remains:
  - `components.return_cant.instances[].source_face_perimeter_ref`
- note now states clearly that the anchor is canonical, but the resolved reference is not migrated yet

No actual value migration was added.

## Canonical dependency conclusion

Canonical upstream dependency for return/cant is:

```text
components.face.confirmed_perimeter
```

`source_face_perimeter_ref` is now the explicit read-only dependency anchor that points there.

This means:

- return/cant does not own or invent perimeter by itself
- return/cant depends on face perimeter truth
- readiness must stay blocked until the real reference/value path exists

## Context-only root geometry conclusion

`quote_geometry.letter_perimeter_m` remains context-only.

It is still visible in the readonly model, but only as:

- root geometry context
- not canonical dependency ref
- not resolved `confirmed_perimeter_m`

This slice reduces ambiguity without promoting root geometry into component truth.

## Tests run

```powershell
Set-Location C:\Users\offic\workos_app_vs\frontend
npm.cmd run test -- src/pages/ProductSystem.badges.test.tsx
```

Result:

- `4 passed`

Coverage proved by the focused test:

- `source_face_perimeter_ref` appears
- `components.face.confirmed_perimeter` appears
- `quote_geometry.letter_perimeter_m` appears as root geometry context
- readiness does not become ready
- `confirmed_perimeter_m` is not presented as migrated/confirmed value
- no promote button exists
- no mutation call exists

## Screenshot paths

- `docs/worklog/realignment/assets/2026-07-09_return_cant_source_face_perimeter_ref_readonly_slice_v1/product_system_letters_context.png`
- `docs/worklog/realignment/assets/2026-07-09_return_cant_source_face_perimeter_ref_readonly_slice_v1/product_system_return_cant_truth_container.png`
- `docs/worklog/realignment/assets/2026-07-09_return_cant_source_face_perimeter_ref_readonly_slice_v1/product_system_source_face_perimeter_ref.png`
- `docs/worklog/realignment/assets/2026-07-09_return_cant_source_face_perimeter_ref_readonly_slice_v1/product_system_quote_geometry_context_only.png`

## Blockers remaining

- `confirmed_perimeter_m` still missing on return/cant instance
- `material_profile` still missing
- `layer_group_ids` still missing
- `confirmation_state` still missing
- readiness remains blocked until later migration slices land

## Forbidden scope confirmation

- no confirmed_perimeter_m migration
- no material_profile migration
- no layer_group_ids migration
- no confirmation_state migration
- no delete
- no seed modified
- no DB migration
- no seed live
- no Pricing
- no ProductDefinition
- no Product Truth writer change
- no ProductAggregate runtime write
- no LOGO activation

## Next recommended prompt

```text
TASK — RETURN_CANT_CONFIRMED_PERIMETER_M_READONLY_SLICE_V1
```

Recommended scope:

- second migration slice only for `confirmed_perimeter_m`
- derive it strictly from the canonical face dependency anchor
- keep root geometry context-only
- no Pricing
- no ProductDefinition
- no writer
- no delete
