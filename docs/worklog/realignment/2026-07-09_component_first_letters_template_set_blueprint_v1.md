# COMPONENT_FIRST_LETTERS_TEMPLATE_SET_BLUEPRINT_V1

## Scope

- Blueprint / design / contract only.
- No implementation.
- No delete.
- No frontend change.
- No backend change.
- No seed change.
- No DB change.
- No migration.
- No live seed.
- No Pricing.
- No ProductDefinition.
- No Product Truth writer.
- No ProductAggregate runtime write.
- No LOGO activation.
- No replacement of `TPL-VOLUMETRIC-LETTERS_v2`.

## HEAD before

- `07ba892`

## Files read

- `docs/worklog/realignment/2026-07-09_return_cant_source_face_perimeter_ref_readonly_slice_v1.md`
- `docs/worklog/realignment/2026-07-09_return_cant_component_truth_container_migration_plan_v1.md`
- `docs/worklog/realignment/2026-07-09_component_templates_calculation_ownership_alignment_v1.md`
- `docs/worklog/realignment/2026-07-09_product_component_composition_contract_v1.md`
- `docs/worklog/realignment/2026-07-09_product_component_composition_read_model_alignment_v1.md`
- `docs/worklog/realignment/2026-07-09_product_template_truth_inventory_delete_candidates_audit_v1.md`
- `docs/architecture/product-system/PRODUCT_SYSTEM_PRODUCT_TEMPLATE_VS_COMPONENT_TEMPLATE_CONTRACT.md`
- `docs/architecture/product-system/PRODUCT_SYSTEM_COMPONENT_OWNED_CALCULATION_BOUNDARY.md`
- `docs/architecture/product-system/PRODUCT_SYSTEM_COMPONENT_LEVEL_CALCULATION_READINESS.md`
- `docs/architecture/product-system/FORM_SYSTEM_COMPONENT_FIELD_OWNERSHIP_MAP.md`
- `docs/architecture/product-system/RETURN_CANT_COMPONENT_CONFIRMATION_CONTRACT.md`
- `backend/seeds/seed_tpl_volumetric_letters_v2.py`
- `backend/data/shared_volumetric_component_contracts.py`
- `backend/data/mini_module_registry_volumetric_v2.py`
- `backend/services/product_aggregate_service.py`
- `frontend/src/features/product-system/returnCantReadonlyContainerModel.ts`

## Searches run

- `TPL-VOLUMETRIC-LETTERS_v2`
- `TPL-VOLUMETRIC-FACE_v1`
- `TPL-VOLUMETRIC-BACK_v1`
- `TPL-VOLUM-ALUMINIU_v1`
- `TPL-VOLUMETRIC-LED_v1`
- `TPL-VOLUMETRIC-FINISH_v1`
- `comp_face_litere`
- `comp_spate_litere`
- `comp_lateral_litere`
- `comp_led_litere`
- `comp_finisaj_litere`
- `components_json`
- `operations_json`
- `required_materials_json`
- `composition_modules`
- `component template`
- `product template`
- `product aggregate`
- `return_cant`
- `components.return_cant.instances`
- `source_face_perimeter_ref`
- `components.face.confirmed_perimeter`

## New template set

### New Product Template

- `TPL-LETTERS-COMPOSER_v1`

### New Component Templates

- `TPL-COMP-LETTER-FACE_v1`
- `TPL-COMP-LETTER-BACK_v1`
- `TPL-COMP-LETTER-RETURN-CANT_v1`
- `TPL-COMP-LETTER-LED_v1`
- `TPL-COMP-LETTER-FINISH_v1`
- `TPL-COMP-LETTER-MOUNTING_v1`

Design rule for the whole set:

```text
New composer is product-first only for identity/composition.
All calculable technical truth belongs to component templates.
```

## Product composer contract

### `TPL-LETTERS-COMPOSER_v1`

Must contain only:

- product identity
- product family
- offerability flag, default inactive
- component composition list
- component dependency graph
- allowed component variants
- product-level validation summary
- read-model hints

Must not contain:

- face/back/cant material truth
- per-component operation truth
- pricing formula
- calculable resource requirements
- Product Truth component fields
- execution task truth

Proposed minimum composer payload shape:

```text
template_code
product_family
status = inactive_blueprint
component_composition = [FACE, BACK, RETURN_CANT, LED?, FINISH, MOUNTING?]
component_dependency_graph
allowed_variants_summary
validation_summary
read_model_hints
```

## Component template contracts

### FACE — `TPL-COMP-LETTER-FACE_v1`

- Role: structural face.
- Inputs:
  - `layer_group_ids`
  - `selected_layer_refs`
  - `face_material`
  - `face_thickness_mm`
  - `face_finish_target`
- Outputs:
  - `confirmed_perimeter`
  - `confirmed_area`
  - `face_cutting_operation`
  - `face_material_consumption`
- Dependencies:
  - SVG/layer confirmation.
- Blockers:
  - selected face layer missing
  - material missing
  - perimeter not confirmed

### BACK — `TPL-COMP-LETTER-BACK_v1`

- Role: structural back.
- Inputs:
  - `source_face_geometry_ref`
  - `back_material`
  - `back_thickness_mm`
  - `backing_mode`
- Outputs:
  - `back_cutting_operation`
  - `back_material_consumption`
- Dependencies:
  - face geometry.
- Blockers:
  - back material missing
  - backing mode missing

### RETURN_CANT — `TPL-COMP-LETTER-RETURN-CANT_v1`

- Role: structural volume / return / cant.
- Inputs:
  - `source_face_perimeter_ref`
  - `material_profile`
  - `depth_mm`
  - `finish_type`
  - `color_source`
  - `layer_group_ids`
- Outputs:
  - `confirmed_perimeter_m`
  - `return_material_consumption`
  - `modelare_cant_operation`
  - `bonding_operation`
  - `finish_operation_ref`
- Dependencies:
  - `components.face.confirmed_perimeter`
- Blockers:
  - `source_face_perimeter_ref` missing
  - `material_profile` missing
  - `confirmation_state` missing

### LED — `TPL-COMP-LETTER-LED_v1`

- Role: functional lighting.
- Inputs:
  - `lighting_mode`
  - `source_face_area_ref`
  - `led_density`
  - `led_module_type`
  - `power_supply_policy`
- Outputs:
  - `led_count`
  - `power_w`
  - `power_supply_count`
  - `led_install_operation`
- Dependencies:
  - face area / lighting confirmation.
- Blockers:
  - lighting mode missing
  - area not confirmed
  - led density missing

### FINISH — `TPL-COMP-LETTER-FINISH_v1`

- Role: functional finish.
- Inputs:
  - `finish_target_component_ids`
  - `finish_type`
  - `color_code`
  - `print_required`
  - `lamination_required`
- Outputs:
  - `finish_operations`
  - `finish_material_consumption`
- Dependencies:
  - target components.
- Blockers:
  - finish target missing
  - finish type missing

### MOUNTING — `TPL-COMP-LETTER-MOUNTING_v1`

- Role: functional mounting/support.
- Inputs:
  - `mounting_mode`
  - `wall_type`
  - `mounting_height`
  - `support_required`
- Outputs:
  - `mounting_operations`
  - `support_materials`
- Dependencies:
  - product geometry / backing.
- Blockers:
  - mounting mode missing
  - support requirement unknown

## Dependency graph

```text
FACE
  -> RETURN_CANT
  -> BACK

FACE
  -> LED

FACE / BACK / RETURN_CANT
  -> FINISH

BACK / PRODUCT
  -> MOUNTING
```

### Interpretation

- FACE produces the primary geometry.
- RETURN_CANT consumes the face perimeter.
- BACK consumes face geometry.
- LED consumes face area and lighting-specific confirmation.
- FINISH consumes completed structural component targets.
- MOUNTING consumes whole-product/backing context.

### Ownership rules

- geometry producer: FACE
- geometry consumers: RETURN_CANT, BACK, LED
- material truth producer: each component for its own material family
- operation producer: each component for its own operations
- blocker producer: each component owns its missing truth blockers
- forbidden behavior: no component may invent another component's missing truth

## Product Truth target paths

### `components.face.instances[]`

- Required:
  - `instance_id`
  - `layer_group_ids`
  - `selected_layer_refs`
  - `material`
  - `thickness_mm`
  - `confirmed_perimeter`
  - `confirmed_area`
  - `blockers`
  - `readiness`
- Optional:
  - `finish_target`
  - `source_notes`
- Legacy compatibility note:
  - older face fields may survive temporarily as diagnostics only.

### `components.back.instances[]`

- Required:
  - `instance_id`
  - `source_face_geometry_ref`
  - `back_material`
  - `back_thickness_mm`
  - `backing_mode`
  - `blockers`
  - `readiness`
- Optional:
  - `bevel_enabled`

### `components.return_cant.instances[]`

- Required:
  - `instance_id`
  - `source_face_perimeter_ref`
  - `material_profile`
  - `depth_mm`
  - `finish_type`
  - `layer_group_ids`
  - `confirmation_state`
  - `blockers`
  - `readiness`
- Optional:
  - `color_source`
  - `confirmed_perimeter_m`
  - `finish_operation_ref`
- Legacy compatibility note:
  - `components.returnCant.*` remains temporary compatibility only.

### `components.led.instances[]`

- Required:
  - `instance_id`
  - `source_face_area_ref`
  - `lighting_mode`
  - `led_density`
  - `led_module_type`
  - `power_supply_policy`
  - `blockers`
  - `readiness`
- Optional:
  - `led_count`
  - `power_w`
  - `power_supply_count`

### `components.finish.instances[]`

- Required:
  - `instance_id`
  - `finish_target_component_ids`
  - `finish_type`
  - `blockers`
  - `readiness`
- Optional:
  - `color_code`
  - `print_required`
  - `lamination_required`

### `components.mounting.instances[]`

- Required:
  - `instance_id`
  - `mounting_mode`
  - `support_required`
  - `blockers`
  - `readiness`
- Optional:
  - `wall_type`
  - `mounting_height`
  - `support_materials`

## Old vs new comparison matrix

| old template / old field | problem | new component template | new target path | migration risk | keep old temporarily? | delete candidate later? |
|---|---|---|---|---|---|---|
| `TPL-VOLUMETRIC-LETTERS_v2.components_json` | parent still carries structural truth hints | `TPL-LETTERS-COMPOSER_v1` + all new component templates | composition list only in composer | high | yes | yes |
| `TPL-VOLUMETRIC-LETTERS_v2.operations_json` | parent carries operation truth support rows | component templates own operations | per-component `*.instances[].operation_*` or outputs | high | yes | yes |
| `TPL-VOLUMETRIC-LETTERS_v2.required_materials_json` | parent carries material support rows | component templates own material truth | per-component material fields/consumption | high | yes | yes |
| `TPL-VOLUMETRIC-FACE_v1` | still mixed with old parent fallback | `TPL-COMP-LETTER-FACE_v1` | `components.face.instances[]` | medium | yes | maybe |
| `TPL-VOLUMETRIC-BACK_v1` | still blocked by implicit material truth | `TPL-COMP-LETTER-BACK_v1` | `components.back.instances[]` | medium | yes | maybe |
| `TPL-VOLUM-ALUMINIU_v1` | mixed legacy/read-only migration path | `TPL-COMP-LETTER-RETURN-CANT_v1` | `components.return_cant.instances[]` | high | yes | maybe |
| `TPL-VOLUMETRIC-LED_v1` | strategy/truth still mixed | `TPL-COMP-LETTER-LED_v1` | `components.led.instances[]` | medium | yes | maybe |
| `TPL-VOLUMETRIC-FINISH_v1` | finish/artwork/cant boundary mixed | `TPL-COMP-LETTER-FINISH_v1` | `components.finish.instances[]` | medium | yes | maybe |
| `components.returnCant.*` | legacy alias family | `TPL-COMP-LETTER-RETURN-CANT_v1` | `components.return_cant.instances[]` | high | yes | yes |
| current `components.return_cant.instances[]` readonly target | readonly explanation only | `TPL-COMP-LETTER-RETURN-CANT_v1` | same canonical path family | medium | yes | no |

## Implementation phases

### Phase 1

- docs/contract only

### Phase 2

- create new seed/registry files, inactive
- no Work Intake activation

### Phase 3

- Product System readonly display for new component-first set

### Phase 4

- fixture test comparing old vs new structure

### Phase 5

- owner review

### Phase 6

- optional migration / activation only after explicit GO

## Risks

- new set can duplicate the old set if owner/governance boundaries are not explicit
- if composer is allowed to regrow operation/material truth, the new set will repeat the old problem
- if LED/FINISH/MOUNTING are not clearly kept functional, structural and functional boundaries can blur again
- if old aliases are deleted before the new set is proven, diagnostics and compatibility will regress

## Forbidden scope confirmation

- no implementation
- no delete
- no frontend modified
- no backend modified
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
TASK — COMPONENT_FIRST_LETTERS_TEMPLATE_SET_INACTIVE_SEED_PLAN_V1
```

Recommended scope:

- plan inactive seed/registry creation for the new component-first set
- no activation in Work Intake
- no Pricing activation
- no migration of old templates yet
