# 2026-07-03 Intake V6 Direct Priced Quote Audit

## 1. Context

Audit read-only pentru intrebarea owner: daca eliminam mental model-ul QuoteWizard si clarificam flow-ul V6, putem trimite din Intake V6 direct in Oferte/Quotes cu pretuire inclusa?

Workspace verificat in sesiunea curenta: `C:\Users\offic\workos_app_vs`. Folderele cerute au fost prezente: `frontend`, `backend`, `docs`, `fisiere-teste-svg`.

Boundary respectat: nu am modificat UI/copy/pricing/statusuri/snapshot/order/DB schema/seed; nu am apasat `Scrie totaluri pe oferta`, `Trimite in ofertare`, snapshot, review, accept sau convert; nu am intrat in ProductAggregate, Task Graph, ExecutionPlan, Inventory write sau Employee Mobile. Singura modificare este acest worklog.

Audit companion: `docs/worklog/realignment/2026-07-03_quotewizard_role_and_intake_v6_quote_flow_audit.md`.

## 2. Intrebarea owner

Scenariul dorit:

```txt
Intake V6 complet
  -> calculeaza pretul comercial server-side
  -> creeaza quote in Quotes/Oferte cu totalurile deja scrise
  -> quote apare direct ca Priced / Pretuit
  -> fara pas separat manual "Scrie totaluri pe oferta"
```

Raspuns scurt: **da, tehnic exista deja o forma single-step (`handoff-to-offer`) care poate crea/reutiliza draftul si scrie totalurile in aceeasi operatie backend; nu este insa sigur sa devina auto-write tacit. Varianta recomandata este un CTA explicit in Intake V6, de tip `Creeaza oferta pretuita`, care reutilizeaza aceleasi guarduri: dry-run ready, total/hash asteptat, confirmare operator, quote eligibility, fara snapshot/order existent.**

## 3. Flow actual Intake V6 -> Quote

Flow-ul actual dovedit prin cod, teste si runtime:

1. Intake V6 creeaza sau reutilizeaza un draft quote intern.
2. Draftul V6 este intentionat nepretuit: `subtotal`, `total_before_vat`, `vat`, `grand_total`, `unit_price` si `total` pe line items sunt sterse/null in `_strip_v6_draft_quote_pricing_fields()`.
3. In `/quotes/:quoteId`, `Quotes.tsx` detecteaza quote V6 dupa `intakeId`/cod `Q-V6-IV6-{uuid}` si afiseaza `IntakeV6QuoteCommercialSpinePanel`.
4. Panoul V6 face `GET /api/v1/intake-v6/workspaces/{workspace_id}/priced-quote-dry-run`.
5. Daca dry-run este ready dar quote totals lipsesc, UI arata `Pregatit de scriere`, total propus si butonul `Scrie totaluri pe oferta`.
6. `POST /api/v1/intake-v6/workspaces/{workspace_id}/priced-quote/write` scrie oficial totalurile si seteaza quote status `priced`.
7. Dupa write urmeaza separat Quote Snapshot V2, pricing review, owner approval, accept, convert-to-order.

QuoteWizard nu este calea V6 oficiala. Pentru V6, calea reala este `Flux comercial V6` + dry-run/write/snapshot/review.

## 4. Runtime read-only pentru quote-ul cerut

Ruta verificata in browser, read-only:

```txt
http://127.0.0.1:3000/quotes/Q-V6-IV6-1A59D22C-1783033637
```

Stack local pornit fara editarea `.env.local`:

- backend: `127.0.0.1:8000`
- frontend: `127.0.0.1:3000`
- frontend env runtime: `VITE_API_BASE_URL=http://127.0.0.1:8000`

Observatii DOM:

| Camp | Valoare |
| --- | --- |
| Quote code | `Q-V6-IV6-1A59D22C-1783033637` |
| Quote DB id | `14` |
| Status | `Draft` |
| Card total | `Nepretuit (draft V6)` |
| Client | `Client Test Smoke` |
| Intake linkage | `IV6-187e351c-0bde-448d-b764-58bf2456ae06` |
| Panou activ | `Flux comercial V6` |
| Hero/dry-run total | `6.445,87 RON` |
| Dry-run label | `Pregatit de scriere` |
| Mutative CTA vizibil | `Scrie totaluri pe oferta` |
| `Trimite in ofertare` | dezactivat in acest runtime, lipseste `clientAnalysisHash` in context |

GET-uri read-only din browser:

```json
{
  "quote": {
    "id": 14,
    "code": "Q-V6-IV6-1A59D22C-1783033637",
    "status": "draft",
    "subtotal": null,
    "total_before_vat": null,
    "vat": null,
    "grand_total": null,
    "intake_code": "IV6-187e351c-0bde-448d-b764-58bf2456ae06",
    "line_items": "[{\"productCode\": \"TPL-VOLUMETRIC-LETTERS_v2\", \"description\": \"kjb\", \"quantity\": 19, \"unit_price\": null, \"total\": null}]"
  },
  "dryRun": {
    "pricing_status": "V6_PRICED_DRY_RUN_READY",
    "pricing_source": "intake_v6_backend_priced_dry_run",
    "subtotal_net": 5416.7,
    "total_gross": 6445.87,
    "currency": "RON",
    "blockers": [],
    "warnings_count": 8,
    "dry_run_only": true,
    "persistence": {
      "creates_quote": false,
      "updates_quote": false,
      "writes_quote_totals": false,
      "creates_quote_snapshot": false,
      "creates_order": false
    }
  },
  "spine": {
    "quote_exists": true,
    "quote_id": 14,
    "quote_code": "Q-V6-IV6-1A59D22C-1783033637",
    "quote_status": "draft",
    "quote_commercial_totals": {
      "available": false,
      "grand_total": 0,
      "blocker": "QUOTE_NOT_PRICED"
    },
    "pricing_review": { "completed": false },
    "owner_approval": { "exists": false, "valid": false, "stale": false },
    "quote_accepted": false,
    "v6_order_conversion": {
      "converted": false,
      "blocked_reasons": [
        "PRICING_REVIEW_REQUIRED",
        "OWNER_APPROVAL_REQUIRED",
        "QUOTE_NOT_ACCEPTED"
      ]
    }
  }
}
```

Nu am executat POST-uri mutative.

## 5. Ce face dry-run

`backend/services/intake_v6_priced_quote_dry_run_service.py` construieste o previzualizare backend-only:

- citeste workspace-ul V6;
- construieste pricing input preview;
- citeste material breakdown;
- construieste `CommercialPriceProposalService.build_preview()`;
- blocheaza daca pricing input nu este ready, commercial proposal lipseste/nu e ready, exista owner decision obligatoriu necunoscut, hourly commercial usage interzis sau total zero;
- calculeaza totaluri comerciale in RON;
- intoarce `pricing_status`, `commercial_totals`, `commercial_line_items`, `internal_cost_trace`, `pricing_input_trace`, `commercial_proposal_trace`, `warnings`, `blockers`.

Dry-run nu scrie nimic:

```json
{
  "dry_run_only": true,
  "persistence": {
    "creates_quote": false,
    "updates_quote": false,
    "writes_quote_totals": false,
    "creates_quote_snapshot": false,
    "creates_order": false
  }
}
```

Testele confirma: dry-run nu creeaza/updateaza quote, nu foloseste V4 draft builder si nu copiaza totaluri frontend preview.

## 6. Ce face write totals

`backend/services/intake_v6_priced_quote_write_service.py` este writer-ul oficial V6. El nu foloseste QuoteWizard generic si nu creeaza quote, snapshot sau order.

Write-ul:

- reruleaza server-side dry-run in `pricing_mode="write_priced_quote"`;
- cere `operator_confirmation=true`;
- cere `pricing_status == V6_PRICED_DRY_RUN_READY`;
- cere `pricing_source == intake_v6_backend_priced_dry_run`;
- refuza total zero/missing;
- verifica `expected_total_gross` fata de totalul recomputat pe server;
- verifica optional `expected_pricing_hash` fata de hash-ul recomputat pe server;
- cere line items pozitive;
- cere quote V6 legat la acelasi workspace;
- refuza status terminal/accepted/converted;
- refuza quote deja priced;
- refuza quote cu snapshot sau order existent;
- scrie `status="priced"`, line items, `subtotal`, `total_before_vat`, `vat`, `grand_total`, `margin_pct`, si provenance in `notes.intake_v6_linkage_v1.intake_v6_priced_quote_write_v1`.

Testele confirma blockers pentru dry-run blocked, zero total, expected total mismatch, quote non-V6, workspace mismatch, already priced, snapshot exists, accepted quote, order exists, missing operator confirmation, forbidden V4/V2 source, missing line items.

## 7. Ce face handoff-to-offer

`backend/services/intake_v6_offer_handoff_service.py` este deja single-step:

1. construieste `IntakeV6CreateDraftQuoteRequest` cu confirmari interne (`confirm_internal_draft_quote`, `confirm_no_order`, `confirm_no_execution`, `confirm_no_inventory`);
2. apeleaza `create_or_reuse_guarded_draft_quote_from_intake_v6_workspace()`;
3. apeleaza `write_intake_v6_priced_quote_totals()` pe quote-ul rezultat;
4. intoarce `next_route: /quotes/{quote_code}`.

Acesta este cel mai apropiat mecanism existent de scenariul `Intake V6 -> Oferte cu pretuire inclusa`.

Important: handoff-to-offer nu ocoleste guardurile. Cere in request:

- `client_analysis_hash` de 64 caractere;
- `expected_total_gross`;
- `expected_pricing_hash` optional, dar UI il trimite cand exista;
- `operator_confirmation=true`.

Frontend-ul actual il expune prin butonul `Trimite in ofertare` din `IntakeV6QuoteCommercialSpinePanel`. In runtime-ul auditului pentru quote-ul cerut, butonul era disabled pentru ca `clientAnalysisHash` nu era disponibil in pagina quote existenta.

## 8. Conditii pentru auto-priced quote

O oferta V6 poate fi creata direct ca priced numai daca sunt pastrate aceste conditii minime:

1. Workspace V6 este complet suficient pentru pricing input preview.
2. Product/pricing input adapter este `ready`, fara blockers.
3. Material breakdown este disponibil sau CPP poate produce total valid fara el, conform politicii curente.
4. CommercialPriceProposal este disponibil si `status == ready`.
5. Nu exista commercial blockers obligatorii sau owner decisions obligatorii necunoscute.
6. `pricing_source` este backend V6: `intake_v6_backend_priced_dry_run`.
7. `commercial_totals.subtotal_net > 0` si `commercial_totals.total_gross > 0`.
8. Exista line items comerciale pozitive.
9. Serverul recomputa dry-run in momentul write-ului.
10. Request-ul include totalul asteptat si, ideal, pricing hash-ul vazut de operator.
11. Operatorul face o actiune explicita de confirmare, nu un autosave tacit.
12. Quote-ul tinta este V6, workspace-ul se potriveste si nu este deja priced.
13. Nu exista snapshot sau order legat de quote-ul tinta.
14. Dupa write, acceptarea si conversia raman blocate pana la snapshot/review/owner approval/accept.

Fara aceste conditii, auto-priced devine o scriere comerciala tacita, nu o simplificare de UX.

## 9. Riscuri auto-write tacit

1. **Race cu pricing state**: operatorul vede un total, dar datele workspace/ratele se schimba inainte de write. Hash-ul si expected totalul exista tocmai pentru a prinde asta.
2. **Transformarea preview-ului in pret oficial fara confirmare**: dry-run este explicit `dry_run_only` si nu are drept de persistenta.
3. **Scriere peste quote istoric**: writer-ul refuza already priced, snapshot/order, status terminal. Auto-write ar trebui sa pastreze aceleasi refuzuri.
4. **Confuzie intre draft intern si oferta client**: draft quote nu inseamna oferta finala. Chiar priced, quote-ul nu este acceptabil/convertibil fara snapshot/review/owner approval.
5. **Warnings comerciale**: dry-run poate fi ready cu warnings. Pentru quote-ul auditului exista 8 warnings. Auto-write tacit ar ascunde deliberarea operatorului.
6. **Lipsa client_analysis_hash in Quotes detail**: runtime-ul arata ca `Trimite in ofertare` poate fi disabled cand contextul de analiza nu este disponibil; un flow din Intake V6 trebuie sa aduca explicit hash-ul corect.
7. **Product Truth gaps**: Pricing Registry/CPP nu repara Product Truth incomplet. Daca inputul nu e ready, write trebuie blocat.
8. **Snapshot provenance**: Snapshot V2 cere write provenance cu `frontend_preview_not_used=true` si `no_v4_v2_commercial_truth=true`; orice auto-write trebuie sa lase acelasi trace.

## 10. Variante comparate A/B/C/D/E

| Varianta | Descriere | Verdict |
| --- | --- | --- |
| A | Flow actual: Intake V6 creeaza draft nepretuit; in Quotes operatorul apasa `Scrie totaluri pe oferta`. | Functional si guard-uit, dar UX are un pas separat si mentine mental model-ul de draft nepretuit. |
| B | Auto-priced strict, fara actiune explicita: la completarea Intake V6, sistemul scrie automat quote priced. | Nerecomandat. Ar elimina confirmarea operatorului si ar slabi rolul expected total/hash ca bariera constienta. |
| C | Auto-write dar marcheaza quote-ul ca needing review/internal approval. | Partial acceptabil tehnic, dar tot risca write tacit. Review-ul de dupa nu inlocuieste confirmarea de dinaintea scrierii pretului oficial. |
| D | CTA explicit in Intake V6: `Creeaza oferta pretuita`, afiseaza dry-run backend, apoi apeleaza `handoff-to-offer` cu total/hash/confirmare. | Recomandat ca next safe product step. Elimina pasul separat din Quotes fara sa elimine guardurile. |
| E | Doua butoane in Intake V6: `Creeaza draft` si `Creeaza oferta pretuita`. | Recomandat daca owner vrea sa pastreze ambele moduri. Cel mai clar pentru rollout si training operator. |

## 11. Decizie recomandata

Recomandare: **D sau E, nu B.**

Formulare concreta:

```txt
Intake V6 poate trimite direct in Oferte cu pret inclus daca actiunea este explicita si foloseste backend-ul existent `handoff-to-offer`, nu daca sistemul scrie automat fara confirmare.
```

Decizia D este cea mai simpla daca owner vrea un singur flow principal: `Creeaza oferta pretuita`.

Decizia E este mai sigura operational daca inca avem nevoie de draft intern pentru review/audit/training: `Creeaza draft` ramane, iar `Creeaza oferta pretuita` devine flow-ul preferat cand dry-run este ready.

In ambele cazuri, QuoteWizard trebuie eliminat mental din V6: nu redenumim neaparat componenta generic legacy, dar V6 operator copy ar trebui sa vorbeasca despre `Flux comercial V6`, `dry-run backend`, `oferta pretuita`, `snapshot/review/approval`, nu despre QuoteWizard.

## 12. Next safe step

Micro-slice recomandat dupa GO owner:

1. In Intake V6 Review/Confirm, afiseaza dry-run backend oficial si blockers/warnings.
2. Adauga CTA explicit `Creeaza oferta pretuita` care trimite `client_analysis_hash`, `expected_total_gross`, `expected_pricing_hash`, `operator_confirmation=true` catre `POST /workspaces/{id}/handoff-to-offer`.
3. Pastreaza sau separa `Creeaza draft intern` conform deciziei D/E.
4. Dupa succes, navigheaza la `/quotes/{quote_code}`.
5. In Quotes, quote-ul trebuie sa apara `priced`, dar snapshot/review/approval/accept/convert raman gate-uri separate.
6. Adauga teste frontend pentru CTA si teste backend existente/targeted pentru handoff-to-offer; nu atinge CostEngine/Pricing Registry/Inventory.

## 13. Ce NU am modificat

- Nu am modificat UI.
- Nu am modificat copy runtime.
- Nu am redenumit QuoteWizard.
- Nu am schimbat pricing logic.
- Nu am schimbat statusuri.
- Nu am creat/scris quote totals.
- Nu am creat snapshot.
- Nu am completat pricing review.
- Nu am facut owner approval.
- Nu am acceptat oferta.
- Nu am convertit in order.
- Nu am schimbat DB schema sau seeds.
- Nu am atins ProductAggregate, Task Graph, ExecutionPlan, Inventory write sau Employee Mobile.

## 14. Comenzi si verificari

Citiri/audit static:

- `frontend/src/pages/Quotes.tsx`
- `frontend/src/components/workos/QuoteWizard.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6QuoteCommercialSpinePanel.tsx`
- `frontend/src/lib/intakeV6/intakeV6Api.ts`
- `frontend/src/lib/intakeV6/intakeV6QuoteDisplay.ts`
- `frontend/src/lib/intakeV6/intakeV6QuoteNotes.ts`
- `backend/routers/intake_v6_workspaces.py`
- `backend/services/intake_v6_commercial_quote_service.py`
- `backend/services/intake_v6_priced_quote_dry_run_service.py`
- `backend/services/intake_v6_priced_quote_write_service.py`
- `backend/services/intake_v6_offer_handoff_service.py`
- `backend/services/intake_v6_quote_snapshot_v2_service.py`
- `backend/services/intake_v6_internal_draft_quote_policy_service.py`
- `backend/services/intake_v6_material_breakdown_service.py`
- `backend/services/intake_v6_pricing_preview_sync_service.py`
- `backend/schemas/intake_v6.py`
- `docs/architecture/product-system/V6_PRICED_QUOTE_WRITE_PATH_DESIGN.md`
- `docs/qa/BUILD_INTAKE_V6_QUOTES_INTEGRATION.md`
- `backend/tests/test_intake_v6_priced_quote_write.py`
- `backend/tests/test_intake_v6_priced_quote_dry_run.py`
- `backend/tests/test_intake_v6_offer_handoff_service.py`
- `frontend/src/components/workos/intake-v6/IntakeV6QuoteCommercialSpinePanel.test.tsx`

Runtime read-only:

- browser route: `/quotes/Q-V6-IV6-1A59D22C-1783033637`
- GET `/api/v1/entities/quotes?search=Q-V6-IV6-1A59D22C-1783033637&limit=5`
- GET `/api/v1/intake-v6/workspaces/187e351c-0bde-448d-b764-58bf2456ae06/priced-quote-dry-run`
- GET `/api/v1/intake-v6/workspaces/187e351c-0bde-448d-b764-58bf2456ae06/commercial-spine-state`

Post-edit validation:

```powershell
git diff --check -- docs/worklog/realignment/2026-07-03_intake_v6_direct_priced_quote_audit.md
```
