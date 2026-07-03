# BUILD: Quote PDF Real Path Currency Fix

## Why prior tests passed but PDF was still RON

Commits `9788454` and `bb738ef` fixed:

- `quote_document_service.py` commercial document DTO + HTML export
- Quote list UI and composition preview summary

They did **not** fix the PDF path used from **Trimitere asistată** (`QuoteSendDialog`):

- UI button **PDF** called client-side `generateQuotePDF()` (`jsPDF` in `quotePdfGenerator.ts`)
- That path hardcoded `RON` / `formatRON` on every total line
- Backend `QuotePdfPanel` (`POST /pdf/generate`) was a separate, less-used path

## Real path identified

| Layer | Detail |
|-------|--------|
| UI | `QuoteSendDialog.tsx` — button **PDF** in assisted send flow |
| Also | `QuotePdfPanel.tsx` — **Generează PDF** (`/api/v1/entities/quotes/{id}/pdf/generate`) |
| Backend service | `QuotePdfService` → `QuoteDocumentService.build_commercial_document()` → `_render_pdf_html()` → xhtml2pdf |
| Not used for send PDF | `quote_output_composition_service.py` |

## Root cause

1. **Primary (user report):** `QuoteSendDialog` used `quotePdfGenerator.ts` with hardcoded RON labels (`768 RON` for EUR amounts).
2. **Secondary:** `quote_pdf_service._render_pdf_html` used `totals.get("currency", "RON")` fallbacks — OK when DTO correct, but commercial section could diverge; unified `presentation_currency`.

## Fix

### Frontend

- `QuoteSendDialog`: when `quote.dbId` present, PDF button calls backend `generateQuotePdf` + `downloadLatestPdf` (same as `QuotePdfPanel`).
- `quotePdfGenerator.ts`: client fallback uses `quote.currency` via `formatQuoteMoney` (no hardcoded RON).
- `QuoteSendDialog` header total uses `formatQuoteMoney` with quote currency.

### Backend

- `quote_pdf_service._render_pdf_html`: single `presentation_currency` from `totals.currency` or `commercial.currency`.

## Tests added

- `frontend/src/lib/quotePdfGenerator.test.ts` — EUR summary not RON
- `frontend/src/components/workos/QuoteSendDialog.test.tsx` — backend PDF path + EUR display
- `backend/tests/test_quote_pdf_generation.py` — `test_pdf_eur_currency_from_dto`

## Smoke (manual)

1. Open priced EUR volumetric quote from DB.
2. **Trimitere asistată** → **PDF** → download.
3. PDF totals show **EUR** (e.g. `768,00 EUR`), not RON/lei.
4. **Generează PDF** panel still works with same backend DTO.

## Boundaries

- CostEngine, pricing formulas, schema/migration — not touched
- No invented FX; no live rates

## Remaining risks

- Old PDFs in archive generated before fix still show RON until regenerated
- Client fallback jsPDF still used only when `quote.dbId` is missing (mock/local)
