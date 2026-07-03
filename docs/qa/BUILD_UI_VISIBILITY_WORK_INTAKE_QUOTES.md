# BUILD — UI Visibility & Routing: Work Intake and Quote Forms

**Date:** 2026-06-07  
**Base HEAD:** `eacb66d` (docs: record migration hygiene validation)  
**Build commit:** *(see git log after commit)*  
**Scope:** Browser-first visibility/routing for Work Intake detail, volumetric quote handoff, generic Ofertă nouă  
**Out of scope:** pricing, CostEngine, readiness policy, Reference Catalogs, quote/order creation

---

## 1. Pre-flight

| Check | Result |
|-------|--------|
| Branch | `master` |
| HEAD (start) | `eacb66d` |
| History includes eacb66d, 83396d6, c80e616, c952293, a6c1480 | Yes |
| Backend `:8000/health` | `healthy` |
| Frontend `:3000` | Up (Vite) |
| Counts before | intakes **11**, quotes **7**, orders **8** |

Untracked (not committed): `.git_cmd_out.txt`, `docs/architecture/PRICING_RATE_BASIS_AND_CURRENCY_AUDIT.md`

---

## 2. Browser visibility inventory (before fix)

| form/action | expected | actual (before) | visible | problem | recommended fix |
|-------------|----------|-----------------|---------|---------|-----------------|
| Cerere Nouă | On `/intake`, opens dialog | Present in header | Yes | — | Keep |
| Confirmă sugestia / Template confirmat | Visible in template area | Present mid-page | Yes (below fold) | Buried under identity/delivery | Action map + jump link |
| TPL product form | On WI-SMOKE-P001 detail | `Product001IntakeSpecEditor` rendered | Yes (deep scroll) | No top anchor; operator must scroll | Section id + jump links |
| Marchează Gata pt. Ofertă | Bottom actions + reasons | Present at bottom | Yes (below fold) | Disabled reasons only at bottom | Surface in action map |
| Deschide ofertare preliminară | Visible, opens volumetric workspace | In product form + bottom `NextStepPanel` only | Yes (buried) | Primary CTA not above fold | Action map primary CTA |
| Volumetric quote workspace | Title, method cards, intake values | Opens from handoff | Yes | — | Keep routing |
| Ofertă Nouă | Generic `QuoteWizard` | Button visible | Yes | **After intake handoff, stale `location.state` reopened volumetric workspace** | Clear nav state on adhoc open/close |
| Action summary / next action | Near top of intake detail | **Missing** | **No** | Operator cannot see status/next step without scrolling | Add `IntakeActionSummary` |

---

## 3. Root causes

| Issue | File / component | Condition / logic | Minimal fix |
|-------|------------------|-------------------|-------------|
| No near-top action map | `IntakeDetail.tsx` | Only bottom `NextStepPanel` when `ready_for_quote` | Add `IntakeActionSummary` after title |
| CTAs buried below long page | `IntakeDetail.tsx` | Single long column; product form after identity + assist + delivery | Section anchors (`intake-section-*`) + jump links |
| Disabled ready reasons not visible early | `IntakeDetail.tsx` | `readiness.missing` only in bottom bar | Show missing list in action map when not ready |
| Ofertă nouă reuses intake handoff | `Quotes.tsx` | `wizardOpen` + persisted `location.state.templateCode` | `openAdhocWizard` / `closeWizard` clear state via `navigate(..., { state: {} })` |

---

## 4. Fixes made

1. **`IntakeActionSummary`** — near-top panel: template / spec / terrain / intake status, primary next action, missing prerequisites, jump links.
2. **`intakeActionSummary.ts`** — pure logic for next-action selection (no policy change).
3. **Section anchors** on template assist, product spec, terrain, ready-actions (`scroll-mt-4`).
4. **`Quotes.tsx`** — clear React Router state when opening ad-hoc wizard or closing any wizard (prevents volumetric workspace hijacking generic path).

No pricing, CostEngine, readiness policy, or backend changes.

---

## 5. Files changed

- `frontend/src/components/workos/IntakeActionSummary.tsx` (new)
- `frontend/src/lib/intakeActionSummary.ts` (new)
- `frontend/src/lib/intakeActionSummary.test.ts` (new)
- `frontend/src/pages/IntakeDetail.tsx`
- `frontend/src/pages/IntakeDetail.visibility.test.tsx` (new)
- `frontend/src/pages/Quotes.tsx`
- `frontend/src/pages/Quotes.visibility.test.tsx` (new)
- `docs/qa/BUILD_UI_VISIBILITY_WORK_INTAKE_QUOTES.md` (this file)

---

## 6. Tests / lint

```text
vitest run:
  intakeActionSummary.test.ts — 3 passed
  IntakeDetail.visibility.test.tsx — 5 passed
  Quotes.visibility.test.tsx — 1 passed
  QuoteWizard.volumetricRouting.test.tsx — 4 passed (regression)

eslint changed frontend files — 0 errors (2 pre-existing hook warnings in IntakeDetail.tsx)
```

Backend tests: not run (backend untouched).

---

## 7. Browser smoke (after fix) — WI-SMOKE-P001

| Step | Result |
|------|--------|
| `/intake` — Cerere Nouă visible | PASS |
| Action map near top on detail | PASS — "Hartă acțiuni — unde ești și ce urmează" |
| Template confirmed `TPL-VOLUMETRIC-LETTERS` | PASS |
| Jump links (spec, materiale, ofertare) | PASS |
| Product form / geometry / Vector Studio | PASS (reachable via scroll or jump) |
| Deschide ofertare preliminară (top CTA) | PASS → `/quotes` volumetric workspace |
| Values 4800 / 600 / 60 / 2.88 / 18 / 9 | PASS |
| Calculează preliminar | PASS → **844.41 EUR** |
| Creează ofertă comercială disabled + blockers | PASS (3 gate items shown) |
| Închide workspace | PASS |
| Ofertă nouă → generic wizard (client + template steps) | PASS (after state clear fix) |
| Anulează — no quote created | PASS |

Route regression: `/intake`, `/quotes`, `/product-system`, `/inventory/pricing` — loaded without error during session.

---

## 8. Counts before / after

| Entity | Before | After |
|--------|--------|-------|
| Intakes | 11 | 11 |
| Quotes | 7 | 7 |
| Orders | 8 | 8 |

---

## 9. Confirmations

- No pricing changes
- No CostEngine changes
- No quote/order created
- Reference Catalogs not started
- Readiness policy unchanged (`evaluateIntakeReadyPrerequisites` reused as-is)
- Other templates unaffected (action map is generic; volumetric form still gated by `shouldShowVolumetricProductForm`)

---

## 10. PASS / FAIL

**PASS** — forms and primary actions are visible in browser; volumetric handoff and generic Ofertă nouă both work; simulation baseline 844.41 EUR; counts unchanged.
