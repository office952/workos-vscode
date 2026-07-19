# INTAKE V6 LETTER PILOT COMPLETION REPORT

## 1. Verdict

**PASS** — product decisions dominate Page 2 Finisaje/Iluminare; composition/scope/pricing are quieter without changing truth, pricing math, Montaj, or backend.

## 2. Mini decizia agentului

Complete the accepted letter Design System pilot by demoting ERP-dense chrome (composition technical noise, scope detail, always-on pricing lines/sliders) so Față/Cant/Spate and Iluminare own the viewport. Presentation-only; keep confirmation, blockers, and commercial access honest.

## 3. Git state

| Item | Value |
|------|--------|
| Branch | `feature/product-system-active-path-isolation-v1` |
| Baseline | `8aafbd1` |
| Pre-commit HEAD | `7a3bf6f` |
| Foreign WIP | Present — untouched |

## 4. Runtime environment

| Surface | Value |
|---------|--------|
| FE | `http://127.0.0.1:3000` |
| Proxy requirement | `BACKEND_PORT=8003` |
| BE | `http://127.0.0.1:8003` (200) |
| Compatibility | Workspace create/upload/review via FE proxy succeeded in live script |
| Fixtures | ACM segmented + simple letters |

## 5. Design checkpoint

Created before code: `DESIGN_CHECKPOINT.md` (hierarchy, classifications, disclosure plan, screenshot/regression plan).

## 6. Full hierarchy before

Composition (dense) → scope card → blocker banner → tabs → letter pilot → sticky pricing lines + always-visible commercial sliders → diagnostics.

## 7. Full hierarchy after

Produs compact + L1 confirm → compact scope → blockers → Finisaje/Iluminare decisions → Rezultat comercial (secondary) → Ajustări comerciale disclosure → technical composition disclosure → footer next action.

## 8. Composition before

Cyan/emerald weight; template/authority warnings on expanded L1; confirm sometimes competed with technical chrome.

## 9. Composition after

Title “Produs”; identity + status + Confirmă CTA always when actionable; registry/authority warnings inside “Detalii tehnice compoziție”; probe `technicalAuthorityOnL1=false`.

## 10. Scope/contract disclosure

Compact “Scope ofertă” strip; excluded modules behind `aria-expanded` disclosure; operator blocker banner unchanged for counts/visibility.

## 11. Product decision priority

Primary: Față/Cant/Spate + Iluminare. Secondary: commercial result. Tertiary: technical/registry. Letter anatomy pilot unchanged functionally.

## 12. Pricing rail before

Wide sticky rail; line rows + sliders always visible; visually equal to product column.

## 13. Pricing rail after

“Rezultat comercial”; `data-pricing-weight="secondary"`; narrower column; line details on request; commercial adjustments accordion collapsed by default.

## 14. Pricing calculation preservation

No CostEngine/pricing service/formula changes. Only layout, labels, disclosure, contrast, and column width.

## 15. Finisaje state

Letter anatomy remains; less competition from composition/pricing chrome (`06`, `07`).

## 16. Iluminare state

Tab intact; decisions + calculated results still present (`13`).

## 17. Calculated results

Still under Iluminare results grouping; not replaced by pricing.

## 18. Technical disclosure

Composition technical accordion + per-item details + commercial adjustments disclosure. Discoverable via toggles with `aria-expanded`.

## 19. Guidance preservation

Footer retains “Următorul pas”; sticky counts/drawer pattern reused; no duplicate primary CTA in pricing rail.

## 20. Status/count preservation

Blocker/warning counts still shown in banner + footer (live ACM: blockers visible; continue-to-confirm remains gated when incomplete).

## 21. Accessibility

- Disclosures: `aria-expanded` on composition, scope, commercial, technical toggles  
- Pricing state readable via text (cost / unavailable / tarife lipsă), not color alone  
- Narrow viewport keeps totals/actions (`15`)  
- Footer not replaced by rail as sole next-action owner  

## 22. Tests

35/35 Vitest PASS (composition 5, scope 2, live calc 28).

## 23. Live validation

`run-pilot-completion-live.mjs` exit 0. ACM + simple letters Page 2; reload; Montaj tab screenshot; Confirmare attempt remains honest when incomplete.

## 24. Screenshots

See `SCREENSHOTS.md` — before baselines + after 06–18 present under `screenshots/`.

## 25. Honest visual opinion

- Physical product dominates more than before — **yes**.  
- Composition understandable &lt;5s — **yes** (identity + CTA).  
- Pricing clearly secondary — **yes** (label + weight + collapsed details).  
- Blockers impossible to miss — **yes** (red banner retained).  
- Disclosure reduces noise without hiding truth — **yes** (authority in disclosure).  
- Less ERP-like — **yes**, still not “brochure” calm.  
- Page too tall? — **slightly**, blocker banner + composition cards still add height when unconfirmed.  
- Compact pricing too hidden? — **no**; total/state + Detalii linii remain.  
- Still weak: large blocker banner visual weight; unconfirmed composition cards still open by default.

## 26. Hidden regressions

| Check | Result |
|-------|--------|
| Hidden required confirmation | No — CTA L1 |
| Missing price blocker | No — tarife lipsă / guidance retained |
| Incorrect sticky count | No evidence of count change |
| Duplicate guidance | Footer remains next-action owner |
| Collapsed inaccessible | Toggles present |
| Pricing total hidden | No |
| Responsive overflow | Narrow shot OK |
| Rail/footer overlap | Footer visible |
| Technical on L1 | Cleared for authority strings |
| Page 1 wiring | Not modified this build |
| Support role | Not modified this build |
| FinishSetup persistence | Untouched |
| Confirmare access | Honest when incomplete |
| Montaj change | Presentation-only tab visit; no IA |
| Global token drift | No global CSS |

## 27. Files modified

- `frontend/src/components/workos/intake-v6/IntakeV6ProductCompositionPanel.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ProductCompositionPanel.test.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6OfferScopeReviewSummary.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6OfferScopeReviewSummary.test.tsx` (new)
- `frontend/src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.test.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6PricingInputPanel.tsx`
- `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx`
- `docs/qa/intake-v6-letter-pilot-completion-2026-07-19/**`
- `docs/worklog/realignment/2026-07-19_intake_v6_letter_pilot_completion.md`

## 28. Files intentionally not modified

Backend, analyzer, SVG ingest, ProductDefinition services, pricing formulas, Montaj IA, global CSS, DB/migrations/seeds, Page 1 wiring, foreign WIP.

## 29. Dead pieces check

No orphaned testids for confirm CTA. Linked-segment content moved under unified technical accordion (`intake-v6-product-composition-technical`); tests updated.

## 30. Duplicate design-system check

Reused existing `IntakeV6TechnicalDetailsAccordion`, `v6` presentation atoms, Operator Guidance Model — no new design system.

## 31. Worklog

`docs/worklog/realignment/2026-07-19_intake_v6_letter_pilot_completion.md`

## 32. Commit

Isolated commit: `refactor(intake-v6): complete letter configurator pilot` (see git after commit).

## 33. Metoda de lucru si logica abordarii

Checkpoint-first → classify chrome as primary/secondary/technical → demote without changing truth → quiet pricing identity → unit tests → live screenshots → honest visual review → isolated commit.

## 34. Roadmap awareness checkpoint

Aligns with letter configurator Design System pilot completion after wiring repair acceptance; does not open Montaj IA, segmented background, or global Intake redesign.

## 35. Cat sunt in directia stabilita

**92/100%** — Page 2 product-first quieting delivered; residual ERP weight is intentional blocker honesty + unconfirmed composition expand.

## 36. Ce am construit este conform planului?

**DA** — tracks A–D, checkpoint-before-code, presentation-only, tests + live + screenshots + worklog + isolated commit boundary.

## 37. Next recommended build

One coherent build after owner GO: **Page 2 blocker-banner density calm** (keep counts, reduce equal-weight card competition) — or stop and accept pilot as complete.
