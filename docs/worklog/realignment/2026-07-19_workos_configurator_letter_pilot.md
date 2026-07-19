# Worklog — Configurator Design System Pilot: Volumetric Letters

**Date:** 2026-07-19  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Baseline:** `ee93b19`  
**Mode:** Frontend presentation pilot only

## Design checkpoint

`docs/qa/workos-configurator-letter-pilot-2026-07-19/DESIGN_CHECKPOINT.md` — written **before** code.

## Pilot scope

- Letter finish presentation + Față / Cant / Spate anatomy chrome
- Lighting input vs result separation
- Scoped typography (`v6Pilot`) — no global `v6.page` rewrite
- Technical disclosure demotion (ownership tokens, artwork metadata)
- Tests + live screenshots + isolated commit

## Components changed

- `atoms/intakeV6Presentation.tsx` — add `v6Pilot`
- `reviewFieldLayout.ts` — `PILOT_REVIEW_*` (Montaj keeps `REVIEW_*`)
- `layerCardCollapsedLayout.ts` — summary/name uplift
- `IntakeV6LayerCardCollapsedHeader.tsx` — anatomy column labels
- `IntakeV6ReviewLetterGroupsSection.tsx`
- `IntakeV6ArtworkFinishSection.tsx` (+ test expand disclosure)
- `IntakeV6ReturnCantFields.tsx` — pilot field chrome in review layout
- `IntakeV6ReviewLightingSection.tsx`
- `steps/IntakeV6ReviewStep.tsx` — soften finish ownership tokens only

## Screenshots

`docs/qa/workos-configurator-letter-pilot-2026-07-19/screenshots/` — see `screenshots_index.md`

## Tests

```text
vitest: LetterGroupFinishes, LetterGroups collapsed, ArtworkFinish,
        ReviewLighting, ReturnCantFields, OperatorWorkspaceFooter
→ 62+59 green (targeted)
```

## Risks

- Pilot tokens are local; full Finisaje/Iluminare chrome still mixed with contract fields above letter adapter
- Dropdown option strings for light color may still be English from template options (result panel uses RO)
- Sticky footer can occlude element screenshots — viewport scroll used for evidence

## Frozen (untouched)

Backend · PD · Aggregate · Montaj IA · Page 1 · segmented · electrical contracts · pricing logic · global theme

## Commit

`refactor(intake-v6): apply configurator design pilot to letters`
