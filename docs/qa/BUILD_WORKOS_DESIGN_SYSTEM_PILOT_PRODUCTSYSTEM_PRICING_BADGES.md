# BUILD — WorkOS Design System Pilot 05: ProductSystem + Pricing Badges

## Purpose

Adopt WorkOS design-system `SourceBadge` and `StatusBadge` primitives in **ProductSystem** and **Pricing** UI only. Visual/semantic cleanup with **no** pricing calculation, CostEngine, backend, DB, or business-logic changes.

## Scope

### In scope

- ProductSystem header `SourceBadge` from existing `loadMode`
- ProductSystem template active/archived badges (`productSystem` domain)
- ProductSystem material registry status chips (`pricing` domain, display-only labels preserved)
- Pricing registry header `SourceBadge`
- Pricing registry row status badges (`pricing` domain)
- Pricing readiness gate badges in material drawer
- Pricing markup policy status badges
- Pricing source review status badge in material drawer
- Design-system token domains: `productSystem`, `pricing`
- Targeted Vitest coverage + read-only runtime smoke

### Out of scope / boundaries

- No DB changes, seed, migrations, fresh dev.db
- No backend changes
- No CostEngine / pricing calculation changes
- No Material Price Registry persistence changes
- No ProductSystem business logic / schema / API changes
- No TPL-VOLUMETRIC-LETTERS / Product 001 costing rules changes
- No Quotes / QuoteWizard / Commercial Document changes
- No Work Intake / Orders / Operator / Execution changes
- No Employee Payments / Tablet changes
- No App shell / `index.css` / `tailwind.config` changes
- No commit (manual commit-tree pending)

## Files changed

| File | Change |
|------|--------|
| `frontend/src/components/workos/design-system/tokens.ts` | Added `productSystem` + `pricing` domains |
| `frontend/src/components/workos/design-system/StatusBadge.test.tsx` | Domain mapping tests |
| `frontend/src/pages/ProductSystem.tsx` | `SourceBadge`, material registry `StatusBadge` |
| `frontend/src/features/product-system/TemplateLibraryView.tsx` | Template Activ/Arhivat → `StatusBadge` |
| `frontend/src/features/product-system/templateStudioPanels.tsx` | Editor command bar Activ/Arhivat → `StatusBadge` |
| `frontend/src/components/pricing/PricingRegistrySpaciousView.tsx` | Header Live DB → `SourceBadge` |
| `frontend/src/components/pricing/PricingEntryRow.tsx` | Local badge → design-system `StatusBadge` |
| `frontend/src/pages/Pricing.tsx` | Gate/policy/source-review badges; removed dead `DataSourceBadge` |
| `frontend/src/pages/ProductSystem.badges.test.tsx` | **New** page badge tests |
| `frontend/src/pages/Pricing.badges.test.tsx` | **New** page badge tests |

## Modules touched

- ProductSystem page + Template Library + Blueprint Studio command bar
- Pricing Registry spacious view + entry rows + material detail drawer + markup drawer policy rows
- Design-system tokens/tests only (no new primitives)

## Local badges removed/replaced

| Location | Before | After |
|----------|--------|-------|
| `Pricing.tsx` | Local `DataSourceBadge` (unused) | **Removed** |
| `Pricing.tsx` | `GateBadge` colored dot/text | `StatusBadge` domain `pricing` |
| `Pricing.tsx` | `PolicyRow` inline markup status span | `StatusBadge` domain `pricing` |
| `Pricing.tsx` | Material drawer source review colored text | `StatusBadge` domain `pricing` |
| `PricingRegistrySpaciousView.tsx` | Inline “Live DB” span | `SourceBadge` |
| `PricingEntryRow.tsx` | Local `StatusBadge` + severity classes | Design-system `StatusBadge` |
| `TemplateLibraryView.tsx` | Activ/Arhivat inline spans | `StatusBadge` domain `productSystem` |
| `templateStudioPanels.tsx` | Activ/Arhivat inline span | `StatusBadge` domain `productSystem` |
| `ProductSystem.tsx` | Material registry inline spans | `StatusBadge` domain `pricing` |
| `ProductSystem.tsx` | (no header source badge) | `SourceBadge` from `loadMode` |

**Left unchanged (intentional):** `OperationRoutingBadge`, validation save chip, legacy/experimental warning banners, `materialRegistryDisplay.ts` business helpers, pricing detail panel severity text (non-badge).

## Source semantics

### ProductSystem

Maps existing `loadMode` (no new data architecture):

| `loadMode` | `SourceBadge` |
|------------|---------------|
| `api` | `db` |
| `empty_real` | `empty` |
| `mock` | `mock` |
| `auth_required` | `error` |
| `error` | `error` |

Mock/auth/error warning text in header **preserved**.

### Pricing

Maps existing page `source` state from registry API load:

| `source` | `SourceBadge` |
|----------|---------------|
| `db` | `db` |
| `loading` | `loading` |
| `error` | `error` |

## Status domains used

### `productSystem`

- `active`, `archived` on template library rows and editor command bar

### `pricing`

- Registry rows: `owner_confirmed`, `needs_review`, `estimated`, `missing_price`, `active`, …
- Material registry chips in ProductSystem editor (labels preserved via `label` prop)
- Readiness gates: `ready`, `blocked`, `needs_review`, `missing_source`, `no_price`
- Markup policies: `active`, `draft`, `archived`
- Source review: `accepted`, `pending`, `needs_review`, `rejected`, …

## Token mappings added

**`productSystem`:** active/configured/approved → emerald; draft/experimental → violet; needs_review → amber; needs_owner_review → orange; inactive/archived/legacy → slate.

**`pricing`:** active/owner_confirmed/ready/reviewed/approved/configured/accepted → emerald; needs_review/needs_owner_review/estimated/pending → amber/orange; missing_price/no_price/missing/blocked/rejected → red; inactive/archived → slate; unknown/null → slate fallback.

## Tests run + results

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run `
  src/components/workos/design-system/StatusBadge.test.tsx `
  src/components/workos/design-system/SourceBadge.test.tsx `
  src/pages/ProductSystem.badges.test.tsx `
  src/pages/Pricing.badges.test.tsx `
  src/features/product-system/productSystemNavigation.test.ts `
  src/lib/pricingRegistry.test.ts
```

**Result: PASS — 6 files, 74 tests**

## Runtime smoke (read-only)

| Route | Result |
|-------|--------|
| `/product-system` | PASS — page loads; `SourceBadge` `data-source=db`; `TPL-VOLUMETRIC-LETTERS` visible; `StatusBadge` `productSystem/active`; no observed console error collection |
| `/inventory/pricing` (Pricing nav) | PASS — page loads; `SourceBadge` `data-source=db`; pricing row badges `domain=pricing`; owner-confirmed + missing-price warnings visible; materials/templates displayed |

Note: `/pricing` redirects to dashboard; canonical operator route is **`/inventory/pricing`**.

## Visual before/after summary

- Badge shape/tone unified with prior pilots (Quotes, Operations, Employee Payments)
- Romanian operational labels preserved (`Activ`, `Arhivat`, `Owner-confirmed`, gate labels, etc.)
- Source truthfulness unchanged — badges reflect existing load modes, not invented `sourcesDetail`
- Operational density and layouts preserved

## Deferred items

- Tablet-specific design-system adoption
- Commercial document visual output badges
- Global shell polish
- Full ProductSystem/Pricing page layout redesign
- Pricing detail panel severity text → badge (optional later)
- Centralizing all RO status labels in tokens vs local `label` props

## READY

**READY for manual commit-tree review** — targeted tests green, smoke read-only PASS, boundaries respected, no commit performed.
