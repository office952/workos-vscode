# BUILD — WorkOS Design System Pilot 04: Quotes UI Badges

## Purpose

Visual/semantic adoption of shared `SourceBadge` and `StatusBadge` in Quotes UI. No pricing, CostEngine, commercial document, quote lifecycle, or backend changes.

## Context

- Branch: `local/integration-pr4-plus-svg-path`
- Base HEAD at start: `3c3c48a` (operations badge adoption)
- Prior pilots: Work Intake, Employee Payments, Orders/Operator/Execution

## Scope

### In scope

- `Quotes.tsx` — source badge, quote status badges (list + detail)
- `tokens.ts` — quote domain RO legacy aliases + expired tone
- Design-system + Quotes targeted tests

### Out of scope (boundaries)

- No DB / seed / migrations / backend
- No CostEngine / Pricing / commercial document logic
- No Quote → Order acceptance/conversion logic changes
- No Work Intake / Orders / Operator / Execution / Employee Payments / ProductSystem / Tablet
- No App shell / `index.css` / `tailwind.config`
- No PDF/HTML/TXT export changes

## Files changed

| File | Change |
|------|--------|
| `frontend/src/pages/Quotes.tsx` | `SourceBadge` + `StatusBadge`; remove local `DataSourceBadge`; fix header to use `quotesSource` |
| `frontend/src/components/workos/design-system/tokens.ts` | Quote RO legacy aliases; `expired`/`expirata` → orange |
| `frontend/src/components/workos/design-system/StatusBadge.test.tsx` | Extended quote domain coverage |
| `frontend/src/pages/Quotes.badges.test.tsx` | **New** — Quotes badge adoption + regression guards |

## Modules touched

- Quotes page header (source badge)
- Quote list cards (`QuoteCard`)
- Quote detail header status badge
- Status filter chips (labels from preserved `statusConfig`)

**Not touched:** `QuoteCommercialDocument`, `QuoteWizard`, `VolumetricQuoteReadinessChip`, commercial action panels, component breakdown table logic.

## Local badges removed / replaced

| Removed | Replaced with |
|---------|---------------|
| `DataSourceBadge` (~24 lines) | `<SourceBadge source={quotesSource} />` |
| `QuoteStatusBadge` inline Tailwind | `StatusBadge domain="quote"` + preserved RO/EN labels via wrapper |

**Preserved:**

- `statusConfig` — filter chip labels only (no `cls`)
- `VolumetricQuoteReadinessChip` — readiness semantics unchanged (deferred visual adoption)

## Source semantics

```ts
const quotesSource = sourcesDetail?.quotes ?? source;
<SourceBadge source={quotesSource} />
```

- **Fix:** header previously used aggregate `source`; now uses `quotesSource` (matches commercial action guard pattern)
- `db` → Live DB
- `empty` → Live DB (gol)
- `mock` → Mock Data
- `mixed` → Mixed Source (slate)
- Commercial actions still gated by `canMutateQuotes = quotesSource === "db"` (unchanged)

## Quote statuses covered

**UI statuses (QuoteStatus type):** `draft`, `priced`, `sent`, `viewed`, `negotiating`, `accepted`, `rejected`, `expired`

**Token aliases added (defensive, not in current UI data):** `trimisa`, `acceptata`, `refuzata`, `expirata`, `anulata`, `in_negociere`, `cancelled`

**Labels preserved in Quotes wrapper:**

| Status | Label shown |
|--------|-------------|
| draft | Draft |
| priced | Priced |
| sent | Trimis |
| viewed | Vizualizat |
| negotiating | Negociere |
| accepted | Acceptat |
| rejected | Respins |
| expired | Expirat |

**Tone change:** `expired` / `expirata` → orange (was slate in tokens; aligns with terminal-expiry semantics)

## Readiness / commercial visual cleanup

**Deferred:** `VolumetricQuoteReadinessChip` — separate component with multi-state readiness (`ready`, `ready_with_warnings`, `requires_acknowledgement`, `blocked`) and count suffixes. Not a simple quote status; adopting `StatusBadge` would require new generic mappings and risk conflating backend readiness with quote lifecycle status.

**Unchanged:** commercial action panels, disabled reasons, warning panels, readiness acknowledgement modals.

## Tests run + results

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run `
  src/components/workos/design-system/StatusBadge.test.tsx `
  src/components/workos/design-system/SourceBadge.test.tsx `
  src/pages/Quotes.badges.test.tsx `
  src/pages/Quotes.liveSourceGuard.test.tsx `
  src/pages/Quotes.commercialActions.test.tsx `
  src/pages/Quotes.commercialNavigation.test.tsx `
  src/pages/Quotes.readiness.test.tsx `
  src/pages/Quotes.list.readiness.test.tsx `
  src/pages/Quotes.route.test.tsx `
  src/pages/Quotes.visibility.test.tsx
```

**Result: 68/68 PASS** (10 files)

## Runtime smoke (read-only) — 2026-06-13

| Route | Result | Evidence |
|-------|--------|----------|
| `/quotes` | **PASS** | `SourceBadge` Live DB; quote badges `Priced` (violet); fixtures `QT-E2E-COMMERCIAL-001`, `QT-E2E-COMMERCIAL-WARN-001`; no mock/disconnected |
| `/quotes/QT-E2E-COMMERCIAL-001` | **PASS** | Detail status badge design-system; commercial actions enabled; breakdown visible; total 1.104,33; readiness chip present; 0 console errors |

No DB mutations. No quote actions performed.

## Visual before / after

| Element | Before | After |
|---------|--------|-------|
| Source badge | Local rounded-full; aggregate `source` | `SourceBadge`; `quotesSource` |
| Quote status | Inline Tailwind per status | `StatusBadge domain="quote"` + label override |
| Expired tone (tokens) | slate | orange |

Layout, filters, totals, commercial panels unchanged.

## Deferred items

- `VolumetricQuoteReadinessChip` → design-system generic adoption
- Commercial document visual system
- Quote commercial document output styling
- Global shell polish
- ProductSystem/Pricing adoption
- Tablet-specific adoption

## Commit status

**NOT COMMITTED** — ready for manual commit-tree review.
