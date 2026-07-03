# BUILD — Commercial Offer Document Consistency Fix

## Purpose

Fix client-facing commercial offer document so visible line items sum to subtotal (ex-VAT), with clean Romanian text and no internal cost breakdown leakage.

## Problem observed

On Quote detail / commercial document for volumetric quotes (e.g. `QT-E2E-COMMERCIAL-001`):

- Internal summary: Subtotal ~934,79 EUR, TVA 21% ~196,31 EUR, Total ~1.131,09 EUR
- Client document showed ~6 breakdown lines totaling ~238,43 EUR (internal component costs without markup)
- Document subtotal still showed full quote subtotal → **incoherent for clients**

## Root cause

1. **Subtotal / totals** come from quote DB columns via `_build_document_totals()` in `quote_document_service.py` (`total_before_vat`, `grand_total`, VAT from quote/snapshot). These include commercial markup (~25% on fixture).
2. **Line items** were built from `component_breakdown` in `line_items` JSON using raw `material_cost + labor_cost` (or `operation_cost`) — **internal costs, no markup**.
3. **Mismatch**: component sums reflected CostEngine cost base; subtotal reflected priced quote with margin.
4. **0,00 EUR lines**: zero-cost components in breakdown.
5. **"CNC/laser"**: `PRODUCT_COMMERCIAL_TEXT` (e.g. plexi template) and volumetric operations labels.
6. **"Valabilitate: —" / "până la —"**: `valid_until` null rendered as em-dash in UI and HTML export.

## Strategy

- **Display layer only** — no CostEngine, pricing registry, or template changes.
- After building raw lines from breakdown, **`_finalize_client_line_items()`**:
  - Drops zero-value and internal labels (`layer_*`, structure IDs).
  - If sum(lines) ≠ `total_before_vat` (±0.02), **single client line fallback**:
    - Volumetric: `Litere volumetrice luminoase conform specificațiilor`
    - Other: `Produs realizat conform specificațiilor clientului`
- **Client text**: volumetric `PRODUCT_COMMERCIAL_TEXT` updated; `_prepare_client_product_text()` sanitizes CNC/laser for volumetric.
- **Validity**: `validity_display` — `15 zile de la emitere` or `N zile (până la DATE)`; no bare em-dash.
- **Removed `component_breakdown` from commercial document DTO** (internal only).

## Before / after (numeric)

| Metric | Before (client doc) | After (fixture `QT-E2E-COMMERCIAL-001`, current `dev.db`) |
|--------|---------------------|-------------------------------------------------------------|
| Visible line sum | ~238,43 (6 lines, internal costs) | **928,01 RON** (1 line) |
| Subtotal ex-VAT | 928,01 RON (quote column) | **928,01 RON** |
| Line sum = subtotal | **FAIL** | **PASS** |
| TVA | 176,32 RON (19%) | 176,32 RON |
| Grand total | 1.104,33 RON | **1.104,33 RON** (unchanged) |
| Line count | 6 (+ 0,00 line) | **1** |

Note: User-reported EUR figures (934,79 / 1.131,09) reflect EUR presentation; current seeded fixture stores RON presentation with `exchange_rate` on wrapper — totals unchanged from quote columns.

## Files changed

| File | Change |
|------|--------|
| `backend/services/quote_document_service.py` | Line-item finalization, validity display, volumetric text, remove internal breakdown from DTO |
| `backend/routers/quote_documents.py` | HTML validity labels via `validity_display` |
| `backend/tests/test_quote_commercial_document.py` | Consistency + validity + fallback tests |
| `frontend/src/api/quoteDocuments.ts` | `validity_display` on `CommercialTerms` |
| `frontend/src/components/workos/QuoteCommercialDocument.tsx` | Validity label helper, hide product codes on lines |
| `frontend/src/components/workos/QuoteCommercialDocument.test.tsx` | Consistency display tests |

## Commands + results

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_quote_commercial_document.py -q
# 38 passed

cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/components/workos/QuoteCommercialDocument.test.tsx
# 5 passed
```

## Runtime smoke (`QT-E2E-COMMERCIAL-001`)

Service-level check against `backend/dev.db`:

- `line_sum_eq_subtotal`: true
- `line_count`: 1
- `total_eq_subtotal_tva`: true
- `no_zero_lines`: true
- `no_layer`: true
- `no_pana_la_dash`: true
- `no_cnc` in client DTO: true (after removing `component_breakdown` from response)
- `grand_total`: 1.104,33 RON

## Boundaries confirmed

- No CostEngine change
- No pricing registry change
- No ProductSystem template change
- No schema/migration change
- No seed change
- No quote status/governance change
- No output snapshot governance change

## Next steps

- If future commercial mapping can distribute priced amounts per component with sum = subtotal, extend `_finalize_client_line_items()` to keep detailed lines when aligned.
- Optional: browser smoke on `/quotes/QT-E2E-COMMERCIAL-001` with dev auth when stack is up.
