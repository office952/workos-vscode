# BUILD — WorkOS Commercial Document Visual Output

## Purpose

Client-facing visual polish for the **Commercial Document preview** in Quotes UI. Design-system badge adoption in the internal commercial action panel. No pricing, CostEngine, export engine, backend, or data contract changes.

## Context

- Branch: `local/integration-pr4-plus-svg-path`
- Base HEAD at start: `c3734dd` (`feat(tablet): adopt design system badges`)
- Prior design-system pilots: Work Intake, Employee Payments, Operations, Quotes list/detail, Product Pricing, Tablet

## Variant chosen

**VARIANT A — Safe frontend preview polish only**

- Modified `QuoteCommercialDocument.tsx` preview/document display and operator chrome styling
- Modified `QuoteCommercialActionPanel.tsx` for `StatusBadge` adoption (internal panel)
- **Did not modify** backend HTML export (`downloadQuoteDocument` → `GET .../commercial-document/export`)
- **Did not modify** data mapping, DTO fields, or financial calculations

## Scope

### In scope

- Commercial document preview shell (letterhead, sections, financial summary presentation)
- Operator chrome around preview (quick summary cards, preview toggle)
- `StatusBadge` in operator header and commercial action panel
- Targeted Vitest coverage

### Out of scope (boundaries)

- No DB / seed / migrations / backend
- No CostEngine / Pricing / Quote pricing API
- No Quote → Order acceptance/conversion logic
- No commercial document data contract change
- No PDF/HTML export engine rewrite (backend renderer untouched)
- No Work Intake / Orders / Operator / Execution
- No Employee Payments / ProductSystem / Pricing / Tablet
- No App shell / `index.css` / `tailwind.config`
- No SourceBadge in client-facing document letterhead (internal metadata only)
- No hiding warnings or changing CTA enable/disable logic

## Files changed

| File | Change |
|------|--------|
| `frontend/src/components/workos/QuoteCommercialDocument.tsx` | Document shell, letterhead (client, quote code, dates), line items table layout, financial summary emphasis, readiness panel styling, operator `StatusBadge` |
| `frontend/src/components/workos/QuoteCommercialActionPanel.tsx` | Replace purple inline status span with `StatusBadge domain="quote"` + preserved RO label |
| `frontend/src/components/workos/QuoteCommercialDocument.test.tsx` | Extended visual output + financial value regression tests |
| `frontend/src/components/workos/QuoteCommercialActionPanel.badges.test.tsx` | **New** — action panel badge adoption |

## Component modified

**Primary:** `QuoteCommercialDocument` — client-facing preview when operator clicks **Previzualizare**.

**Secondary:** `QuoteCommercialActionPanel` — internal commercial guidance (not client document).

## Export touched?

**No.**

Export is a separate backend HTML renderer invoked by `downloadQuoteDocument()` in `frontend/src/api/quoteDocuments.ts` → `backend/routers/quote_documents.py`. Preview markup changes do not flow to export.

## Values unchanged confirmation

- All amounts rendered via existing `formatCurrency()` on DTO fields (`totals.subtotal`, `totals.tva`, `totals.grand_total`, line item `total` / `unit_price`)
- `commercial.tva_percent` displayed as-is (no hardcoded TVA)
- `totals.currency` displayed as-is (no hardcoded currency)
- No recalculation, aggregation, or field removal
- Fixture EUR total remains **1.103,64 EUR** in tests

## Tests run + results

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run `
  src/components/workos/design-system/StatusBadge.test.tsx `
  src/components/workos/design-system/SourceBadge.test.tsx `
  src/components/workos/QuoteCommercialDocument.test.tsx `
  src/components/workos/QuoteCommercialActionPanel.badges.test.tsx `
  src/pages/Quotes.commercialActions.test.tsx `
  src/api/quoteDocuments.test.ts
```

| Suite | Result |
|-------|--------|
| `QuoteCommercialDocument.test.tsx` | **11 passed** |
| `QuoteCommercialActionPanel.badges.test.tsx` | **1 passed** |
| `StatusBadge.test.tsx` + `SourceBadge.test.tsx` + `Quotes.commercialActions.test.tsx` + `quoteDocuments.test.ts` | **59 passed** |
| **Total** | **71 passed** |

Coverage highlights:

- Preview renders without crash
- Header shows quote code, client, issue date
- Financial summary values unchanged (subtotal, TVA 209,69 EUR, grand total 1.103,64 EUR)
- No `structure/layer_N`, no false `0,00 EUR`
- Readiness warnings/blockers remain visible
- Design-system `StatusBadge` in operator chrome and action panel
- Existing commercial actions tests remain green

## Runtime smoke (read-only)

| Route | Result | Notes |
|-------|--------|-------|
| `http://127.0.0.1:3000/quotes` | **PASS** | Page loads; quotes list from Live DB |
| `http://127.0.0.1:3000/quotes/QT-E2E-COMMERCIAL-001` | **PASS** | Quote detail + commercial document panel |
| Backend `http://127.0.0.1:8000/health` | **PASS** | `{"status":"healthy"}` |
| Commercial document API `GET /quotes/1/commercial-document` | **PASS** | `grand_total=1104.33`, `currency=RON`, `subtotal=928.01`, `tva=176.32` |

**Smoke verifications (QT-E2E-COMMERCIAL-001):**

1. Page loads without crash — **PASS**
2. Commercial document preview opens via **Previzualizare** — **PASS**
3. Document letterhead visible: quote code, client, emitere, valabilitate, versiune — **PASS**
4. Operator quick summary: **1.104,33 RON**, TVA 19% — **PASS** (matches backend DTO)
5. Financial line item in preview: **928,01 RON** (subtotal line) — **PASS**
6. Component breakdown (Quotes detail table, separate from doc DTO) — **PASS** (6 components visible)
7. Governance warnings / informational warnings — **PASS** (visible in quote detail)
8. Commercial CTAs unchanged: Trimite oferta, Creează comandă, revizie — **PASS**
9. No export/download triggered — **PASS** (read-only)
10. Console errors — not observed during smoke navigation

**Note:** Commercial document preview shows RON totals from backend DTO (`totals.currency=RON`). Quote action panel may show EUR display from quote entity currency field — pre-existing dual-display pattern; this build did not change currency logic.

## Before / after visual summary

| Area | Before | After |
|------|--------|-------|
| Operator panel | Flat grid, no status badge | Summary cards + `StatusBadge` in operator chrome |
| Client preview | Sections only, no letterhead | Document shell with letterhead (title, quote code, client, dates, validity) |
| Line items | Simple flex rows | Column headers + grid layout, tabular nums |
| Financial summary | Inline totals block | Bordered summary card; larger TOTAL emphasis |
| Readiness notes | Red border box | Same content; refined border/background |
| Action panel status | Purple inline span | `StatusBadge domain="quote"` with preserved RO label |

## Badge adoption

| Location | Badge | Why |
|----------|-------|-----|
| `QuoteCommercialDocument` operator header | `StatusBadge domain="quote"` | Operator context; not in client letterhead |
| `QuoteCommercialActionPanel` | `StatusBadge domain="quote"` + `formatQuoteStatusLabel` | Replaces local purple span; preserves RO labels |
| Client document letterhead | **None** | Source/status internal metadata must not clutter client output |

**SourceBadge:** Not introduced — no prior source concept in commercial document preview.

## Deferred items

- True PDF/HTML export template redesign (backend renderer)
- Email send template polish
- Deeper client-facing branding system (company letterhead identity)
- Live E2E smoke on `QT-E2E-COMMERCIAL-001` when backend is healthy

## Commands

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/components/workos/QuoteCommercialDocument.test.tsx src/components/workos/QuoteCommercialActionPanel.badges.test.tsx
```

## Next steps

- Manual visual review on a seeded quote with commercial document DTO
- Optional follow-up: align backend HTML export styling with preview shell (separate build, VARIANT B)
