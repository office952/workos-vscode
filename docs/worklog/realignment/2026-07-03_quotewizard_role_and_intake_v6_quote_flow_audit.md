# 2026-07-03 QuoteWizard Role and Intake V6 Quote Flow Audit

## 1. Context

Audit read-only pentru rolul real al termenului `QuoteWizard` in flow-ul Intake V6 -> Oferte. Workspace verificat inainte de audit: `C:\Users\offic\workos_app_vs`. Folderele cerute au fost vizibile: `frontend`, `backend`, `docs`, `fisiere-teste-svg`.

Boundary respectat: nu am modificat UI/copy/pricing/statusuri/snapshot/order/DB schema/seed; nu am intrat in ProductAggregate, Task Graph, ExecutionPlan sau Employee Mobile. Singura modificare este acest worklog.

## 2. Mesaj exact gasit

Mesaj runtime pe oferta auditata:

```txt
Draft quote from Intake V6 workspace IV6-1A59D22C. Requires pricing review in QuoteWizard — no final commercial price. Internal review-only draft — not approved for client send, order, or production.
```

Sursa cod: `backend/services/intake_v6_commercial_quote_service.py`, in `_normalize_v6_quote_draft_payload()`, campul JSON `notes.human_summary`.

## 3. Oferta testata

Oferta: `Q-V6-IV6-1A59D22C-1783033637`.

Runtime URL verificat: `/quotes/Q-V6-IV6-1A59D22C-1783033637` pe frontend local `http://127.0.0.1:3000`.

Rezultat runtime vizibil:

| Camp | Valoare |
| --- | --- |
| Quote code | `Q-V6-IV6-1A59D22C-1783033637` |
| Quote DB id | `14` |
| Status UI | `Draft` |
| Total quote row | `null` / afisat ca `Nepretuit (draft V6)` |
| Intake linkage | `IV6-187e351c-0bde-448d-b764-58bf2456ae06` |
| Panou dreapta | `Flux comercial V6` |
| Dry-run total propus | `6.445,87 RON` |
| Dry-run status | `Pregatit de scriere` |
| Buton mutativ prezent | `Scrie totaluri pe oferta` |
| Link/CTA QuoteWizard in card V6 | Nu |

Confirmare read-only prin proxy-ul folosit de frontend:

```json
{
  "id": 14,
  "code": "Q-V6-IV6-1A59D22C-1783033637",
  "status": "draft",
  "subtotal": null,
  "total_before_vat": null,
  "vat": null,
  "grand_total": null,
  "intake_code": "IV6-187e351c-0bde-448d-b764-58bf2456ae06",
  "line_items": "[{\"productCode\": \"TPL-VOLUMETRIC-LETTERS_v2\", \"description\": \"kjb\", \"quantity\": 19, \"unit_price\": null, \"total\": null}]"
}
```

## 4. Toate aparitiile QuoteWizard / pricing review relevante

Inventar cautat pentru termenii ceruti in `frontend`, `backend`, `docs`, teste, worklogs; excluse `node_modules`, `dist`, `coverage`, `__pycache__`, `.git`. Aparitiile din docs/worklogs sunt numeroase si majoritar istorice; tabelul de mai jos listeaza aparitiile active/relevante si grupeaza documentatia istorica.

| Path | Linie/context | Tip | Runtime activ? | Observatii |
| --- | --- | --- | --- | --- |
| `frontend/src/App.tsx` | routes `/quotes`, `/quotes/:quoteId`; nu exista `/quote-wizard` | route/page | Da | `Quotes` este pagina fizica pentru Oferte; nu exista ruta separata QuoteWizard. |
| `frontend/src/pages/Quotes.tsx` | import `QuoteWizard`; render `<QuoteWizard>` pentru `wizardOpen`; `Oferta noua` -> `openAdhocWizard()` | UI copy activ / componenta React | Da | QuoteWizard este modal in pagina Oferte. |
| `frontend/src/pages/Quotes.tsx` | `deriveIntakeV6WorkspaceId()` pentru `Q-V6-IV6-{uuid}` | UI/runtime glue | Da | Leaga oferta V6 la workspace pentru panoul comercial V6. |
| `frontend/src/pages/Quotes.tsx` | `Nepretuit (draft V6)` si text placeholder V6 | UI copy activ | Da | Explica de ce quote row zero/null nu este total final. |
| `frontend/src/components/workos/QuoteWizard.tsx` | header: `QuoteWizard — multi-step UI for pricing...`; `POST /api/v1/entities/quotes/price` | componenta React | Da | Modal generic de pricing/quote creation; nu pagina separata. |
| `frontend/src/components/workos/QuoteWizard.tsx` | `priceQuote(...)` in submit | componenta React | Da | Apeleaza endpoint generic `/entities/quotes/price`; nu writer-ul V6. |
| `frontend/src/components/workos/VolumetricLettersQuoteFlow.tsx` | `Replaces generic QuoteWizard UX for this template only` | componenta React / legacy compat | Partial | Flow volumetric legacy/compat, nu panoul V6 de pe oferta auditata. |
| `frontend/src/components/workos/intake-v6/IntakeV6QuoteCommercialSpinePanel.tsx` | `Flux comercial V6`, `Prețuire oficială`, `Scrie totaluri pe ofertă` | UI copy activ / componenta React | Da | Mecanismul V6 activ pentru oferta auditata. |
| `frontend/src/components/workos/intake-v6/IntakeV6QuoteCommercialSpinePanel.tsx` | `writeIntakeV6PricedQuote(...)` | componenta React | Da | Butonul scrie totaluri prin endpoint V6 dedicat. |
| `frontend/src/lib/intakeV6/intakeV6Api.ts` | `GET /priced-quote-dry-run`, `POST /priced-quote/write`, `POST /complete-pricing-review`, `POST /accept`, `POST /convert-to-order` | client API | Da | Suprafata frontend pentru flow V6 real. |
| `frontend/src/lib/intakeV6/intakeV6QuoteDisplay.ts` | `isUnpricedIntakeV6Quote()`, `Nepretuit (draft V6)` | UI display helper | Da | `draft` + `grandTotal <= 0/null` devine `Nepretuit`. |
| `frontend/src/lib/intakeV6/intakeV6QuoteNotes.ts` | citeste `notes.human_summary` | UI display helper | Da | De aici apare mesajul backend cu QuoteWizard in card. |
| `frontend/src/lib/commercialSpineNavigation.ts` | `buildQuoteWizardNavStateFromIntake()` | UI navigation | Da, legacy naming | Numele QuoteWizard e folosit ca nav-state conceptual, nu ca ruta. |
| `frontend/src/lib/intakeV6/intakeV6QuoteHandoff.ts` | alias `buildV4QuoteWizardNavState as buildV6QuoteWizardNavState` | legacy compat | Partial | V6 pastreaza numele de handoff QuoteWizard din V4/V2. |
| `frontend/src/lib/quoteCommercialGuidance.ts` | copy generic: calculeaza pretul in QuoteWizard | UI copy activ pentru non-V6/generic | Da, dar nu pe cardul V6 auditata | Copy generic istoric; V6 are panou propriu. |
| `frontend/src/lib/quoteIntakeCommercialGuard.ts` | `requires_pricing_review`, `pricing_review` | guard frontend | Da pentru IV3/generic | Pricing review este gate real, nu neaparat QuoteWizard. |
| `backend/routers/quotes.py` | `POST /api/v1/entities/quotes/price` | backend router | Da | Endpoint generic folosit de QuoteWizard; creeaza/persista quote priced via QuoteOrchestrator. |
| `backend/services/quote_orchestrator.py` | `build_snapshot(...)` | backend service | Da | Motor generic pentru `/entities/quotes/price`; nu writer V6. |
| `backend/services/intake_v6_commercial_quote_service.py` | `Draft quote from Intake V6... Requires pricing review in QuoteWizard...` | backend service / UI copy activ | Da | Sursa exacta a mesajului reclamat. Numele este ramas din contractul vechi de handoff. |
| `backend/services/intake_v6_commercial_quote_service.py` | `_strip_v6_draft_quote_pricing_fields()` | backend service | Da | Draft-ul V6 sterge `subtotal`, `vat`, `grand_total` si preturile de line item. |
| `backend/routers/intake_v6_workspaces.py` | `/workspaces/{id}/priced-quote-dry-run` | backend router | Da | Preview oficial backend, read-only. |
| `backend/routers/intake_v6_workspaces.py` | `/workspaces/{id}/priced-quote/write` | backend router | Da | Endpoint-ul butonului `Scrie totaluri pe oferta`. |
| `backend/routers/intake_v6_workspaces.py` | `/quotes/{quote_id}/complete-pricing-review` | backend router | Da | Marcheaza pricing review dupa ce exista totaluri. |
| `backend/routers/intake_v6_workspaces.py` | `/quotes/{quote_id}/owner-approval`, `/accept`, `/convert-to-order` | backend router | Da | Gate-uri downstream catre oferta acceptata/order. |
| `backend/services/intake_v6_priced_quote_dry_run_service.py` | `CommercialPriceProposalService(...).build_preview(...)` | backend service | Da | Calculeaza total comercial V6 preview, fara persistenta. |
| `backend/services/intake_v6_priced_quote_write_service.py` | `write_intake_v6_priced_quote_totals(...)` | backend service | Da | Recalculeaza dry-run server-side, valideaza hash/total, scrie quote `priced`. |
| `backend/services/intake_v6_offer_handoff_service.py` | `handoff-to-offer` creeaza/reutilizeaza draft si apoi write | backend service | Da | Single-step V6 handoff poate scrie totaluri daca operatorul confirma. |
| `backend/services/intake_v6_quote_to_order_service.py` | `_extract_v6_pricing_review_totals()` | backend service | Da | Pricing review cere quote totals sau snapshot V2; daca lipsesc, blocheaza. |
| `backend/services/intake_v3_*`, `backend/services/intake_v4_*` | `requires_pricing_review`, manual pricing review | backend legacy/compat | Da pentru V3/V4 | Conceptul de pricing review e real si partajat; QuoteWizard ca nume vine din flow-uri mai vechi. |
| `backend/tests/test_intake_v6_priced_quote_write.py` | teste pentru `V6_PRICED_QUOTE_WRITTEN` si blockers | test | Da | Acopera writer-ul V6. |
| `backend/tests/test_intake_v6_priced_quote_dry_run*.py` | teste dry-run V6 | test | Da | Acopera preview-ul oficial backend. |
| `backend/tests/test_intake_v6_offer_handoff_service.py` | next route `/quotes/Q-V6...` | test | Da | Acopera handoff-ul catre Oferte. |
| `frontend/src/components/workos/QuoteWizard*.test.tsx` | mocks/tests QuoteWizard | test | Da | Confirma componenta reala si ruta modal. |
| `frontend/src/pages/Quotes*.test.tsx` | mocks QuoteWizard, ruta `/quotes/:quoteId?`, `Oferta noua opens generic quote wizard` | test | Da | Confirma integrarea in Oferte. |
| `docs/architecture/product-system/V6_PRICED_QUOTE_WRITE_PATH_DESIGN.md` | `QuoteWizard pricing path ... FORBIDDEN_FOR_V6` | docs | Nu runtime | Documenteaza ca V6 nu trebuie sa foloseasca QuoteWizard generic pentru write oficial. |
| `docs/qa/BUILD_INTAKE_V6_QUOTES_INTEGRATION.md` | dry-run -> write -> snapshot -> review/approval/accept/convert | docs | Nu runtime | Documenteaza flow-ul actual implementat. |
| `docs/worklog/realignment/2026-07-01_*` | audit/design V6 priced quote bridge/write | worklog | Nu runtime | Istoric direct relevant: zero quote, write bridge, dry-run. |
| `docs/architecture/*`, `docs/qa/*`, `docs/audit/*` | multe mentiuni QuoteWizard V2/V3/V4/volumetric | docs/worklog | Nu runtime | Majoritar legacy/tranzitional; util ca istoric, nu dovada de ruta actuala. |

## 5. Exista ruta/pagina QuoteWizard?

Nu exista ruta fizica vizibila `/quote-wizard` sau similara in `frontend/src/App.tsx`.

Ruta reala pentru oferta este `/quotes/:quoteId`. Pagina Oferte (`frontend/src/pages/Quotes.tsx`) importa si randeaza `QuoteWizard` ca modal. `Ofertă nouă` deschide acest modal; intake handoff poate seta nav-state `openWizard`, tot in `/quotes`.

Concluzie: QuoteWizard exista ca modal/componenta accesibila din UI prin `/quotes`, nu ca pagina separata.

## 6. Exista componenta QuoteWizard?

Da. `frontend/src/components/workos/QuoteWizard.tsx` este componenta React reala.

Rol:

- UI multi-step pentru selectare client/template, configurare dimensiuni/cantitate, `quote_input`, pricing si preview.
- Nu calculeaza costuri local.
- Apeleaza `priceQuote()` din `frontend/src/api/quotes.ts`.
- `priceQuote()` trimite `POST /api/v1/entities/quotes/price`.
- Backend-ul generic `backend/routers/quotes.py` paseaza la `QuoteOrchestrator` si persista quote priced daca snapshot-ul e `priced`.

Folosire:

- Importata in `frontend/src/pages/Quotes.tsx`.
- Deschisa de butonul `Ofertă nouă`.
- Deschisa si de state-ul de navigare din intake legacy/volumetric.

Pentru oferta V6 auditata: componenta nu este CTA-ul direct. Cardul V6 afiseaza `Flux comercial V6` si foloseste `IntakeV6QuoteCommercialSpinePanel`.

## 7. Exista serviciu/backend QuoteWizard?

Nu exista un serviciu backend numit `QuoteWizard`.

Echivalent backend generic pentru QuoteWizard:

- `frontend/src/api/quotes.ts` -> `POST /api/v1/entities/quotes/price`
- `backend/routers/quotes.py::price_quote()`
- `backend/services/quote_orchestrator.py::build_snapshot()`

Echivalent backend nou pentru V6:

- `GET /api/v1/intake-v6/workspaces/{workspace_id}/priced-quote-dry-run`
- `POST /api/v1/intake-v6/workspaces/{workspace_id}/priced-quote/write`
- `POST /api/v1/intake-v6/quotes/{quote_id}/complete-pricing-review`
- `POST /api/v1/intake-v6/quotes/{quote_id}/owner-approval`
- `POST /api/v1/intake-v6/quotes/{quote_id}/accept`
- `POST /api/v1/intake-v6/quotes/{quote_id}/convert-to-order`

## 8. Flow real Intake V6 -> Draft Quote

Flow observat/dovedit:

1. Intake V6 produce Product Truth / pricing input preview si poate crea un draft quote intern.
2. Draft quote-ul V6 este creat prin `create-draft-quote` cu `notes.intake_v6_linkage_v1`, `quote_input_payload`, snapshot de handoff si `human_summary`.
3. Draft quote-ul V6 nu primeste automat totaluri oficiale. `_strip_v6_draft_quote_pricing_fields()` seteaza `subtotal`, `total_before_vat`, `vat`, `grand_total` si line item price/total la `null`.
4. Panoul `Flux comercial V6` incarca dry-run backend prin `priced-quote-dry-run` si afiseaza total propus/oficial, dar dry-run-ul nu scrie DB.
5. Totalurile devin oficiale pe quote doar dupa `POST /priced-quote/write`.
6. Dupa write, quote-ul devine `priced`, are line items pozitive, `requires_pricing_review=false` in linkage si trace `intake_v6_priced_quote_write_v1`.
7. Apoi urmeaza snapshot V2, pricing review, owner approval, accept, convert-to-order.

## 9. De ce apare Nepretuit / Draft

Pentru oferta auditata, quote row are `status=draft`, `grand_total=null`, line item `unit_price=null`, `total=null`. Frontend helper-ul `isUnpricedIntakeV6Quote()` intoarce true pentru quote V6 cu status `draft` si `grandTotal <= 0/null`; `formatV6QuoteTotalLabel()` afiseaza `Nepretuit (draft V6)`.

Motivul nu este lipsa calculului in dry-run. Motivul este ca totalul dry-run nu a fost inca scris pe quote prin endpoint-ul V6 dedicat.

## 10. Ce inseamna Pretuire oficiala / Total estimat

In panoul `Flux comercial V6`, `Prețuire oficială` este sectiunea care arata starea bridge-ului V6:

- daca quote totals exista pe quote, afiseaza `Prețuit` si total oficial pe quote;
- daca nu exista, dar dry-run-ul backend este ready, afiseaza `Pregatit de scriere` si `Total propus`;
- pentru oferta auditata, `6.445,87 RON` vine din dry-run backend (`CommercialPriceProposalService` / material breakdown), nu din quote row.

## 11. Ce face Scrie totaluri pe oferta

Butonul `Scrie totaluri pe ofertă` apeleaza `writeIntakeV6PricedQuote(workspaceId, body)` din `frontend/src/lib/intakeV6/intakeV6Api.ts`, adica:

```txt
POST /api/v1/intake-v6/workspaces/{workspace_id}/priced-quote/write
```

Backend-ul `write_intake_v6_priced_quote_totals()`:

- recalculeaza dry-run-ul server-side in `pricing_mode="write_priced_quote"`;
- cere `operator_confirmation=true`;
- verifica `pricing_status == V6_PRICED_DRY_RUN_READY`;
- verifica sursa `intake_v6_backend_priced_dry_run`;
- refuza total zero/missing;
- verifica `expected_total_gross` si `expected_pricing_hash`;
- refuza quote gresit, workspace mismatch, quote deja priced, quote terminal, snapshot/order existent;
- mapeaza liniile dry-run pozitive in line items quote;
- seteaza `status="priced"`, `subtotal`, `total_before_vat`, `vat`, `grand_total`, `line_items`, si trace in notes.

Nu am apasat butonul in runtime.

## 12. Ipoteza owner verificata

Ipoteza: `QuoteWizard poate fi problema pe care o ocolim pentru ca nu putem afisa/scrie pretul final imediat dupa Intake V6.`

Rezultat: partial adevarata ca istorie/nume, falsa ca mecanism activ.

Dovezi:

- QuoteWizard generic este real, dar foloseste `/entities/quotes/price`, nu write-ul V6.
- Documentatia V6 marcheaza `QuoteWizard pricing path` ca `FORBIDDEN_FOR_V6` pentru write oficial.
- Oferta auditata afiseaza `Flux comercial V6`, nu deschide QuoteWizard.
- Pretul `6.445,87 RON` exista ca dry-run backend si este `Pregatit de scriere`.
- Quote-ul ramane `Draft/Nepretuit` pentru ca write-ul oficial nu a fost executat.
- Mesajul activ din backend spune `Requires pricing review in QuoteWizard`, dar sistemul nou cere in practica `Scrie totaluri pe oferta` -> snapshot/review/approval.

## 13. Verdict asupra QuoteWizard

QuoteWizard este real ca modal React si flow generic vechi/curent pentru quote creation/pricing non-V6. Nu este pagina separata si nu este serviciu backend. Pentru Intake V6, rolul sau a fost inlocuit operational de `Flux comercial V6` + writer-ul V6 dedicat, dar copy-ul activ din draft quote inca foloseste numele vechi `QuoteWizard`.

## 14. Decizie recomandata A/B/C/D

Recomandare: **Decizia B — QuoteWizard este vechi, dar rolul lui a fost preluat de Flux comercial V6**.

Nu recomand schimbarea copy-ului in acest audit. Micro-slice-ul urmator poate propune alinierea mesajului `human_summary` dupa GO owner, astfel incat sa mentioneze pasul real V6 (`Flux comercial V6` / `Scrie totaluri pe oferta` / pricing review), nu QuoteWizard generic.

## 15. Ce NU am modificat

- Nu am modificat UI.
- Nu am redenumit QuoteWizard.
- Nu am schimbat copy runtime.
- Nu am schimbat pricing logic.
- Nu am schimbat statusuri.
- Nu am schimbat Quote/Order snapshot.
- Nu am facut DB migration.
- Nu am facut seed.
- Nu am apasat `Scrie totaluri pe oferta`.
- Nu am creat order/snapshot/accept/conversion.
- Nu am intrat in ProductAggregate / Task Graph / ExecutionPlan / Employee Mobile.

## 16. Riscuri ramase

1. Copy-ul activ `Requires pricing review in QuoteWizard` poate induce operatorul in eroare pentru V6, deoarece pagina reala arata `Flux comercial V6` si nu ofera CTA catre QuoteWizard.
2. Exista coexistenta de termeni: `QuoteWizard`, `Flux comercial V6`, `pricing review`, `write priced quote totals`. Functional sunt distincte; semantic pot parea acelasi lucru.
3. `Trimite in ofertare` si `Scrie totaluri pe oferta` sunt ambele mutative in panoul V6; auditul nu a validat prin click, doar prin cod/runtime read-only.
4. `.env.local` pointeaza frontend-ul local la `8005`; pentru audit am pornit frontend cu override env catre backend `8000`. Aceasta nu schimba repo-ul, dar trebuie stiut pentru reproducere.

## 17. Next safe step

Micro-slice recomandat dupa GO owner:

1. Schimbare stricta de copy pentru V6 `human_summary`, fara pricing/status/snapshot/order changes.
2. Test focused pentru `readIntakeV6QuoteHumanSummary` / Quotes detail daca exista deja pattern.
3. Eventual doc update: mapare `QuoteWizard legacy name` -> `Flux comercial V6 / priced quote write`.

Nu executa acest micro-slice fara GO owner pentru UI/copy.

## Runtime verification

Comenzi si verificari:

- `Get-Location` -> `C:\Users\offic\workos_app_vs`.
- Foldere vazute: `backend`, `docs`, `fisiere-teste-svg`, `frontend`.
- Pornire backend directa read-only pentru runtime: uvicorn `127.0.0.1:8000`, fara `--reload`.
- Pornire frontend din `frontend/` pe `127.0.0.1:3000` cu `VITE_API_BASE_URL=http://127.0.0.1:8000` in environment, fara editarea `.env.local`.
- Browser route: `http://127.0.0.1:3000/quotes/Q-V6-IV6-1A59D22C-1783033637`.
- Requests observate la load: `GET /api/v1/auth/me`, `GET /api/v1/entities/quotes`, `GET /api/v1/intake-v6/workspaces/187e351c-0bde-448d-b764-58bf2456ae06/commercial-spine-state`, `GET /api/v1/intake-v6/workspaces/187e351c-0bde-448d-b764-58bf2456ae06/priced-quote-dry-run`, `GET /api/v1/intake-v6/workspaces/187e351c-0bde-448d-b764-58bf2456ae06/material-breakdown`.
- Nu am executat POST-uri mutative din browser.
