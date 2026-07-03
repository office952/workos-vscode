# BUILD — Volumetric Intake Page v2

**Date:** 2026-06-07  
**Base HEAD:** `942e1f0` (fix: surface intake quote forms and actions)  
**Build commit:** *(see git log after commit)*  
**Scope:** Dedicated shell for `TPL-VOLUMETRIC-LETTERS` on Work Intake detail  
**Out of scope:** pricing, CostEngine, readiness policy, Reference Catalogs, quote/order creation, `Product001IntakeSpecEditor` rewrite

---

## 1. Pre-flight

| Check | Result |
|-------|--------|
| Branch | `master` |
| HEAD (start) | `942e1f0` |
| Backend `:8000/health` | `200` |
| Frontend `:3000` | `200` |
| Counts before | intakes **11**, quotes **7**, orders **8** |

Untracked (not committed): `.git_cmd_out.txt`, `docs/architecture/PRICING_RATE_BASIS_AND_CURRENCY_AUDIT.md`

---

## 2. Problem found

`IntakeDetail` was a monolithic generic CRM page. For `TPL-VOLUMETRIC-LETTERS`, the real product form existed but was surrounded by irrelevant UI: CUI/SmartBill, backend assist, sheet assist, totem terrain fields, duplicated CTAs, and generic status panels.

Build `942e1f0` improved visibility (action map, anchors) but did not fix the structural shell problem.

---

## 3. Contract summary

See `docs/architecture/VOLUMETRIC_INTAKE_PAGE_CONTRACT.md`.

- Dedicated `VolumetricLettersIntakePage` for confirmed or pre-confirm volumetric family
- `Product001IntakeSpecEditor` remains core form (`showQuotePrepPanel={false}`)
- Terrain N/A for non-install delivery; install terrain without totem fields
- Single handoff CTA → `VolumetricLettersQuoteFlow`
- Status conflict warning when stored status is ahead of computed readiness

---

## 4. Code audit (before implementation)

| File / component | Responsibility | Volumetric route |
|------------------|----------------|------------------|
| `IntakeDetail.tsx` | Monolithic page + routing | **Router** — early return to volumetric shell |
| `VolumetricLettersIntakePage.tsx` | *(new)* dedicated shell | **Keep** — compact context, template, spec, terrain, handoff, gate |
| `Product001IntakeSpecEditor` | Product form | **Keep** — unchanged contract |
| `IntakeActionSummary` | Action map | **Reuse** |
| `BackendAssistSection` | Template/sheet assist | **Hide** after template confirm on volumetric route |
| `IdentitySection` | CUI / fiscal | **Hide** on volumetric route |
| `AuditTerenSection` | Terrain audit | **Conditional** — install only, `isTotemFamily={false}` |
| `NextStepPanel` | Bottom duplicate CTA | **Hide** on volumetric route |
| Generic summary bar | product_family + dimensions | **Hide** on volumetric route |

---

## 5. Root cause

Template-specific volumetric work shared the same JSX tree as totem/generic families. No routing split existed — only conditional fragments (`showProduct001Spec`) inside the full generic page.

---

## 6. Fixes made

1. **`volumetricIntakeRoute.ts`** — `shouldUseVolumetricIntakePage`, `hasIntakeStatusReadinessConflict`
2. **`VolumetricLettersIntakePage.tsx`** — dedicated shell per contract
3. **`IntakeDetail.tsx`** — thin router; generic path unchanged for other families
4. **Tests** — routing, shell visibility, generic regression, quote wizard regression

No pricing, CostEngine, readiness policy, or backend changes.

---

## 7. Files changed

- `docs/architecture/VOLUMETRIC_INTAKE_PAGE_CONTRACT.md` (new)
- `frontend/src/lib/volumetricIntakeRoute.ts` (new)
- `frontend/src/lib/volumetricIntakeRoute.test.ts` (new)
- `frontend/src/components/workos/VolumetricLettersIntakePage.tsx` (new)
- `frontend/src/pages/IntakeDetail.tsx`
- `frontend/src/pages/IntakeDetail.volumetricShell.test.tsx` (new)
- `frontend/src/pages/IntakeDetail.visibility.test.tsx`
- `docs/qa/BUILD_VOLUMETRIC_INTAKE_PAGE_V2.md` (this file)

---

## 8. UI removed/hidden from volumetric route only

- `IdentitySection` (CUI/SmartBill primary workflow)
- Live mode mockData banner
- `BackendAssistSection` after template confirmation
- Material/Sheet Assist primary panels
- Generic client bar (`product_family`, dimensions as SoT)
- `NextStepPanel` duplicate quote CTA
- Totem terrain fields (`macara`, foundation, surface type)
- `Product001IntakeSpecEditor` quote prep panel (`showQuotePrepPanel={false}`)

---

## 9. Preserved

- `Product001IntakeSpecEditor` and `product_spec_json` contract
- `VolumetricLettersQuoteFlow` handoff via `/quotes` nav state
- `evaluateIntakeReadyPrerequisites` / mark-ready policy
- Generic `IntakeDetail` for non-volumetric families (verified WI-3320)
- Generic **Ofertă nouă** wizard from `/quotes`

---

## 10. Tests / lint

```text
vitest run:
  volumetricIntakeRoute.test.ts — 5 passed
  IntakeDetail.volumetricShell.test.tsx — 12 passed
  IntakeDetail.visibility.test.tsx — 5 passed
  Quotes.visibility.test.tsx — 1 passed

eslint (changed files): 0 errors (2 pre-existing useEffect warnings in IntakeDetail.tsx)
```

Backend tests: not run (no backend changes).

---

## 11. Browser smoke

### WI-SMOKE-P001 (`/intake/WI-SMOKE-P001`)

| Step | Result |
|------|--------|
| Dedicated volumetric page (no generic CUI/assist) | PASS |
| Compact context visible | PASS |
| Template badge `TPL-VOLUMETRIC-LETTERS` | PASS |
| `Product001IntakeSpecEditor` + geometry sections | PASS |
| Vector Studio accessible | PASS |
| Teren N/A (courier) | PASS |
| No totem/macara/foundation fields | PASS |
| **Deschide ofertare preliminară** visible | PASS |
| Opens `VolumetricLettersQuoteFlow` | PASS |
| Values 4800 / 600 / 60 / 2.88 / 18 / 9 | PASS |
| Preliminary simulation | **844.41 EUR** PASS |
| Commercial quote disabled (blockers) | PASS |

### WI-3320 (`/intake/WI-3320`)

| Step | Result |
|------|--------|
| Generic path (Identificare Client, Backend Assist, totem terrain) | PASS |
| No `volumetric-intake-page` test id | PASS |

### `/quotes`

| Step | Result |
|------|--------|
| **Ofertă nouă** opens generic `QuoteWizard` | PASS |
| Cancel — no quote/order created | PASS |

### Route regression

`/intake`, `/quotes`, `/product-system`, `/inventory/pricing` — reachable.

---

## 12. Counts before / after

| Entity | Before | After |
|--------|--------|-------|
| intakes | 11 | 11 |
| quotes | 7 | 7 |
| orders | 8 | 8 |

No quote or order created during smoke.

---

## 13. Confirmations

| Item | Status |
|------|--------|
| No pricing changes | Yes |
| No CostEngine changes | Yes |
| No quote/order created | Yes |
| No Reference Catalogs started | Yes |
| Readiness policy unchanged | Yes |
| `Product001IntakeSpecEditor` contract unchanged | Yes |
| `VolumetricLettersQuoteFlow` unchanged (routing only) | Yes |
| Generic/non-volumetric intake unaffected | Yes |

---

## 14. Result

**PASS** — dedicated volumetric shell live; generic path and quote handoff preserved.
