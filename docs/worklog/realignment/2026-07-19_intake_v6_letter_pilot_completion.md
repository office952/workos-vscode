# Worklog — Intake V6 Letter Pilot Completion

| Field | Value |
|-------|--------|
| Date | 2026-07-19 |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Baseline | `8aafbd1b05c522d6f22b2f9acd737e83809e43dd` (wiring repair accepted) |
| HEAD before | `7a3bf6f383ac4a18abb5226101cb4b9f48b50067` |
| Runtime | FE `:3000` · `BACKEND_PORT=8003` · BE `:8003` |
| Design checkpoint | `docs/qa/intake-v6-letter-pilot-completion-2026-07-19/DESIGN_CHECKPOINT.md` |
| Scope | Frontend presentation only — composition / scope / pricing rail quieting around letter pilot |

## Hierarchy before → after

**Before:** Composition card + violet/dense scope + sticky pricing (lines + sliders always on) competed with Față/Cant/Spate and Iluminare.

**After:**
1. Produs identity + confirm CTA  
2. Compact scope strip  
3. Blocker banner (counts preserved)  
4. Letter finish / lighting decisions  
5. Rezultat comercial (secondary, details on request)  
6. Ajustări comerciale disclosure  
7. Technical composition disclosure  
8. Footer = next action  

## Component changes

- `IntakeV6ProductCompositionPanel` — quieter shell; registry warnings behind technical accordion; confirm CTA stays L1  
- `IntakeV6OfferScopeReviewSummary` — compact strip + excluded-modules disclosure  
- `IntakeV6LiveCalculationSummary` — title “Rezultat comercial”; `data-pricing-weight="secondary"`; line details opt-in  
- `IntakeV6PricingInputPanel` — quieter chrome  
- `IntakeV6ReviewStep` — commercial sliders in technical accordion; narrower rail column  

## Tests

`vitest` 35/35:
- `IntakeV6ProductCompositionPanel.test.tsx`
- `IntakeV6OfferScopeReviewSummary.test.tsx` (new)
- `IntakeV6LiveCalculationSummary.test.tsx`

Live: `run-pilot-completion-live.mjs` exit 0; probe `pricingWeight=secondary`, `technicalAuthorityOnL1=false`, `footerNext=true`.

## Screenshots

`docs/qa/intake-v6-letter-pilot-completion-2026-07-19/screenshots/` + `SCREENSHOTS.md`.

## Risks / remaining visual weak spots

- Blocker banner is still large (intentionally — must not miss blockers).  
- Unconfirmed composition still expands component cards by default (CTA priority).  
- Pricing still shows internal cost + missing-rate chip (required honesty).  

## Dead pieces

None introduced. No Montaj/backend/analyzer/pricing-math changes.

## Next recommendation

Owner GO only: optional Finisaje decision density polish (letter anatomy spacing) without touching commercial truth — or Page 1 operator calm pass if still ERP-dense after this Page 2 quieting.
