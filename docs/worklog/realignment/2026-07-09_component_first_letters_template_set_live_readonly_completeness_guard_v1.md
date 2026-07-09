# COMPONENT_FIRST_LETTERS_TEMPLATE_SET_LIVE_READONLY_COMPLETENESS_GUARD_V1

## Scope

- Readonly completeness guard only.
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
- No LOGO activation.

## HEAD before

- `22b6fe3`

## Files read

- `docs/worklog/realignment/2026-07-09_component_first_letters_template_set_inactive_backend_readonly_alignment_v1.md`
- `docs/worklog/realignment/2026-07-09_component_first_letters_template_set_inactive_readonly_product_system_slice_v1.md`
- `docs/worklog/realignment/2026-07-09_component_first_letters_template_set_inactive_seed_implementation_v1.md`
- `backend/seeds/seed_tpl_letters_component_first_v1.py`
- `frontend/src/pages/ProductSystem.tsx`
- `frontend/src/pages/ProductSystem.badges.test.tsx`
- `frontend/src/lib/api.ts`

## Searches run

- `LIVE SEEDED INACTIVE ROWS`
- `CODE CONTRACT FALLBACK`
- `TPL-LETTERS-COMPOSER_v1`
- `TPL-COMP-LETTER-FACE_v1`
- `TPL-COMP-LETTER-BACK_v1`
- `TPL-COMP-LETTER-RETURN-CANT_v1`
- `TPL-COMP-LETTER-LED_v1`
- `TPL-COMP-LETTER-FINISH_v1`
- `TPL-COMP-LETTER-MOUNTING_v1`
- `product-system-component-first-source-label`
- `component-first letters template set`
- `active = false`
- `inactive`
- `candidate`
- `readonly`
- `buildComponentFirstReadonlySetModel`
- `componentFirstSourceLabel`

## Current source-state audit

### Where is sourceMode/sourceLabel calculated now?

Before this slice:

- `buildComponentFirstReadonlySetModel()` in `ProductSystem.tsx`
- `componentFirstSourceLabel()` mapped only two states

After this slice:

- `assessComponentFirstLiveCompleteness()` in `frontend/src/features/product-system/componentFirstReadonlyCompleteness.ts`
- `buildComponentFirstReadonlySetModel()` consumes that assessment and maps four source states

### What condition previously triggered LIVE SEEDED INACTIVE ROWS?

Composer row present in API/catalog was sufficient.

### Was composer alone sufficient?

Yes. That was the gap.

### Was there verification for all 6 component rows?

No.

### Was there verification that all rows have `active = false`?

No.

### Was partial live possible?

Yes, but it was mislabeled as full live when composer existed.

### Was invalid active row possible?

Yes, but it could still read as live seeded inactive.

## Expected rows list

Composer:

- `TPL-LETTERS-COMPOSER_v1`

Components:

- `TPL-COMP-LETTER-FACE_v1`
- `TPL-COMP-LETTER-BACK_v1`
- `TPL-COMP-LETTER-RETURN-CANT_v1`
- `TPL-COMP-LETTER-LED_v1`
- `TPL-COMP-LETTER-FINISH_v1`
- `TPL-COMP-LETTER-MOUNTING_v1`

Expected total:

- `7`

Central definition:

- `COMPONENT_FIRST_EXPECTED_TEMPLATE_CODES`
- `COMPONENT_FIRST_EXPECTED_ROW_COUNT`

## Completeness rule

Assessment order:

1. If any expected live row has `active !== false` -> `blocked_invalid_live_state`
2. Else if `foundRowCount === 0` -> `code_contract_fallback`
3. Else if `foundRowCount === 7` and every found row has `active === false` -> `live_seeded_inactive`
4. Else -> `partial_live_inactive`

UI must never claim full live completeness unless rule 3 is true.

## Source states

### A. LIVE SEEDED INACTIVE ROWS

When:

- `7/7` expected rows found
- all found rows have `active === false`

### B. PARTIAL LIVE INACTIVE ROWS

When:

- `0 < foundRowCount < 7`
- no activation leak
- missing rows use readonly contract fallback in the component list

### C. CODE CONTRACT FALLBACK

When:

- `foundRowCount === 0`
- full readonly contract preview is shown

### D. BLOCKED / INVALID LIVE STATE

When:

- any expected row exists with `active !== false`

## UI changes

Frontend-only readonly refinement in `ProductSystem.tsx`:

- new completeness helper module
- source label now supports 4 states
- new badge `completeness: X/7`
- missing live rows list for partial/fallback states
- invalid active rows list for blocked state
- component cards mark `contract fallback row` when a live row is absent in partial state

No buttons, no mutations, no new workflow actions.

## Tests run

```powershell
Set-Location C:\Users\offic\workos_app_vs\frontend
npm.cmd run test -- src/pages/ProductSystem.badges.test.tsx
```

Result:

- `9 passed`

Verified:

- complete `7/7` inactive rows => `LIVE SEEDED INACTIVE ROWS`
- `0/7` live rows => `CODE CONTRACT FALLBACK`
- partial `3/7` => `PARTIAL LIVE INACTIVE ROWS`
- any expected row active => `BLOCKED / INVALID LIVE STATE`
- completeness count `X/7`
- missing rows shown in partial state
- no activate/promote/write/pricing/create-quote buttons

## Screenshot paths

- `docs/worklog/realignment/assets/2026-07-09_component_first_letters_template_set_live_readonly_completeness_guard_v1/product_system_overview_context.png`
- `docs/worklog/realignment/assets/2026-07-09_component_first_letters_template_set_live_readonly_completeness_guard_v1/component_first_letters_template_set_section.png`
- `docs/worklog/realignment/assets/2026-07-09_component_first_letters_template_set_live_readonly_completeness_guard_v1/component_first_source_label_closeup.png`
- `docs/worklog/realignment/assets/2026-07-09_component_first_letters_template_set_live_readonly_completeness_guard_v1/component_first_completeness_count_closeup.png`
- `docs/worklog/realignment/assets/2026-07-09_component_first_letters_template_set_live_readonly_completeness_guard_v1/component_first_activation_guard_closeup.png`

Live browser proof in current environment:

- `CODE CONTRACT FALLBACK`
- `completeness: 0/7`

This is correct because seed live remains forbidden and the inert rows are not present in the current DB.

## Sincere UI opinion

### Is live complete clear?

Yes. `LIVE SEEDED INACTIVE ROWS` now requires `7/7`, not composer-only presence.

### Is fallback clear?

Yes. `CODE CONTRACT FALLBACK` plus `0/7` and the missing-rows list make the absence explicit.

### Is partial clear?

Yes. `PARTIAL LIVE INACTIVE ROWS`, `X/7`, missing rows, and `contract fallback row` chips reduce ambiguity.

### Is invalid/blocked clear?

Yes. `BLOCKED / INVALID LIVE STATE` with invalid row codes is direct and hard to misread as inert.

### Risk that it still looks active/offerable?

Low. INACTIVE / CANDIDATE / READONLY chips remain, and blocked/partial labels are visually distinct.

### What remains too technical?

Missing-row codes and blocker lists are still engineering-facing. Acceptable for this stage, but owner-language summary can still improve later.

## Risks

### Risk 1

Partial live environments can still look information-dense because fallback contract rows fill missing slots.

### Risk 2

Completeness is assessed in the frontend layer; backend transport shape did not change.

### Risk 3

If a later slice seeds only some rows live without owner review, the UI will now correctly refuse full-live labeling, but operators must understand partial is not failure—it is guarded visibility.

## Recommendation

Next slice:

1. `COMPONENT_FIRST_LETTERS_TEMPLATE_SET_READONLY_FIXTURE_COMPARISON_V1`

Suggested goal:

- compare old letters v2 vs new component-first readonly structure using controlled fixtures
- still readonly only

What must wait:

1. Work Intake exposure
2. Pricing activation
3. ProductDefinition activation
4. ProductAggregate runtime wiring
5. seed live without owner GO
6. old-set replacement
7. delete review

What must not be deleted yet:

1. `TPL-VOLUMETRIC-LETTERS_v2`
2. old component templates
3. `components.returnCant.*` compatibility language
4. old diagnostics/read-model support rows

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
- No worktree cleanup
- No untracked/noise staged

## Next recommended prompt

`TASK — COMPONENT_FIRST_LETTERS_TEMPLATE_SET_READONLY_FIXTURE_COMPARISON_V1`

Recommended scope:

- readonly only
- fixture comparison between old active letters set and new component-first inert set
- no activation
- no Pricing
- no ProductDefinition
- no ProductAggregate runtime mutation
- no seed live
- no delete

## Roadmap awareness checkpoint

- Current spine position: blueprint done, inert seed done, readonly Product System proof done, source provenance clarified, live completeness guard done, still before activation or live seed adoption.
- Direction adherence: `99/100`.
- Dead pieces check: old letters v2, old component templates, and compatibility aliases remain necessary.
- Forbidden scope confirmation: respected in full.
