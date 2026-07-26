# COMPONENT_FIRST_LETTERS_TEMPLATE_SET_READONLY_FIXTURE_COMPARISON_V1

## Scope

- Readonly fixture comparison guard only.
- No activation.
- No seed live.
- No `seed_sync_all` change.
- No migration.
- No DB write.
- No backend change.
- No Pricing / ProductDefinition / ProductAggregate / Quote / Order / Execution change.

## HEAD before

- `865ef2f`

## Files touched

- `frontend/src/features/product-system/componentFirstReadonlyCompleteness.ts`
- `frontend/src/features/product-system/componentFirstReadonlyCompleteness.test.ts`
- `frontend/src/pages/ProductSystem.tsx`
- `frontend/src/pages/ProductSystem.badges.test.tsx`
- `docs/worklog/realignment/2026-07-09_component_first_letters_template_set_readonly_fixture_comparison_v1.md`
- `docs/worklog/realignment/assets/2026-07-09_component_first_letters_template_set_readonly_fixture_comparison_v1/*.png`

## Problem closed

After the 7/7 completeness guard, UI knew whether rows were complete, partial, or absent.
This slice adds readonly drift detection between:

- canonical fallback contract fixture
- live seeded inactive rows when present
- UI source/completeness model

## Helper added

Extended `componentFirstReadonlyCompleteness.ts` with:

- `COMPONENT_FIRST_FALLBACK_CONTRACT_FIXTURE`
- `validateComponentFirstFallbackContract()`
- `assessComponentFirstContractDrift()`
- drift labels and contract-check tones

## Drift states

| State | Meaning |
|---|---|
| `NO_DRIFT` | Fallback contract valid; live rows found match contract where metadata exists |
| `FALLBACK_CONTRACT_DRIFT` | Canonical fallback fixture is internally inconsistent |
| `LIVE_ROW_CONTRACT_DRIFT` | Live row metadata/shape differs from fallback contract |
| `LIVE_EXTRA_EXPECTED_FAMILY_ROW` | Unexpected component-first family row in catalog/API |
| `BLOCKED_INVALID_LIVE_STATE` | Active or unsafe inactive live row detected |

## Comparison rules

### Fallback contract

- exactly 7 expected rows
- composer exactly once
- 6 component templates exactly once
- no missing expected code
- no duplicate expected code
- no extra code in fixture
- composer carries full composition list
- component rows carry role/kind/target metadata

### Live rows

- compare only when row exists in API/catalog
- require `active === false` for safe inactive comparison
- compare `family_id`, `family_name`, `notes.template_kind`, `notes.readiness` when present
- compare composer composition codes and component contract metadata when present
- if metadata missing, emit `metadata_unavailable_*` warning and do not invent truth

## UI changes

Readonly drift guard panel in Product System:

- `contract check: OK / WARNING / BLOCKED`
- `expected rows: 7`
- `live rows: X/7`
- `drift: <state>`
- drift warnings / extra family rows / fallback issues / metadata unavailable lists

No CTA, no activate/promote/write controls.

## Tests run

```powershell
cd frontend
npm.cmd run test -- src/features/product-system/componentFirstReadonlyCompleteness.test.ts src/pages/ProductSystem.badges.test.tsx
```

Result:

- `19 passed`

Coverage:

- fallback contract exactly 7 rows
- composer + 6 components
- duplicate expected code => fallback drift
- 7/7 matching inactive live rows => `NO_DRIFT`
- partial live rows reported without live-complete claim
- active row => `BLOCKED_INVALID_LIVE_STATE`
- metadata unavailable => warning only, no invented drift
- extra family row detection
- UI contract check + drift guard rendering

## UI verification

URL:

- `http://127.0.0.1:3000/product-system`

Live browser proof:

- `contract check: OK`
- `drift: NO_DRIFT`
- `live rows: 0/7`

Screenshot paths:

- `docs/worklog/realignment/assets/2026-07-09_component_first_letters_template_set_readonly_fixture_comparison_v1/product_system_overview_context.png`
- `docs/worklog/realignment/assets/2026-07-09_component_first_letters_template_set_readonly_fixture_comparison_v1/component_first_letters_template_set_section.png`
- `docs/worklog/realignment/assets/2026-07-09_component_first_letters_template_set_readonly_fixture_comparison_v1/component_first_contract_comparison_drift_guard_closeup.png`
- `docs/worklog/realignment/assets/2026-07-09_component_first_letters_template_set_readonly_fixture_comparison_v1/component_first_source_state_completeness_closeup.png`
- `docs/worklog/realignment/assets/2026-07-09_component_first_letters_template_set_readonly_fixture_comparison_v1/component_first_activation_no_write_guard_closeup.png`

## Honest limitations

1. Drift comparison is frontend-only; backend transport unchanged.
2. Missing metadata yields warnings, not false PASS on row-shape drift.
3. With 0/7 live rows, comparison is fallback self-check + absence proof, not live-vs-fallback row diff.

## Sincere UI opinion

- Contract check badge makes drift visible without looking like activation.
- `OK` with `0/7` is honest: fallback contract is valid, live comparison not yet possible.
- Metadata warnings may feel noisy once live rows appear without full notes payload.
- Still engineering-facing, but shorter than the full component cards.

## Forbidden scope confirmation

- No seed live
- No `seed_sync_all`
- No migration
- No DB write
- No delete/cleanup
- No writer path
- No activate/promote/write button
- No Pricing
- No ProductDefinition runtime
- No ProductAggregate runtime
- No Quote / Order / Execution
- No Work Intake exposure
- No `TPL-VOLUMETRIC-LETTERS_v2` change
- No LOGO activation
- No component root/quote

## Next recommended slice

`COMPONENT_FIRST_LETTERS_TEMPLATE_SET_READONLY_OWNER_REVIEW_CARD_V1`

Suggested scope:

- owner-language summary card above engineering panel
- readonly only
- no activation
- no seed live

## Roadmap awareness checkpoint

- Spine position: blueprint → inert seed → readonly Product System → source provenance → completeness guard → fixture comparison guard → still before activation/live seed.
- Direction adherence: `99/100`.
