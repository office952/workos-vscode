# HOTFIX: V2 → QuoteWizard PSU handoff

## Problem

After routing volumetric intakes to WorkIntake V2 (`/intake-v2/:id`), operators could complete lighting with a valid **multi-PSU** plan (e.g. `2×200 W`, 400 W total) but **QuoteWizard** still blocked commercial readiness with:

> Consum LED … W necesită sursă ≥ … W — maxim configurat 200 W

Root causes:

1. **Stale handoff** — `Deschide QuoteWizard` passed `productSpecInitial` from the last list refresh, not the live V2 `spec` (including `psu_configuration`).
2. **Single-PSU sizing overwrite** — `applyFrontlitConstructionDefaults` ran single-PSU `computePsuSizing` (max 200 W) and set `psu_sizing_status: insufficient_capacity` even when V2 had `psu_allocation_status: ok` and adequate total capacity.
3. **Classic prefill gap** — `mapProductSpecToVolumetricQuotePrefill` only mapped `selected_psu_watts`; when that field was missing, QuoteWizard had no compatibility mirror from `psu_configuration`.

## Why QuoteWizard saw 200 W while V2 had 2×200 W

- V2 lighting stage stores `psu_configuration: [200, 200]` and `psu_total_capacity_watts: 400`.
- Handoff used stale intake snapshot with `selected_psu_watts: 200` only.
- Readiness checks single-PSU capacity (200 W) against `required_psu_watts` (~369 W) and failed.

## Files changed

| File | Change |
|------|--------|
| `frontend/src/pages/WorkIntakeV2.tsx` | Handoff passes live `handoffSpec` to QuoteWizard nav state |
| `frontend/src/components/workos/workIntakeV2/WorkIntakeV2Flow.tsx` | Persist + normalize spec on handoff; callback receives live payload |
| `frontend/src/lib/volumetricFrontlitIntake.ts` | Depth alias sync; preserve V2 multi-PSU when total ≥ required |
| `frontend/src/lib/volumetricQuoteInput.ts` | `effectiveReturnDepthMm` prefill; PSU mirror from `psu_configuration` |
| `frontend/src/components/workos/workIntakeV2/stages/V2ProductionStage.tsx` | Return depth select (30/60/80/100 mm) |
| `frontend/src/components/workos/workIntakeV2/stages/V2QuoteStage.tsx` | Display effective return depth |
| `frontend/src/lib/volumetricQuoteInput.test.ts` | Depth + PSU prefill tests |
| `frontend/src/lib/volumetricFrontlitIntake.test.ts` | Depth sync + multi-PSU preservation tests |

**Not changed:** CostEngine formulas, classic `VolumetricLettersQuoteFlow` PSU UI, `intakeReadinessStages` merge (scope A), backend paint gates (scope C), arch docs (scope D).

## Compatibility behavior

QuoteWizard / CostEngine still price a **single** `selected_psu_watts` field.

Compatibility mirror when classic field is absent:

```
selected_psu_watts = max(psu_configuration unit watts)
```

Example: `[200, 200]` → `selected_psu_watts = 200` (largest unit, not sum).

V2 quote stage summary still shows **`2×200 W`** via `formatPsuConfiguration`.

## Readiness behavior

- `hasValidPsuSelection` accepts `psu_allocation_status === "ok"` + non-empty `psu_configuration`.
- `applyFrontlitConstructionDefaults` now preserves V2 multi-PSU when `psu_total_capacity_watts >= required_psu_watts` and sets `psu_sizing_status: ok` (clears insufficient_capacity blocker).
- Handoff persists normalized spec before navigation so QuoteWizard receives current `product_spec_json` shape.

## Tests run

```bash
cd frontend
npm run lint
npx vitest run src/lib/volumetricQuoteInput.test.ts src/lib/volumetricFrontlitIntake.test.ts
npx vitest run src/components/workos/workIntakeV2/WorkIntakeV2Flow.test.tsx src/pages/WorkIntakeV2.test.tsx
# optional e2e when stack up:
# npx playwright test e2e/work-intake-v2-volumetric.spec.ts
```

## Remaining gap

**CostEngine multi-PSU pricing is not implemented.** Readiness and handoff accept V2 multi-PSU planning; quote simulation still uses one `selected_psu_watts` for costing. Full multi-PSU BOM/pricing is a follow-up.

## Operator path

```
/intake → Continuă în WorkIntake V2 → /intake-v2/IR-… → Quote stage → Deschide QuoteWizard
```

Live test intake: `IR-MQ47AGDG` (lleexxaa.svg, stock white cant, 2×200 W lighting).
