# COMPONENT_FIRST_LETTERS_TEMPLATE_SET_INACTIVE_SEED_IMPLEMENTATION_V1

## Scope

- Implement grouped inert seed only.
- No activation.
- No UI change.
- No delete.
- No old-seed modification.
- No DB schema change.
- No migration.
- No live seed run.
- No Pricing change.
- No ProductDefinition change.
- No ProductAggregate runtime-write change.
- No Product Truth writer change.
- No Quote/Order change.
- No Execution change.
- No LOGO activation.
- No replacement of `TPL-VOLUMETRIC-LETTERS_v2`.

## HEAD before

- `19bbf00`

## Files read

- `docs/worklog/realignment/2026-07-09_component_first_letters_template_set_inactive_seed_plan_v1.md`
- `docs/worklog/realignment/2026-07-09_component_first_letters_template_set_blueprint_v1.md`
- `docs/worklog/realignment/2026-07-09_product_component_composition_contract_v1.md`
- `docs/architecture/product-system/PRODUCT_SYSTEM_PRODUCT_TEMPLATE_VS_COMPONENT_TEMPLATE_CONTRACT.md`
- `docs/architecture/product-system/PRODUCT_SYSTEM_COMPONENT_OWNED_CALCULATION_BOUNDARY.md`
- `docs/architecture/product-system/PRODUCT_SYSTEM_COMPONENT_LEVEL_CALCULATION_READINESS.md`
- `backend/seeds/seed_tpl_volumetric_letters_v2.py`
- `backend/models/product_templates.py`
- `backend/models/product_template_module_links.py`
- `backend/services/product_template_availability_service.py`
- `backend/services/product_aggregate_service.py`
- `backend/services/active_template_scope.py`
- `backend/data/shared_volumetric_component_contracts.py`
- `backend/data/mini_module_registry_volumetric_v2.py`
- `backend/scripts/seed_sync_all.py`
- `backend/tests/test_seed_tpl_volumetric_logo_v1.py`
- `backend/tests/test_active_template_scope.py`
- `backend/tests/_db_fixture.py`

## Searches run

- `ProductTemplate`
- `active`
- `offerable`
- `work intake`
- `availability`
- `seed_tpl_volumetric_letters_v2`
- `components_json`
- `operations_json`
- `required_materials_json`
- `component_template_code`
- `linked_child_allowed`
- `composition_modules`
- `product_template_availability_service`
- `product_aggregate_service`
- `TPL-VOLUMETRIC-LETTERS_v2`
- `TPL-LETTERS-COMPOSER_v1`
- `TPL-COMP-LETTER-FACE_v1`
- `TPL-COMP-LETTER-BACK_v1`
- `TPL-COMP-LETTER-RETURN-CANT_v1`
- `TPL-COMP-LETTER-LED_v1`
- `TPL-COMP-LETTER-FINISH_v1`
- `TPL-COMP-LETTER-MOUNTING_v1`

## Files touched

- `backend/seeds/seed_tpl_letters_component_first_v1.py`
- `backend/tests/test_seed_tpl_letters_component_first_v1.py`
- `docs/worklog/realignment/2026-07-09_component_first_letters_template_set_inactive_seed_implementation_v1.md`

## Seed file created

- `backend/seeds/seed_tpl_letters_component_first_v1.py`

This seed intentionally:

- creates only `product_templates` rows
- creates no `product_template_module_links`
- creates no dossier rows
- creates no executable operations
- creates no executable required materials
- is not registered in `backend/scripts/seed_sync_all.py`

## Templates created

Product Template:

- `TPL-LETTERS-COMPOSER_v1`

Component Templates:

- `TPL-COMP-LETTER-FACE_v1`
- `TPL-COMP-LETTER-BACK_v1`
- `TPL-COMP-LETTER-RETURN-CANT_v1`
- `TPL-COMP-LETTER-LED_v1`
- `TPL-COMP-LETTER-FINISH_v1`
- `TPL-COMP-LETTER-MOUNTING_v1`

## Seed implementation summary

The new grouped seed implements the accepted inert plan in the smallest runtime-safe form:

1. One grouped seed entrypoint only.
2. Seven `product_templates` rows only.
3. Every row persists with `active=False`.
4. Every row persists `operations_json=[]`.
5. Every row persists `required_materials_json=[]`.
6. Composer `components_json` stores composition metadata only.
7. Component `components_json` stores contract metadata only.
8. `notes` stores inert activation metadata because `product_templates` has no explicit `offerable` or `work_intake_exposed` columns.

No new helper file was needed.

## Inactive guarantees

Guaranteed by implementation:

- `active = False` for all 7 rows
- `offerable = false` only in inert metadata, not a new DB column
- `work_intake_exposed = false` only in inert metadata, not a new DB column
- `pricing_active = false` in inert metadata
- `product_definition_active = false` in inert metadata
- `product_aggregate_runtime_consumed = false` in inert metadata
- `operations_json = []`
- `required_materials_json = []`
- no module links created
- no dossiers created

## Composer seed shape implemented

`TPL-LETTERS-COMPOSER_v1` now persists:

- `template_code`
- `family_id`
- `family_name`
- `description`
- `active=False`
- `components_json` with:
  - component composition list
  - target Product Truth paths
  - allowed component variants
  - immediate dependency references
- `notes` JSON with:
  - readiness `planned`
  - blockers
  - activation guard
  - `component_dependency_graph`
  - no-offer / no-Work-Intake / no-Pricing / no-ProductDefinition flags

It does not persist:

- component material truth
- component operation truth
- pricing formulas
- execution task truth
- executable BOM

## Component seed shapes implemented

### FACE

- `TPL-COMP-LETTER-FACE_v1`
- `component_id = comp_letter_face_v1`
- target path `components.face.instances[]`
- required inputs / outputs / blockers / readiness / activation guard persisted in inert metadata

### BACK

- `TPL-COMP-LETTER-BACK_v1`
- `component_id = comp_letter_back_v1`
- target path `components.back.instances[]`
- immediate dependency hint on face geometry persisted in inert metadata

### RETURN_CANT

- `TPL-COMP-LETTER-RETURN-CANT_v1`
- `component_id = comp_letter_return_cant_v1`
- target path `components.return_cant.instances[]`
- immediate dependency hint on `components.face.confirmed_perimeter`

### LED

- `TPL-COMP-LETTER-LED_v1`
- `component_id = comp_letter_led_v1`
- target path `components.led.instances[]`
- immediate dependency hint on `components.face.confirmed_area`

### FINISH

- `TPL-COMP-LETTER-FINISH_v1`
- `component_id = comp_letter_finish_v1`
- target path `components.finish.instances[]`
- immediate dependency hints on FACE / BACK / RETURN_CANT target components

### MOUNTING

- `TPL-COMP-LETTER-MOUNTING_v1`
- `component_id = comp_letter_mounting_v1`
- target path `components.mounting.instances[]`
- immediate dependency hints on BACK plus product install context

## Dependency graph persistence

Implemented as composer metadata only, not runtime behavior.

Canonical graph persisted in composer `notes`:

- FACE -> RETURN_CANT
- FACE -> BACK
- FACE -> LED
- FACE -> FINISH
- BACK -> FINISH
- RETURN_CANT -> FINISH
- BACK -> MOUNTING
- PRODUCT -> MOUNTING

Component templates repeat only local dependency hints inside their own inert contract metadata.

No executable module-link graph was created.

## Activation leak checks

### Check 1 — live seed runner

`backend/scripts/seed_sync_all.py` was inspected.

Result:

- the new seed was not registered there
- no auto-live execution path was introduced

### Check 2 — availability classification

Focused test verified that `ProductTemplateAvailabilityService` does not treat `TPL-LETTERS-COMPOSER_v1` as offerable.

Result:

- `quote_offerable = false`
- `runtime_module = false`
- status resolved as archived/inactive because DB `active=False`

### Check 3 — ProductAggregate / module-link leak

No `ProductTemplateModuleLink` rows are created by the seed.

Result:

- no aggregate-linked module path is introduced
- no old product template gains new child links

### Check 4 — old letters template mutation

Focused test inserted a sentinel `TPL-VOLUMETRIC-LETTERS_v2` row, ran the new seed, and verified the sentinel row remained byte-for-byte unchanged across the tested persisted fields.

## Tests run

```powershell
Set-Location C:\Users\offic\workos_app_vs\backend
.\.venv\Scripts\python.exe -m pytest tests/test_seed_tpl_letters_component_first_v1.py -q
```

Result:

- `3 passed`

Validated by tests:

1. grouped seed builds 7 inert payloads
2. all rows are inactive
3. all rows have empty operations/material arrays
4. composer stores dependency graph metadata
5. component rows store Product Truth target paths
6. composer is not offerable in availability
7. no module links are created
8. old `TPL-VOLUMETRIC-LETTERS_v2` row is not touched
9. new seed is not present in `SEED_PIPELINE`

## Risks

### Risk 1

Because no module links are created, the new set remains intentionally invisible to composition-driven runtime and aggregate paths until a later explicit slice.

### Risk 2

The inert metadata lives in `notes` and `components_json` because the current schema has no dedicated `offerable`, `work_intake_exposed`, or dependency-graph columns.

### Risk 3

If a later slice registers this seed inside `seed_sync_all.py` without owner GO, the inert set will start appearing in environments that run the canonical seed pipeline.

## Forbidden scope confirmation

- No old seed file was modified.
- No DB schema was modified.
- No migration was run.
- No live seed was run.
- No Pricing path was changed.
- No ProductDefinition path was changed.
- No Product Truth writer path was changed.
- No ProductAggregate runtime write path was changed.
- No UI was changed.
- No LOGO behavior was changed.
- No old set was deprecated.
- No old set was replaced.
- No delete happened.

## Next recommended prompt

`TASK — COMPONENT_FIRST_LETTERS_TEMPLATE_SET_INACTIVE_READONLY_PRODUCT_SYSTEM_SLICE_V1`

Recommended next scope:

- read-only only
- no activation
- no Pricing
- no ProductDefinition
- no ProductAggregate runtime mutation
- surface the new inert set in Product System diagnostics only if owner wants preview visibility

## Roadmap awareness checkpoint

- Current spine position: blueprint done, seed plan done, inert seed rows implemented, still before any readonly preview or activation discussion.
- Direction adherence: `99/100`.
- Dead pieces check: old letters v2 and compatibility aliases remain necessary and untouched.
- Forbidden scope confirmation: respected in full.