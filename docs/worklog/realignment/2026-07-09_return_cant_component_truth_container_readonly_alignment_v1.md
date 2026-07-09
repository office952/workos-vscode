# RETURN_CANT_COMPONENT_TRUTH_CONTAINER_READONLY_ALIGNMENT_V1

## Scope

- Read-only only.
- No Product Truth write.
- No data move.
- No delete.
- No Pricing.
- No ProductDefinition.
- No Product Truth writer.
- No ProductAggregate runtime write.
- No LOGO activation.

## HEAD before

- `41c762a`

## Files read

- `docs/worklog/realignment/2026-07-09_product_component_composition_read_model_alignment_v1.md`
- `docs/worklog/realignment/2026-07-09_product_component_composition_contract_v1.md`
- `docs/worklog/realignment/2026-07-09_product_template_truth_inventory_delete_candidates_audit_v1.md`
- `docs/worklog/realignment/2026-07-09_return_cant_component_source_path_alignment_readonly_v1.md`
- `docs/architecture/product-system/RETURN_CANT_COMPONENT_CONFIRMATION_CONTRACT.md`
- `docs/architecture/product-system/PRODUCT_SYSTEM_COMPONENT_OWNED_CALCULATION_BOUNDARY.md`
- `docs/architecture/product-system/FORM_SYSTEM_COMPONENT_FIELD_OWNERSHIP_MAP.md`
- `frontend/src/pages/ProductSystem.tsx`
- `frontend/src/pages/ProductSystem.badges.test.tsx`
- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldsReadonlyMapper.ts`
- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldCaptureReadonlyAdapter.ts`
- `backend/data/mini_module_registry_volumetric_v2.py`
- `backend/data/shared_volumetric_component_contracts.py`
- `backend/services/product_aggregate_service.py`
- `backend/services/intake_v6_modular_form_contract_service.py`

## Files touched

- `frontend/src/pages/ProductSystem.tsx`
- `frontend/src/pages/ProductSystem.badges.test.tsx`
- `docs/worklog/realignment/2026-07-09_return_cant_component_truth_container_readonly_alignment_v1.md`

## Current return_cant language audit

### Canonical language already present

- `components.return_cant.*`
- `components.return_cant.instances.*`
- `components.face.confirmed_perimeter`

These already exist in readonly mapper/adapter language as the intended target model, even though they are not runtime write targets yet.

### Legacy aliases still present

- `components.returnCant.depthMm`
- `components.returnCant.finishType`
- `components.returnCant.colorCode`
- older `components.return.depth_mm`

These remain compatibility / readonly interpretation language only.

### Root context language still present

- `quote_geometry.letter_perimeter_m`
- generic `letter_perimeter_m`

This is context/evidence, not final component-owned perimeter truth.

### Parent aggregate support language still present

- linked module traces inside ProductAggregate
- parent rows and aggregate summaries in Product System
- component presence inferred from dossier + linked modules

These remain support/read-model language, not primary truth.

### Missing fields in real component-owned truth

- stable `instance_id`
- explicit `source_face_perimeter_ref`
- explicit `confirmed_perimeter_m` for return/cant instance
- explicit `material_profile` truth field
- explicit `layer_group_ids`
- explicit `confirmation_state`

## RETURN_CANT_TRUTH_CONTAINER_TARGET

Target readonly container:

```text
components.return_cant.instances[]
```

Each future instance should be able to carry:

- `instance_id`
- `component_template_code`
- `component_id`
- `layer_group_ids`
- `source_face_component_id`
- `source_face_perimeter_ref`
- `perimeter_source`
- `confirmed_perimeter_m`
- `material_profile`
- `depth_mm`
- `finish_type`
- `color_source`
- `operation_modelare_cant_ref`
- `operation_bonding_ref`
- `resource_requirements_ref`
- `confirmation_state`
- `blockers[]`

This slice does not write these fields. It aligns the readonly model and shows where each one currently comes from.

## FACE_TO_RETURN_CANT_DEPENDENCY

Explicit conclusion:

- `return_cant` must not invent its own perimeter.
- `return_cant` depends on face perimeter truth.
- target dependency language is:

```text
components.face.confirmed_perimeter
```

- until that dependency is explicit and confirmed, `return_cant` remains `blocked` / `partial`.
- `quote_geometry.letter_perimeter_m` remains root geometry context only.

## Source type table

| field | current source type | current source | target path | conclusion |
|---|---|---|---|---|
| `instance_id` | `missing` | source rows are not stabilized as canonical instance ids | `components.return_cant.instances[].instance_id` | missing |
| `component_template_code` | `component template / registry` | `TPL-VOLUM-ALUMINIU_v1` | `components.return_cant.instances[].component_template_code` | real boundary already exists |
| `component_id` | `component template / registry` | `comp_lateral_litere` | `components.return_cant.instances[].component_id` | real identity already exists |
| `layer_group_ids` | `missing` | selected refs / layer confirmations exist but are not component truth | `components.return_cant.instances[].layer_group_ids` | missing |
| `source_face_component_id` | `parent aggregate support` | implied by `comp_face_litere` in composition | `components.return_cant.instances[].source_face_component_id` | support only |
| `source_face_perimeter_ref` | `missing` | face dependency target exists in language, not as explicit reference | `components.return_cant.instances[].source_face_perimeter_ref` | missing |
| `perimeter_source` | `root geometry context` | `quote_geometry.letter_perimeter_m` | `components.return_cant.instances[].perimeter_source` | blocked until face dependency is explicit |
| `confirmed_perimeter_m` | `missing` | no component-owned confirmed perimeter for return/cant | `components.return_cant.instances[].confirmed_perimeter_m` | missing |
| `material_profile` | `component template / registry` | profile gate in `TPL-VOLUM-ALUMINIU_v1` | `components.return_cant.instances[].material_profile` | template exists, truth field missing |
| `depth_mm` | `Form System capture` | `finish_setup.return_depth_mm` | `components.return_cant.instances[].depth_mm` | capture only |
| `finish_type` | `Form System capture` | `finish_setup.return_finish_type` | `components.return_cant.instances[].finish_type` | capture only |
| `color_source` | `Form System capture` | `return_oracal_code` and finish payload | `components.return_cant.instances[].color_source` | capture/catalog interpretation only |
| `operation_modelare_cant_ref` | `component template / registry` | `RETURN_PROFILE_MACHINE_FORMING` | `components.return_cant.instances[].operation_modelare_cant_ref` | exists as operation identity |
| `operation_bonding_ref` | `component template / registry` | `RETURN_PROFILE_FACE_BONDING` | `components.return_cant.instances[].operation_bonding_ref` | exists as operation identity |
| `resource_requirements_ref` | `parent aggregate support` | `operation_resource_requirements` boundary | `components.return_cant.instances[].resource_requirements_ref` | external support boundary only |
| `confirmation_state` | `missing` | global/workflow confirmation only | `components.return_cant.instances[].confirmation_state` | missing |
| `blockers` | `component truth` | readonly mapper blockers | `components.return_cant.instances[].blockers[]` | already explicit and useful |

## Legacy alias conclusion

`components.returnCant.*` remains legacy alias language only.

It must be treated as:

- compatibility / readonly interpretation
- not canonical target path
- not permission to treat current runtime shape as completed component truth

## ProductAggregate boundary conclusion

- ProductAggregate remains derived read model.
- parent aggregate support rows can explain why something is visible, but they do not satisfy component-owned truth requirements.
- the new UI makes this explicit inside the return/cant truth container section.

## UI changes

- Extended the existing `VOLUM ALUMINIU / CANT` card in Product System.
- Added a new read-only `Return/Cant truth container` section.
- Added explicit target container label:
  - `components.return_cant.instances[]`
- Added explicit FACE -> RETURN_CANT dependency note:
  - `components.face.confirmed_perimeter`
- Added explicit legacy alias note:
  - `components.returnCant.*`
- Added a source-type table for key fields.
- Added explicit ProductAggregate read-model disclaimer.

## Screenshot paths

- `docs/worklog/realignment/assets/2026-07-09_return_cant_component_truth_container_readonly_alignment_v1/product_system_letters_context.png`
- `docs/worklog/realignment/assets/2026-07-09_return_cant_component_truth_container_readonly_alignment_v1/product_system_return_cant_truth_container.png`
- `docs/worklog/realignment/assets/2026-07-09_return_cant_component_truth_container_readonly_alignment_v1/product_system_face_to_return_cant_dependency.png`
- `docs/worklog/realignment/assets/2026-07-09_return_cant_component_truth_container_readonly_alignment_v1/product_system_return_cant_legacy_alias_and_missing_fields.png`

## Tests run

```powershell
Set-Location C:\Users\offic\workos_app_vs\frontend
npm.cmd run test -- src/pages/ProductSystem.badges.test.tsx
```

Result:

- `4 passed`

Coverage added by this slice:

- Return/Cant truth container appears
- target container appears
- dependency on `components.face.confirmed_perimeter` appears
- legacy alias note appears
- status remains blocked/partial
- no promote button
- no mutation call

## Blockers

- no explicit face confirmed perimeter reference yet
- no explicit material profile truth field yet
- no explicit layer_group_ids truth field yet
- no explicit confirmation_state truth field yet
- no explicit confirmed_perimeter_m field for the return/cant instance yet

## Recommendation

1. Next move should still be read-only or migration-planning oriented.
2. The next meaningful task is to align the return/cant container and dependency language all the way through readonly mapper outputs.
3. Delete, Pricing, ProductDefinition, and writer work must still wait.

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
TASK — RETURN_CANT_COMPONENT_TRUTH_CONTAINER_READONLY_ENDPOINT_ALIGNMENT_V1
```

Suggested scope:

- align Product System readonly language with readonly mapper / adapter outputs
- if useful, expose the same container language through one stable read-only audit/endpoint surface
- keep all changes read-only
- no delete
- no Pricing
- no ProductDefinition
- no writer
