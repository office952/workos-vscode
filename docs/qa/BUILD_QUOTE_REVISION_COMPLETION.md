# BUILD: Quote Revision Completion

## 1. Scop build

Finalizează flow-ul de **revizie ofertă** în Quotes: eligibilitate pe status, dialog operator (motiv + discount), recalcul via endpoint existent extins, istoric revizii în payload, fără redesign Pricing/Commercial.

## 2. Fișiere atinse

| Fișier | Rol |
|--------|-----|
| `frontend/src/lib/quoteRevision.ts` | Eligibilitate, source resolve, build request, history extract |
| `frontend/src/lib/quoteRevision.test.ts` | Unit tests helpers |
| `frontend/src/components/workos/QuoteRevisionDialog.tsx` | Dialog revizie |
| `frontend/src/components/workos/QuoteRevisionDialog.test.tsx` | Tests dialog |
| `frontend/src/api/quotes.ts` | `priceExistingQuote`, tipuri revision; `postQuoteSendLog` types/API (forward-compat WIP send-log, fără backend în acest build) |
| `frontend/src/pages/Quotes.tsx` | Buton + dialog revizie (integrare minimă) |
| `frontend/src/lib/dataStore.ts` | Map `revisionHistory` din snapshot |
| `frontend/src/lib/mockData.ts` | Tip `QuoteRevisionHistoryEntry` |
| `backend/routers/quotes.py` | `POST /{quote_id}/price` — draft price vs revision |
| `backend/services/quote_legacy_revision.py` | Reconstrucție source din snapshot legacy |
| `backend/tests/test_quote_revision.py` | Tests endpoint revision |
| `backend/validators/status_lifecycle.py` | Tranziții `sent/viewed/negotiating → priced` pentru revizie |
| `backend/tests/test_quote_in_place_pricing_contract.py` | Contract revision + legacy + terminal reject |

## 3. Audit inițial

- **Există:** `quoteRevision.ts` (post `4a5ca39`), WIP dialog + tests, WIP `priceExistingQuote`, backend `POST /price` parțial.
- **Incomplet:** integrare Quotes page, `revisionHistory` în store, backend legacy path + tests, QA doc.
- **Off-scope WIP împletit:** send-log commercial, `QuoteCommercialActionPanel`, refactor Quotes actions — **exclus** din commit.
- **Decizie:** frontend + backend minimal (nu frontend-only).

## 4. Comportament implementat

1. Operator vede buton **Revizie** pe oferte eligibile (`data-testid="quote-revision-action"`).
2. Dialog: motiv (obligatoriu), discount % opțional, rezumat versiune/status.
3. Submit → `priceExistingQuote(id, buildQuoteRevisionRequest(...))`.
4. Succes: toast, `onRevised` → refresh listă; versiune +1, status `priced`, entry în `revision_history`.
5. Erori: mesaj controlat (eligibilitate, pricing blocked, legacy missing snapshot).
6. Oferte neeligibile: fără buton / mesaj în dialog dacă deschis invalid.

## 5. Statusuri eligibile / neeligibile

| Eligibil | Neeligibil |
|----------|------------|
| `draft`, `priced`, `sent`, `viewed`, `negotiating` | `accepted`, `rejected`, `expired` |

Aliniat frontend (`isQuoteRevisionEligible`) și backend (`_assert_quote_revision_allowed`).

## 6. Contract frontend/backend

**Request:** `POST /api/v1/entities/quotes/{quote_id}/price`

```json
{
  "revision_reason": "string (required for revision)",
  "discount_percent": 0,
  "source": { "...": "full pricing source OR omitted for legacy" }
}
```

**Response (revision):** `revised: true`, `quote_version`, `status: "priced"`, `revision_history` entry, pricing totals.

**Legacy:** body fără `source` — backend reconstruiește din `quote_input` snapshot via `build_legacy_revision_source_from_quote`.

## 7. Teste rulate și rezultate

| Suite | Comandă | Rezultat |
|-------|---------|----------|
| Frontend unit | `npm run test -- quoteRevision QuoteRevisionDialog` | **17 passed** |
| Typecheck | `npm run typecheck` | **PASS** |
| Validate frontend | `npm run validate:frontend` | **PASS** |
| Backend | `pytest backend/tests/test_quote_revision.py backend/tests/test_quote_legacy_revision.py` | **10 passed** |

## 8. Boundary

- Fără Pricing engine change (reutilizează pipeline existent).
- Fără CostEngine.
- Fără migrations / schema DB.
- Fără seed / e2e.
- Fără ANAF / clients.
- Fără Work Intake V2.
- Fără ProductSystem onboarding.
- Fără color registry / volumetric preview.
- Send-log backend **nu** intră în acest build (doar tipuri API frontend pentru WIP unstaged).

## 9. Riscuri rămase

- Oferte legacy fără snapshot complet → revizie respinsă cu mesaj explicit.
- `postQuoteSendLog` în `quotes.ts` fără endpoint backend în același commit — WIP send-log separat.
- Istoric revizii vizibil doar dacă backend persistă `revision_history` în entity JSON.

## 10. Verdict

**PASS — committed** (după staging scoped + validări).
