# Build — PRODUCT_COMPILER_DISPLAY_SHELL_V1 (labels / IA only)

| Field | Value |
|-------|-------|
| **Date** | 2026-07-23 |
| **Verdict** | **PASS** |
| **Root** | `C:\w\psiso` |
| **Branch** | `feature/product-system-active-path-isolation-v1` |
| **Base** | Nivel 2B `858b10c2` — Clean Product System internal module naming |
| **Plan** | [`plan__workos_product_system_simplification_pass.md`](./plan__workos_product_system_simplification_pass.md) |
| **Forbidden (respected)** | DB/`module_template_*` rename, migrations, API contracts, formulas/pricing, PD/Aggregate **behavior**, Execution materialization, seed/reset, CPP/EIC, SVG/DWG |

---

## Verdict

**PASS**

Display shell only: Product Compiler as the visible PD+Aggregate concept; Execution Plan three-state strip; HR / Machines / Pricing marked as internal registries. No contract or compiler behavior changes. Vitest green. Runtime screenshots under `audit_assets/21_product_compiler_shell_*`.

---

## Cat suntem in directia stabilita

**86/100%**

| Layer | Score | Note |
|------:|------:|------|
| Product Template → Module produs vocabulary | 98% | From Nivel 1–2B |
| Product Compiler as single visible concept | 85% | Shell + stage labels on studio / aggregate / form / modules map |
| Execution Plan 3 states | 80% | Strip on `/execution` + V2 truth panel; Operational remains blocked |
| Registries not operator spine | 82% | Nav + page helper copy for Pricing / Utilaje / Pontaj |
| Adapter for `module_template_*` | 40% | Display helper added; not wired on every table cell yet |
| Nivel 3 real rename | 0% | Intentionally deferred |

Prior plan baseline was **80/100%**; this build lifts IA clarity without touching engines.

---

## What changed (labels / IA)

### Vocabulary & shells

| File | Change |
|------|--------|
| [`productTemplateModulesVocabulary.ts`](../../frontend/src/features/product-system/productTemplateModulesVocabulary.ts) | `PRODUCT_COMPILER_*`, Execution Plan 3 states, registry nav labels, `displayModuleTemplateWireLabel()` adapter |
| [`ProductCompilerDisplayShell.tsx`](../../frontend/src/features/product-system/ProductCompilerDisplayShell.tsx) | Visible Product Compiler chrome + stage chips |
| [`ExecutionPlanStatesStrip.tsx`](../../frontend/src/components/execution/ExecutionPlanStatesStrip.tsx) | Preview → Draft Plan → Operational Plan |

### Product System surfaces

| Surface | Label / IA |
|---------|------------|
| Studio tab | **Product Compiler** (was „Structură produs”) |
| Structure panel | Product Compiler shell + graph stage heading |
| Aggregate overview | Product Compiler · Graf tehnic (wire note: ProductAggregate) |
| Form System PD section | Product Compiler · Definiție |
| E2E readiness pipeline | Compiler · Definiție / Graf; Ofertă (CPP); Cost intern (EIC); Execution Plan · Preview |
| Template detail materials | Product Compiler · Definiție |
| Candidate Module produs readiness | Product Compiler · Definiție — readiness |

### Execution / registries / map

| Surface | Change |
|---------|--------|
| `/execution` | Execution Plan states strip |
| `ExecutionPlanV2TruthPanel` | Title + states strip + Draft/Operational wording |
| App nav | Pricing (registry), Utilaje (registry) |
| Personal nav | Pontaj (registry intern) |
| Pricing Registry / Utilaje pages | Helper copy: not Product Template → Module produs → Compiler spine |
| `/modules` Control Center | PRESENT_SYSTEMS / ownership rows → Product Compiler · Definiție / Graf tehnic |

---

## Intentionally left internal

| Keep | Why |
|------|-----|
| Service names / APIs `ProductDefinition*` / `ProductAggregate*` | Behavior + contracts unchanged |
| Wire fields `module_template_*` | Nivel 3 — adapter helper only |
| Guard copy mentioning ProductDefinition / ProductAggregate | Honesty / forbidden-path language |
| Template codes `TPL-COMP-*` | Identity, not UI type labels |
| Operational Plan materialize | Still GO-gated / blocked |

---

## Tests run

```powershell
cd C:\w\psiso\frontend
npx --yes pnpm@8.10.0 exec vitest run `
  src/features/product-system/productTemplateModulesVocabulary.test.ts `
  src/features/product-system/ProductCompilerDisplayShell.test.tsx `
  src/pages/ModuleChain.test.tsx `
  src/lib/personalNavigation.test.ts `
  src/lib/productSystemCanonicalModel.test.ts `
  src/pages/ProductSystem.badges.test.tsx `
  src/features/product-system/TemplateLibraryView.test.tsx
```

**Result:** 7 files / **91 passed**

---

## Runtime

| Item | Value |
|------|--------|
| Frontend | http://127.0.0.1:3000 |
| Backend | http://127.0.0.1:8000 (`healthy`, COMPATIBLE) |
| Dev Mode | ON (`VITE_ENABLE_DEV_AUTH` via stack) |
| Capture | `frontend/scripts/capture-product-compiler-display-shell-v1-screenshots.mjs` |

---

## Screenshots

- `docs/worklog/realignment/audit_assets/21_product_compiler_shell_products_catalog.png`
- `docs/worklog/realignment/audit_assets/21_product_compiler_shell_product_template_detail.png`
- `docs/worklog/realignment/audit_assets/21_product_compiler_shell_studio_structure.png` (shell count=2 on Compiler tab)
- `docs/worklog/realignment/audit_assets/21_product_compiler_shell_components.png`
- `docs/worklog/realignment/audit_assets/21_product_compiler_shell_modules_map.png`
- `docs/worklog/realignment/audit_assets/21_product_compiler_shell_execution_plan_states.png`

---

## Nivel 3 remainder

1. Wire `displayModuleTemplateWireLabel` onto remaining admin tables that still print raw `module_template_*` keys.
2. Optional route cosmetic `/product-system/components` → modules path id.
3. **Do not** DB/API rename until owner GO + dual-read period.
4. Doc sync of stale Implementation Route status lines (separate docs build).

---

## Honest UI opinion

The Product Compiler shell makes the studio structure tab readable as one concept instead of “another Aggregate panel.” Execution Plan states on `/execution` are clear but still educational chrome until Draft/Operational data is bound per-order on the dashboard. Registry nav suffixes reduce the chance that Pricing/Utilaje/Pontaj feel like peer product steps — good enough for this slice; Intake commercial chrome was out of scope and still needs a later Ofertă vs Cost intern pass.

---

## Files touched (summary)

- Vocabulary + display shells + tests
- `ProductSystem.tsx`, Aggregate/Form/E2E/Template detail/Catalog shell/Candidate panel
- `ExecutionDashboard.tsx`, `ExecutionPlanV2TruthPanel.tsx`
- `App.tsx`, `personalNavigation.ts`, `Utilaje.tsx`, `PricingRegistrySpaciousView.tsx`
- `currentTruthControlCenter.ts`
- Capture script + this worklog + audit screenshots
