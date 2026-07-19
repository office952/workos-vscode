# Intake V6 — Confirmation Honesty Audit

**Date:** 2026-07-19  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Baseline:** `48a262a`  
**Mode:** Audit + minimal frontend presentation alignment (no domain / backend)

## Verdict

**PARTIAL → aligned after presentation fixes.**

Core question — *Can a new operator understand why they cannot finish?*

| Before fix | After fix |
|------------|-----------|
| **NO** — ✓ Configurare while unfinished; checklist ignored composition; enum leak `product_composition_not_confirmed`; footer progress 1/2 on wrong axis | **YES for primary blocker** — progress ✓ gated by readiness; checklist includes composition; RO copy; footer next-action = composition |

Domain predicates unchanged. Remaining UX debt (count mismatches drawer vs spine, pricing rail noise, Confirmare reachable via progress nav) documented — not domain bugs.

## Pre-flight

| Item | Value |
|------|--------|
| HEAD at start | `48a262a` |
| Foreign WIP | Present — untouched |
| FE / BE | `:3001` / `:8003` (proxy health 200) |
| Workspace | `c9ef796a-…` / `IV6-15CCCD91` |
| Fixture | `litere-cu-fundal-acm-segmentat.svg` |

## Inventory (sources)

| Concern | Source |
|---------|--------|
| Checklist progress | `resolveConfirmChecklistProgress` ← `useIntakeV6FinalHandoff` |
| Submit disabled reason | `resolveConfirmSubmitDisabledReason` → footer `confirmFooter` |
| Guidance spine | `buildIntakeV6OperatorGuidanceModel` (confirm uses `confirmDisabledReason`) |
| Consolidated status | `buildIntakeV6ConfirmConsolidatedStatus` |
| Final gates (comp/seg/elec) | `buildFinalConfirmationBlockers` |
| Continuă / ready | `canContinueFromReviewStep` / `isIntakeV6ReadyForQuotePreview` |
| Progress ✓ | `IntakeV6ProgressBar` (was index-only) |

## Track findings

### 1. Checklist UI
**Before:** items = finish + operator (+ boundary). Composition missing → finish could show done while composition blocks.  
**Fix:** composition row + progress count includes composition.

### 2. Final handoff
`canSubmit` requires ready preview + handoff + checkboxes. Access to Confirmare only needs analysis ready — reachable unfinished (by design of `canAccessIntakeV6Step`).

### 3. Footer guidance
Live: `Confirmare incompletă · … · Următorul pas: Confirmă compoziția produsului.` — correct after spine; progress count was dishonest until composition in checklist.

### 4. Submit reason
Fallback `"Workspace-ul nu este gata pentru preview."` hid composition. Prefer `firstBlocker`.

### 5. Readiness predicates
Honest. Domain OK — do not change.

### 6. Status vocabulary
Consolidated indicator uses Blocant / Avertizare / Pregătit. Observation leaked readiness enum — fixed in `formatQuoteHandoffBlocker`.

### 7. Segmented / electrical
`buildFinalConfirmationBlockers`: PROPOSED → warning; validation → blocker; electrical unconfirmed → warning. Confirmare does not list them in handoff checklist (still via final blockers / counts). Destination Montaj — copy already RO.

### 8. Accessibility
Footer `role="status"` + next action. Progress now `data-step-complete` + `aria-current`. Incomplete visited steps amber (not false ✓).

## Conflicts proven (live)

1. Progress **✓ Configurare** while composition unconfirmed.  
2. Checklist **1/2** while composition blocked.  
3. Observation **`Workspace readiness: product_composition_not_confirmed`**.  
4. Sticky **N elemente** vs footer **1 blocant** (different aggregators — documented, not fixed this build).  
5. Drawer **Probleme — 8** vs spine counts (drawer includes pricing/detail rows).

## Fixes made (presentation only)

- `IntakeV6ProgressBar` + Header: ✓ only when `isAnalysisReadyForReview` / `canContinueFromReviewStep`
- Checklist + `resolveConfirmChecklistProgress`: composition item
- `resolveConfirmSubmitDisabledReason`: prefer `firstBlocker`
- `formatQuoteHandoffBlocker`: RO for composition / finish / scope readiness codes

## Tests

40 Vitest tests PASS (submit reason, handoff readiness, handoff panel, progress bar, guidance, consolidated status).

## Screenshots

See `screenshots/` + `screenshots_index.md`.

## Frozen / not modified

Backend, schema, contracts, PD, Aggregate, analyzer, pricing logic, Montaj IA, Page 1 structure, status vocabulary IDs, DB/seeds.

## Next recommended build (owner GO)

**Confirmare count channel consolidation** — sticky “N elemente” vs guidance “1 blocant” vs drawer “Probleme — N” into one count model (presentation only).
