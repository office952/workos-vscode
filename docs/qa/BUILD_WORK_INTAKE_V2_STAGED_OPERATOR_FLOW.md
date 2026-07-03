# BUILD: WorkIntake V2 — Staged Operator Flow

**Date:** 2026-06-07  
**Status:** PASS (additive parallel route)  
**Baseline HEAD:** `7c40f36` — front-lit production rules UI wiring  
**Route:** `/intake-v2/:id`  
**Template scope:** `TPL-VOLUMETRIC-LETTERS` only

---

## Build status

| Check | Result |
|-------|--------|
| Working tree clean at start | Yes |
| V2 route created | Yes — `/intake-v2/:id` |
| Existing `/intake/:id` unchanged | Yes |
| No CostEngine / Pricing / spine changes | Yes |
| Not committed / not pushed | Yes |

---

## Why parallel, not replacement

Operators need a clearer staged flow without risking the verified classic intake. V2 reuses the same `product_spec_json`, parsers, production rules, and QuoteWizard handoff — but presents **one active task at a time** with a persistent repair panel. Classic WorkIntake remains the production path until V2 is promoted explicitly.

---

## Stages implemented

| # | Stage | Component | Persistence boundary |
|---|-------|-----------|----------------------|
| 1 | Context | `V2ContextStage` | Template confirm (`confirmed_template_code`), assignee blur |
| 2 | SVG | `V2SvgStage` | Save SVG analysis → `product_spec_json` |
| 3 | Layere & geometrie | `V2LayersGeometryStage` | Confirm letters layer + save geometry |
| 4 | Producție | `V2ProductionStage` | Save production options (chamfer locked, face vinyl, return color) |
| 5 | Iluminare & sursă | `V2LightingStage` | Confirm lighting + PSU sizing |
| 6 | Verificare | `V2VerificationStage` | Read-only checklist with go-to-stage |
| 7 | Ofertare | `V2QuoteStage` | QuoteWizard handoff summary (uses existing nav helpers) |

---

## Files changed / added

**Page & routing**
- `frontend/src/pages/WorkIntakeV2.tsx`
- `frontend/src/App.tsx` — route `/intake-v2/:id`

**Orchestration**
- `frontend/src/components/workos/workIntakeV2/WorkIntakeV2Flow.tsx`
- `frontend/src/components/workos/workIntakeV2/WorkIntakeV2StageNav.tsx`
- `frontend/src/components/workos/workIntakeV2/WorkIntakeV2RepairPanel.tsx`
- `frontend/src/components/workos/workIntakeV2/shared.ts`
- `frontend/src/components/workos/workIntakeV2/stages/V2*.tsx` (7 stages)

**Libs**
- `frontend/src/lib/workIntakeV2/types.ts`
- `frontend/src/lib/workIntakeV2/stageCompletion.ts`
- `frontend/src/lib/workIntakeV2/repairPanel.ts`

**Link from classic**
- `frontend/src/components/workos/templateIntakeWorkspace/VolumetricLettersWorkspace.tsx`

**Tests**
- `frontend/src/lib/workIntakeV2/workIntakeV2.test.ts`
- `frontend/src/components/workos/workIntakeV2/WorkIntakeV2Flow.test.tsx`
- `frontend/src/pages/WorkIntakeV2.test.tsx`
- `frontend/e2e/work-intake-v2-volumetric.spec.ts`

**Docs**
- `docs/qa/BUILD_WORK_INTAKE_V2_STAGED_OPERATOR_FLOW.md` (this file)
- `docs/audits/WORKOS_FORM_FLOW_AUDIT_AND_FLUID_PROPOSAL.md` — §14 note

---

## Persistence behavior

- All confirm/save actions call `intakesApi.update` with `normalizeIntakeProductSpecForSave` payload (same as `Product001IntakeSpecEditor`).
- Layer confirm uses `mapSvgVectorAnalysisToProductSpec` with `layerMappingConfirmed: true` and persists immediately.
- No second data model; refresh rehydrates from `product_spec_json`.
- Mock source (`source === "mock"`) is read-only for saves.

---

## Readiness behavior

- Per-stage completion: `stageCompletion.ts`
- Repair panel: `repairPanel.ts` — merges vector + front-lit missing with stage links
- QuoteWizard opens only when verification stage complete (`isWorkIntakeV2StageComplete("verification")`)
- Uses `buildQuoteWizardNavStateFromIntake` / `navigateToQuotesList` — no quote gate bypass

---

## Tests run

| Suite | Command | Result |
|-------|---------|--------|
| Lint | `npm run lint` | **PASS** |
| V2 unit | `workIntakeV2.test.ts` + `psuAllocation.test.ts` + `lightingPlanning.test.ts` | **22/22 PASS** |
| V2 component | `WorkIntakeV2Flow.test.tsx` + `WorkIntakeV2.test.tsx` | **13/13 PASS** |
| E2E smoke | `work-intake-v2-volumetric.spec.ts` | **1/1 PASS** |

**Total V2:** 35 unit/component + 1 E2E — all passed (2026-06-07, simplified Lighting & PSU).

---

## Post-smoke refinement (2026-06-07)

### No auto-refresh / stage jump after SVG upload
- `activeStage` persisted in `sessionStorage` per intake id
- `productSpecInitial` merges via `mergeLocalVectorSpecFields` — never full remount/seed on refetch
- SVG file pick updates local state only; save uses `skipRefresh`; stage changes only on explicit nav / Continue

### Input hierarchy
- Shared tokens: larger fields (`text-[13px]`), muted intros (`v2StageIntroClass`), compact labels
- Applied to SVG, Lighting, Quote panels

### Lighting & PSU — job-level (normal flow)
- **Normal operator flow is job-level, not group-based.** Etapa 5 does **not** show „Grupuri iluminare”, „Adaugă grup”, group name inputs, or per-group watt fields.
- Operator selects: **sistem iluminare** (module / bandă), **variantă** (0.72 / 1 / 1.44 W module; 60 or 120 LED/m bandă), **culoare lumină** (caldă / rece — same cost).
- App estimates **consum LED** (`total_led_watts`) and **necesar sursă +15%** (`required_psu_watts`) from geometry + variant.
- **Propunere automată surse** via `allocatePSUCombination()` — fewest units, then minimal overshoot (e.g. 57.5→60 W, 308→`2 × 160 W`).
- UI shows total PSU capacity, reserve margin, and warning when insufficient.
- Operator **confirms** the proposed combination (`Confirmă iluminarea & sursele`); save disabled when underpowered.

### Multi-transformer (automatic combination)
- Multiple transformers are supported as **automatic PSU combination** at job level: `psu_configuration: number[]` (e.g. `[160, 160]`, `[200, 160]`).
- Stage nav / quote handoff summarize formatted config (e.g. `2 × 160 W`) — not per named circuit.
- CostEngine single-PSU field unchanged — documented gap.

### Manual override (secondary / advanced)
- Collapsed `<details>` „Override manual surse (avansat)” — not part of normal workflow.
- Operator may pick alternate catalog units and document stock reason (`psu_override_reason`).
- Underpowered manual selection → blocker + visible warning.

### Readiness (job-level)
- Readiness does **not** require completing lighting groups or per-group PSU.
- Repair messages are job-level: select lighting system, select LED variant, estimated consumption missing, PSU insufficient, manual override underpowered.

### Named group / circuit planning — deferred
- Per-zone planning (ex: LITERELE LEX, LITERELE HOTEL) is a **future advanced feature**, not current required flow.
- Legacy `lighting_groups[]` shape may remain in `IntakeProductSpec` for backward compatibility; V2 normal UI does not create or edit named groups.

### New files
- `frontend/src/lib/workIntakeV2/psuAllocation.ts`
- `frontend/src/lib/workIntakeV2/lightingPlanning.ts`
- Tests: `psuAllocation.test.ts`, `lightingPlanning.test.ts`

---

## Known gaps

- Embedded simulate tab not duplicated in V2 quote stage (classic tab link optional only).
- Legacy `evaluateIntakeReadyPrerequisites` (description, delivery) not enforced in V2 context stage — operator-focused subset only.
- No URL hash for deep-linking to a specific stage.
- V2 not exposed in main nav; experimental link from volumetric workspace only.
- Full-repo TypeScript check may still fail on pre-existing issues unrelated to this build.

---

## Acceptance checklist

- [x] V2 route created
- [x] Existing WorkIntake still works (no route replacement)
- [x] V2 only for TPL-VOLUMETRIC-LETTERS
- [x] All 7 stages
- [x] `product_spec_json` persistence on save/confirm
- [x] Readiness repair actions with go-to-stage
- [x] E2E smoke spec added
- [x] No CostEngine/Pricing/spine regression
