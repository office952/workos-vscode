# Build: Intake V6 — formular Alucobond / Bond flat

**Date:** 2026-07-24  
**Status:** implemented  
**Boundary:** UI only — same AcmPanel patches / drafts / confirms

## Problem

Formularul Bond/Alucobond părea brut și „nu funcționa”:
- Editorul real era în Sheet cu 3 coloane nested (listă | accordion | rail)
- Domeniul Panou/carcasă arăta doar teaser Fundal; CTA nu deschidea Sheet-ul
- Accordion în accordion / border în border

## Fix

1. **`variant="workbench"`** pe `IntakeV6AcmPanelConfigRegion` — formular flat în Panou/carcasă
2. **`presentation="flat"`** pe inspector — Geometrie / Construcție / Material mereu deschise (fără accordion wall)
3. Formularul e **inline** în `panou_carcasa` când există instanță ACM
4. Sheet „Compoziție” nu mai conține ConfigRegion (evită dublu flush + nesting)
5. Buton strip **Panou Alucobond** sare direct la domeniul panou

## Verification

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run `
  src/components/workos/intake-v6/acm-panel/IntakeV6AcmPanelConfigRegion.blueprint.test.tsx `
  src/components/workos/intake-v6/acm-panel/IntakeV6AcmPanelInspector.commitSemantics.test.tsx `
  src/components/workos/intake-v6/steps/IntakeV6ReviewStep.commercialSettings.test.tsx
```
