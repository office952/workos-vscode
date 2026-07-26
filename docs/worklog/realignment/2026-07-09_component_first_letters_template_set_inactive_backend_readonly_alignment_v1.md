# COMPONENT_FIRST_LETTERS_TEMPLATE_SET_INACTIVE_BACKEND_READONLY_ALIGNMENT_V1

## Scope

- Read-only source alignment only.
- No activation.
- No Work Intake exposure.
- No Pricing activation.
- No ProductDefinition activation.
- No ProductAggregate runtime mutation.
- No Product Truth writer change.
- No delete.
- No old-set replacement.
- No `seed_sync_all` change.
- No seed live.
- No migration.
- UI change limited to source labeling clarity.

## HEAD before

- `1f2df20`

## Files read

- `docs/worklog/realignment/2026-07-09_component_first_letters_template_set_inactive_readonly_product_system_slice_v1.md`
- `docs/worklog/realignment/2026-07-09_component_first_letters_template_set_inactive_seed_implementation_v1.md`
- `docs/worklog/realignment/2026-07-09_component_first_letters_template_set_inactive_seed_plan_v1.md`
- `backend/seeds/seed_tpl_letters_component_first_v1.py`
- `backend/tests/test_seed_tpl_letters_component_first_v1.py`
- `frontend/src/pages/ProductSystem.tsx`
- `frontend/src/pages/ProductSystem.badges.test.tsx`
- `frontend/src/lib/api.ts`
- `backend/services/product_template_availability_service.py`
- `backend/services/product_aggregate_service.py`
- `backend/services/active_template_scope.py`
- `backend/routers/product_templates.py`

## Searches run

- `TPL-LETTERS-COMPOSER_v1`
- `TPL-COMP-LETTER-FACE_v1`
- `TPL-COMP-LETTER-BACK_v1`
- `TPL-COMP-LETTER-RETURN-CANT_v1`
- `TPL-COMP-LETTER-LED_v1`
- `TPL-COMP-LETTER-FINISH_v1`
- `TPL-COMP-LETTER-MOUNTING_v1`
- `code contract fallback`
- `ProductTemplateAvailabilityService`
- `product_templates router`
- `productTemplatesApi`
- `ProductAggregate`
- `seed_sync_all`
- `active_template_scope`
- `no module links`
- `operations_json`
- `required_materials_json`

## Backend readonly source audit

### Does a GET endpoint already exist that can read the 7 inactive rows?

Yes.

The existing entity route under `backend/routers/product_templates.py` already exposes `GET /api/v1/entities/product_templates` and `GET /api/v1/entities/product_templates/all`, and the frontend `productTemplatesApi.list()` already consumes that family of routes.

### Can ProductSystem consume inactive rows through the existing API?

Yes.

The frontend already loads:

- template rows through `productTemplatesApi.list()`
- availability metadata through `productTemplateAvailabilityApi.list({ offerable_only: false, include_runtime_modules: true, include_archived: true })`

That is sufficient to read inactive rows when they are present in DB.

### Is only the live-vs-fallback label missing?

Yes.

The previous slice already had enough read-only data-flow, but the source explanation was too soft. It read more like a sentence than a hard provenance state.

### Is a backend helper justified?

No.

There is no shape problem that requires a backend helper. The ambiguity was in presentation, not transport.

### Is a new GET-only endpoint justified?

No.

Current backend surfaces already separate the two required concerns:

- raw template rows
- availability / offerability / archive status

Adding a new endpoint here would duplicate information and increase maintenance surface without improving safety.

### Should the frontend fallback remain temporarily?

Yes.

Reason:

- `seed live` remains forbidden
- the accepted inert seed is intentionally not in `seed_sync_all`
- the browser/live environment may legitimately have no inert rows yet

Therefore the fallback remains acceptable as a temporary readonly contract preview, but it must be clearly labeled and never masquerade as live data.

## Implementation level decision

Decision: `no backend change`

Rationale:

1. existing GET routes already expose inactive template rows when present
2. availability service already excludes the set from active/offerable runtime
3. ProductAggregate is already not the source of this panel
4. the remaining problem was provenance clarity, not backend capability

## Live-vs-fallback labeling

UI labeling is now explicit.

Possible source labels:

- `LIVE SEEDED INACTIVE ROWS`
- `CODE CONTRACT FALLBACK`

Current live browser proof shows:

- `CODE CONTRACT FALLBACK`

Meaning:

- the accepted inert contract exists in code
- live rows are absent in the current environment
- UI is showing a review-safe readonly fallback, not pretending to read live DB rows

The mocked focused frontend test still proves the alternate branch:

- when rows are present in API data, the label becomes `LIVE SEEDED INACTIVE ROWS`

`NOT AVAILABLE / BLOCKED` was not implemented because the accepted fallback is still safe and intentional for this stage.

## Activation leak checks

Confirmed again from accepted prior slices plus current audit:

- `seed_sync_all` does not run the new seed
- no module links are created by the inert seed
- rows are inactive by design
- no Work Intake exposure
- no Pricing activation
- no ProductDefinition activation
- no ProductAggregate runtime consumption path for the set
- no writer path involved
- no mutation endpoint added in this slice

## UI changes

Small frontend-only clarification:

- replaced the soft source sentence with an explicit source badge
- `CODE CONTRACT FALLBACK` now reads as a distinct state, not just narrative text
- supporting explanatory sentence remains beside it

No buttons, no mutations, no new workflow actions.

## Tests run

```powershell
Set-Location C:\Users\offic\workos_app_vs\frontend
npm.cmd run test -- src/pages/ProductSystem.badges.test.tsx
```

Result:

- `5 passed`

Verified relevant points:

- readonly section still appears
- source label is explicit
- mocked API scenario renders `LIVE SEEDED INACTIVE ROWS`
- no activate/promote/write buttons
- no Pricing activation
- no Work Intake exposure
- no ProductDefinition activation

## Screenshot paths

- `docs/worklog/realignment/assets/2026-07-09_component_first_letters_template_set_inactive_backend_readonly_alignment_v1/product_system_overview_context.png`
- `docs/worklog/realignment/assets/2026-07-09_component_first_letters_template_set_inactive_backend_readonly_alignment_v1/component_first_letters_template_set_section.png`
- `docs/worklog/realignment/assets/2026-07-09_component_first_letters_template_set_inactive_backend_readonly_alignment_v1/component_first_source_label_closeup.png`
- `docs/worklog/realignment/assets/2026-07-09_component_first_letters_template_set_inactive_backend_readonly_alignment_v1/component_first_activation_guard_closeup.png`
- `docs/worklog/realignment/assets/2026-07-09_component_first_letters_template_set_inactive_backend_readonly_alignment_v1/component_first_dependency_graph_closeup.png`

## Sincere UI opinion

### Is it clear whether the data is live or fallback?

Yes, now it is materially clearer.

`CODE CONTRACT FALLBACK` reads as state, not commentary. That is a significant improvement over the previous slice.

### Is there still risk that it looks active?

Low.

The source label plus the inactive/candidate/readonly chips make it difficult to misread as active runtime data.

### Is it clearer than the previous slice?

Yes.

The previous slice was accurate, but the provenance depended too much on reading a sentence carefully. The new label makes the distinction scannable.

### What remains too technical?

The blocker list and dependency graph are still engineering-dense. That is acceptable for this stage, but still not owner-optimized language.

## Risks

### Risk 1

The fallback remains code-owned, so it must stay synchronized with the accepted inert seed contract until live rows exist more consistently.

### Risk 2

Because no backend source change was made, consumers still need to understand that live-vs-fallback is resolved in the UI layer.

### Risk 3

If a later slice partially seeds only some rows live, the UI must not overclaim `LIVE SEEDED INACTIVE ROWS` unless the set is complete enough for that label.

## Recommendation

Next slice:

1. `COMPONENT_FIRST_LETTERS_TEMPLATE_SET_LIVE_READONLY_COMPLETENESS_GUARD_V1`

Suggested purpose:

- define exactly what minimum live row presence is required before the UI may label the set as `LIVE SEEDED INACTIVE ROWS`
- keep readonly only

What must wait:

1. Work Intake exposure
2. Pricing activation
3. ProductDefinition activation
4. ProductAggregate runtime wiring
5. old-set replacement
6. delete review

What must not be deleted yet:

1. `TPL-VOLUMETRIC-LETTERS_v2`
2. old component templates
3. `components.returnCant.*` compatibility language
4. old read-model support rows

## Forbidden scope confirmation

- No activation
- No Work Intake exposure
- No Pricing
- No ProductDefinition
- No ProductAggregate runtime mutation
- No Product Truth writer change
- No delete
- No old-set replacement
- No `seed_sync_all` change
- No seed live
- No migration
- No LOGO activation

## Next recommended prompt

`TASK — COMPONENT_FIRST_LETTERS_TEMPLATE_SET_LIVE_READONLY_COMPLETENESS_GUARD_V1`

Recommended scope:

- readonly only
- no activation
- no Pricing
- no ProductDefinition
- no ProductAggregate runtime mutation
- no seed live
- no delete
- define exact completeness criteria for when UI may say `LIVE SEEDED INACTIVE ROWS`

## Roadmap awareness checkpoint

- Current spine position: blueprint done, inert seed done, readonly Product System proof done, source provenance clarified, still before any activation or live seed adoption.
- Direction adherence: `99/100`.
- Dead pieces check: old letters v2, old component templates, and compatibility aliases remain necessary.
- Forbidden scope confirmation: respected in full.