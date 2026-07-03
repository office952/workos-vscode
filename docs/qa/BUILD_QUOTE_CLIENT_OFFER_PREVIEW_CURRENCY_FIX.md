# BUILD: Quote Client Offer Preview Currency Fix

## Symptom

Quotes detail UI mismatch (screenshot):

- List + **Sumar Preț** → EUR (from `quote.currency` / `line_items` snapshot)
- **Ofertă pentru client** + **Detaliere preț** + **Descarcă HTML** → RON

PDF from **Trimitere asistată** also showed RON when backend was stale.

## Root cause

1. **Stale uvicorn on :8000** — process was not restarted after commits `9788454` / `bb738ef` / `82b496b`. Live `GET /commercial-document` returned `totals.currency=RON` while current codebase returns `EUR` for the same quote (`id=26`).
2. **Parsing hardening** — `quote_document_service` now uses `_resolve_canonical_snapshot()` aligned with frontend `extractQuotePayload` for Shape B (`line_items` + `component_breakdown` + `revision_source`).
3. **Commercial terms sync** — after totals build, `commercial.currency` matches `totals.currency`.

## Components / endpoints

| UI | Component | Endpoint |
|----|-----------|----------|
| Ofertă pentru client | `QuoteCommercialDocument.tsx` | `GET /api/v1/entities/quotes/{id}/commercial-document` |
| Descarcă HTML | same | `GET .../commercial-document/export` |
| PDF send | `QuoteSendDialog` → `QuotePdfService` | `POST .../pdf/generate` |

## Fix

- `backend/services/quote_document_service.py` — canonical snapshot resolution + commercial/totals currency alignment
- Tests: Shape B EUR in `test_quote_commercial_document.py`
- `frontend/src/components/workos/QuoteCommercialDocument.test.tsx`

## After deploy

**Restart backend** (required — reload alone may not replace old process on Windows if port held):

```powershell
# stop old uvicorn on :8000, then:
cd C:\Users\offic\workos\backend
$env:DATABASE_URL='sqlite+aiosqlite:///C:/Users/offic/workos/backend/dev.db'
$env:JWT_SECRET_KEY='local-dev-secret-not-for-production'
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Verify:

```powershell
(Invoke-RestMethod http://127.0.0.1:8000/api/v1/entities/quotes/26/commercial-document).totals.currency
# Expected: EUR
```

## Boundaries

- No CostEngine / pricing / schema changes
- No invented FX
