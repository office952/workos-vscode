# BUILD: Quote Send Log Completion

## 1. Audit inițial

| # | Finding |
|---|---------|
| **WIP găsit** | `quote_send_log.py`, `test_quote_send_log.py`, `quoteSendLog.ts`, `QuoteSendDialog.tsx` (rewrite), teste FE — toate **untracked** față de `348650a` |
| **`quotes.ts` (HEAD)** | `postQuoteSendLog`, `QuoteSendLogRequest/Response` — deja comis în revision build |
| **`quotes.py` (HEAD)** | `POST /{quote_id}/send-log` + import `quote_send_log` — **endpoint comis fără service file** (gap critic) |
| **Service backend** | `backend/services/quote_send_log.py` — complet, necomis |
| **Teste** | FE: `quoteSendLog.test.ts`, `QuoteSendDialog.test.tsx`; BE: `test_quote_send_log.py` — necomise |
| **DB/model** | Fără migrare; persistență în `quotes.line_items` JSON wrapper → `commercial_delivery_log[]`; status pe coloana `quotes.status`; `revision_history` separat în același wrapper |
| **Decizie** | Comitem service + teste + dialog finalizat; nu schimbăm schema DB, pricing, revision flow |

## 2. Scope

Flow **trimitere asistată**: operator loghează canal/destinatar/notă; backend persistă audit trail; status → `sent` doar din `draft`/`priced`; retrimiteri pe `sent`/`viewed`/`negotiating` nu degradează statusul.

## 3. Fișiere atinse

| Fișier | Rol |
|--------|-----|
| `backend/services/quote_send_log.py` | Validare payload, lifecycle, append log |
| `backend/tests/test_quote_send_log.py` | Contract endpoint |
| `frontend/src/lib/quoteSendLog.ts` | Helpers FE + eligibilitate |
| `frontend/src/lib/quoteSendLog.test.ts` | Unit tests |
| `frontend/src/components/workos/QuoteSendDialog.tsx` | Dialog trimitere asistată |
| `frontend/src/components/workos/QuoteSendDialog.test.tsx` | Tests dialog |
| `frontend/src/pages/Quotes.tsx` | `onRegistered` → refresh (fără dublu `updateQuoteStatus`) |

**Deja în HEAD (revision build):** `quotes.py` endpoint, `quotes.ts` API, `mockData` types, integrare butoane Quotes.

## 4. Endpoint implementat

`POST /api/v1/entities/quotes/{quote_id}/send-log`

Permisiune: `quote.send`

## 5. Payload / response

**Request:**
```json
{
  "channel": "email_manual",
  "recipient": "client@example.com",
  "note": "Trimis manual",
  "document_ref": "Q-001.pdf"
}
```

**Response:**
```json
{
  "quote_id": 1,
  "quote_code": "Q-001",
  "status": "sent",
  "quote_version": 2,
  "sent_at": "2026-06-09T12:00:00Z",
  "status_changed": true,
  "log_entry": { "channel": "email_manual", "sent_at": "...", "quote_version": 2 }
}
```

Canal valid: `email_manual`, `whatsapp`, `phone`, `print`, `other`.

## 6. Status lifecycle rules

| Status curent | După send-log |
|---------------|---------------|
| `draft`, `priced` | → `sent` (`status_changed: true`) |
| `sent`, `viewed`, `negotiating`, `accepted` | neschimbat |
| `rejected`, `expired` | blocat (422) |

Tranziții validate via `validate_transition` când status se schimbă.

## 7. Persistență

- **Unde:** `quotes.line_items` (JSON string) → cheie `commercial_delivery_log` (array append-only).
- **Entry:** `id`, `event_type: quote_send_assisted`, `channel`, `sent_at`, `quote_version`, `old_status`, `new_status`, `recipient`, `note`, `document_ref`, `actor_email`.
- **Nu se atinge:** `subtotal`, `grand_total`, `margin_pct`, pricing snapshot payload, `revision_history` (doar citit/ păstrat).

## 8. Ce NU se modifică

- Pricing engine / pipeline recalcul.
- CostEngine.
- Schema DB / migrations.
- `revision_history` (except append log separat).
- ProductSystem, Work Intake V2, ANAF/clients, SmartBill.
- Seed / e2e.

## 9. Teste rulate

| Suite | Rezultat |
|-------|----------|
| `pytest test_quote_send_log.py` | PASS |
| `pytest test_quote_revision.py test_quote_legacy_revision.py test_quote_in_place_pricing_contract.py test_quote_send_log.py` | PASS |
| `npm run test -- quoteSendLog QuoteSendDialog` | PASS |
| `npm run typecheck` | PASS |
| `npm run validate:frontend` | PASS |

## 10. Boundary

Send-log build separat de Quote Revision; reutilizează `postQuoteSendLog` din `quotes.ts`. `QuoteCommercialActionPanel` rămâne WIP unstaged.

## 11. Riscuri rămase

- `draft` → `sent` fără pricing prealabil (permis de lifecycle existent; UI afișează buton și pe draft).
- `accepted` permis la backend pentru audit re-trimitere; UI nu expune buton dedicat.
- Istoric `commercial_delivery_log` nu e mapat încă în `dataStore` (afișare listă — build viitor).

## 12. Verdict

**PASS — committed**
