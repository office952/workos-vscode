# 2026-07-03 Intake V6 Create Priced Quote CTA

## 1. Context

Owner decision: Intake V6 ramane entry point pentru V6. V6 nu trebuie sa foloseasca QuoteWizard ca mental model. QuoteWizard ramane temporar pentru generic/legacy.

Scop micro-slice: adaugare CTA explicit in pasul final Intake V6 pentru a crea o oferta pretuita folosind flow-ul backend V6 existent, fara auto-write tacit si fara QuoteWizard.

## 2. Decizie: fara QuoteWizard pentru V6

CTA nou: `Creeaza oferta pretuita`.

Copy asociat:

```txt
Scrie totalurile comerciale V6 pe oferta. Nu creeaza comanda, executie sau miscari de stoc.
```

Confirmare explicita operator:

```txt
Creez oferta pretuita folosind totalurile comerciale V6 calculate pe server. Aceasta actiune scrie preturile pe oferta, dar nu creeaza comanda, executie sau miscari de stoc.
```

Nu am folosit sau modificat QuoteWizard.

## 3. Endpoint/backend reutilizat

Endpoint reutilizat: `POST /api/v1/intake-v6/workspaces/{workspace_id}/handoff-to-offer`.

Nu am creat endpoint nou.

Audit scurt inainte de cod:

1. Exista endpoint single-step draft + priced? Da: `handoff-to-offer`.
2. `handoff-to-offer` scrie deja totalurile? Da. Creeaza/reutilizeaza draft V6, apoi apeleaza `write_intake_v6_priced_quote_totals`.
3. Payload cerut: `client_analysis_hash`, `expected_total_gross`, optional `expected_pricing_hash`, `operator_confirmation`.
4. Expected total/hash: vin din `priced-quote-dry-run`, respectiv `commercial_totals.total_gross` si `pricing_hash`.
5. Success returneaza: `status`, `quote_created`, `quote_id`, `quote_code`, `quote_status`, `commercial_totals`, `line_items`, `pricing_trace`, `warnings`, `blockers`, `can_create_quote_snapshot`, `next_route`.
6. Blockers/guards: dry-run blocked, zero/missing totals, expected total mismatch, expected hash mismatch, target not V6, workspace mismatch, already priced, snapshot exists, order exists, terminal/converted quote, missing operator confirmation, forbidden pricing source, missing line items, invalid notes.
7. Poate fi apelat din Intake V6 fara QuoteWizard? Da.
8. Daca exista draft quote: service-ul il poate reutiliza si scrie totalurile daca este eligibil.
9. Daca exista priced quote: write-ul blocheaza cu `V6_PRICED_QUOTE_WRITE_ALREADY_PRICED`.
10. Daca exista snapshot/order: write-ul blocheaza cu snapshot/order blockers; nu suprascrie.

## 4. Conditii de enable/disable

CTA-ul este enabled doar cand:

- exista workspace id;
- exista `clientAnalysisHash`;
- workspace-ul este ready pentru quote preview;
- handoff-ul V6 este permis;
- nu exista binding blockers/fatal blockers active;
- confirmarea operatorului este persistata;
- operatorul a bifat confirmarea interna si boundary-ul no order/execution/stock;
- `priced-quote-dry-run` este `V6_PRICED_DRY_RUN_READY`;
- `commercial_totals.total_gross` este disponibil;
- nu exista alta actiune de submit in curs;
- nu exista deja rezultat priced in sesiunea curenta.

Cand este disabled, UI afiseaza motiv real, de exemplu `Confirma explicit draftul intern.` sau mesajul din dry-run blocker.

## 5. Confirmare operator

Folosita confirmare browser `window.confirm`, pentru ca nu exista un dialog local dedicat in acest pas.

Mesajul confirma explicit:

- totalurile sunt calculate pe server;
- actiunea scrie preturile pe oferta;
- nu creeaza comanda;
- nu creeaza executie;
- nu creeaza miscari de stoc.

Nu contine `QuoteWizard`.

## 6. Fisiere modificate

| Path | Schimbare |
| --- | --- |
| `frontend/src/components/workos/intake-v6/steps/IntakeV6ConfirmStep.tsx` | Adaugat CTA priced quote, confirmare explicita, handoff-to-offer call, disabled reasons si success/error state. |
| `frontend/src/components/workos/intake-v6/IntakeV6ConfirmStep.test.tsx` | Adaugat mock-uri dry-run/handoff, reparat `workspaceState` in footer test harness, adaugat test pentru CTA priced quote. |

## 7. Teste rulate

Focused frontend:

```powershell
pnpm.cmd --dir frontend exec vitest run src/components/workos/intake-v6/IntakeV6ConfirmStep.test.tsx
```

Rezultat: `8 passed`.

Backend cerut:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v6_offer_handoff_service.py tests/test_intake_v6_priced_quote_write.py tests/test_intake_v6_priced_quote_dry_run.py tests/test_intake_v6_zero_quote_fast_guard.py -q
```

Rezultat: `28 passed, 6 failed`. Cele 6 fail-uri sunt in `tests/test_intake_v6_priced_quote_dry_run.py`, unde `FakeDb` nu are `get_bind` pentru `company_commercial_settings_service.get_eur_to_ron_rate`. Nu am modificat backend in acest slice.

Frontend typecheck:

```powershell
pnpm.cmd --dir frontend exec tsc --noEmit --pretty false
```

Rezultat: fara erori TypeScript; doar warning pnpm despre campul `pnpm` din `package.json`.

Diff check:

```powershell
git diff --check -- frontend/src/components/workos/intake-v6/steps/IntakeV6ConfirmStep.tsx frontend/src/components/workos/intake-v6/IntakeV6ConfirmStep.test.tsx
```

Rezultat: fara output.

## 8. Runtime verification

Workspace test folosit: `IV6-CA9DA36C`, id `aa8ed7b0-4712-4744-a4d3-0867a2d242e2`.

UI route:

```txt
http://127.0.0.1:3000/intake-v6/aa8ed7b0-4712-4744-a4d3-0867a2d242e2/operator
```

Verificari UI in Confirm:

- total server-side vizibil: `6.554,21 RON`;
- CTA vizibil: `Creeaza oferta pretuita`;
- subtext vizibil: nu creeaza comanda/executie/stoc;
- QuoteWizard absent din snapshot;
- buton disabled initial cu motiv real: `Confirma explicit draftul intern.`;
- dupa bifare confirmari, buton enabled;
- confirm dialog afisat si acceptat.

Dupa success, UI a navigat la:

```txt
http://127.0.0.1:3000/quotes/Q-V6-IV6-CA9DA36C-1783037396
```

Browser DOM check:

- quote nou prezent;
- status `Priced` prezent;
- total `6.554,21` prezent;
- `QuoteWizard` absent.

Console/network: nu au aparut 404/500 vizibile in runtime snapshot; pagina a ramas functionala dupa navigare.

## 9. Quote nou creat

Quote creat/verificat:

```txt
Q-V6-IV6-CA9DA36C-1783037396
```

Quote id: `18`.

## 10. Status quote

Status DB/API: `priced`.

## 11. Totaluri scrise

Read-only DB/API:

| Camp | Valoare |
| --- | ---: |
| subtotal | 5416.70 |
| total_before_vat | 5416.70 |
| vat | 1137.51 |
| grand_total | 6554.21 |
| line_item_count | 7 |
| first_line_unit_price | 25.00 |
| first_line_total | 524.32 |

## 12. Downstream flags

| Flag | Valoare |
| --- | --- |
| `quote_snapshot_created` | `false` |
| `order_created` | `false` |
| `snapshot_count` | `0` |
| `order_count` | `0` |
| `accepted_snapshot_v2_id` | `null` |

Nu am creat order, execution plan sau inventory mutation.

## 13. Console/network

Nu am observat 404/500 relevante in runtime browser snapshot dupa click si navigare. Verificarea principala a fost DOM + API + DB read-only.

## 14. Ce NU am modificat

- Nu am folosit QuoteWizard.
- Nu am sters QuoteWizard.
- Nu am modificat flow generic/manual QuoteWizard.
- Nu am modificat pricing formula.
- Nu am calculat pret in UI.
- Nu am modificat Cost Engine.
- Nu am modificat CommercialPriceProposal.
- Nu am modificat DB schema.
- Nu am facut seed sau migration.
- Nu am creat order.
- Nu am creat execution plan.
- Nu am mutat inventory.
- Nu am intrat in ProductAggregate, Task Graph, ExecutionPlan sau Employee Mobile.
- Nu am facut UI/UX mare.

## 15. Riscuri ramase

- `handoff-to-offer` pastreaza `human_summary` creat la draft. Dupa priced write, notes-ul nu contine QuoteWizard, dar textul de summary inca spune ca totalurile nu au fost inca scrise. Recomand micro-slice separat pentru copy post-write daca owner vrea ca human summary sa reflecte statusul priced.
- Backend subset cerut are 6 fail-uri preexistente/probabil independente in dry-run tests din cauza `FakeDb.get_bind` lipsa pentru setari comerciale.

## 16. Next safe step

Micro-slice recomandat: actualizare non-breaking in `write_intake_v6_priced_quote_totals` pentru `notes.human_summary` post-priced, plus test care confirma ca priced quote notes spun ca totalurile au fost scrise si nu mentioneaza QuoteWizard.
