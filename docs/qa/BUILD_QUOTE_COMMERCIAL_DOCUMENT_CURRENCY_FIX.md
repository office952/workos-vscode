# BUILD — Quote Commercial Document Currency Fix

## Bug

Intake/Quote pricing runs in **EUR** (e.g. 768 EUR), but commercial document / PDF export labeled totals as **RON/lei** without conversion — `768 lei` instead of `768 EUR`.

## Cauza

`QuoteDocumentService._build_commercial_terms()` always applied `DEFAULT_COMMERCIAL_TERMS["currency"] = "RON"` and never read `cost_result.currency` from the priced quote snapshot in `line_items`.

**Tip:** label-only bug (amounts were correct quote columns; currency label wrong). No hidden FX math — wrong default currency.

## Regula implementată

1. **Fără `exchange_rate` în snapshot:** document folosește `cost_result.currency` (ex. EUR); sumele rămân neschimbate.
2. **Cu `exchange_rate` explicit în wrapper snapshot:** prezentare RON = sumă × curs; afișare `source_currency`, `exchange_rate`, `source_amounts` în EUR.
3. **Fără curs inventat, fără live FX, fără hardcode.**

## Fișiere modificate

- `backend/services/quote_document_service.py` — extract currency, optional FX, totals presentation
- `backend/tests/test_quote_commercial_document.py` — EUR preserve + FX convert + HTML export
- `docs/qa/BUILD_QUOTE_COMMERCIAL_DOCUMENT_CURRENCY_FIX.md`

## Tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_quote_commercial_document.py -q
```

## Smoke

- Quote snapshot `cost_result.currency = EUR`, `grand_total = 768` → commercial document `totals.currency = EUR`, `768 EUR` în export HTML.
- Cu `exchange_rate: 5.0` în wrapper → `grand_total` prezentat `3840 RON`, sursă EUR în `source_amounts`.

## Neatins

- CostEngine formulas / calculate paths
- Pricing registry formulas
- TVA logic (still derived from quote columns + tva_percent)
- SmartBill
- Schema / migrations
- `dev.db` quote history (no backfill)

## Riscuri rămase

- `Quotes.tsx` / `QuoteCommercialActionPanel.tsx` încă afișează hardcoded `RON` în listă — UI list, nu PDF DTO.
- `quote_output_composition_service` hardcode RON separat — out of scope dacă nu e același export path.
- `exchange_rate` nu e persistat automat la pricing — doar citit dacă există în wrapper JSON.

## HEAD

Branch: `local/integration-pr4-plus-svg-path` (pre-commit)
