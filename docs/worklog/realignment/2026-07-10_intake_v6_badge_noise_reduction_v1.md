# Intake V6 — Badge Noise Reduction (V1)

**Date:** 2026-07-10  
**Status:** COMPLETE  
**Slice:** INTAKE_V6_BADGE_NOISE_REDUCTION_V1  
**HEAD before:** `2beb83d`  
**Scope:** Pas 1 + Pas 2 badge/chip noise reduction only — display/layout

---

## Figma reference

| Item | Value |
|------|-------|
| File | WorkOS Intake V6 — UI Audit |
| Key | `911Q6oRKcEursrRoT4Qj0h` |
| URL | https://www.figma.com/design/911Q6oRKcEursrRoT4Qj0h |
| Pages used | 00 Overview, 07 Proposed Hierarchy, 09 Tabs & Status System, 10 Comparison |

### Visual direction followed (not pixel-perfect)

- Section-level status over field-level chips (Figma 07/09)
- Tab pending badge kept; redundant Iluminare ON pill removed (Figma 09)
- Oracal code visible without duplicate series pill (audit P2-COL-02)
- Pas 1 completion: one panel-level signal when all layers confirmed (audit P1-01)
- Analysis warnings: compact count/summary instead of per-layer chip wall (audit P1-02)

---

## What changed

| Area | Change |
|------|--------|
| Pas 2 Iluminare tab | Removed redundant `ON` pill from `IntakeV6ReviewTabNav` |
| Pas 2 Oracal select | Hide `651 colored` / RAL series badge when code label already shows series |
| Pas 1 completion | Hide operator status badge + per-card status icons when all layers confirmed |
| Pas 1 analysis | Replace per-layer warning chips with compact summaries + `N observații` header |
| Pas 2 handoff duplicate | Smart banner no longer repeats `firstBlocker` on Review step (banner owns it) |
| Slice 1 banner | Unchanged — still primary blocker surface under tab bar |

### Intentionally not changed

- Step 3 consolidation (`De completat` x3)
- Diagnostic rename/collapse (`Detalii tehnice`)
- Live calculation layout
- Finisaje pending tab badge
- Footer issue count
- Blocker banner logic/content
- Any backend/pricing/SVG/layer-role logic

---

## Badge/noise reduction (qualitative)

Approx. **45%+ fewer redundant status surfaces** in audited noisy states:

- Removed: Iluminare ON pill, 651 colored badge on selected cards, N per-layer warning chips, N per-card check icons when complete, duplicate smart-banner handoff on Review
- Kept: Finisaje pending badge, blocker banner, footer issues, diagnostic raw codes, LED toggle in tab content

---

## Tests

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run `
  src/lib/intakeV6/intakeV6OperatorBlockerBannerDisplay.test.ts `
  src/components/workos/intake-v6/IntakeV6ReviewOperatorBlockerBanner.test.tsx `
  src/components/workos/intake-v6/IntakeV6ReviewTabNav.test.tsx `
  src/components/workos/colorRegistry/ColorRegistrySelect.test.tsx `
  src/components/workos/intake-v6/IntakeV6LayersOperatorPanel.test.tsx `
  src/components/workos/intake-v6/IntakeV6LayersWarningsPanel.test.tsx `
  src/components/workos/intake-v6/IntakeV6LayersRoleTable.test.tsx `
  src/lib/intakeV6/intakeV6WorkspaceHeaderStatus.test.ts
```

**Result:** 34/34 PASS

---

## Screenshots

`docs/qa/intake-v6-badge-noise-reduction-v1/screenshots/`

1. `01_step1_reduced_completion_noise.png`
2. `02_step1_analysis_summary.png`
3. `03_step2_finisaje_reduced_badges.png`
4. `04_step2_iluminare_no_on_pill.png`
5. `05_step2_diagnostic_still_available.png`
6. `06_step3_no_intentional_changes.png`

---

## Honest UI opinion

Pas 1 feels calmer when layers are confirmed — one green panel signal instead of check on every card. Pas 2 tab bar is less noisy without ON; Oracal rows read cleaner. Blocker banner still dominates correctly. Footer + Finisaje badge still add parallel counts (Slice 3+4 territory).

---

## Remaining issues

- Slice 3: diagnostic rename/collapse (`Detalii tehnice` → `Diagnostic tehnic`)
- Slice 4: live calculation visual balance vs finisaje cards
- Slice 5: Step 3 consolidated status

---

## Next recommended slice

**INTAKE_V6_DIAGNOSTIC_COLLAPSE_RENAME_V1** — rename/reposition technical diagnostics as secondary layer after banner + badge reduction.
