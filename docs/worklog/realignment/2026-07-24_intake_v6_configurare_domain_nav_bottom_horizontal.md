# Intake V6 Configurare — domain nav horizontal at top

**Date:** 2026-07-24  
**Scope:** Pas 2 Configurare — Finisaje / Iluminare / Panou / Montaj as horizontal strip.

## Owner correction

Initial ask placed the bar toward subsol. Owner override: **„bara asta sa fie sus”** — horizontal domain nav at the **top** of the Configurare form card (under step chrome, above form body).

## Change

- Bar: `IntakeV6ReviewTabNav` (not app global sidebar).
- Orientation: horizontal; placement: top of form region (`data-domain-nav-placement="top"`).
- Compoziție remains a compact control on the right of the strip.
- Footer sticky offset plumbing removed (no longer needed).
- ARIA: `role="tablist"` + `aria-orientation="horizontal"`.

## Files

- `IntakeV6ReviewWorkbenchLayout.tsx`
- `IntakeV6ReviewTabNav.tsx`
- `IntakeV6ReviewStep.tsx`
- `IntakeV6ReviewFormRegion.tsx`
- related unit tests
