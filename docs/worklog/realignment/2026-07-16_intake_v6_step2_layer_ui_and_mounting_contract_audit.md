# Worklog — Intake V6 Step2 layer UI + mounting + readiness UX audit

**Date:** 2026-07-16  
**Task:** `WORKOS-INTAKE-V6-STEP1-TO-STEP2-LAYER-UI-AND-MOUNTING-CONTRACT-PLAN-V1` (amended docs)  
**Branch baseline:** `feature/product-system-active-path-isolation-v1` @ `47cc4c1` (revert docs commit)  
**Mode:** PLAN / docs-only — no frontend/backend product changes, no runtime writes, no Build Locally, no commit of this pack until owner accepts.

**Plan pack:**
- `.compound-engineering/intake-v6-step2-layer-ui-and-mounting-contract/plan.md`
- `.compound-engineering/intake-v6-step2-layer-ui-and-mounting-contract/decision-log.md`

**Fixture:**
- Workspace `11891d68-c4c8-4719-acc5-f8fcb22a44af`
- SVG `C:\Users\offic\Desktop\fisiere-teste-svg\gradi-curat.svg`
- Backend probe `:8001` (existing listener; not restarted)

---

## 1. Readiness banner correction (audit)

### Stack
- `IntakeV6ReviewOperatorBlockerBanner.tsx` — title “Acțiune necesară înainte de Confirmare”
- `intakeV6OperatorBlockerBannerDisplay.ts` — merges handoff reasons + runtime/planner codes; generic technical fallback
- `intakeV6QuoteHandoffReadiness.ts` `buildReviewHandoffSurfacing` — residual vector + missing prices reasons

### Fixture handoff (read-only)
- `handoff_allowed=false`
- Fatal-ish: `readiness_not_ready:runtime_capture_blocked`, `operator_confirmation_missing`, `runtime_capture:MOUNTING_SOLUTION_MISSING`, `pricing_adapter_not_ready`
- Warnings include `unclassified_vector_artwork_requires_decision` + canonical unresolved warnings

### Classifications
| Message | Class | Notes |
|---------|-------|-------|
| Residual unclassified vector | WARNING_ACTIONABLE (+ wording FALSE_POSITIVE risk) | Delta ≈ artwork perimeter while artwork `confirmed=false` |
| Missing configured tariff | FALSE_POSITIVE candidate | Flag true; local predicate zero hits |
| Generic technical blockers | DUPLICATE/STALE wording | `MOUNTING_SOLUTION_MISSING` unmapped in FE |
| Mounting missing | BLOCKING_ACTIONABLE | Real gate |

### Target UX
Compact: `N probleme blochează Confirmarea · M avertisment`; expandable; no generic when codes exist; warnings amber.

---

## 2. Residual vector provenance

| Metric | Value |
|--------|-------|
| Raw cutting perimeter | ≈ 31.637 m (`path_geometry_summary`) |
| Letter group perimeter sum | ≈ 26.747 m |
| Artwork return perimeter | ≈ 4.891 m |
| BE rule | `raw > confirmed_letters[+confirmed_artwork]` |

Artwork rows: `print_laminate`, `confirmed=false`. Step1 roles already `printed_artwork`. Residual tracks **unconfirmed finish contribution**, not an unknown layer family.

---

## 3. Missing tariff warning provenance

Material-breakdown totals: `contains_missing_prices=true`, currency EUR, estimated total ≈ 725.16.

Only null `unit_price` consumable with qty>0: `led_total_watts` (`informational_only`) — excluded by `_is_price_missing_for_quantity`.

Local replay of missing-price helpers: **no hits**. Banner reason on this fixture is a **FALSE_POSITIVE candidate** / totals inconsistency.

Commercial dry-run: status `V6_PRICED_DRY_RUN_BLOCKED`; 9 commercial lines with null unit prices (RON totals null) — deferred to pricing audit.

---

## 4. Logo template existence / resolution

| Surface | Finding |
|---------|---------|
| Composition recommendation/confirmed | `TPL-VOLUMETRIC-LOGO_v1` for Logo 1/2 |
| Root binding | `TPL-VOLUMETRIC-LETTERS_v2` |
| Product System `template-availability` | **No LOGO template rows** on this DB |
| Linked BOM | `artwork_*_logo_instance_001/002` materials + print/laminate/application ops present |

Conclusion: **absent from availability registry surface** on fixture DB; still resolved as **linked child under letters** in composition + breakdown. Not a separate offerable root. Not omitted from live materialization.

---

## 5. Layer-to-template matrix

| Layer | Role | Template |
|-------|------|----------|
| pseudo maria/soare/ana/gradinita | face | `TPL-VOLUMETRIC-LETTERS_v2` |
| Logo 1 / Logo 2 | printed_artwork | `TPL-VOLUMETRIC-LOGO_v1` (linked) |

Matches expected owner mapping.

---

## 6. Layer-to-pricing-line provenance matrix (summary)

Present under letters-root breakdown:
- Plexiglas 3 mm (letters) + plexi per logo instance
- Forex 10 mm (letters, face-area fallback) + forex per logo instance (bbox fallback)
- Cant/volume combined perimeter (letters + artwork)
- Print + laminate materials/services per logo
- CNC face / CNC backing (letters-scoped)
- LED modules (145), PSU, adhesives, wires; LED watts informational

Logo geometry: **not omitted**; **linked**; **double-count risk** on areas/return vs letters — quantify later.

Full table: plan.md §8.

---

## 7. Pricing non-regression tests (planned for implementation GO)

See plan.md §9 — UI/mounting/banner must not mutate pricing inputs; snapshot linked-logo line keys; no formula changes.

---

## 8. Explicit deferral statement

**Numerical pricing correction is deferred to GRADI-CURAT PRICING TRUTH AUDIT** (RON/EUR, CPP vs EIC, VAT, tariffs, logo double-count, hourly commercial ban, partial totals).

---

## 9. Owner-visible verification (post-implementation)

Compact banner + mounting sentinel + labeled Spate + linked logo provenance + Forex preserved — see plan.md §11.

---

## 10. Recommended order

```text
Step 2 UI + mounting + readiness UX
→ GRADI-CURAT PRICING TRUTH AUDIT
→ ProductAggregate / commercial continuation
→ Quote / Order same-scenario E2E
```

---

## Commands run (read-only)

```powershell
# workspace composition / roles
Invoke-RestMethod .../intake-v6/workspaces/11891d68-... 

# material-breakdown + handoff + priced-quote-dry-run
Invoke-RestMethod .../material-breakdown
Invoke-RestMethod .../quote-handoff-preview
Invoke-RestMethod .../priced-quote-dry-run

# Product System availability
Invoke-RestMethod .../api/v1/product-system/template-availability
```

No workspace PATCH/POST. No seed. No listener restart.

---

## Status line

`INTAKE V6 STEP 2 LAYER UI + MOUNTING + READINESS UX PLAN READY FOR OWNER REVIEW`
