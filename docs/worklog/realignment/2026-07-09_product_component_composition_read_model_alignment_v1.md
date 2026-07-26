# PRODUCT_COMPONENT_COMPOSITION_READ_MODEL_ALIGNMENT_V1

## Scope

- Read-model / UI-readonly alignment only.
- No delete.
- No seed change.
- No DB change.
- No migration.
- No live seed.
- No Pricing.
- No ProductDefinition.
- No Product Truth writer.
- No ProductAggregate runtime write.
- No LOGO activation.

## HEAD before

- `95c01ab`

## Files read

- `docs/worklog/realignment/2026-07-09_product_component_composition_contract_v1.md`
- `docs/worklog/realignment/2026-07-09_product_template_truth_inventory_delete_candidates_audit_v1.md`
- `docs/worklog/realignment/2026-07-09_return_cant_component_source_path_alignment_readonly_v1.md`
- `docs/worklog/realignment/2026-07-09_component_templates_calculation_ownership_alignment_v1.md`
- `docs/architecture/product-system/PRODUCT_SYSTEM_PRODUCT_TEMPLATE_VS_COMPONENT_TEMPLATE_CONTRACT.md`
- `docs/architecture/product-system/PRODUCT_SYSTEM_COMPONENT_OWNED_CALCULATION_BOUNDARY.md`
- `docs/architecture/product-system/PRODUCT_SYSTEM_COMPONENT_LEVEL_CALCULATION_READINESS.md`
- `docs/architecture/product-system/FORM_SYSTEM_COMPONENT_FIELD_OWNERSHIP_MAP.md`
- `docs/architecture/product-system/RETURN_CANT_COMPONENT_CONFIRMATION_CONTRACT.md`
- `backend/services/product_aggregate_service.py`
- `backend/services/product_template_availability_service.py`
- `backend/data/mini_module_registry_volumetric_v2.py`
- `backend/data/shared_volumetric_component_contracts.py`
- `backend/seeds/seed_tpl_volumetric_letters_v2.py`
- `backend/seeds/seed_tpl_volumetric_logo_v1.py`
- `frontend/src/pages/ProductSystem.tsx`
- `frontend/src/pages/ProductSystem.badges.test.tsx`

## Files touched

- `frontend/src/pages/ProductSystem.tsx`
- `frontend/src/pages/ProductSystem.badges.test.tsx`
- `docs/worklog/realignment/2026-07-09_product_component_composition_read_model_alignment_v1.md`

## Read-model composition audit

### What Product System / ProductAggregate already expose

- Structural components are visible today through a mix of:
  - dossier-derived ProductAggregate components
  - child template links
  - shared volumetric contracts
  - ownership panel diagnostics
- Functional components are visible through the same mixed stack.

### Source breakdown

#### Comes from dossier

- `comp_face_litere`
- `comp_lateral_litere`
- `comp_spate_litere`
- `comp_led_litere`
- `comp_finisaj_litere`

ProductAggregate currently builds component rows from dossier sections and assigns mini-module codes via a dossier component id map.

#### Comes from child templates

- `TPL-VOLUMETRIC-FACE_v1`
- `TPL-VOLUMETRIC-BACK_v1`
- `TPL-VOLUM-ALUMINIU_v1`
- `TPL-VOLUMETRIC-LED_v1`
- `TPL-VOLUMETRIC-FINISH_v1`
- `TPL-METAL-PREMOUNT-STRUCTURE_v1`

Child templates contribute linked-module materials and operations into ProductAggregate and drive the shared component boundary shown in Product System.

#### Comes from parent rows

- `components_json`
- `operations_json`
- `required_materials_json`

These still feed ProductAggregate as `parent` provenance and remain part of the support structure, even though they should not be treated as authoritative component-owned truth.

#### Comes from shared contracts

- component role labels
- shared module identity
- profile-level direction for Letters and Logo
- ownership/readiness orientation

#### Is derived read model only

- ProductAggregate merged materials
- ProductAggregate merged operations
- ProductAggregate provenance summary
- warnings like `PARENT_COMPONENTS_EMPTY`

#### Still easy to confuse with truth source

- parent support rows in `TPL-VOLUMETRIC-LETTERS_v2`
- dossier-derived component presence
- ProductAggregate merged rows

This slice makes that boundary explicit in UI.

## STRUCTURAL_COMPOSITION map

### FACE

- component role: structural face
- component_template_code: `TPL-VOLUMETRIC-FACE_v1`
- component_id: `comp_face_litere`
- structural_required: `true`
- current wiring: `partial`
- Product Truth target: `components.face.*`
- geometry dependency: `selected_layer_refs + face area + perimeter`
- material dependency: fallback/partial face material
- operation dependency: `debitare_fata / face_cnc_cut`
- calculation readiness: `partial`
- blockers:
  - `FACE_MATERIAL_MISSING`
  - `SELECTED_FACE_LAYER_MISSING`
  - `FACE_FINISH_TARGET_MISSING`
- current source type: `shared contract`

### BACK

- component role: structural backing / rear closure
- component_template_code: `TPL-VOLUMETRIC-BACK_v1`
- component_id: `comp_spate_litere`
- structural_required: `true`
- current wiring: `partial`
- Product Truth target: `components.back.*`
- geometry dependency: follows face geometry and area
- material dependency: implicit from backing mode / parent flow
- operation dependency: `debitare_spate / back_cut`
- calculation readiness: `blocked`
- blockers:
  - `BACK_MATERIAL_MISSING`
  - `BACKING_MODE_CONFIRMATION_REQUIRED`
- current source type: `shared contract`

### RETURN_CANT

- component role: structural return / volumetric side
- component_template_code: `TPL-VOLUM-ALUMINIU_v1`
- component_id: `comp_lateral_litere`
- structural_required: `true`
- current wiring: `partial`
- Product Truth target: `components.return_cant.*`
- geometry dependency: depends on face confirmed perimeter
- material dependency: child template profile gate only
- operation dependency:
  - `modelare_cant`
  - `RETURN_PROFILE_MACHINE_FORMING`
  - `RETURN_PROFILE_FACE_BONDING`
- calculation readiness: `blocked`
- blockers:
  - `RETURN_CANT_MATERIAL_MISSING`
  - `RETURN_CANT_DEPENDENCY_FACE_GEOMETRY_UNCONFIRMED`
  - `RETURN_CANT_SOURCE_STATE_NOT_CONFIRMED`
- current source type: `component template`

## FUNCTIONAL_COMPOSITION map

### LED

- functional role: lighting/electrical boundary
- component_template_code: `TPL-VOLUMETRIC-LED_v1`
- component_id: `comp_led_litere`
- depends_on structural components:
  - face
  - whole product geometry
- component-owned area today: partial
- consequence/derived area today: PSU/strategy still partly product-context-like
- readiness: `partial`
- blockers:
  - `LIGHTING_MODE_CONFIRMATION_REQUIRED`
  - `LIGHTING_LED_COUNT_MISSING`

### FINISH

- functional role: finish/artwork boundary
- component_template_code: `TPL-VOLUMETRIC-FINISH_v1`
- component_id: `comp_finisaj_litere`
- depends_on structural components:
  - face
  - return/cant
  - artwork scope
- component-owned area today: partial
- consequence/derived area today: review payload still carries too much shared finish logic
- readiness: `blocked`
- blockers:
  - `FINISH_TARGET_MISSING`
  - `PRINT_REQUIRED_UNKNOWN`

### SUPPORT/MOUNTING

- functional role: optional support/mounting boundary
- component_template_code: `TPL-METAL-PREMOUNT-STRUCTURE_v1`
- component_id: `comp_premount_bars`
- depends_on structural components:
  - overall width / installation strategy
- component-owned area today: partial
- consequence/derived area today: `metal_support_required` bridge still acts too close to primary truth
- readiness: `blocked`
- blockers:
  - `TRIGGER_FIELD_MISMATCH`
  - `SUPPORT_REQUIRED_UNKNOWN`

## ProductAggregate boundary conclusion

- ProductAggregate is now explicitly surfaced as derived read model in the Product System ownership area.
- New wording makes clear that ProductAggregate must not be treated as primary truth source.
- When ProductAggregate compensates for missing component truth, it is now described as support/diagnostic output only.
- Parent rows from `TPL-VOLUMETRIC-LETTERS_v2` are therefore better framed as legacy/support/aggregate inputs, not component-owned truth.

## UI changes

- Extended the existing Product System ownership panel.
- Added a new read-only `Structural composition map` section.
- Added a new read-only `Functional composition map` section.
- Added a ProductAggregate boundary disclaimer inside both sections.
- No new page.
- No button.
- No mutation.

## Screenshot paths

- `docs/worklog/realignment/assets/2026-07-09_product_component_composition_read_model_alignment_v1/product_system_products_context.png`
- `docs/worklog/realignment/assets/2026-07-09_product_component_composition_read_model_alignment_v1/product_system_letters_context.png`
- `docs/worklog/realignment/assets/2026-07-09_product_component_composition_read_model_alignment_v1/product_system_structural_composition_map.png`
- `docs/worklog/realignment/assets/2026-07-09_product_component_composition_read_model_alignment_v1/product_system_face_back_return_status.png`
- `docs/worklog/realignment/assets/2026-07-09_product_component_composition_read_model_alignment_v1/product_system_productaggregate_read_model_disclaimer.png`

## Tests run

```powershell
Set-Location C:\Users\offic\workos_app_vs\frontend
npm.cmd run test -- src/pages/ProductSystem.badges.test.tsx
```

Result:

- `4 passed`

What the focused test now proves:

- structural composition map appears
- FACE / BACK / RETURN_CANT appear
- overall composition status is `PARTIAL`, not `READY`
- ProductAggregate is marked as derived read model
- no promote button exists
- no mutation call is introduced

## Blockers

- face confirmed perimeter still not explicit enough as dependency source
- back material truth still implicit
- return_cant component truth container still incomplete
- finish boundary still mixed
- support boundary still bridged through derived semantics

## Recommendation

1. Next move should stay read-only or read-model-alignment oriented.
2. `return_cant` truth container remains the most important next step.
3. Delete and migration work must still wait.

## Forbidden scope confirmation

- no delete performed
- no seed modified
- no DB migration
- no seed live
- no Pricing
- no ProductDefinition
- no Product Truth writer change
- no UI mutation beyond read-only clarification
- no ProductAggregate runtime write
- no LOGO activation

## Next recommended prompt

```text
TASK — RETURN_CANT_COMPONENT_TRUTH_CONTAINER_READONLY_ALIGNMENT_V1
```

Suggested scope:

- align `components.return_cant.instances.*` container language in UI + readonly audit helpers
- make the face -> return_cant dependency explicit
- keep all changes read-only
- do not activate component root, ProductDefinition, Pricing, or delete
