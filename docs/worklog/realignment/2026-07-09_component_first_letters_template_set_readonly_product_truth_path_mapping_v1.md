# COMPONENT_FIRST_LETTERS_TEMPLATE_SET_READONLY_PRODUCT_TRUTH_PATH_MAPPING_V1

## Scope

- Readonly Product Truth path mapping contract only.
- No Product Truth write.
- No Intake V6 activation.
- No Work Intake exposure.
- No live Form System activation.
- No seed live / seed_sync_all / migration / DB write.
- No backend change.
- No Pricing / ProductDefinition / ProductAggregate / Quote / Order / Execution change.

## HEAD before

- `39639d1`

## Files touched

- `frontend/src/features/product-system/componentFirstReadonlyProductTruthMapping.ts`
- `frontend/src/features/product-system/componentFirstReadonlyCompleteness.test.ts`
- `frontend/src/pages/ProductSystem.tsx`
- `frontend/src/pages/ProductSystem.badges.test.tsx`
- `docs/worklog/realignment/2026-07-09_component_first_letters_template_set_readonly_product_truth_path_mapping_v1.md`
- `docs/worklog/realignment/assets/2026-07-09_component_first_letters_template_set_readonly_product_truth_path_mapping_v1/*.png`

## Problem closed

Form System readiness declared future field groups, but Product Truth destination paths were implicit.
This slice maps field groups to future `product.components.*` paths with strict source/state policy and `may_write_now: false` everywhere.

## Helper added

`componentFirstReadonlyProductTruthMapping.ts`:

- `COMPONENT_FIRST_PRODUCT_TRUTH_MAPPING_CONTRACT` (29 entries: composer 3 + components 26)
- `validateComponentFirstProductTruthMappingContract()`
- `assessComponentFirstProductTruthMapping(formReadiness, ownerSummary)`
- compact path summaries for UI

## Mapping states

| State | When |
|---|---|
| `READONLY_MAPPING_READY` | form READONLY_READY_FOR_MAPPING + full contract + no write |
| `READONLY_MAPPING_FALLBACK_ONLY` | form READONLY_FALLBACK_ONLY |
| `READONLY_MAPPING_PARTIAL` | partial form readiness or incomplete contract |
| `BLOCKED_INVALID_LIVE_STATE` | form blocked invalid live |
| `BLOCKED_PRODUCT_TRUTH_WRITE_LEAK` | may_write_now true or unsafe state policy |

## State policy

- `suggested` != `confirmed_later`
- `fallback_readonly` / `hydrated_readonly` != confirmed
- `manual_draft` is not Product Truth
- `confirmed_later` requires future owner GO + operator confirmation
- All entries: `may_write_now: false`, `writePolicy: readonly_mapping_only`

## UI block

**Product Truth mapping** below Form System readiness:

- Mapping contract X/29
- Runtime link: not linked yet / readonly mapping only
- State badge
- Write policy + state policy lines
- Compact path examples (FACE/LED/FINISH/MOUNTING -> product.components.*)
- Guard: no confirmed Product Truth values / no Intake V6 write

## Relationship to Form System readiness

Consumes `assessComponentFirstFormSystemReadiness` output — mapping blocked when form readiness blocked.

## Tests run

```powershell
cd frontend
npm.cmd run test -- src/features/product-system/componentFirstReadonlyCompleteness.test.ts src/pages/ProductSystem.badges.test.tsx
```

Result:

- `72 passed`

## UI verification

URL:

- `http://127.0.0.1:3000/product-system`

Live browser proof (0/7):

- `Mapping contract: 29/29`
- `Runtime Product Truth link: readonly mapping only`
- `State: READONLY_MAPPING_FALLBACK_ONLY`
- `Write policy: no Product Truth write`
- Form readiness visible above mapping block

Screenshot paths:

- `docs/worklog/realignment/assets/2026-07-09_component_first_letters_template_set_readonly_product_truth_path_mapping_v1/product_system_overview_context.png`
- `docs/worklog/realignment/assets/2026-07-09_component_first_letters_template_set_readonly_product_truth_path_mapping_v1/component_first_letters_template_set_section.png`
- `docs/worklog/realignment/assets/2026-07-09_component_first_letters_template_set_readonly_product_truth_path_mapping_v1/component_first_product_truth_mapping_closeup.png`
- `docs/worklog/realignment/assets/2026-07-09_component_first_letters_template_set_readonly_product_truth_path_mapping_v1/component_first_form_readiness_with_product_truth_mapping.png`
- `docs/worklog/realignment/assets/2026-07-09_component_first_letters_template_set_readonly_product_truth_path_mapping_v1/component_first_no_write_no_confirmed_truth_guard_closeup.png`

## Sincere UI opinion

- **NU scrie Product Truth?** DA — write policy + guard explicit.
- **suggested vs confirmed clar?** DA — state policy line.
- **Cine detine paths?** DA — component-owned paths in compact list.
- **Prea tehnic pentru owner?** DA partial — owner review above still primary.
- **Risc fielduri confirmate?** Scazut — no values shown, only path prefixes.
- **Imbunatatiri viitoare (NU acum):** owner-language path labels, per-field expandable mapping table after GO.

## Forbidden scope confirmation

All forbidden items respected — frontend/docs/tests only.

## Limitations

1. Mapping is code contract only; no runtime Product Truth API.
2. 29 entries not rendered individually in UI (compact summaries only).
3. `confirmed_later` path binding assumes future Intake V6 confirmation flow.

## Next recommended slice

`COMPONENT_FIRST_LETTERS_TEMPLATE_SET_READONLY_LIVE_SEED_DECISION_CARD_V1` (owner GO framing only, still no seed live unless explicit approval)

## Roadmap awareness checkpoint

- Spine: completeness → drift → dossier → owner review → form readiness → Product Truth mapping → still before activation/live seed/Intake write.
- Direction adherence: `99/100`.
