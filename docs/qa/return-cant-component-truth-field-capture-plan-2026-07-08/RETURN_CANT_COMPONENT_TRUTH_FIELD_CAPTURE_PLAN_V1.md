# RETURN_CANT_COMPONENT_TRUTH_FIELD_CAPTURE_PLAN_V1

## Verdict

```text
RETURN_CANT_FIELD_CAPTURE_PLAN_READY
```

## Scope checked

- docs-only
- no runtime field capture implementation
- no UI implementation changes
- no Pricing changes
- no preview/calculation implementation

## HEAD

- before: `a9b36b1`
- after: pending at write time

## Evidence reviewed

- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldsReadonlyMapper.ts`
- `frontend/src/components/workos/intake-v6/IntakeV6ReturnCantBlockedStateAwarenessPanel.tsx`
- `frontend/src/lib/intakeV6/productTruth/productTruthDraftBuilder.ts`
- `frontend/src/lib/intakeV6/intakeV6LayerRoleBridge.ts`
- `frontend/src/lib/intakeV6/intakeV4QuoteGeometry.ts`
- `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx`
- `backend/services/form_system_contract_backbone_service.py`
- `backend/services/intake_v6_modular_form_contract_service.py`
- `docs/architecture/product-system/RETURN_CANT_COMPONENT_TRUTH_PATHS_CANONICALIZATION.md`
- `docs/architecture/product-system/RETURN_CANT_TRUTH_FIELDS_READONLY_MAPPER_CONTRACT.md`
- `docs/architecture/product-system/RETURN_CANT_MISSING_TRUTH_FIELDS_CONTRACT.md`
- `docs/architecture/product-system/FORM_SYSTEM_FIELD_CONTRACT_MAP.md`
- `docs/architecture/product-system/COMMERCIAL_PREVIEW_BOUNDARY_CONTRACT.md`
- `docs/architecture/product-system/MATERIAL_COLOR_CATALOGS_AND_INVENTORY_KEY_MODEL_V1.md`

## Decizia operationala

Planul este READY pentru ca exista deja toate cele 4 categorii de evidence necesare:

1. suprafata operator existenta pentru return/cant in `Review > Finisaje`
2. layer/group confirmation deja modelata in `layerRoleConfirmationToV6Setup`
3. geometry suggestion deja modelata in `IntakeV4QuoteGeometry`
4. Pricing boundary deja formalizat separat la `/inventory/pricing`

Lipsesc runtime writers si path-uri canonice efective, dar acestea sunt blocaje de implementare, nu blocaje de plan.

## Field capture checklist

| field | source | confirmation action | Product Truth path | pricing key needed | blocker inchis | blocker ramas |
|---|---|---|---|---|---|---|
| depth_mm | `finish_setup.return_depth_mm` / group cant depth | operator confirma depth | `components.return_cant.depth_mm` | indirect prin `return_cant.material_profile.material_cost_per_ml` | `RETURN_CANT_HEIGHT_CONFIRMATION_REQUIRED` | material, finish, color, groups, perimeter, state |
| material_profile | selector form/operator | operator alege si confirma profilul | `components.return_cant.material_profile` | `return_cant.material_profile.material_cost_per_ml` | `RETURN_CANT_MATERIAL_MISSING` | restul truth fields |
| finish_type | `finish_setup.return_finish_type` / group finish | operator confirma finish type | `components.return_cant.finish_type` | none direct | `RETURN_CANT_FINISH_MISSING` | color target conditional + restul |
| color_target.oracal_code | color picker Oracal | operator confirma codul | `components.return_cant.color_target.oracal_code` | none direct | `RETURN_CANT_COLOR_TARGET_MISSING` in caz Oracal | restul |
| color_target.ral_code | color picker RAL | operator confirma codul | `components.return_cant.color_target.ral_code` | none direct | `RETURN_CANT_COLOR_TARGET_MISSING` in caz RAL | restul |
| color_target.paint_target | paint target select | operator confirma target-ul | `components.return_cant.color_target.paint_target` | none direct | `RETURN_CANT_COLOR_TARGET_MISSING` in caz paint | restul |
| layer_group_ids | `svg.selected_layer_refs[]` + confirmed roles | operator confirma selectie + mapping la componenta | `components.return_cant.layer_group_ids` | none | `RETURN_CANT_LAYER_GROUP_SOURCE_MISSING` | perimeter/state/alte fields |
| confirmation_state | gate compus | operator confirma setul complet al componentei | `components.return_cant.confirmation_state` | none | `RETURN_CANT_SOURCE_STATE_NOT_CONFIRMED` | poate ramane dependency missing |
| perimeter_source | dependency declaration | operator/Form System confirma sursa canonica | `components.return_cant.perimeter_source` | `return_cant.labor.cost_per_ml` indirect prin quantity basis | `RETURN_CANT_PERIMETER_MISSING` | dependency face confirmed perimeter |
| face.confirmed_perimeter | geometry + confirmed roles + operator confirmation | operator confirma dependency source | `components.face.confirmed_perimeter` | `return_cant.labor.cost_per_ml` indirect | `RETURN_CANT_DEPENDENCY_FACE_GEOMETRY_UNCONFIRMED` | component fields neconfirmate |
| perimeter_dependency.face_confirmed_perimeter.* | mirror din dependency | se reflecta dupa confirmarea source-ului | `components.return_cant.perimeter_dependency.face_confirmed_perimeter.*` | none | `RETURN_CANT_DEPENDENCY_FACE_GEOMETRY_UNCONFIRMED` | none daca source confirmed |

## Pricing boundary confirmation

- cost material ramane in Pricing
- cost manopera ramane in Pricing
- pret/tarif ramane in Pricing
- componenta nu stocheaza cost/pret

## Analyzer boundary confirmation

- analyzer sugereaza perimetrul
- analyzer nu confirma truth
- analyzer nu da pret/cost
- Product Truth confirma perimetrul

## Recommended implementation order

1. `components.face.confirmed_perimeter` read-only contract adapter
2. `components.return_cant.perimeter_source` contract adapter
3. `components.return_cant.depth_mm`, `finish_type`, `layer_group_ids` contract adapter
4. `components.return_cant.material_profile` contract adapter
5. `components.return_cant.color_target.*` contract adapter
6. `components.return_cant.confirmation_state` contract adapter

## Forbidden scope confirmation

- no component root
- no component quote
- no Logo offerability
- no Pricing changes
- no Quote/Order
- no Execution
- no ProductAggregate
- no TaskGraph
- no ExecutionPlan
- no DB/seed/migration
- no UI nou
- no endpoint public nou

## Validation

- `git diff --check`
- docs-only diff confirmed

## Next prompt

```text
RETURN_CANT_TRUTH_FIELD_CAPTURE_READONLY_CONTRACT_ADAPTER_V1
```