# COMPONENT_FIRST_LETTERS_TEMPLATE_SET_INACTIVE_READONLY_PRODUCT_SYSTEM_SLICE_V1

## Scope

- Readonly Product System UI only.
- No activation.
- No Work Intake exposure.
- No Pricing activation.
- No ProductDefinition activation.
- No ProductAggregate runtime mutation.
- No Product Truth writer change.
- No delete.
- No old-set replacement.
- No seed live.
- No migration.
- No `seed_sync_all` change.
- UI proof required and completed.

## HEAD before

- `7ab7db6`

## Files read

- `docs/worklog/realignment/2026-07-09_component_first_letters_template_set_inactive_seed_implementation_v1.md`
- `docs/worklog/realignment/2026-07-09_component_first_letters_template_set_inactive_seed_plan_v1.md`
- `docs/worklog/realignment/2026-07-09_component_first_letters_template_set_blueprint_v1.md`
- `backend/seeds/seed_tpl_letters_component_first_v1.py`
- `backend/tests/test_seed_tpl_letters_component_first_v1.py`
- `frontend/src/pages/ProductSystem.tsx`
- `frontend/src/pages/ProductSystem.badges.test.tsx`
- `frontend/src/features/product-system/TemplateLibraryView.tsx`
- `frontend/src/lib/api.ts`
- `frontend/src/lib/activeTemplateScope.ts`
- `frontend/src/features/product-system/productSystemNavigation.ts`
- `backend/services/product_template_availability_service.py`
- `backend/services/product_aggregate_service.py`
- `backend/services/active_template_scope.py`

## Searches run

- `TPL-LETTERS-COMPOSER_v1`
- `TPL-COMP-LETTER-FACE_v1`
- `TPL-COMP-LETTER-BACK_v1`
- `TPL-COMP-LETTER-RETURN-CANT_v1`
- `TPL-COMP-LETTER-LED_v1`
- `TPL-COMP-LETTER-FINISH_v1`
- `TPL-COMP-LETTER-MOUNTING_v1`
- `ProductSystem`
- `product-system`
- `active = False`
- `inactive`
- `candidate`
- `ProductTemplateAvailabilityService`
- `ProductAggregate`
- `no module links`
- `operations_json`
- `required_materials_json`

## Files touched

- `frontend/src/pages/ProductSystem.tsx`
- `frontend/src/pages/ProductSystem.badges.test.tsx`
- `docs/worklog/realignment/2026-07-09_component_first_letters_template_set_inactive_readonly_product_system_slice_v1.md`

## Read-only source audit

### Is the new set visible through the current backend service?

Answer: yes in principle, but only if the inert rows exist in the live DB.

Reason:

- `productTemplatesApi.list()` reads all `product_templates` rows.
- `productTemplateAvailabilityApi.list({ offerable_only: false, include_runtime_modules: true, include_archived: true })` includes inactive / archived entries.
- `ProductTemplateAvailabilityService` does not require `quote_offerable` to return archived rows when `include_archived=true`.

### Can ProductSystem read the 7 rows without activation?

Answer: yes, if the rows are present in DB. They remain non-offerable because:

- `active=False`
- owner-valid scope excludes them
- no module links exist

### Does availability service exclude the new set from offerable/active?

Answer: yes.

Confirmed by focused seed tests and by code audit:

- backend owner-valid active scope allows only the existing offerable root set
- inactive rows resolve to non-offerable / archived behavior
- no Work Intake root emerges

### Does ProductAggregate consume the new set?

Answer: no, not as runtime-linked aggregate composition.

Reason:

- the inert seed creates no `product_template_module_links`
- `ProductAggregateService` depends on parent rows, dossier rows, and active module links
- this new set has no dossier rows and no module links

### Is a backend GET-only helper required?

Answer: no.

Final approach:

- frontend existing APIs remain enough when the inert rows exist in DB
- because `seed live` is forbidden in this slice, the UI also carries a readonly `code_contract_fallback` model so the owner can still review the set in browser without activating or seeding it live

This fallback is explicitly labeled as code-contract fallback, not live seeded truth.

## UI changes

Implemented a new readonly panel in `ProductSystem.tsx`:

- title: `Component-first letters template set`
- visible on the Product System catalog screen
- also visible inside the template editor when one of the component-first template codes is selected

The panel surfaces:

- global status chips: `INACTIVE`, `CANDIDATE`, `READONLY`
- `active = false`
- `no Work Intake exposure`
- `no Pricing activation`
- `no ProductDefinition activation`
- `no ProductAggregate runtime wiring`
- `no executable operations`
- `no executable BOM`
- source mode note:
  - `live seeded rows`
  - or `code contract fallback until live seed is intentionally applied`

## Displayed templates

Product Template:

- `TPL-LETTERS-COMPOSER_v1`

Component Templates:

- `TPL-COMP-LETTER-FACE_v1`
- `TPL-COMP-LETTER-BACK_v1`
- `TPL-COMP-LETTER-RETURN-CANT_v1`
- `TPL-COMP-LETTER-LED_v1`
- `TPL-COMP-LETTER-FINISH_v1`
- `TPL-COMP-LETTER-MOUNTING_v1`

## Composer display conclusion

`TPL-LETTERS-COMPOSER_v1` is shown as:

- `Product Template / composer only`
- composition list
- dependency graph authority
- activation guard
- blockers
- explicit statements:
  - `does not own material truth`
  - `does not own operation truth`

This matches the accepted contract direction.

## Component display conclusion

Each of the six component templates is shown with:

- template code
- component id
- structural / functional role
- Product Truth target path
- dependency hints
- blockers
- readiness `planned`
- `active = false`

This is readonly only. No action controls were introduced.

## Dependency graph conclusion

Readable text graph is displayed directly in the panel:

- `comp_letter_face_v1 -> comp_letter_return_cant_v1`
- `comp_letter_face_v1 -> comp_letter_back_v1`
- `comp_letter_face_v1 -> comp_letter_led_v1`
- `comp_letter_face_v1 -> comp_letter_finish_v1`
- `comp_letter_back_v1 -> comp_letter_finish_v1`
- `comp_letter_return_cant_v1 -> comp_letter_finish_v1`
- `comp_letter_back_v1 -> comp_letter_mounting_v1`
- `product_root -> comp_letter_mounting_v1`

No charting, no image graph, no mutation behavior.

## No mutation guarantee

The panel adds no new actions.

Verified absence of:

- activate button
- promote button
- write button
- pricing button
- create quote button
- Work Intake exposure action

The focused frontend test asserts the absence of these mutation labels.

## Tests run

```powershell
Set-Location C:\Users\offic\workos_app_vs\frontend
npm.cmd run test -- src/pages/ProductSystem.badges.test.tsx
```

Result:

- `5 passed`

What the focused test proves now:

- the new readonly section appears
- `TPL-LETTERS-COMPOSER_v1` appears
- all 6 component templates appear
- inactive/candidate/readonly labels appear
- `active = false` appears
- no Pricing / Work Intake / ProductDefinition activation labels appear as false/blocked
- no activate/promote/write/pricing/create-quote buttons appear

## Screenshot paths

- `docs/worklog/realignment/assets/2026-07-09_component_first_letters_template_set_inactive_readonly_product_system_slice_v1/product_system_overview_context.png`
- `docs/worklog/realignment/assets/2026-07-09_component_first_letters_template_set_inactive_readonly_product_system_slice_v1/component_first_letters_template_set_section.png`
- `docs/worklog/realignment/assets/2026-07-09_component_first_letters_template_set_inactive_readonly_product_system_slice_v1/component_first_composer_card_closeup.png`
- `docs/worklog/realignment/assets/2026-07-09_component_first_letters_template_set_inactive_readonly_product_system_slice_v1/component_first_components_list_closeup.png`
- `docs/worklog/realignment/assets/2026-07-09_component_first_letters_template_set_inactive_readonly_product_system_slice_v1/component_first_dependency_graph_closeup.png`
- `docs/worklog/realignment/assets/2026-07-09_component_first_letters_template_set_inactive_readonly_product_system_slice_v1/component_first_activation_guard_closeup.png`

## Sincere UI opinion

### Is it clear for the owner?

Mostly yes.

The strong status chips and the repeated `no activation` style rows make the inactive intent visible early.

### Is it too technical?

Partially yes.

The panel is still owner-usable, but the composition list and graph lines are engineering-heavy. It reads more like an architecture proof panel than a business-facing candidate card.

### Is the inactive state obvious?

Yes.

The top chips, `active = false`, and `code contract fallback` line make it hard to mistake for a live offerable product.

### Is there still risk that it looks active/offerable?

Low, but not zero.

The panel sits inside the live Product System catalog, so a fast scan could still make someone assume the set exists live. The fallback source note helps, but a stronger “not seeded live / review-only” banner would reduce that risk further.

### What should improve later?

1. Add a stronger owner-facing banner like `Not seeded live. Review-only contract preview.`
2. Replace some low-level graph strings with a more human-readable dependency legend.
3. Add a compact summary row with `Why blocked` in owner language, not only technical blockers.

## Risks

### Risk 1

Because live seed is forbidden, the panel currently uses a code-contract fallback when DB rows are absent. That is correct for this slice, but it must remain labeled as fallback so it is not mistaken for live catalog data.

### Risk 2

The panel is information-dense. Without a future owner-language summary, it may still feel more like an engineering audit than a product decision card.

### Risk 3

If a later slice seeds the rows live but changes the contract shape without updating this panel, readonly drift could appear between fallback and DB-backed modes.

## Recommendation

Next slice:

1. `COMPONENT_FIRST_LETTERS_TEMPLATE_SET_INACTIVE_BACKEND_READONLY_ALIGNMENT_V1`

Suggested goal:

- add a minimal backend readonly alignment surface only if needed to make the panel source explicit without relying on fallback once owner wants live diagnostics

What must wait:

1. Work Intake exposure
2. Pricing activation
3. ProductDefinition activation
4. ProductAggregate runtime wiring
5. any old-set replacement
6. any delete review

What must not be deleted yet:

1. `TPL-VOLUMETRIC-LETTERS_v2`
2. old component templates
3. old alias layers such as `components.returnCant.*`
4. old diagnostics/read-model supports

## Forbidden scope confirmation

- No activation.
- No Work Intake exposure.
- No Pricing.
- No ProductDefinition.
- No ProductAggregate runtime mutation.
- No Product Truth writer change.
- No delete.
- No old-set replacement.
- No `seed_sync_all` change.
- No seed live.
- No migration.
- No LOGO activation.

## Next recommended prompt

`TASK — COMPONENT_FIRST_LETTERS_TEMPLATE_SET_INACTIVE_BACKEND_READONLY_ALIGNMENT_V1`

Recommended scope:

- keep readonly only
- no activation
- no Pricing
- no ProductDefinition
- no ProductAggregate runtime mutation
- no seed live
- no delete
- align the UI panel with an explicit backend GET-only source only if owner wants the fallback removed from the live catalog surface

## Roadmap awareness checkpoint

- Current spine position: blueprint done, inert seed done, readonly Product System proof done, still before any backend activation or runtime composition wiring.
- Direction adherence: `99/100`.
- Dead pieces check: old letters v2, old component templates, and compatibility aliases remain necessary and untouched.
- Forbidden scope confirmation: respected in full.