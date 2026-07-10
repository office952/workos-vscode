# Intake V6 — Diagnostic Collapse & Rename (V1)

**Date:** 2026-07-10  
**Status:** COMPLETE  
**Slice:** INTAKE_V6_DIAGNOSTIC_COLLAPSE_RENAME_V1  
**HEAD before:** `1c289e2`  
**Scope:** Step 2 diagnostic layer rename/collapse only — display/layout

---

## Runtime verified

- URL: http://127.0.0.1:3000/intake-v6/22ef834d-f2d0-453b-a7a7-118928c98a39/operator
- Pas 1, Pas 2 Finisaje/Iluminare, diagnostic zone, footer, Pas 3 regression

---

## Source semantics (four signals — verified in code)

| Signal | Source | Counts | Operator action? |
|--------|--------|--------|------------------|
| **Tab badge (Finisaje `2`)** | `pendingConfirmationCount` in `IntakeV6ReviewStep` | Letter groups with `resolveLayerCardStatus === "warning"` + unconfirmed artwork rows | **Yes** — finish/config in Finisaje tab |
| **Blocker banner** | `buildOperatorBlockerBannerDisplay` | Handoff surfacing reasons + mapped runtime/planner blocker codes (max 3 Romanian bullets) | **Yes** — primary above-fold guidance |
| **Diagnostic count** | `buildReviewDiagnosticEntryCount` | Unique raw blocker codes from backbone + runtime capture + promotion planner (fallback: field counts) | **No** — technical evidence only |
| **Footer issues (`N`)** | `IntakeV6OperatorWorkspaceFooter` | `footerBlocker` + header status warn/bad rows + `reviewWarnings` + status actions | **Mixed** — operational summary, not raw codes |

**Key difference:** Tab badge `2` ≠ footer `8` ≠ diagnostic codes. Tab badge tracks **unconfirmed finisaje in active tab**. Footer aggregates **workspace-level operational issues** (pricing, layers, operator confirmation, review warnings). Diagnostic holds **raw form-system codes** (e.g. `SELECTED_LAYER_REFS_MISSING`).

---

## Figma reference

| Item | Value |
|------|-------|
| File | WorkOS Intake V6 — UI Audit |
| Key | `911Q6oRKcEursrRoT4Qj0h` |
| Pages | 00 Overview, 07 Proposed Hierarchy, 09 Tabs & Status System, 10 Comparison |

Direction: primary operator truth first; secondary diagnostics lower and collapsible; no hidden blockers.

---

## Files inspected

- `IntakeV6ReviewStep.tsx`
- `IntakeV6TechnicalDetailsAccordion.tsx`
- `FormSystemBackboneAwarenessPanel.tsx`
- `FormSystemRuntimeCaptureReadModelPanel.tsx`
- `ProductTruthPromotionPlannerPanel.tsx`
- `IntakeV6ReviewOperatorBlockerBanner.tsx`
- `IntakeV6OperatorWorkspaceFooter.tsx`
- `intakeV6OperatorBlockerBannerDisplay.ts`

## Files modified

| File | Change |
|------|--------|
| `atoms/IntakeV6TechnicalDetailsAccordion.tsx` | Count in header, hint, controlled open, chevron, `data-expanded` |
| `atoms/IntakeV6TechnicalDetailsAccordion.test.tsx` | New |
| `lib/intakeV6/intakeV6ReviewDiagnosticEntryCount.ts` | Display-only diagnostic count helper |
| `lib/intakeV6/intakeV6ReviewDiagnosticEntryCount.test.ts` | New |
| `steps/IntakeV6ReviewStep.tsx` | Merge 3 panels into collapsed accordion; controlled expand on banner jump |
| `IntakeV6ReviewOperatorBlockerBanner.tsx` | Link copy aligned to new title |
| `IntakeV6OperatorWorkspaceFooter.tsx` | Label → „Probleme & acțiuni necesare” |
| `intakeV6OperatorBlockerBannerDisplay.ts` | Generic message references new section title |
| Tests updated for copy/regression |

---

## Implementation

1. Renamed section: **„Detalii tehnice și diagnostic”**
2. Form System Backbone + Runtime Capture + Product Truth Promotion moved **inside** the accordion (previously always visible above fold)
3. Default **collapsed**; header shows `N elemente` + hint „Pentru verificare avansată”
4. Banner „Vezi detalii tehnice și diagnostic” expands section then scrolls to anchor
5. Footer label clarified — operational actions, not raw diagnostic codes
6. Tab badge logic **unchanged** (still finisaje pending only)

---

## Tests

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run `
  src/components/workos/intake-v6/atoms/IntakeV6TechnicalDetailsAccordion.test.tsx `
  src/lib/intakeV6/intakeV6ReviewDiagnosticEntryCount.test.ts `
  src/components/workos/intake-v6/IntakeV6ReviewOperatorBlockerBanner.test.tsx `
  src/lib/intakeV6/intakeV6OperatorBlockerBannerDisplay.test.ts `
  src/components/workos/intake-v6/IntakeV6OperatorWorkspaceFooter.test.tsx `
  src/components/workos/intake-v6/IntakeV6ReviewTabNav.test.tsx `
  src/components/workos/colorRegistry/ColorRegistrySelect.test.tsx `
  src/components/workos/intake-v6/IntakeV6LayersOperatorPanel.test.tsx `
  src/components/workos/intake-v6/IntakeV6LayersWarningsPanel.test.tsx
```

**Result:** 31/31 PASS

---

## Screenshots

`docs/qa/intake-v6-diagnostic-collapse-rename-v1/screenshots/`

1. `01_step2_diagnostic_collapsed_default.png`
2. `02_step2_diagnostic_expanded_raw_codes.png`
3. `03_step2_blocker_visible_diagnostic_collapsed.png`
4. `04_step2_tab_badge_and_footer_relationship.png`
5. `05_step1_no_badge_noise_regression.png`
6. `06_step2_iluminare_no_on_regression.png`
7. `07_step3_no_intentional_changes.png`

---

## Forbidden scope

No backend, DB, pricing, Product System, Product Truth write, SVG/layer logic, Step 3 consolidation, live calculation layout changes.

---

## Regressions verified

- Pas 1 badge noise reduction intact
- Iluminare ON pill absent
- 651 colored badge hidden when code visible
- Blocker banner visible with diagnostic collapsed
- Step 3 unchanged

---

## Honest opinion

The rename is clearer for operators — „diagnostic” alone sounded like errors. Collapsing the three form-system panels removes the biggest above-fold noise without hiding blockers (banner still explains action). Tab badge `2` and footer `8` still feel like parallel counts but now have clearer labels; full deduplication needs a future consolidation slice. Weakest remaining point: footer still aggregates many scopes into one number.

---

## Remaining

- Slice 4: live calculation visual balance
- Slice 5: Step 3 consolidated status
- Optional: further footer/tab count deduplication

---

## Next safe step

**INTAKE_V6_LIVE_CALCULATION_BALANCE_V1** — rebalance live calc prominence vs finisaje cards after diagnostic demotion.

---

## Commit

Message: `Refine Intake V6 technical diagnostics`
