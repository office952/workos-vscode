# 2026-07-03 V6 Active Copy Remove QuoteWizard

## 1. Context

Micro-slice sigur dupa auditul de impact QuoteWizard. Decizia owner: nu stergem `QuoteWizard` acum, pentru ca ramane runtime activ pentru flow generic/manual/legacy, dar V6 nu trebuie sa mai mentioneze `QuoteWizard` in copy activ.

Boundary respectat: nu am sters `QuoteWizard.tsx`, nu am redenumit componenta, nu am schimbat UI layout, flow comercial, pricing logic, statusuri, backend API contract, DB schema, seed, Quote/Order snapshot, ProductAggregate, Task Graph, ExecutionPlan sau Employee Mobile.

## 2. Inventar copy relevant

| Path | Linie/context | Tip | V6 activ? | Generic/legacy? | Actiune |
| --- | --- | --- | --- | --- | --- |
| `backend/services/intake_v6_commercial_quote_service.py` | `Draft quote from Intake V6... Requires pricing review in QuoteWizard...` | backend copy salvat in `quote.notes.human_summary` | Da | V6 | Inlocuit cu copy V6 fara QuoteWizard. |
| `backend/services/intake_v6_quote_to_order_service.py` | `price the quote in QuoteWizard or freeze...` | backend blocker/error copy | Da | V6 | Inlocuit cu instructiune V6 backend totals / Snapshot V2. |
| `frontend/src/lib/intakeV6/intakeV6QuoteNotes.ts` | citeste `human_summary` din JSON notes | frontend display helper | Da | V6 | Neschimbat; afiseaza ce vine din backend. |
| `frontend/src/lib/intakeV6/intakeV6QuoteDisplay.ts` | `Nepretuit (draft V6)` | frontend V6 label | Da | V6 | Neschimbat; corect pentru draft nepretuit. |
| `frontend/src/components/workos/intake-v6/IntakeV6QuoteCommercialSpinePanel.tsx` | `Flux comercial V6`, `Scrie totaluri pe oferta` | frontend V6 spine copy | Da | V6 | Neschimbat; deja aliniat cu flow-ul real. |
| `frontend/src/components/workos/QuoteWizard.tsx` | componenta si copy generic | componenta runtime | Nu pentru V6 final pricing | generic/legacy | Neschimbat intentionat. |
| `frontend/src/components/workos/VolumetricLettersQuoteFlow.tsx` | legacy QuoteWizard copy | componenta runtime legacy | Nu pentru V6 final pricing | generic/legacy | Neschimbat intentionat. |
| `backend/services/intake_v4_*` | copy QuoteWizard | backend V4 legacy | Nu | legacy | Neschimbat intentionat. |
| `docs/**`, `docs/worklog/**` | multe mentiuni QuoteWizard | documentatie/istoric | Nu runtime | mixed | Nerescris in masa. |

## 3. Sursa mesajului V6

Mesajul confuz venea din backend, nu din frontend.

Sursa: `_normalize_v6_quote_draft_payload()` in `backend/services/intake_v6_commercial_quote_service.py`.

Mecanism:

1. Backend-ul creeaza payload-ul de draft quote V6.
2. Scrie `notes` ca JSON.
3. Pune textul in `notes.human_summary`.
4. Frontend-ul `readIntakeV6QuoteHumanSummary()` citeste acel camp.
5. `Quotes.tsx` il afiseaza in detail card.

Deci mesajul este salvat in quote notes la momentul crearii draftului. Nu este generat dinamic la render.

Limitare intentionata: quote-urile V6 deja persistate in DB pot pastra vechiul `human_summary` pana cand sunt regenerate sau actualizate printr-un script/migration dedicat. Acest micro-slice nu face DB migration si nu rescrie quote notes existente.

## 4. Copy nou

Copy introdus pentru drafturile V6 noi:

```txt
Draft generat din Intake V6 workspace {workspace_code}. Totalurile sunt pregatite ca preview V6, dar nu au fost inca scrise pe oferta ca pret comercial final. Oferta este doar pentru revizie interna si nu poate fi trimisa clientului, acceptata, transformata in comanda sau trimisa in productie.
```

Blocker V6 pricing review actualizat:

```txt
Quote has no commercial totals — write the official V6 backend totals on the quote or freeze a Quote Snapshot V2 with commercial total before completing pricing review.
```

## 5. Fisiere modificate

| Path | Schimbare |
| --- | --- |
| `backend/services/intake_v6_commercial_quote_service.py` | Eliminat `QuoteWizard` din `human_summary` V6 activ. |
| `backend/services/intake_v6_quote_to_order_service.py` | Eliminat `QuoteWizard` din blocker V6 `QUOTE_NOT_PRICED`. |
| `backend/tests/test_intake_v6_zero_quote_fast_guard.py` | Adaugat test ca `human_summary` V6 nu contine `QuoteWizard` si contine copy V6 nou. |

## 6. Ce NU am modificat

- Nu am sters `QuoteWizard.tsx`.
- Nu am sters importuri QuoteWizard.
- Nu am schimbat butonul `Oferta noua`.
- Nu am schimbat `/api/v1/entities/quotes/price`.
- Nu am schimbat priced dry-run/write/handoff logic.
- Nu am schimbat statusuri quote.
- Nu am schimbat snapshot/order.
- Nu am facut DB migration sau seed.
- Nu am rescris docs/worklogs in masa.

## 7. Validare

Targeted test:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v6_zero_quote_fast_guard.py -q
```

Rezultat: `4 passed, 3 warnings`.

Search post-edit:

- `backend/services/intake_v6*.py` nu mai contine `QuoteWizard`.
- `backend/services/intake_v6*.py` nu mai contine `Requires pricing review in QuoteWizard`.

## 8. Next safe step

Optional, cu GO owner separat: redenumire locala V6 `handleOpenQuoteWizard` -> `handleCreateDraftQuote` si curatare copy V6/legacy helper names fara rename global al componentei `QuoteWizard`.
