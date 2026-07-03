# BUILD: Work Intake V2 — Unified Operator Flow

**Date:** 2026-06-09  
**Status:** **PASS — committed**  
**Route:** `/intake-v2/:id`  
**Template scope:** `TPL-VOLUMETRIC-LETTERS` (+ legacy `litere_volumetrice` family fallback)  
**Commit message:** `feat: unify Work Intake V2 operator flow`

---

## 1. Audit summary

Prior audit verdict: **NEEDS DE-SCOPE**. WIP unified flow was functional locally (95 unit tests) but imported untracked **color registry** and **volumetric finish preview** components. Partial commit would break clean checkout.

This build commits the full unified operator workspace **after** removing those dependencies and replacing finish UI with simple text inputs + inline summary.

---

## 2. Scope

| Included | Excluded |
|----------|----------|
| Unified single-page layout (zones A–E) | Color registry UI / data |
| Operational header, cards, hooks | Volumetric finish preview panel |
| Autosave + save status model | Playwright e2e / seed scripts |
| Template config + legacy family hotfix | Backend API changes |
| Readiness gates (stageCompletion, repairPanel, geometrySync) | Quotes / pricing / CostEngine |
| Embedded SVG / layers / production / lighting stages | Work Intake V1 changes |
| Wizard deprecated cleanup (StageNav, RepairPanel, Context/Quote/Verification stages) | Duplicate QA docs |

---

## 3. Files included

### Components (`frontend/src/components/workos/workIntakeV2/`)

| File | Role |
|------|------|
| `WorkIntakeV2Flow.tsx` | Unified orchestration |
| `WorkIntakeV2Flow.test.tsx` | Integration tests (36) |
| `WorkIntakeV2OperationalHeader.tsx` | Zone A — readiness, save, CTA |
| `cards/WorkIntakeV2JobDetailsCard.tsx` | Zone B |
| `cards/WorkIntakeV2GraphicsLayersCard.tsx` | Zone C |
| `cards/WorkIntakeV2VolumetricRulesCard.tsx` | Zone D |
| `cards/WorkIntakeV2ReadinessHandoffCard.tsx` | Zone E |
| `hooks/useWorkIntakeV2AutoSave.ts` | Debounced persist |
| `hooks/useWorkIntakeV2ZoneScroll.ts` | Repair → zone scroll |
| `unified/stageIdToZoneId.ts` (+ test) | Stage → zone mapping |
| `previews/VolumetricLettersQuotePreview.tsx` | Handoff preview (simple formatters) |
| `stages/V2{Svg,LayersGeometry,Production,Lighting}Stage.tsx` | Embedded panels |
| `shared.ts` | Shell / field classes |

**Deleted:** `WorkIntakeV2StageNav.tsx`, `WorkIntakeV2RepairPanel.tsx`, `stages/V2ContextStage.tsx`, `V2QuoteStage.tsx`, `V2VerificationStage.tsx`

### Lib (`frontend/src/lib/workIntakeV2/`)

| File | Role |
|------|------|
| `templateConfig/*` | Resolver, volumetric letters config, readiness strategy |
| `saveModel.ts` | Autosave debounce constants + status helpers |
| `zoneLabels.ts` | Zone checklist labels |
| `stageCompletion.ts` (+ test) | Readiness gates |
| `repairPanel.ts` | Blockers + repair list |
| `geometrySync.ts` (+ test) | SVG geometry merge |
| Existing: `lightingPlanning`, `psuAllocation`, `types`, `vectorRepair`, `workIntakeV2.test` |

### Contract helpers

| File | Change |
|------|--------|
| `intakeProductSpec.ts` | Finish fields: `return_finish_system`, RAL/Oracal codes, face vinyl series/code (no registry UI) |
| `intakeVolumetricSpec.ts` | Mounting / roll width options used by production stage |

---

## 4. Unified zones / cards

```txt
┌─ A Header (sticky): readiness · save · CTA ─────────────────┐
├─ B Job Details ──────────┬─ D Volumetric Rules ────────────┤
│  C SVG / Layers          │  E Readiness / Handoff           │
└──────────────────────────┴──────────────────────────────────┘
```

Test ids: `work-intake-v2-zone-header`, `-job-details`, `-graphics-layers`, `-volumetric-rules`, `-readiness-handoff`

---

## 5. Readiness gates

**`stageCompletion.ts`**

- Return depth via `effectiveReturnDepthMm`
- Return finish: standard / RAL (code+name) / Oracal (series+code+name)
- Face vinyl: series + code when enabled; roll width 1000/1260
- SVG parse, layer confirm, geometry confirmed, lighting/PSU complete

**`repairPanel.ts`**

- Zone-native repair actions (scroll to zone, not wizard stage)
- `getFirstWorkIntakeV2BlockerLabel` for header CTA reason

**`geometrySync.ts`**

- File pick → parse → layer mapping → geometry confirmation pipeline

---

## 6. Legacy template hotfix

`resolveWorkIntakeTemplateConfig({ confirmedTemplateCode, productFamily })`:

1. Explicit `TPL-VOLUMETRIC-LETTERS` → volumetric config
2. Missing template + `litere_volumetrice` family → same config (`resolvedViaLegacyFamily: true`)
3. Unknown template → unsupported screen

UI note: `work-intake-v2-template-legacy-family-note`

---

## 7. Autosave / save model

- `WORK_INTAKE_V2_AUTOSAVE_MS` debounce in `saveModel.ts`
- `useWorkIntakeV2AutoSave` → `onSaveProductSpec(normalizeIntakeProductSpecForSave(spec))`
- Header shows `work-intake-v2-save-status`: dirty / saving / saved / error
- Handoff: explicit persist before `onOpenQuoteWizard`

---

## 8. Wizard deprecated cleanup

Removed 7-stage wizard navigation:

- Sidebar `WorkIntakeV2StageNav`
- Sticky `WorkIntakeV2RepairPanel` (logic → readiness card)
- Separate Context / Verification / Quote stages
- Wizard Continue buttons (`work-intake-v2-continue-*`)

---

## 9. De-scope explicit

| Area | In this build? |
|------|----------------|
| `ColorRegistrySelect` / `colorRegistry/*` | **No** — replaced with text inputs for RAL/Oracal/face codes |
| `VolumetricFinishDisplayPanel` / `volumetricFinishDisplay` | **No** — inline `SimpleFinishSummary` in production stage |
| Playwright e2e / seed | **No** |
| Backend | **No** |
| Quotes / pricing engine | **No** (handoff callback unchanged) |

---

## 10. Tests run

```powershell
cd frontend
npm run test -- workIntakeV2 WorkIntakeV2
npm run typecheck   # PASS on committed scope; workspace may fail if unrelated untracked tests present
cd ..
npm run validate:frontend
```

| Suite | Result |
|-------|--------|
| WI V2 unit/integration (9 files) | **95/95 PASS** |
| `npm run typecheck` (WI V2 files) | **PASS** |
| `npm run validate:frontend` | **PASS on clean checkout** (no untracked broken tests in `src/`) |

Grep verification (staged WI V2 scope): **zero** matches for `ColorRegistrySelect`, `colorRegistry`, `VolumetricFinishDisplayPanel`, `volumetricFinishDisplay`.

---

## 11. Clean checkout safety

All imports in committed WI V2 files resolve to **tracked** paths. No dependency on:

- `frontend/src/lib/colorRegistry/**`
- `frontend/src/components/workos/colorRegistry/**`
- `VolumetricFinishDisplayPanel.tsx`
- `volumetricFinishDisplay.ts`

---

## 12. Remaining risks

| Risk | Notes |
|------|-------|
| Finish inputs are manual text (no palette validation) | Color registry build will restore searchable selectors |
| E2E not in this commit | Run separately with seed fixture |
| `onContinue` props on embedded stages | Optional dead path; low risk |
| Workspace `validate:frontend` may fail | Unrelated untracked WIP (e.g. operational registry tests) outside this commit |

---

## 13. Verdict

**PASS — committed**

Unified Work Intake V2 operator flow is portable, readiness-hardened, and de-scoped from color registry / volumetric preview WIP.
