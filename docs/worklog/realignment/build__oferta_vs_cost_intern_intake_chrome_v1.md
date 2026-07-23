# Build — OFERTA_VS_COST_INTERN_INTAKE_CHROME_V1 (labels / IA only)

| Field | Value |
|-------|-------|
| **Date** | 2026-07-23 |
| **Verdict** | **PASS_WITH_WARNINGS** |
| **Root** | `C:\w\psiso` |
| **Branch** | `feature/product-system-active-path-isolation-v1` |
| **Base** | Nivel 2B `858b10c2` · Product Compiler shell `4690f7d5` |
| **Plan** | [`plan__workos_product_system_simplification_pass.md`](./plan__workos_product_system_simplification_pass.md) |
| **Forbidden (respected)** | Formulas / pricing engines, DB/API/schema, Nivel 3 `module_template_*` rename, Product System feature expansion beyond labels/chrome, commit without confirmation |

---

## Verdict

**PASS_WITH_WARNINGS**

Operator chrome now separates three channels in Intake V6 / Quotes / Pricing / Product System surfaces:

1. **Ofertă client** — price to customer (CPP / Snapshot V2)
2. **Cost intern estimativ** — internal estimate (EIC / live technical breakdown)
3. **Registry intern** — Pricing / Utilaje / Pontaj helpers (not the offer spine)

No formula, API, DB, or schema changes. Vitest targeted suite green. Runtime screenshots under `audit_assets/22_oferta_vs_cost_intern_*`.

**Warnings (honest):** early Intake V6 steps (Straturi) still emphasize scope copy like „Ofertă pentru produs complet” (what is offered, not the price channel). Quote list KPI titles still say „VALOARE TOTALĂ” rather than „Ofertă client”. Confirm / Pricing / Quotes detail / registry headers carry the new vocabulary clearly.

---

## Cat suntem in directia stabilita

**90/100%**

| Layer | Score | Note |
|------:|------:|------|
| Ofertă client vs Cost intern estimativ in Intake V6 chrome | 92% | Live calc, confirm hero, spine, truth notice, official blocker copy |
| Quotes frozen offer vs live internal cost | 90% | Snapshot V2 vs technical breakdown clearly labeled |
| Registries marked helper / not spine | 88% | Nav + Pricing/Utilaje page helper copy; Product System link uses `Pricing (registry)` |
| Product Compiler language preserved | 95% | From prior shell build; not diluted |
| Deep technical / legacy surfaces | 70% | Some „comercial” wording remains in non-offer-flow admin (e.g. ClientWorkspace) |
| Nivel 3 wire rename | 0% | Intentionally deferred |

Prior Product Compiler shell baseline was **86/100%**; this build lifts offer/cost operator clarity without touching engines.

---

## What is Ofertă client

- The commercial value destined for the customer (CPP / backend V6 dry-run totals / Quote Snapshot V2).
- Shown as: „Ofertă client”, „Ofertă client netă”, „Ofertă client cu TVA”, „Ofertă client înghețată”.
- Not cost of workshop / not registry rates.

## What is Cost intern estimativ

- Internal estimate for atelier / margin reference (EIC / material-operation breakdown).
- Shown as: „Cost intern estimativ” on confirm KPI, live calc, Quotes technical channel.
- Must never replace Ofertă client after freeze.

## What remains Registry intern

- **Pricing (registry)** — `/inventory/pricing` (page title still „Pricing Registry”; helper copy says registry intern).
- **Utilaje (registry)** — `/utilaje`.
- **Pontaj (registry intern)** — Personal nav.
- Not steps in Product Template → Module produs → Product Compiler → Ofertă client.

---

## Labels / IA changes (this finish pass)

| Surface | Change |
|---------|--------|
| Vocab module | `intakeV6OfferCostChromeVocabulary.ts` (+ test) |
| Aggregate truth notice | Compact copy without „preț oficial”; full notice uses boundary help + Product Compiler + registry help |
| Pricing input panel | Remaining „Preț comercial oficial” → Ofertă client; null-preview Product Truth copy; default title „Rezumat Ofertă client (V6)” |
| Official pricing blockers | „Oferta client nu este disponibilă…“ (display strings only) |
| Quote commercial spine | Flux / totals / footer use Ofertă client wording |
| Confirm KPI / Live calc | Already on vocab; tests updated |
| Quotes | Breakdown section title → „Ofertă client — breakdown pe componente“ |
| Pricing Registry page | Helper: Oferta client pe canal CPP; registry intern framing |
| Product System layout link | `Pricing (registry)` via vocabulary |
| Price breakdown / labor studio | Column headers Ofertă client / Cost intern estimativ |
| Control Center input line | „Rezultat comercial“ → „Ofertă client“ |
| Product Compiler no-price help | Mentions Ofertă client explicitly |

---

## Intentionally unchanged

| Keep | Why |
|------|-----|
| CPP / EIC / 7G technical names in parentheses | Honesty for engineers; not operator primary labels |
| Page title „Pricing Registry“ | Registry product name; helper text marks non-spine |
| „Ofertă pentru produs complet“ (offer scope) | Scope of composition, not price-channel chrome |
| Formulas, dry-run contracts, Snapshot schema | Out of bounds — UI/IA only |
| `module_template_*` wire fields | Nivel 3 |
| Commit | Explicitly not made |

---

## Recommendation (do not implement here)

If operators still confuse Confirm hero „Ofertă client (estimată)“ with frozen Snapshot totals, a later contract/UX build could add an explicit state chip (`dry-run` vs `snapshot frozen`) — that needs product decision, not more label churn alone.

---

## Audited pages / routes

| Route | Role in audit |
|-------|----------------|
| `/intake` | Work Intake list chrome |
| `/intake-v6/operator` (and workspace operator) | Commercial Intake chrome |
| `/quotes` (+ detail selection) | Ofertă client frozen vs Cost intern channel |
| `/product-system/products` | Catalog / Compiler shell intact |
| `/product-system/products/TPL-VOLUMETRIC-LETTERS_v2` | Template detail |
| `/inventory/pricing` | Registry intern helper |
| `/utilaje` | Registry intern helper |
| `/work-intake` | **Does not exist** — Work Intake is `/intake` |

---

## Tests run

```powershell
cd C:\w\psiso\frontend
npx --yes pnpm@8.10.0 exec vitest run `
  src/lib/intakeV6/intakeV6OfferCostChromeVocabulary.test.ts `
  src/lib/intakeV6/intakeV6OfficialPricing.test.ts `
  src/components/workos/intake-v6/IntakeV6AggregateCostTruthNotice.test.tsx `
  src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.test.tsx `
  src/components/workos/intake-v6/IntakeV6PricingInputPanel.test.tsx `
  src/features/product-system/productTemplateModulesVocabulary.test.ts `
  src/features/product-system/ProductCompilerDisplayShell.test.tsx `
  src/pages/Pricing.badges.test.tsx `
  src/pages/Quotes.badges.test.tsx `
  src/pages/ProductSystem.badges.test.tsx

# Extra related
npx --yes pnpm@8.10.0 exec vitest run `
  src/components/workos/intake-v6/FormSystemBackboneAwarenessPanel.test.tsx `
  src/lib/personalNavigation.test.ts
```

| Suite | Result |
|-------|--------|
| Primary targeted (10 files) | **110 passed** |
| Extra related (2 files) | **12 passed** |
| `validate:frontend` | **Not claimed green** (known TS debt) |

---

## Runtime

| Item | Value |
|------|--------|
| Frontend | http://127.0.0.1:3000 (`200`) |
| Backend | http://127.0.0.1:8000/api/v1/system/health (`200`) |
| Dev Mode | ON via local stack / `import.meta.env.DEV` |
| Capture | `frontend/scripts/capture-oferta-vs-cost-intern-intake-chrome-v1-screenshots.mjs` |

---

## Screenshots

- `docs/worklog/realignment/audit_assets/22_oferta_vs_cost_intern_intake.png`
- `docs/worklog/realignment/audit_assets/22_oferta_vs_cost_intern_intake_v6_operator.png`
- `docs/worklog/realignment/audit_assets/22_oferta_vs_cost_intern_quotes.png`
- `docs/worklog/realignment/audit_assets/22_oferta_vs_cost_intern_quotes_detail.png`
- `docs/worklog/realignment/audit_assets/22_oferta_vs_cost_intern_product_system_products.png`
- `docs/worklog/realignment/audit_assets/22_oferta_vs_cost_intern_product_template_letters.png`
- `docs/worklog/realignment/audit_assets/22_oferta_vs_cost_intern_pricing_registry.png`
- `docs/worklog/realignment/audit_assets/22_oferta_vs_cost_intern_utilaje_registry.png`

---

## Nivel 3 leftovers (out of scope)

1. No `module_template_*` rename.
2. Wire display adapter still not on every admin cell (from prior shell build).
3. Dual-read / DB rename remains owner-GO only.

---

## Honest operator clarity opinion

On Confirm / Quotes detail / Pricing Registry header, an operator can now tell **what the client pays** from **what the workshop estimates** and from **admin registries**. The remaining confusion risk is early Intake steps (scope language) and generic KPI words on the Quotes list — polishable later without engine changes. Directionally this closes the Ofertă vs Cost intern chrome gap called out after Product Compiler shell.

---

## Next build

1. Optional microcopy polish: Quotes list KPI → „Ofertă client (cu TVA)“; Intake scope chip keep „Ofertă…“ but add tooltip „canal Ofertă client“.
2. Doc sync of stale commercial wording in non-operator docs.
3. Nivel 3 only with owner GO.
4. **Do not** expand Product System features or touch CPP/EIC formulas in a labels pass.

---

## Files touched (finish pass)

- `frontend/src/lib/intakeV6/intakeV6OfferCostChromeVocabulary.ts` (+ test; may pre-exist)
- `frontend/src/lib/intakeV6/intakeV6OfficialPricing.ts` (+ test)
- `frontend/src/components/workos/intake-v6/IntakeV6AggregateCostTruthNotice.tsx` (+ test)
- `frontend/src/components/workos/intake-v6/IntakeV6PricingInputPanel.tsx` (+ test)
- `frontend/src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.test.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6QuoteCommercialSpinePanel.tsx`
- `frontend/src/components/pricing/PricingRegistrySpaciousView.tsx`
- `frontend/src/features/product-system/ProductSystemLayout.tsx`
- `frontend/src/features/product-system/productTemplateModulesVocabulary.ts`
- `frontend/src/features/product-system/PriceBreakdownSection.tsx`
- `frontend/src/features/product-system/TemplatePricingStudioPanel.tsx`
- `frontend/src/lib/currentTruthControlCenter.ts`
- `frontend/src/pages/Quotes.tsx` (+ `Quotes.badges.test.tsx`)
- `frontend/scripts/capture-oferta-vs-cost-intern-intake-chrome-v1-screenshots.mjs`
- This worklog + `audit_assets/22_*` screenshots

**Commit:** not made (awaiting user confirmation).
