# BUILD: Quote Currency Display Cleanup

## Purpose

Remove remaining hardcoded RON/lei labels in quote list UI, commercial action panel, and quote output composition preview — without changing CostEngine, pricing formulas, or schema.

## Context

Prior commit `9788454` fixed commercial document export (`quote_document_service.py`) so EUR snapshots stay EUR unless an explicit `exchange_rate` exists on the line_items wrapper.

This build extends the same display rule to remaining quote UI and composition preview paths.

## Audit — hardcodings found

| Location | Issue | Scope |
|----------|-------|-------|
| `frontend/src/pages/Quotes.tsx` | `RON` after totals (list card, KPI subtitles, line items, pricing summary) | UI list/detail only |
| `frontend/src/components/workos/QuoteCommercialActionPanel.tsx` | `RON` on commercial totals and revision history | UI only |
| `backend/services/quote_output_composition_service.py` | `currency: "RON"` in commercial_summary default and compose path | Composition preview DTO + HTML export template fallbacks |

Not bugs (left unchanged):

- `QuoteOutputCompositionPreview.tsx` — already reads `commercial_summary.currency` from API
- `quote_document_service.py` — fixed in prior build
- Legacy quotes without snapshot currency — controlled `RON` fallback when `cost_result.currency` absent

## Fixes applied

### Frontend

- `frontend/src/lib/quoteCurrency.ts` — extract `cost_result.currency` from line_items (canonical + Shape B wrapper); `formatQuoteMoney`, KPI label helper
- `frontend/src/lib/dataStore.ts` — map `currency` on `Quote` from line_items
- `frontend/src/lib/mockData.ts` — optional `currency` on `Quote`
- `frontend/src/pages/Quotes.tsx` — display amounts with quote currency; KPI subtitle reflects single currency or "valori în monede diferite"
- `frontend/src/components/workos/QuoteCommercialActionPanel.tsx` — totals use quote currency

### Backend

- `backend/services/quote_output_composition_service.py` — `_build_commercial_summary()` mirrors document service: snapshot currency, optional explicit `exchange_rate` conversion to RON with `source_amounts`

## Paths intentionally not changed

- CostEngine, pricing formulas, payroll, inventory, SmartBill
- Schema / migrations / seeds / dev.db
- Auto-persist of `exchange_rate` at pricing (still manual on wrapper)
- Other pages that show order totals in RON (orders workspace — separate domain)

## Tests

### Backend

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_quote_commercial_document.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_quote_output_composition_preview.py -q
.\.venv\Scripts\python.exe -m pytest tests -k "quote_output or commercial_document or currency" -q
```

### Frontend

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/quoteCurrency.test.ts
```

## Smoke (manual)

1. Quote with EUR volumetric snapshot (e.g. 768 EUR grand total).
2. Quotes list card shows `768,00 EUR` not `768 lei/RON`.
3. Commercial action panel totals show EUR.
4. Commercial document export still EUR (regression from prior build).
5. Output composition preview commercial summary shows EUR when no `exchange_rate`.

## Boundaries confirmed

- No CostEngine / pricing / schema changes
- No invented FX — conversion only when `exchange_rate` on line_items wrapper
- No commit of `backend/test_placeholder.db`

## Remaining risks

- KPI aggregates sum numeric totals across quotes; when currencies differ, subtitle warns "valori în monede diferite" but sum is not FX-normalized
- Revision history entries do not store per-version currency; display uses active quote currency
- `exchange_rate` not auto-persisted at pricing
