# WorkOS - Audit de stare dupa remedieri runtime si cleanup Intake V6

## Executive verdict

- Verdict general: `PARTIAL PASS`
- Runtime local actual: `PASS`
- Flux comercial Intake -> Quote -> Order -> Execution: `PASS` cu observatii de modelare si cleanup
- Intake V6 ca workspace activ: `PASS`
- Cleanup semantic V6 versus mostenire V4: `PARTIAL`
- Coerenta currency EUR/RON: `PARTIAL PASS`
- Stabilitate structurala pe frontend: `PARTIAL`, din cauza unor resturi V4 active in suprafete V6 si a unor riscuri latente de runtime

Concluzia practica este directa: sistemul porneste, rutele principale raspund, build-ul frontend trece, testele tintite V6 trec, iar fluxul comercial principal functioneaza local. Totusi, cleanup-ul Intake V6 nu este terminat. Exista inca dependente reale de nomenclatura si prezentare V4 in cod V6, iar modelul de date pentru comenzi ramane mai sarac decat snapshot-ul comercial care il alimenteaza.

## Ce s-a rezolvat

- Frontend-ul a vorbit corect cu backend-ul local pe `127.0.0.1:8000` prin override-ul din `frontend/.env.local`.
- Nu s-a mai observat fallback runtime catre `8001`, desi fallback-ul vechi exista in continuare in `frontend/src/lib/config.ts`.
- White screen-ul mentionat anterior nu s-a reprodus pe rutele testate.
- Eroarea de tip import/export pentru `INTAKE_V4_DEFAULT_RETURN_DEPTH_MM` nu apare in starea curenta: simbolul exista in `frontend/src/lib/intakeV6/intakeV4LetterGroups.ts` si este consumat din `frontend/src/lib/intakeV6/intakeV6LetterGroups.ts`.
- Intake V6 operator workspace se incarca si expune suprafata activa de lucru, inclusiv upload-ul SVG, prin `frontend/src/pages/IntakeV6OperatorWorkspaceApp.tsx`.
- Fluxul Quote -> Order ramane conectat functional, inclusiv panel-ul comercial V6 si conversia dedicata din backend.
- Build-ul frontend a trecut.
- Testele tintite Intake V6 au trecut.
- Typecheck-ul aplicatiei frontend pe `tsconfig.app.json` a trecut in acest mediu.

## Ce ramane blocat sau incomplet

- Cleanup-ul semantic V6 nu este finalizat. Exista inca fisiere, tipuri, aliasuri, route helpers, test ids si suprafete de prezentare care poarta `V4` in interiorul fluxului V6.
- Exista risc runtime latent in cel putin trei componente V6 care refera `v4` in JSX fara import explicit detectat:
  - `frontend/src/components/workos/intake-v6/IntakeV6QuoteCommercialSpinePanel.tsx`
  - `frontend/src/components/workos/intake-v6/IntakeV6NestingPreviewPanel.tsx`
  - `frontend/src/components/workos/intake-v6/IntakeV6SheetFootprintOverridePanel.tsx`
- Modelul `Orders` nu are camp explicit de currency in tabelul principal, desi handoff-ul comercial conserva informatie de moneda si de rata in snapshot/handoff.
- Product Definition nu apare ca etapa persistata separata in fluxul operational; exista efectiv ca structura tranzitorie folosita la cotare si handoff, nu ca entitate operationala independenta.
- Repo-ul ramane cu debt structural cunoscut in afara tipcheck-ului aplicatiei frontend. Faptul ca `tsconfig.app.json` trece nu inseamna ca intreaga suprafata de validare a repo-ului este curata.
- Fallback-ul de dezvoltare din `frontend/src/lib/config.ts` ramane setat pe `8001`, ceea ce poate reintroduce confuzie sau regresii daca override-ul din env lipseste.

## Runtime smoke status

Status executat local, read-only, pe stack-ul curent:

- Backend health: `PASS`
  - raspuns sanatos pe `/health`
- Frontend root/dashboard: `PASS`
- Quotes: `PASS`
- Orders: `PASS`
- Execution: `PASS`
- Intake V6 operator: `PASS`
- Erori de consola observabile in smoke: `nu s-au reprodus`
- White screen: `nu s-a reprodus`
- Cereri runtime catre `8001`: `nu s-au observat`

Validari executabile confirmate in audit:

- `frontend`: `npm.cmd run build` -> `PASS`
- `frontend`: testele V6 tintite in Vitest -> `PASS`
- `frontend`: `npm.cmd exec -- tsc -p tsconfig.app.json --noEmit` -> `PASS`

Observatie importanta: acest rezultat confirma functionalitatea actuala locala, nu curata automat toate ramurile legacy sau toate caile rare de executie.

## Flow map

### 1. Intake

- Status: `PASS`
- Entry activ in shell: `frontend/src/App.tsx`
- Ruta activa dedicata V6 este `/intake-v6/operator` si este expusa explicit in navigatie.
- Wrapper-ul activ este `frontend/src/pages/IntakeV6OperatorWorkspaceApp.tsx`.
- Workspace-ul V6 foloseste `useIntakeV6Workspace(workspaceId)` si leaga importul SVG in UI.

### 2. Product Definition

- Status: `PARTIAL`
- Exista functional ca structura pentru quote/pricing, dar nu apare ca etapa de business persistata separat intre Intake si Quote.
- Practic, comportamentul este suficient pentru fluxul curent, dar modelarea domeniului ramane incompleta daca se doreste urmarire operationala explicita a acestei etape.

### 3. Quote

- Status: `PASS`
- Quotes este rutat activ din `frontend/src/App.tsx`.
- Pagina `frontend/src/pages/Quotes.tsx` foloseste date backend si logica de currency dedicata prin `frontend/src/lib/quoteCurrency.ts`.
- Exista suprafata comerciala V6 pentru quote-to-order in `frontend/src/components/workos/intake-v6/IntakeV6QuoteCommercialSpinePanel.tsx`.

### 4. Order

- Status: `PASS` cu observatii
- Conversia comerciala dedicata este implementata in backend prin `backend/services/order_currency_conversion_service.py`.
- Handoff-ul conserva total comercial EUR, total baza RON si rata EUR/RON atunci cand sursa este EUR.
- Observatia majora este modelul `backend/models/orders.py`, unde `Orders` nu are camp explicit de currency la nivelul tabelului principal.

### 5. Execution

- Status: `PASS`
- Rutele `/execution` si detaliile de execution au fost prezente si au raspuns in smoke.
- Fluxul operational exista end-to-end dupa Order, chiar daca auditul curent nu a validat in profunzime fiecare subproces intern de productie.

## Legacy / duplicate status

Verdict: `PARTIAL`, cu mostenire reala, nu doar zgomot nominal.

### Ce este clar activ si justificat acum

- `frontend/src/App.tsx` -> `KEEP_ACTIVE`
- `frontend/src/pages/IntakeV6OperatorWorkspaceApp.tsx` -> `KEEP_ACTIVE`
- `frontend/src/lib/quoteCurrency.ts` -> `KEEP_SHARED`
- `backend/services/order_currency_conversion_service.py` -> `KEEP_SHARED`

### Compatibilitate justificata

- `frontend/src/lib/intakeV6/intakeV4LetterGroups.ts` -> `KEEP_SHARED`
  - expune aliasul tranzitional `INTAKE_V4_DEFAULT_RETURN_DEPTH_MM`
- `frontend/src/lib/intakeV6/intakeV6LetterGroups.ts` -> `KEEP_ACTIVE`
  - foloseste aliasul de compatibilitate
- `frontend/src/lib/intakeV6/productionTaskDryRunContracts.ts` -> `BLOCKED_NEEDS_DECISION`
  - aliasarea V4->V6 poate fi acceptabila temporar, dar nu este cleanup final

### Legacy real referentiat activ

- `frontend/src/lib/intakeV6/intakeV4Api.ts` -> `LEGACY_REFERENCED`
- `frontend/src/lib/intakeV6/intakeV6WorkspaceReducer.ts` -> `LEGACY_REFERENCED`
- `frontend/src/lib/intakeV6/useTemplateFormContract.ts` -> `LEGACY_REFERENCED`
- `frontend/src/lib/intakeV6/intakeV4OperatorRoutes.ts` -> `LEGACY_REFERENCED`

Acestea nu sunt doar comentarii sau teste. Ele indica dependenta reala intre suprafata V6 si contracte, denumiri sau rute V4.

### Mock / test support / false positive

- Fisierele `*.test.tsx` si `*.test.ts` din `frontend/src/components/workos/intake-v6` si `frontend/src/lib/intakeV6` care mentioneaza `V4` in test ids sau descrieri -> `KEEP_TEST_SUPPORT`
- Comentarii de tipul "transitional compatibility alias" -> `compatibilitate justificata`, nu cleanup complet

### Duplicate sau overlapping

- `frontend/src/pages/WorkIntake.tsx`
- `frontend/src/pages/IntakeLegacyRoute.tsx`
- `frontend/src/pages/IntakeV6OperatorWorkspaceApp.tsx`

Setul de entrypoints de intake continua sa sugereze coexistenta mai multor generatii. Chiar daca V6 este entrypoint-ul activ dedicat, repo-ul nu comunica inca suficient de strict ce cale este canonica si care sunt doar supravietuiri de tranzitie.

### Delete candidate / blocked needs decision

- `frontend/src/lib/intakeV6/intakeV4OperatorRoutes.ts` -> `BLOCKED_NEEDS_DECISION`
- suprafetele V4 tinute exclusiv pentru compatibilitate tranzitorie -> `DELETE_CANDIDATE` doar dupa decuplarea completa a componentelor V6
- orice alias V4->V6 din contracte dry-run -> `BLOCKED_NEEDS_DECISION`

Nu este recomandata stergerea imediata in orb. Exista inca referinte reale active.

## Currency / EUR-RON audit

Verdict: `PARTIAL PASS`

### Ce este coerent

- Conversia comerciala dedicata Quote -> Order exista centralizat in `backend/services/order_currency_conversion_service.py`.
- Pentru `EUR -> RON`, serviciul:
  - valideaza rata `eur_to_ron_rate`
  - rotunjeste totalul comercial EUR la euro intreg pentru acceptare comerciala
  - calculeaza totalul de baza in RON
  - conserva si varianta bruta comerciala EUR
- Frontend-ul Quotes extrage currency-ul din snapshot in `frontend/src/lib/quoteCurrency.ts` si afiseaza valorile cu currency explicit.

### Ce ramane risc

- `backend/models/orders.py` retine `total_amount`, dar nu are camp explicit `currency` in modelul principal `Orders`.
- Asta inseamna ca afisarea sau raportarea ordinii poate deveni ambigua daca UI-ul nu citeste mereu sursa snapshot potrivita.
- Exista risc de inconsistente de prezentare intre:
  - totalul comercial de quote
  - totalul de baza de order
  - moneda afisata in liste sau tabele simplificate

### Raspunsuri scurte cerute

- EUR/RON coerent? `Da, in handoff-ul central Quote -> Order.`
- Exista RON neconvertit din EUR? `Nu s-a gasit o dovada clara de calcul nerealizat in handoff-ul central.`
- Exista preturi fara currency? `Da, exista risc de prezentare fara currency explicit, in special pe modelul/tabelul Orders.`
- Exista risc pe order snapshot? `Da, risc de pierdere sau ascundere a contextului monetar la suprafetele care citesc doar modelul simplificat Orders.`

## Top 10 probleme ramase

1. Componente V6 active refera `v4` fara import explicit detectat, ceea ce ramane risc runtime latent.
2. Cleanup-ul semantic V6 nu este terminat; contractele si reducer-ele folosesc inca aliasuri si tipuri V4.
3. `frontend/src/lib/config.ts` pastreaza fallback dev spre `8001`, desi runtime-ul curent bun este pe `8000`.
4. Modelul `Orders` nu are camp explicit de currency la nivel principal.
5. Exista coexistenta de entrypoints intake care ingreuneaza delimitarea canonica intre activ si legacy.
6. Product Definition nu este modelat ca etapa persistata separata, ceea ce lasa goluri de urmarire operationala.
7. V6 continua sa foloseasca route helpers si contracte denumite V4 in zone care nu mai par strict de compatibilitate pasiva.
8. Faptul ca smoke-ul trece nu elimina caile rare de executie unde mostenirea V4 poate reaprinde erori.
9. Repo-ul are in continuare debt structural mai larg decat `tsconfig.app.json`, chiar daca validarea aplicatiei trece local.
10. Suprafetele de Orders/raportare pot comunica insuficient contextul monetar daca citesc doar campurile simplificate.

## Plan de stabilizare pe faze

### Faza 1 - Eliminare riscuri runtime latente

- Corecteaza imediat cele trei componente V6 care folosesc `v4` fara import explicit detectat.
- Adauga o verificare tintita care sa esueze daca exista referinte `v4.` in componente V6 fara import.
- Normalizeaza fallback-ul de config frontend astfel incat portul de dezvoltare canonic sa fie un singur adevar operational.

### Faza 2 - Curatare de compatibilitate V4/V6

- Inventariaza toate aliasurile V4->V6 din `frontend/src/lib/intakeV6`.
- Marcheaza fiecare fisier drept:
  - `compatibilitate temporara necesara`
  - `poate fi redenumit acum`
  - `poate fi sters dupa decuplare`
- Redenumește progresiv contractele si helper-ele active V6 care nu mai depind logic de V4.

### Faza 3 - Intarire model comercial si currency

- Introdu currency explicit pe modelul Order sau pe view model-ul canonic folosit de liste si rapoarte.
- Verifica toate suprafetele de afisare Orders pentru a nu amesteca total comercial si total baza fara eticheta.
- Adauga teste de acceptare pentru quote EUR -> order RON, inclusiv snapshot si UI list views.

### Faza 4 - Clarificare operationala a fluxului

- Decide daca Product Definition devine sau nu etapa persistata oficial.
- Daca da, introdu identitate si trasabilitate separata.
- Daca nu, documenteaza explicit ca este doar structura tranzitorie pentru pricing si handoff.

### Faza 5 - Inchidere legacy entrypoints

- Stabileste entrypoint-ul canonic unic pentru intake.
- Marcheaza rutele legacy vizibil ca tranzitorii sau interne.
- Elimina treptat suprafetele duplicate dupa ce observabilitatea si testele confirma lipsa dependintelor.

## Ce nu trebuie facut acum

- Nu sterge in masa fisierele cu `V4` doar pe baza numelui.
- Nu presupune ca toate referintele `V4` sunt doar comentarii sau teste.
- Nu considera smoke-test-ul curent drept dovada ca tot cleanup-ul V6 este finalizat.
- Nu muta logica monetara in mai multe locuri; conversia trebuie sa ramana centralizata.
- Nu lasa `Orders` fara o decizie explicita despre currency daca fluxul comercial continua sa lucreze cu EUR si RON.

## Verdict final practic

Sistemul este utilizabil local si principalele remedieri runtime par efective. Problema care blocheaza cel mai mult stabilizarea nu mai este pornirea aplicatiei, ci faptul ca Intake V6 ruleaza inca pe o baza partial curatata, cu mostenire V4 activa in codul de productie. Asta nu rupe imediat fluxul principal, dar mentine risc de regresii si ambiguitati de model, mai ales in zona UI V6 si in zona currency/order representation.