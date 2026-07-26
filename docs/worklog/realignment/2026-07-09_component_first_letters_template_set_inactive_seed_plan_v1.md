# COMPONENT_FIRST_LETTERS_TEMPLATE_SET_INACTIVE_SEED_PLAN_V1

## Scope

- Planning only.
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
- No Work Intake activation.
- No LOGO activation.
- No replacement of `TPL-VOLUMETRIC-LETTERS_v2`.

## HEAD before

- `0416248`

## Files read

- `docs/worklog/realignment/2026-07-09_component_first_letters_template_set_blueprint_v1.md`
- `docs/worklog/realignment/2026-07-09_product_component_composition_contract_v1.md`
- `docs/worklog/realignment/2026-07-09_product_component_composition_read_model_alignment_v1.md`
- `docs/worklog/realignment/2026-07-09_product_template_truth_inventory_delete_candidates_audit_v1.md`
- `docs/architecture/product-system/PRODUCT_SYSTEM_PRODUCT_TEMPLATE_VS_COMPONENT_TEMPLATE_CONTRACT.md`
- `docs/architecture/product-system/PRODUCT_SYSTEM_COMPONENT_OWNED_CALCULATION_BOUNDARY.md`
- `docs/architecture/product-system/PRODUCT_SYSTEM_COMPONENT_LEVEL_CALCULATION_READINESS.md`
- `backend/seeds/seed_tpl_volumetric_letters_v2.py`
- `backend/data/shared_volumetric_component_contracts.py`
- `backend/data/mini_module_registry_volumetric_v2.py`
- `backend/models/product_templates.py`
- `backend/services/product_template_availability_service.py`
- `backend/services/product_aggregate_service.py`

## Searches run

- `seed_tpl_volumetric_letters_v2`
- `TPL-VOLUMETRIC-LETTERS_v2`
- `ProductTemplate`
- `components_json`
- `operations_json`
- `required_materials_json`
- `composition_modules`
- `child template`
- `component_template_code`
- `availability`
- `offerable`
- `work intake`
- `inactive`
- `registry`
- `shared_volumetric_component_contracts`
- `mini_module_registry_volumetric_v2`

## Safety gate result

- `git rev-parse --short HEAD` returned `0416248`.
- `git diff --cached --name-only` returned empty output.
- `git status -sb` showed only preexisting untracked noise.
- `git diff --check` showed no local diff formatting issue for this slice.

## Decision summary

The repo currently favors grouped product-template seeds that also describe linked module structure in one place.

Examples confirmed by read-only inspection:

- `seed_tpl_volumetric_letters_v2.py` seeds the product template and shapes child/module contract context together.
- `product_templates` currently offers only generic JSON payload columns:
  - `components_json`
  - `operations_json`
  - `required_materials_json`
  - `active`
- `ProductTemplateAvailabilityService` derives Work Intake offerability from:
  - `active`
  - active module links
  - owner-valid active scope
  - parent/module relationship
- `ProductAggregateService` is a read-only merger of parent rows, dossier rows, and linked child templates.

Because of that, the safest future inert seed shape is:

```text
seed new rows as active=False
keep BOM/runtime arrays empty or metadata-only
do not register owner-valid active scope
do not expose Work Intake root
do not let ProductAggregate accidentally consume executable child BOM
```

## Seed file strategy

### Proposed file strategy

Preferred plan for later implementation:

- `backend/seeds/seed_tpl_letters_component_first_v1.py`

Optional helper file only if the implementation grows too large:

- `backend/seeds/_tpl_letters_component_first_payloads.py`

### Why grouped seed instead of 7 separate seed entrypoints

Use one grouped public seed entrypoint because the new set is a composition family, not 7 unrelated templates.

Reasons:

1. The set must remain internally consistent around one dependency graph.
2. The composer and the six components share the same inactive guard policy.
3. One entrypoint reduces accidental partial seeding where only some components exist.
4. One entrypoint makes it easier to keep all seven rows `active=False` by default.
5. One entrypoint mirrors the current repo pattern where Letters v2 orchestration is described in one seed surface.
6. One entrypoint reduces the chance that a future operator runs only one component seed and creates an orphan runtime module.

### Why not seed directly into existing active seed file

Do not append this plan into `seed_tpl_volumetric_letters_v2.py`.

Reasons:

1. That file seeds the currently active letters root.
2. Mixing the new component-first family into the active letters seed increases accidental activation risk.
3. The new set must remain parallel, not a hidden branch of the old set.
4. Review and rollback must be isolated.

### Accidental activation prevention strategy

Future inert seed must enforce all of the following together:

1. Every new `product_templates` row uses `active=False`.
2. The new composer is not added to owner-valid offerable scope.
3. The new composer is not added to Work Intake routing or picker surfaces.
4. Any module-link rows created for the new set stay `active=False` until owner GO.
5. The new component templates carry empty executable BOM arrays until their truth contract is explicitly implemented.
6. Any contract metadata stored in JSON must clearly say `planned`, not `calculable` or `offerable`.

### Duplication prevention stance versus old templates

The new set must be seeded as a parallel candidate family with a different naming namespace.

Required namespace separation:

- Product root stays `TPL-LETTERS-COMPOSER_v1`
- Components stay `TPL-COMP-LETTER-*`
- Component ids stay new and non-overlapping
- No aliasing to `comp_face_litere`, `comp_spate_litere`, `comp_lateral_litere`, `comp_led_litere`, `comp_finisaj_litere`

## Proposed template rows

### Composer row

- `template_code`: `TPL-LETTERS-COMPOSER_v1`
- `family_id`: `litere_component_first_candidate`
- `family_name`: `Litere component-first candidate`
- `active`: `False`

### Component rows

- `TPL-COMP-LETTER-FACE_v1`
- `TPL-COMP-LETTER-BACK_v1`
- `TPL-COMP-LETTER-RETURN-CANT_v1`
- `TPL-COMP-LETTER-LED_v1`
- `TPL-COMP-LETTER-FINISH_v1`
- `TPL-COMP-LETTER-MOUNTING_v1`

All six component rows must also seed with:

- `active=False`
- no Work Intake root behavior
- no offerable behavior
- no BOM execution assumption

## Inactive composer seed shape

### Composer row intent

`TPL-LETTERS-COMPOSER_v1` is only a composition contract holder.

It must not hold:

- face material truth
- back material truth
- return/cant truth
- LED truth
- finish truth
- mounting truth
- executable operation truth
- required runtime material BOM

### Proposed persisted shape inside current schema

Because `product_templates` has no dedicated graph/status metadata columns beyond the generic JSON payloads, the future inert composer seed should use the existing columns like this:

- `components_json`: composition-only contract payload
- `operations_json`: empty list `[]`
- `required_materials_json`: empty list `[]`
- `notes`: explicit activation guard text

### Composer payload shape inside `components_json`

```json
[
  {
    "component_id": "comp_letter_face_v1",
    "component_template_code": "TPL-COMP-LETTER-FACE_v1",
    "role": "face",
    "kind": "structural",
    "required": true,
    "readiness_state": "planned",
    "dependencies": []
  },
  {
    "component_id": "comp_letter_back_v1",
    "component_template_code": "TPL-COMP-LETTER-BACK_v1",
    "role": "back",
    "kind": "structural",
    "required": true,
    "readiness_state": "planned",
    "dependencies": ["comp_letter_face_v1"]
  },
  {
    "component_id": "comp_letter_return_cant_v1",
    "component_template_code": "TPL-COMP-LETTER-RETURN-CANT_v1",
    "role": "return_cant",
    "kind": "structural",
    "required": true,
    "readiness_state": "planned",
    "dependencies": ["comp_letter_face_v1"]
  },
  {
    "component_id": "comp_letter_led_v1",
    "component_template_code": "TPL-COMP-LETTER-LED_v1",
    "role": "lighting",
    "kind": "functional",
    "required": false,
    "readiness_state": "planned",
    "dependencies": ["comp_letter_face_v1"]
  },
  {
    "component_id": "comp_letter_finish_v1",
    "component_template_code": "TPL-COMP-LETTER-FINISH_v1",
    "role": "finish",
    "kind": "functional",
    "required": true,
    "readiness_state": "planned",
    "dependencies": [
      "comp_letter_face_v1",
      "comp_letter_back_v1",
      "comp_letter_return_cant_v1"
    ]
  },
  {
    "component_id": "comp_letter_mounting_v1",
    "component_template_code": "TPL-COMP-LETTER-MOUNTING_v1",
    "role": "mounting",
    "kind": "functional",
    "required": false,
    "readiness_state": "planned",
    "dependencies": ["comp_letter_back_v1", "product_root"]
  }
]
```

### Composer-level metadata that should live in `notes`

Recommended guard note payload, serialized as plain text or structured JSON string in `notes`:

```text
status=inert_candidate
offerable=false
work_intake_exposed=false
pricing_active=false
product_definition_active=false
owner_go_required=true
activation_guard=ALL_COMPONENT_TRUTH_INCOMPLETE
```

### Composer blockers

- `OWNER_GO_REQUIRED`
- `SEED_TESTS_NOT_RUN`
- `COMPONENT_TRUTH_NOT_IMPLEMENTED`
- `PRODUCT_SYSTEM_READONLY_NOT_PROVEN`
- `NO_DEPENDENCY_GRAPH_RUNTIME_REVIEW`

### Composer readiness state

- `planned`

### Composer activation guard

The composer can exist in DB later, but until all activation guards are cleared it must remain:

- inactive in DB
- not owner-valid
- not Work Intake exposed
- not ProductDefinition-active
- not Pricing-active

## Component seed shapes

Common rule for all six component seeds:

- `active=False`
- `operations_json=[]`
- `required_materials_json=[]`
- `components_json` stores only component contract metadata
- `notes` carries explicit `planned` / blocked activation guard text

### A. FACE — `TPL-COMP-LETTER-FACE_v1`

- `component_id`: `comp_letter_face_v1`
- `role`: `face`
- `kind`: `structural`
- `required_inputs`:
  - `layer_group_ids`
  - `selected_layer_refs`
  - `face_material_code`
  - `face_thickness_mm`
  - `face_finish_target`
- `outputs`:
  - `confirmed_area_m2`
  - `confirmed_perimeter_m`
  - `face_geometry_ref`
  - `face_cutting_operation_ref`
- `dependencies`: none upstream beyond source SVG/layer confirmation
- `blockers`:
  - `SOURCE_LAYERS_UNCONFIRMED`
  - `FACE_MATERIAL_MISSING`
  - `FACE_THICKNESS_MISSING`
- `readiness_state`: `planned`
- `product_truth_target_path`: `components.face.instances[]`
- `operation_refs`:
  - `face_cnc_cut`
  - `vinyl_application` as future optional finish-adjacent consequence only
- `material_refs`:
  - `face_material_code`
- `resource_refs`:
  - `cnc_router_capacity`
  - `face_sheet_consumption_policy`
- `activation_guard`: `FACE_CONTRACT_ONLY_NOT_EXECUTABLE`

### B. BACK — `TPL-COMP-LETTER-BACK_v1`

- `component_id`: `comp_letter_back_v1`
- `role`: `back`
- `kind`: `structural`
- `required_inputs`:
  - `source_face_geometry_ref`
  - `back_material_code`
  - `back_thickness_mm`
  - `backing_mode`
- `outputs`:
  - `back_geometry_ref`
  - `back_cut_operation_ref`
  - `back_material_consumption_ref`
- `dependencies`:
  - `comp_letter_face_v1`
- `blockers`:
  - `FACE_GEOMETRY_REF_MISSING`
  - `BACK_MATERIAL_MISSING`
  - `BACKING_MODE_MISSING`
- `readiness_state`: `planned`
- `product_truth_target_path`: `components.back.instances[]`
- `operation_refs`:
  - `back_cut`
- `material_refs`:
  - `back_material_code`
- `resource_refs`:
  - `back_sheet_consumption_policy`
- `activation_guard`: `BACK_CONTRACT_ONLY_NOT_EXECUTABLE`

### C. RETURN_CANT — `TPL-COMP-LETTER-RETURN-CANT_v1`

- `component_id`: `comp_letter_return_cant_v1`
- `role`: `return_cant`
- `kind`: `structural`
- `required_inputs`:
  - `source_face_perimeter_ref`
  - `material_profile_code`
  - `depth_mm`
  - `finish_type`
  - `color_source`
  - `layer_group_ids`
- `outputs`:
  - `confirmed_perimeter_m`
  - `return_profile_material_ref`
  - `modelare_cant_operation_ref`
  - `bonding_operation_ref`
- `dependencies`:
  - `comp_letter_face_v1`
- `blockers`:
  - `SOURCE_FACE_PERIMETER_REF_MISSING`
  - `MATERIAL_PROFILE_MISSING`
  - `DEPTH_MM_MISSING`
  - `CONFIRMATION_STATE_MISSING`
- `readiness_state`: `planned`
- `product_truth_target_path`: `components.return_cant.instances[]`
- `operation_refs`:
  - `RETURN_PROFILE_MACHINE_FORMING`
  - `RETURN_PROFILE_FACE_BONDING`
  - `PAINTING`
- `material_refs`:
  - `MAT-PROFIL-LATERAL-*`
  - `MAT-ORACAL-651`
  - `MAT-VOPSEA-RAL`
  - `MAT-ADEZIV-CANT-LITERE`
- `resource_refs`:
  - `return_profile_machine_requirement`
  - `paint_line_requirement`
- `activation_guard`: `RETURN_CANT_CONTRACT_ONLY_NOT_EXECUTABLE`

### D. LED — `TPL-COMP-LETTER-LED_v1`

- `component_id`: `comp_letter_led_v1`
- `role`: `lighting`
- `kind`: `functional`
- `required_inputs`:
  - `lighting_mode`
  - `source_face_area_ref`
  - `led_density_config`
  - `led_module_type`
  - `psu_policy`
- `outputs`:
  - `led_count`
  - `power_w`
  - `selected_psu_config`
  - `led_install_operation_ref`
- `dependencies`:
  - `comp_letter_face_v1`
- `blockers`:
  - `LIGHTING_MODE_MISSING`
  - `SOURCE_FACE_AREA_REF_MISSING`
  - `LED_DENSITY_CONFIG_MISSING`
- `readiness_state`: `planned`
- `product_truth_target_path`: `components.led.instances[]`
- `operation_refs`:
  - `led_install_letters`
  - `electrical_letters`
- `material_refs`:
  - `MAT-LED-MODULE`
  - `MAT-LED-PSU-12V`
- `resource_refs`:
  - `electrical_assembly_requirement`
- `activation_guard`: `LED_CONTRACT_ONLY_NOT_EXECUTABLE`

### E. FINISH — `TPL-COMP-LETTER-FINISH_v1`

- `component_id`: `comp_letter_finish_v1`
- `role`: `finish`
- `kind`: `functional`
- `required_inputs`:
  - `finish_target_component_ids`
  - `finish_type`
  - `color_code`
  - `print_required`
  - `lamination_required`
- `outputs`:
  - `finish_operation_refs`
  - `finish_material_refs`
  - `finish_scope_summary`
- `dependencies`:
  - `comp_letter_face_v1`
  - `comp_letter_back_v1`
  - `comp_letter_return_cant_v1`
- `blockers`:
  - `FINISH_TARGET_MISSING`
  - `FINISH_TYPE_MISSING`
  - `COLOR_DECISION_MISSING`
- `readiness_state`: `planned`
- `product_truth_target_path`: `components.finish.instances[]`
- `operation_refs`:
  - `painting`
  - `print_application`
  - `lamination_application`
- `material_refs`:
  - `finish_film_code`
  - `paint_code`
  - `print_media_code`
- `resource_refs`:
  - `paint_line_requirement`
  - `print_station_requirement`
- `activation_guard`: `FINISH_CONTRACT_ONLY_NOT_EXECUTABLE`

### F. MOUNTING — `TPL-COMP-LETTER-MOUNTING_v1`

- `component_id`: `comp_letter_mounting_v1`
- `role`: `mounting`
- `kind`: `functional`
- `required_inputs`:
  - `mounting_mode`
  - `wall_type`
  - `mounting_height_mm`
  - `support_required`
- `outputs`:
  - `mounting_operation_refs`
  - `support_material_refs`
  - `mounting_strategy_summary`
- `dependencies`:
  - `comp_letter_back_v1`
  - `product_root`
- `blockers`:
  - `MOUNTING_MODE_MISSING`
  - `SUPPORT_REQUIRED_UNKNOWN`
  - `INSTALL_CONTEXT_MISSING`
- `readiness_state`: `planned`
- `product_truth_target_path`: `components.mounting.instances[]`
- `operation_refs`:
  - `premount_bar_preparation`
  - future mounting installation family refs
- `material_refs`:
  - `MAT-PREMOUNT-BAR-STEEL`
  - `MAT-PREMOUNT-BAR-ALUMINUM`
- `resource_refs`:
  - `metal_fab_requirement`
  - `mounting_kit_requirement`
- `activation_guard`: `MOUNTING_CONTRACT_ONLY_NOT_EXECUTABLE`

## Dependency graph persistence shape

Required graph:

```text
FACE -> RETURN_CANT
FACE -> BACK
FACE -> LED
FACE / BACK / RETURN_CANT -> FINISH
BACK / PRODUCT -> MOUNTING
```

### Persistence conclusion

#### Source of truth

The primary source of truth for this graph should be the composer seed metadata.

Reason:

- the graph expresses composition orchestration
- composition is the Product Template responsibility
- the graph must stay product-level even when components own their own truth

#### Component-local derived hints

Each component seed should also repeat only its immediate upstream dependencies in its own contract metadata.

Reason:

- component validation must know what it depends on
- but component metadata must not become the master graph for the whole product

#### Shared contract role

`shared_volumetric_component_contracts.py` should remain descriptive architecture metadata, not the primary persistence source for the new graph.

Meaning:

- it can later mirror roles and labels
- it must not be the first canonical storage for composer dependency orchestration

#### Mini-module registry role

`mini_module_registry_volumetric_v2.py` should remain runtime/read-model/operational registry direction, not the initial source of truth for this inert seed graph.

Meaning:

- registry is derived/executable support
- seed plan graph is earlier and safer as composition metadata

#### Read-model duplication allowed

One limited duplication is acceptable later:

- composer stores canonical dependency graph
- component seed stores immediate dependency hints
- ProductAggregate or UI may derive a read-model map from those rows

That duplication is acceptable only if read-model outputs are clearly derived.

## Compatibility stance

### Old set status

The old set remains active and authoritative for runtime:

- `TPL-VOLUMETRIC-LETTERS_v2`
- `TPL-VOLUMETRIC-FACE_v1`
- `TPL-VOLUMETRIC-BACK_v1`
- `TPL-VOLUM-ALUMINIU_v1`
- `TPL-VOLUMETRIC-LED_v1`
- `TPL-VOLUMETRIC-FINISH_v1`
- `TPL-METAL-PREMOUNT-STRUCTURE_v1`

### Old set must remain

- active runtime root where already active today
- compatibility surface for current ProductAggregate behavior
- diagnostic surface for current Product System UI
- source of current tests and current Work Intake routing

### Deprecation stance now

Do not mark the old set deprecated in runtime behavior during the seed implementation slice.

Docs-only interpretation allowed later:

- `legacy_active_runtime`
- `replacement_not_ready`

### `components.returnCant.*` stance

Keep as compatibility and diagnostic alias family for now.

Do not delete because:

1. readonly mapper language still depends on it
2. migration to `components.return_cant.instances[]` is not complete
3. old runtime proof still references the alias layer

### When old set can become delete candidate

Only after all of the following are true:

1. new component-first set is seeded and verified inert
2. readonly Product System view for the new set exists and passes
3. component truth fields are actually implemented, not only planned
4. ProductDefinition consumption path is explicitly reviewed
5. Pricing boundary is explicitly reviewed
6. old runtime consumers have zero dependency on the old rows
7. owner GO explicitly opens delete-candidate review

### What must not be deleted yet

- `TPL-VOLUMETRIC-LETTERS_v2`
- old component templates
- old active module links
- parent support rows consumed by current diagnostics
- old dossier-derived aggregate inputs
- `components.returnCant.*` compatibility layer

## Fixture and test plan

No tests were implemented in this task. This is the planned test matrix for the later inert seed implementation slice.

### Seed inactive tests

1. composer row seeds with `active=False`
2. all six component rows seed with `active=False`
3. any new module links seed with `active=False`

### No Work Intake exposure tests

1. new composer is absent from owner-valid Work Intake roots
2. availability endpoint does not classify new composer as `offerable_product`
3. UI label remains candidate/archived/inactive only

### No Pricing activation tests

1. pricing registry paths do not consume the new composer
2. no quote-offerable scope includes `TPL-LETTERS-COMPOSER_v1`
3. empty BOM arrays do not create priced aggregate rows

### Composer boundary tests

1. composer has empty `operations_json`
2. composer has empty `required_materials_json`
3. composer `components_json` contains composition metadata only
4. composer does not masquerade as technical truth container

### Component contract tests

1. each new component template exists with the expected `template_code`
2. each component template exposes the expected `component_id`
3. each component template carries `planned` readiness state
4. each component template declares expected blockers
5. each component template declares expected Product Truth target path

### Dependency graph tests

1. composer metadata stores the exact expected edges
2. component-local dependency hints do not contradict composer graph
3. mounting depends on `back` plus `product_root`

### Old/new coexistence tests

1. old letters v2 remains offerable
2. new composer remains non-offerable
3. old component templates remain visible to current runtime
4. new component-first set does not replace old links

### ProductAggregate non-consumption tests

1. ProductAggregate for old letters v2 remains unchanged
2. no old aggregate row points to the new component-first set
3. new inert templates do not appear as executable linked modules until explicit activation work

## Activation guards

Before the new set can become active, all of these must be true:

1. owner GO recorded explicitly
2. inert seed tests pass
3. Product System readonly display for the new set passes
4. fixture comparison between old and new set passes
5. old template replacement is still blocked until separate approval
6. component truth fields are implemented and verified per component
7. ProductAggregate read-model boundary is rechecked with the new set present
8. ProductDefinition consumption boundary is reviewed and approved
9. Pricing boundary is reviewed and approved
10. Work Intake exposure is reviewed and approved

Mandatory pre-activation rule:

```text
No activation only because rows exist in DB.
Activation requires explicit scope-opening work after component truth completeness.
```

## Risks

### Risk 1

If the implementation later seeds executable BOM rows too early, ProductAggregate or downstream diagnostics may start treating the new set as real runtime input.

### Risk 2

If module links are created active by mistake, the availability view may surface the new family in ways that confuse owner review.

### Risk 3

If new component ids reuse old ids, coexistence tests and diagnostics will become ambiguous.

### Risk 4

If shared contract metadata is promoted to graph source-of-truth, product orchestration and component validation boundaries will blur again.

### Risk 5

If the old active set is marked deprecated too early, current runtime audits and readonly diagnostics lose their baseline before the new set is proven.

## Recommendation

Next implementation slice should remain narrow:

1. create the grouped inert seed only
2. create inactive template rows only
3. create inactive module-link rows only if needed for future visibility
4. keep BOM/runtime arrays empty or metadata-only
5. add only focused seed/availability tests

Do not do yet:

1. ProductDefinition consumption
2. Pricing activation
3. Work Intake activation
4. ProductAggregate runtime behavior changes
5. old-set replacement
6. delete review

## Forbidden scope confirmation

- No implementation of the seeds happened here.
- No seed file was created.
- No backend code was modified.
- No frontend code was modified.
- No DB schema was modified.
- No migration was run.
- No live seed was run.
- No Pricing work was done.
- No ProductDefinition work was done.
- No Product Truth writer work was done.
- No ProductAggregate runtime write work was done.
- No old template was replaced.
- No old template was deleted.

## Next recommended prompt

`TASK — COMPONENT_FIRST_LETTERS_TEMPLATE_SET_INACTIVE_SEED_IMPLEMENTATION_V1`

Recommended scope for that future task:

- implement only the grouped inert seed
- no activation
- no Pricing
- no ProductDefinition
- no Work Intake exposure
- no ProductAggregate runtime change
- no delete
- focused seed/availability tests only

## Roadmap awareness checkpoint

- Current spine position: after blueprint approval, before any inert DB presence.
- Direction adherence: `97/100`.
- Dead pieces check: old letters v2 and compatibility aliases are still live and necessary.
- Forbidden scope confirmation: respected in full.