# Build — Intake V6 offer rail clarity (Pas 2)

| Field | Value |
|-------|-------|
| **Date** | 2026-07-24 |
| **Scope** | Display / IA only on sticky offer rail |
| **Boundary** | No CPP/EIC formula changes; no CostEngine rewrite |

## Problem

Operator screenshot: dual totals (cost intern + Bond), empty client offer, English dry-run blocker, Final / Ofertă fermă / Execution badges — unreadable.

## Change

1. Right-panel rail hierarchy: **Ofertă client** → **Estimări pe produs** (Litere / Panou / Legături) → **Cost intern** → single **Ce blochează**.
2. Humanize backend dry-run English via `intakeV6OperatorFacingPricingBlocker`.
3. ACM block `variant="rail"` — no Final/Execution badges in primary rail.
4. Commercial adjustments collapsed (`<details>`) under the rail.

## Files

- `frontend/src/lib/intakeV6/intakeV6OfficialPricing.ts`
- `frontend/src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.tsx`
- `frontend/src/components/workos/intake-v6/AcmPanelProvisionalPricingBlock.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6PricingInputPanel.tsx`
- `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx`
- targeted Vitest updates
