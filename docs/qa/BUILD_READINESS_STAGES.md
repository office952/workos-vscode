# BUILD-READINESS-STAGES — QA Report

**Task:** Separate Intake, Simulation, Commercial Quote, and Production Readiness  
**Branch:** `master`  
**Base HEAD:** `2520235`  
**Result:** PASS

## Pre-flight

| Item | Value |
|------|-------|
| Branch | `master` |
| HEAD (before) | `2520235` |
| Working tree | clean |
| Ancestors confirmed | `5643dfb`, `25fa94a`, `2777ee9`, `3ebc695`, `2520235`, `0971a06` |
| Backend `:8000` | 200 `/health` |
| Frontend `:3000` | started for validation (`npm run dev`) |
| Counts before | 22 intakes, 7 quotes, 8 orders |

## Phase 1 — Browser readiness audit (before → after)

| route/code | stage shown (before) | blockers before | should block sim? | should block commercial? | should block production? | issue |
|------------|----------------------|-----------------|-------------------|--------------------------|--------------------------|-------|
| IR-MQ3E7K2V | Nou / single gate | Mixed N/A | No | No | No | Stage 0 showed generic guidance only — OK |
| IR-MQ3C869E | Gata pt. Ofertă lump | Vector + geometry + commercial mixed | Only geometry/cost fields | Vector review, assignee, etc. | Vector final, photos | Single blocker list |
| WI-SMOKE-P001 | Gata pt. Ofertă | Terrain + commercial mixed with sim | No (when geometry complete) | Terrain/commercial | Production vector | Simulation blocked by terrain display |
| `/quotes` | QuoteWizard OK | N/A | N/A | N/A | N/A | No regression |

**After implementation:**

| route | stage label observed | notes |
|-------|---------------------|-------|
| IR-MQ3E7K2V | Alege tip lucrare / Stage 0 | No simulation/commercial/production staged blockers |
| IR-MQ3C869E | Specificație începută | Simulation blockers grouped; production vector not in sim group |
| WI-SMOKE-P001 | Gata pentru simulare | Simulate enabled; **844,41 EUR** baseline preserved |
| `/quotes` | Ofertă nouă + list | Generic wizard path intact |

## Phase 3 — Code audit summary

| file | function/component | responsibility | stage | problem | action |
|------|-------------------|----------------|-------|---------|--------|
| `intakeReadiness.ts` | `evaluateIntakeReadyPrerequisites` | Legacy commercial mark-ready | stage3 | Mixed all gates | Kept; wrapped by stages |
| `intakeGateStages.ts` | `resolveIntakeGateStage` | Routing 0–3 | mixed | Conflates sim/commercial | Unchanged routing |
| `intakeActionSummary.ts` | `buildIntakeActionSummary` | Primary action + flat missing | all | Single list | Added staged model |
| `intakeReadinessStages.ts` | `buildIntakeReadinessStages` | **New** staged evaluation | all | — | Created |
| `volumetricIntakeFormPrep.ts` | `buildVolumetricQuotePrepSummary` | sim vs final quote lists | 2/3 | Already split | Reused |
| `ReadinessGatePanel.tsx` | side panel | Flat blockers | 3 | No staging | Staged groups + hint |
| `VolumetricLettersQuoteFlow.tsx` | simulate button | Always clickable | 2 | Non-sim blockers implicit | Disabled on `!simulateReady` |

**Answers:**

1. Readiness calculated in `evaluateIntakeReadyPrerequisites` + `buildIntakeReadinessStages` (display)
2. Single boolean `ready_for_quote` preserved as legacy commercial flag
3. “Gata pt. Ofertă” blocks: assignee, description, delivery, template, envelope, terrain (install), volumetric final-quote fields
4. Simulation blocks: CostEngine quote_input valid set (see architecture doc)
5. Commercial: mark-ready prerequisites + `missingForFinalQuote`
6. Production-only fields no longer implied as simulation blockers in UI
7. Terrain/CUI shown under commercial/production stages, not Stage 0
8. Duplicated lists consolidated via `groupMissingReasonsByStage`
9. Policy runtime unchanged; staging is display-first
10. Safe without backend schema changes — frontend only

## Helper functions

`frontend/src/lib/intakeReadinessStages.ts` — see architecture doc.

## UI changes

- `ReadinessGatePanel` — stage label, grouped missing, simulation-available hint
- `IntakeActionSummary` — per-stage missing summary
- `TemplateStatusPanel` — active stage strip
- `VolumetricLettersQuoteFlow` — simulation blockers list + button gate
- `IntakeDetail.tsx` — passes `productFamily` into action summary

## Tests / lint

```
vitest: 30 passed (intakeReadinessStages, intakeActionSummary, workspace, intakeReadiness)
eslint: changed frontend files — pass
backend: not touched
```

## Browser validation

Headless Playwright (cursor-ide-browser MCP unavailable):

- IR-MQ3E7K2V: Stage 0 only, “Alege tip lucrare”
- IR-MQ3C869E: geometry suggestions visible; staged side panel
- WI-SMOKE-P001: `readiness-stage-label` = “Gata pentru simulare”; simulate not disabled; total contains **844** EUR
- `/quotes`: list + “Ofertă nouă” visible

## Counts after

| Entity | Before | After |
|--------|--------|-------|
| Intakes | 22 | 22 |
| Quotes | 7 | 7 |
| Orders | 8 | 8 |

**Touched intakes:** none (read-only browser validation)

## Confirmations

- [x] No pricing changes
- [x] No CostEngine changes
- [x] No quote/order created
- [x] No Reference Catalogs started
- [x] SVG parser preserved
- [x] Delivery sync preserved (`filterReadinessMissingForDisplay`)
- [x] Generic unresolved Stage 0 preserved
- [x] WI-SMOKE-P001 baseline **844,41 EUR** preserved

## PASS criteria

- [x] Simulation readiness separate from commercial quote readiness
- [x] Production-only blockers do not block preliminary simulation in UI
- [x] Missing reasons grouped by stage
- [x] Generic unresolved remains clean
- [x] Delivery/terrain gating coherent
- [x] SVG geometry suggestions integrate with staged readiness
- [x] WI-SMOKE-P001 remains 844,41 EUR
- [x] `/quotes` generic wizard still works
- [x] No quote/order created

**PASS**
