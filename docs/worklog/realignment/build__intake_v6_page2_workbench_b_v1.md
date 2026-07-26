# Build: Intake V6 Pas 2 — Workbench Variant B (shell)

**Date:** 2026-07-24  
**Status:** Slice A implemented (shell)  
**Boundary:** UI shell only — no CostEngine / CPP / finish-setup persist changes

## Goal

Replace dense Review dashboard chrome with **Workbench Configurator (Variant B)**:
- slim product strip + one status chip
- vertical domain nav (Finisaje / Iluminare / Panou·carcasă / Montaj comercial)
- sticky offer rail
- ACM inspector moved to sheet (“Detalii produs / ACM”)

## What changed

| Area | Change |
|------|--------|
| Domain nav | `intakeV6ReviewDomainNav.ts` expands `montaj` → `panou_carcasa` + `montaj_comercial` (maps back to tab `montaj`) |
| Shell | `IntakeV6ReviewWorkbenchLayout.tsx` |
| Tab nav | vertical orientation + domain ids |
| Review step | wires workbench; splits Montaj clusters by domain; product details Sheet |
| Offer rail | commercial adjustments always visible (not nested accordion) |

## Files

- `frontend/src/lib/intakeV6/intakeV6ReviewDomainNav.ts` (+ test)
- `frontend/src/components/workos/intake-v6/IntakeV6ReviewWorkbenchLayout.tsx` (+ test)
- `frontend/src/components/workos/intake-v6/IntakeV6ReviewTabNav.tsx` (+ test)
- `frontend/src/components/workos/intake-v6/IntakeV6ReviewFormRegion.tsx` (workbench layout option)
- `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx`
- `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.commercialSettings.test.tsx`

## Verification

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run `
  src/lib/intakeV6/intakeV6ReviewDomainNav.test.ts `
  src/components/workos/intake-v6/IntakeV6ReviewTabNav.test.tsx `
  src/components/workos/intake-v6/IntakeV6ReviewWorkbenchLayout.test.tsx `
  src/components/workos/intake-v6/IntakeV6ReviewFormRegion.test.tsx `
  src/components/workos/intake-v6/steps/IntakeV6ReviewStep.commercialSettings.test.tsx
```

**Result:** 5 files / 15 tests passed.

## PASS criteria (Slice A)

- [x] Workbench shell (`data-workbench-variant="b"`)
- [x] Vertical domains including Panou/carcasă ≠ Montaj comercial
- [x] Product details / ACM behind sheet trigger
- [x] Single attention chip on product strip
- [ ] Operator Remus before/after screenshots (manual / e2e when stack live)

## Next (Slice B)

- Simplify Finisaje letter cards (anatomy row)
- Completion marks on domain nav
- Optional e2e smoke for domain switch + Remus screenshots
