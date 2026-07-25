# ACM panel — single final confirm + warning cleanup

| Field | Value |
|-------|-------|
| **Date** | 2026-07-24 |
| **Owner ask** | O singură confirmare la final pe panou ACM; verifică avertizările (Forex / consumabile / residual vector) |
| **Workspace (live)** | `7cedd889-eaf2-46f6-82c4-8ffe93958a56` · Panou / carcasă |

## A. Single final confirmation

Intermediate **Confirmă geometria / Confirmă construcția / Confirmă finisaj** removed from the ACM inspector.

One sticky end-of-form action: **Confirmă panoul Alucobond** (`confirm_panel`) — one PUT that:

- flushes pending numeric drafts
- confirms technical / geometry authorities
- marks `shell_finish.operator_confirmed`

Product Truth boundary preserved: no silent confirm without that button. Composition status still never auto-confirmed.

## B. Warning verdicts

| Warning | Verdict | Operator sees |
|---------|---------|---------------|
| **Forex 10 mm — cantitate lipsă** (Letters+ACM) | Softened to **diagnostic** when `letters_acm_conn_*` present; also excluded from offer-rail **Tarife lipsă**. Letter backs remain structural; null qty is geometry/calc noise. | Group: *Spate litere — cantitate necalculată* (not Lipsa cantitate / Tarife lipsă) |
| **Consumabile + `COMMERCIAL_FORMULA_UNVERSIONED`** | **Suppressed** from primary NEINCLUSE (legacy/atelier bucket). Formula jargon hidden from operator gap text. | Not in primary scare list |
| **Residual vector / Vector Logo chip** | **Fixed pairing** (no more “Confirmă rolurile…” on residual reason). Copy shortened; jump → Finisaje. **Suppressed** when `artworkFinishRowCount === 0` (no Vector Logo rows). | If real logos exist: *Perimetru vector nealocat — verifică Vector Logo în Finisaje.* |

## Files

- `frontend/src/lib/intakeV6/acmPanel/operatorPatch.ts` (+ tests)
- `frontend/src/components/workos/intake-v6/acm-panel/IntakeV6AcmPanelInspector.tsx` (+ commit semantics tests)
- `frontend/src/components/workos/intake-v6/acm-panel/IntakeV6AcmShellFinishPanel.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.tsx` (+ test)
- `frontend/src/lib/intakeV6/intakeV6QuoteHandoffReadiness.ts` (+ tests)
- `frontend/src/lib/intakeV6/intakeV6OperatorBlockerBannerDisplay.ts`
- `frontend/src/components/workos/intake-v6/IntakeV6ReviewOperatorBlockerBanner.tsx`
- `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx`

## Tests

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run `
  src/lib/intakeV6/acmPanel/operatorPatch.test.ts `
  src/components/workos/intake-v6/acm-panel/IntakeV6AcmPanelInspector.commitSemantics.test.tsx `
  src/components/workos/intake-v6/acm-panel/IntakeV6AcmShellFinishPanel.test.tsx `
  src/lib/intakeV6/intakeV6QuoteHandoffReadiness.test.ts `
  src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.test.tsx
```
