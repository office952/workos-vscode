# Intake V6 — Step 2 Blocker Banner from Figma (V1)

**Date:** 2026-07-10  
**Status:** COMPLETE  
**Slice:** INTAKE_V6_STATUS_HIERARCHY_BANNER_FROM_FIGMA_V1  
**HEAD before:** `5e8e129`  
**Scope:** Step 2 UI status hierarchy only — display-only banner under tab bar

---

## Figma reference

| Item | Value |
|------|-------|
| File | WorkOS Intake V6 — UI Audit |
| Key | `911Q6oRKcEursrRoT4Qj0h` |
| URL | https://www.figma.com/design/911Q6oRKcEursrRoT4Qj0h |
| Pages used | 00 Audit Overview, 07 Proposed Hierarchy — Step 2, 09 Tabs & Status System |

### Visual direction followed (not pixel-perfect)

- Single section-level banner directly under tab bar (Figma page 07 item 1).
- Banner stronger than live calculation when blockers exist (rose border/background).
- Max 3 operator bullets — no raw code wall (Figma 09 four-signal system: Blocat / Necesită atenție).
- Tab pending badge and footer issues unchanged (future slice 2).
- Diagnostics remain lower on page with scroll anchor (Figma page 07 item 5 — rename deferred).

---

## What changed

| File | Change |
|------|--------|
| `frontend/src/lib/intakeV6/intakeV6OperatorBlockerBannerDisplay.ts` | Display-only aggregation helper |
| `frontend/src/lib/intakeV6/intakeV6OperatorBlockerBannerDisplay.test.ts` | Helper tests |
| `frontend/src/components/workos/intake-v6/IntakeV6ReviewOperatorBlockerBanner.tsx` | Banner UI component |
| `frontend/src/components/workos/intake-v6/IntakeV6ReviewOperatorBlockerBanner.test.tsx` | Component tests |
| `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx` | Wire banner after tab nav; diagnostic anchor wrapper |

### Banner placement

Immediately after `IntakeV6ReviewTabNav`, before tab panel content.

### Data sources (read-only, no new fetching)

1. `reviewHandoffSurfacing` — existing `buildReviewHandoffSurfacing()`
2. `runtimeCaptureReadModel` — existing Step 2 state
3. `productTruthPromotionPlanner` — existing Step 2 state

### Operator copy

- `SELECTED_LAYER_REFS_MISSING` → „Referințele straturilor selectate lipsesc. Verifică selecția straturilor în Pasul 1.”
- Unknown codes → generic „Există blocaje tehnice…” message
- Handoff reasons from existing surfacing (Romanian)

### Diagnostics preserved

- Form System Backbone, Runtime Capture Read Model, Product Truth Promotion Planner wrapped in `#intake-v6-review-diagnostic-tehnic`
- „Vezi diagnostic tehnic” scrolls to anchor
- Raw codes remain in diagnostic panels
- Footer issues drawer unchanged

### No logic changes

- No backend, pricing, blocker detection, or handoff logic modified
- Helper only maps/displays existing data

---

## Tests

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/intakeV6/intakeV6OperatorBlockerBannerDisplay.test.ts src/components/workos/intake-v6/IntakeV6ReviewOperatorBlockerBanner.test.tsx src/components/workos/intake-v6/IntakeV6ReviewStatusStrip.test.tsx src/components/workos/intake-v6/FormSystemBackboneAwarenessPanel.test.tsx
```

**Result:** 18/18 PASS

---

## Screenshots

**Route:** http://127.0.0.1:3000/intake-v6/22ef834d-f2d0-453b-a7a7-118928c98a39/operator

| File | Description |
|------|-------------|
| `docs/qa/intake-v6-status-hierarchy-banner-v1/screenshots/01_step2_finisaje_banner_visible.png` | Banner under tabs, pending Finisaje badge, live calc sidebar |
| `docs/qa/intake-v6-status-hierarchy-banner-v1/screenshots/02_step2_diagnostic_collapsed_with_banner.png` | Banner above fold, diagnostic collapsed |
| `docs/qa/intake-v6-status-hierarchy-banner-v1/screenshots/03_step2_diagnostic_expanded_raw_codes.png` | Diagnostic expanded, raw codes visible |
| `docs/qa/intake-v6-status-hierarchy-banner-v1/screenshots/04_step3_no_regression.png` | Step 3 baseline |

---

## Honest UI opinion

**Improvement:** Operator now sees why Confirmare is blocked without scrolling past live price. The rose banner correctly competes with the 6k RON headline.

**Still noisy (future slices):** Finisaje tab badge „2”, Iluminare „ON”, footer „8 probleme” — three parallel counts remain by design for this slice.

**Not done:** Diagnostic rename, badge reduction, live calc compact mode, Step 3 consolidation.

---

## Remaining issues (future slices)

- Slice 2: `INTAKE_V6_BADGE_NOISE_REDUCTION_V1`
- Slice 3: Diagnostic rename/collapse
- Slice 4: Live calculation visual balance
- Slice 5: Step 3 consolidated status

---

## Forbidden scope

Confirmed: no backend/DB/pricing/Product System/Product Truth write/logic changes.
